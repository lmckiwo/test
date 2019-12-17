import json
import logging
from status import Status

mod_name = 'ATIC.' + __name__
mod_logger = logging.getLogger(mod_name)

class statusHandler:
    def __init__(self, statusFile='status.json', logFile="alive.log"):
        self.logger = logging.getLogger(mod_name + ".1")
        self.statusFile = statusFile
        # with open (statusFile, 'r') as statusfile:
        #     self.status = json.load(statusfile)

        self.stat = Status(statusFile)

        #### CONST ###
        self.UNDEF = "UNDEF"

    def _refresh(self):
        # with open(self.statusFile, 'r') as outfile:
        #     self.stat.status = json.load(outfile)
        self.stat._readJson(self.statusFile)

    def readStatus(self, car, node, param):
        # if param in self.stat.status[car]["nodes"][node].keys():
        if param in self.stat.getNodeParams(car, node):
        # if param in self.stat.getNodeParams(car, node):
            self._refresh()
            self.logger.debug("status of [" + car + "][" + node + "][" + param + "] is " + self.stat.status[car]["nodes"][node][param])
            # return self.stat.status[car]["nodes"][node][param]
            return self.stat.getNodeParamValue(car, node, param)
        else:
            self.logger.debug("status of [" + car + "][" + node + "][" + param + "] is " + self.UNDEF)
            return self.UNDEF

    def writeStatus(self, car, node, param, status):
        # if node in self.stat.status[car]["nodes"].keys():  # verify if node exist
        self.logger.debug("params passed: " + car + " " + node + " " + param + " " + status)
        if node in self.stat.getNodes(car):
            #self.logger.debug ("param is " + param + " for " , self.stat.status[car]["nodes"][node])
            self.logger.debug ("param is " + param + " for " + node)
            # if param in self.stat.status[car]["nodes"][node].keys():  # verify if the parameter exists
            if param in self.stat.getNodeParams(car, node):
                self.logger.debug("self.stat.status[" + car + "][" + node + "] is good")
                # if self.stat.status[car]["nodes"][node][param] != status:  # update the status if the status is different.
                if self.stat.getNodeParamValue(car, node, param) != status:
                    self.logger.info("Updating " + car + "-" + node + " from " + self.stat.status[car]["nodes"][node][param] + " => " + status)
                    self.stat.status[car]["nodes"][node][param] = status
                    with open (self.statusFile, 'w') as outfile:
                        json.dump(self.stat.status, outfile, indent=4)

                return True
            else:
                return False
        else:
            return False

