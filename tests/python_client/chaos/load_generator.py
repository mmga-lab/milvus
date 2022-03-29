import threading
from multiprocessing import Process
from time import time, sleep

from chaos.checker import (CreateChecker, InsertFlushChecker,
                           SearchChecker, QueryChecker, IndexChecker, Op)
from common import common_func as cf

# how to generate a checker with different scenarios
# we can configure the numbers of different Ops in a checker

class LoadUnit():
    def __init__(self,collection_name=None) -> None:
        self.collection_name = collection_name if collection_name \
                               else cf.gen_unique_str("Checker_")
        self.weights = {}
        self.init_checkers()

    def init_checkers(self):
        """init checkers"""
        weights = self.weights
        self.checkers = {
            Op.create: [CreateChecker() for _ in range(weights.get(Op.create, 0))],
            Op.insert: [InsertFlushChecker() for _ in range(weights.get(Op.insert, 0))],
            Op.flush: [InsertFlushChecker(flush=True) for _ in range(weights.get(Op.flush,0))],
            Op.index: [IndexChecker() for _ in range(weights.get(Op.index, 0))],
            Op.search: [SearchChecker() for _ in range(weights.get(Op.search, 0))],
            Op.query: [QueryChecker() for _ in range(weights.get(Op.query, 0))]             
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