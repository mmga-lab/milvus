import copy
from ast import Load
from gc import collect
import threading
from multiprocessing import Process

import pytest
import os
import time
import json
from time import sleep

from pymilvus import connections
from chaos.checker import (CreateChecker, InsertFlushChecker,
						   SearchChecker, QueryChecker, IndexChecker, Op)
from load_generator import LoadUnit, LoadGenerator
from common.cus_resource_opts import CustomResourceOperations as CusResource
from utils.util_log import test_log as log
from utils.util_k8s import wait_pods_ready, get_pod_list
from utils.util_common import findkeys
from chaos import chaos_commons as cc
from common.common_type import CaseLabel
from chaos import constants
from delayed_assert import expect, assert_expectations


def assert_statistic(checkers, expectations={}):
	for k in checkers.keys():
		# expect succ if no expectations
		succ_rate = checkers[k].succ_rate()
		total = checkers[k].total()
		average_time = checkers[k].average_time
		if expectations.get(k, '') == constants.FAIL:
			log.info(f"Expect Fail: {str(k)} succ rate {succ_rate}, total: {total}, average time: {average_time:.4f}")
			expect(succ_rate < 0.49 or total < 2,
				   f"Expect Fail: {str(k)} succ rate {succ_rate}, total: {total}, average time: {average_time:.4f}")
		else:
			log.info(f"Expect Succ: {str(k)} succ rate {succ_rate}, total: {total}, average time: {average_time:.4f}")
			expect(succ_rate > 0.90 or total > 2,
				   f"Expect Succ: {str(k)} succ rate {succ_rate}, total: {total}, average time: {average_time:.4f}")


def check_cluster_nodes(chaos_config):
	# if all pods will be effected, the expect is all fail.
	# Even though the replicas is greater than 1, it can not provide HA, so cluster_nodes is set as 1 for this situation.
	if "all" in chaos_config["metadata"]["name"]:
		return 1

	selector = findkeys(chaos_config, "selector")
	selector = list(selector)
	log.info(f"chaos target selector: {selector}")
	# assert len(selector) == 1
	selector = selector[0]  # chaos yaml file must place the effected pod selector in the first position
	namespace = selector["namespaces"][0]
	labels_dict = selector["labelSelectors"]
	labels_list = []
	for k, v in labels_dict.items():
		labels_list.append(k + "=" + v)
	labels_str = ",".join(labels_list)
	pods = get_pod_list(namespace, labels_str)
	return len(pods)


def record_results(checkers):
	res = ""
	for k in checkers.keys():
		check_result = checkers[k].check_result()
		res += f"{str(k):10} {check_result}\n"
	return res


class TestChaosBase:
	expect_create = constants.SUCC
	expect_insert = constants.SUCC
	expect_flush = constants.SUCC
	expect_index = constants.SUCC
	expect_search = constants.SUCC
	expect_query = constants.SUCC
	host = '127.0.0.1'
	port = 19530
	_chaos_config = None
	health_checkers = {}

	def parser_testcase_config(self, chaos_yaml, chaos_config):
		cluster_nodes = check_cluster_nodes(chaos_config)
		tests_yaml = constants.TESTS_CONFIG_LOCATION + 'testcases.yaml'
		tests_config = cc.gen_experiment_config(tests_yaml)
		test_collections = tests_config.get('Collections', None)
		for t in test_collections:
			test_chaos = t.get('testcase', {}).get('chaos', {})
			if test_chaos in chaos_yaml:
				expects = t.get('testcase', {}).get('expectation', {}).get('cluster_1_node', {})
				# for the cluster_n_node
				if cluster_nodes > 1:
					expects = t.get('testcase', {}).get('expectation', {}).get('cluster_n_node', {})
				log.info(f"yaml.expects: {expects}")
				self.expect_create = expects.get(Op.create.value, constants.SUCC)
				self.expect_insert = expects.get(Op.insert.value, constants.SUCC)
				self.expect_flush = expects.get(Op.flush.value, constants.SUCC)
				self.expect_index = expects.get(Op.index.value, constants.SUCC)
				self.expect_search = expects.get(Op.search.value, constants.SUCC)
				self.expect_query = expects.get(Op.query.value, constants.SUCC)
				log.info(f"self.expects: create:{self.expect_create}, insert:{self.expect_insert}, "
						 f"flush:{self.expect_flush}, index:{self.expect_index}, "
						 f"search:{self.expect_search}, query:{self.expect_query}")
				return True

		return False


class TestChaos(TestChaosBase):

	@pytest.fixture(scope="function", autouse=True)
	def connection(self, host, port):
		connections.add_connection(default={"host": host, "port": port})
		connections.connect(alias='default')

		if connections.has_connection("default") is False:
			raise Exception("no connections")
		self.host = host
		self.port = port

	# @pytest.fixture(scope="function", autouse=True)
	# def init_health_checkers(self):
	#     checkers = {
	#         Op.create: CreateChecker(),
	#         Op.insert: InsertFlushChecker(),
	#         Op.flush: InsertFlushChecker(flush=True),
	#         Op.index: IndexChecker(),
	#         Op.search: SearchChecker(),
	#         Op.query: QueryChecker()
	#     }
	#     self.health_checkers = checkers

	# def teardown(self):
	#     chaos_res = CusResource(kind=self._chaos_config['kind'],
	#                             group=constants.CHAOS_GROUP,
	#                             version=constants.CHAOS_VERSION,
	#                             namespace=constants.CHAOS_NAMESPACE)
	#     meta_name = self._chaos_config.get('metadata', None).get('name', None)
	#     chaos_res.delete(meta_name, raise_ex=False)
	#     sleep(2)
	#     log.info(f'Alive threads: {threading.enumerate()}')

	@pytest.mark.tags(CaseLabel.L3)
	def test_chaos(self):
		# start the monitor threads to check the milvus ops
		log.info("*********************Chaos Test Start**********************")
		log.info(connections.get_connection_addr('default'))

		def task_exector(weights):
			lu = LoadUnit(weights=weights)
			lu.start_monitor_threads()

		weights = {
			# Op.create: 1,
			# Op.insert: 1,
			# Op.flush: 1,
			# Op.delete: 1,
			# Op.index: 1,
			# Op.search: 1,
			# Op.query: 1,
			# Op.compact: 1,
			Op.loadbalance: 1,
			# Op.drop: 1
		}
		weights_list = [
			{
				"insert": 1,
				"flush": 1
			},
			{
				"search": 1,
				"insert": 1
			}
		]
		# weights = {
		# 		"insert": 1,
		# 		"flush": 1
		# 	}

		# task_exector(weights)

		# task_exector(weights)
		print("#########")
		lu = LoadUnit(weights=weights)
		lu.start_monitor_threads()
		sleep(600)
		# lu.terminate_monitor_threads()

		#
		p_list = []
		check_list = [
			{
				# Op.create: 1,
				Op.insert: 1,
				# Op.flush: 1,
				# # Op.index: 1,
				# Op.search: 1,
				Op.query: 1
			},
			{
				# Op.create: 1,
				Op.insert: 1,
				# Op.flush: 1,
				# Op.index: 1,
				Op.search: 1,
				# Op.query: 1
			}
		]
		# def task_2(weights):
		# 	while True:
		# 		print(f"{os.getpid()} task 2 weights: {weights}")
		# 		sleep(5)
		# for weights in weights_list:
		# 	task_exector(weights)
		# 	print("1111111111")
		# # task_exector(weights_list[0])
		# sleep(600)
		# lg = LoadGenerator()
		# lg.start_load_generator(weights_list=check_list)

		# sleep(600)

	# cc.start_monitor_threads(self.health_checkers)
