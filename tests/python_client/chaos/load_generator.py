import threading
from multiprocessing import Process
from time import time, sleep

from chaos.checker import (CreateChecker, InsertFlushChecker,
                           SearchChecker, QueryChecker, IndexChecker, Op)
from common import common_func as cf

# how to generate a checker with different scenarios
# we can configure the numbers of different Ops in a checker

class LoadUnit():

    # 这个类主要是对一个collection进行多线程的操作，比如创建，插入，查询，索引，删除等
    def __init__(self,collection_name=None, weights={}) -> None:
        if collection_name is not None:
            self.collection_name = collection_name
        else:
            self.collection_name = cf.gen_unique_str("Checker_")

        self.weights = weights
        self.update_checkers()

    def update_checkers(self,weights=None):
        """init checkers"""
        if weights is not None:
            self.weights = weights
        self.checkers = {
            Op.create: [CreateChecker(collection_name=self.collection_name) for _ in range(self.weights.get(Op.create, 0))],
            Op.insert: [InsertFlushChecker(collection_name=self.collection_name) for _ in range(self.weights.get(Op.insert, 0))],
            Op.flush: [InsertFlushChecker(collection_name=self.collection_name, flush=True) for _ in range(self.weights.get(Op.flush,0))],
            Op.index: [IndexChecker(collection_name=self.collection_name) for _ in range(self.weights.get(Op.index, 0))],
            Op.search: [SearchChecker(collection_name=self.collection_name) for _ in range(self.weights.get(Op.search, 0))],
            Op.query: [QueryChecker(collection_name=self.collection_name) for _ in range(self.weights.get(Op.query, 0))]             
        }

    def start_monitor_threads(self):
        """start the threads by checkers"""
        for k, checkers in self.checkers.items():
            for i, ch in enumerate(checkers):
                t = threading.Thread(target=ch.keep_running, args=(), name=f"{k}-{i}", daemon=True)
                t.start()

    def update_monitor_threads(self, weights):
        """update checker"""
        self.termnation_monitor_threads()
        self.weights = weights
        self.init_checkers()
        self.start_monitor_threads()
    
    def termnation_monitor_threads(self):
        """start the threads by checkers"""
        for k, checkers in self.checkers.items():
            for ch in checkers:
                ch.terminate()




class LoadGenerator():

    # 这个类主要是为了对多个collection进行操作，每个collection通过loadunit来进行操作
    # 所以这个类是一个更宏观层面的类，我们的输入主要是collection的数量
    # 这个类用于描述生成多大的压力，例如可以创建多少个collection，每个collection有多少个操作
    def __init__(self,process_num) -> None:
        self.process_num = process_num
        self.scenes = {} # 







def task(collection_name):
    """
    generate a load unit
    """
    load_unit = LoadUnit(collection_name)
    load_unit.start_monitor_threads()
    return load_unit

if __name__ == "__main__":
    p_list = []
    for i in range(2):
        collection_name = cf.gen_unique_str()
        p = Process(target=task, args=(collection_name,))
        p_list.append(p)
        p.start()

    sleep(300)
    for p in p_list:
        p.terminate()
        p.join()
        p.close()