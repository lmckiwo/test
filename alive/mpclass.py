from time import sleep
from random import seed, randint
from ATICHosts import ATICHosts
import logging
import logger_setup

mod_name = 'ATIC'
logger = logging.getLogger(mod_name)

seed(3)
class status:
	def __init__(self, d):
		self.status = d

	def writeStatus(self, param, value):
		self.status[param] = value

	def readStatus(self, param):
		return self.status[param]

class mp:
	def __init__(self, d):
		self.a = "hello "
		self.b = ATICHosts(hostFile="hosts_test.json")
		self.s = status(d)


	def run(self, num):

		ran = randint(0,10)
		sleep(ran)
		print (self.a, num, ran)
		self.s.writeStatus(num, ran)

	def connect(self, car, node):
		self.writeStatus(car, node)
		print(car, node, self.b._connect(car, node), self.b.getHostIP(car))
		print (self.printStatus())

	def printStatus(self):
		print (self.s.status)

	def readStatus(self, param):
		return self.s.readStatus(param)

	def writeStatus(self, param, value):
		self.s.writeStatus(param, value)
