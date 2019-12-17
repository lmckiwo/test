from ATICHosts import ATICHosts
from time import sleep

import logging
import logger_setup
from os import path, remove
from sys import exit
from time import sleep

#import multiprocessing as mp

mod_name = 'ATIC'
logger = logging.getLogger(mod_name)

#lock = mp.Lock()
#hosts = ATICHosts(statusFile = "status.json", hostFile="hosts2.json", lock=lock)
hosts = ATICHosts(statusFile = "status.json", hostFile="hosts.json")

seconds = 120

remoteDir = "/cygdrive/z/CB956001_PTC Program/09 Systems - Projects/ATIP Autonomous Track Inspection Program/Tools/alive-version3.3"

while True:
    if path.isfile(remoteDir + "/stop"):
        exit(0)

#    processes = []
#    for car in hosts.getHosts():
#        processes.append(
#            mp.Process(target=hosts.updateCarStatus, args=(car,))
#        )
#
#    for p in processes:
#        p.start()
#
#    for p in processes:
#        p.join()

    for car in hosts.getHosts():
        hosts.updateCarStatus(car)

    logger.info("Sleeping for " + str(seconds) + " seconds")
    if path.isfile(remoteDir + "/reload"):
        logger.info("reload file detected")
        remove(remoteDir + "/reload")
        exit(0)
    sleep(seconds)
