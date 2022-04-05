import copy
import threading
from multiprocessing import Process
from time import sleep


class Task():
	def __init__(self,name):
		self.name = name

	def keep_running(self):

		while True:
			print(f"task name: {self.name}\n")
			sleep(5)


class LoadUnit():

	def __init__(self, task_ids):
		self.task_ids = task_ids
		self.update_task_list()

	def update_task_list(self):
		self.task_list = [Task(id) for id in self.task_ids]

	def start_thread(self):
		print(self.task_list)
		for task in self.task_list:
			print(task)
			t = threading.Thread(target=task.keep_running, args=())
			t.start()
			t.join()


def task_excutor(t_ids):
	lu = LoadUnit(t_ids)
	lu.start_thread()


if __name__ == '__main__':

	# def task_excutor(t_ids):
	# 	lu = LoadUnit(t_ids)
	# 	lu.start_thread()

	# task_ids = ("a", "b", "c")
	# task_excutor(task_ids)
	# sleep(300)

	task_ids_list = [
		("a-1", "b-1"),
		("a-2", "b-2"),
	]
	p_list = []
	for task_ids in task_ids_list:
		task_ids_copy = copy.deepcopy(task_ids)
		p = Process(target=task_excutor, args=(task_ids_copy,))
		print("process start")
		p_list.append(p)
		p.start()
	sleep(300)




