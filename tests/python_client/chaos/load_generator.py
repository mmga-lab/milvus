import threading
from chaos.checker import (CreateChecker, InsertFlushChecker,
                           SearchChecker, QueryChecker, IndexChecker, Op)



class LoadGenerator():
    def __init__(self, checkers={}) -> None:
        self.checkers = checkers
        pass

    def start_monitor_threads(self):
        """start the threads by checkers"""
        for k, v in self.checkers.items():
            ch, cnt = v[0], v[1]
            for i in range(cnt):
                t = threading.Thread(target=ch.keep_running, args=(), name=k, daemon=True)
                t.start()

    def update_monitor_threads(self, checkers={}):
        """update checker"""
        self.termnation_monitor_threads()
        self.checkers = checkers
    
    def termnation_monitor_threads(self):
        """start the threads by checkers"""
        for k, ch in self.checkers.items():
            ch.terminate()