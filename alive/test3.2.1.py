from ATICHosts import ATICHosts
from time import sleep
import json

import logging
import logger_setup
from os import path, remove
from sys import exit
from time import sleep
import multiprocessing

mod_name = 'ATIC'
logger = logging.getLogger(mod_name)

#lock = mp.Lock()
#hosts = ATICHosts(statusFile = "status.json", hostFile="hosts2.json", lock=lock)

seconds = 120

remoteDir = "/cygdrive/z/CB956001_PTC Program/09 Systems - Projects/ATIP Autonomous Track Inspection Program/Tools/alive-version3.3"


class mp:
    def __init__(self, status, remote):
        self.b = ATICHosts(status=status, remote=remote)
        self.remote = remote
        self.status = status

    def connect(self, car):
        #self.b._connect(car, node)

        self.b.updateCarStatus(car)


if __name__ == '__main__':
    jobs = []

    # lock = multiprocessing.Lock()
    manager = multiprocessing.Manager()
    status = manager.dict()
    remote = manager.dict()
    remote = {}

    hosts = ATICHosts(status=status, remote=remote, statusFile = "status.json", hostFile="hosts2.json")

    nodes = [ (c, n) for c in hosts.getHosts() for n in hosts.getNodes(c) ]

    a = mp(status, remote)

    #for i in hosts.getHosts():
    # for i in ['ATIC-005', 'ATIC-006', 'ATIC-007', 'ATIC-008']:
    for i in ['ATIC-005']:
        p = multiprocessing.Process(target=a.connect, args=(i,))
        jobs.append(p)

    for p in jobs:
        p.start()

    for p in jobs:
        p.join()
        print (p, "has returned")

    print (status)
    with open ("status.json", 'w') as outfile:
        json.dump(status.copy(), outfile, indent=4)
# while True:
#     if path.isfile(remoteDir + "/stop"):
#         exit(0)

# #    processes = []
# #    for car in hosts.getHosts():
# #        processes.append(
# #            mp.Process(target=hosts.updateCarStatus, args=(car,))
# #        )
# #
# #    for p in processes:
# #        p.start()
# #
# #    for p in processes:
# #        p.join()

#     for car in hosts.getHosts():
#         hosts.updateCarStatus(car)

#     logger.info("Sleeping for " + str(seconds) + " seconds")
#     if path.isfile(remoteDir + "/reload"):
#         logger.info("reload file detected")
#         remove(remoteDir + "/reload")
#         exit(0)
#     sleep(seconds)
