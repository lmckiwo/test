from status import Hosts, Vendors
import parameters
import json
import logging
import logger_setup
import argparse

logger = logging.getLogger('ATIC.createStatus')


class StatusFile():
    def __init__(self, hostFile="hosts.json", vendorFile="vendorNodes.json"):
        self.h      = Hosts(hostFile)
        self.v      = Vendors(vendorFile)
        self.status = {}
        self.h._setDefault()

    def createStatusFile(self):
        for host in self.h.getHosts():

            # building up hosts parameters
            config = {}
            for param in parameters.hostParams:
                config[param] = self.h.hosts.get(host).get("config").get(param, "")
            self.status[host] = {"config" : config}

            # # building cn node params
            # config_cn = {}
            # for param in parameters.nodeParams:
            #     config_cn[param] = ""

            # config_vendor = {}
            # for param in parameters.nodeVendorParams:
            #     config_vendor[param] = ""

            _node= {}
            for node in self.h.getNodes(host):
                config = {}
                if self.h.getNodeParamValue(host, node, "vendor") == "cn":
                    for param in parameters.nodeParams:
                        logger.debug("checking for CN parameter for car " + host + " node " + node + " param " + param)
                        logger.debug("hosts value is " + self.h.hosts[host]["nodes"][node].get(param, "NOT FOUND."))
                        config[param] = self.h.hosts.get(host).get("nodes").get(node).get(param, "")
                else:
                    for param in parameters.nodeVendorParams:
                        logger.debug("checking for Vendor parameter for car " + host + " node " + node + " param " + param)
                        logger.debug("hosts value is " + self.h.hosts[host]["nodes"][node].get(param, "NOT FOUND."))
                        config[param] = self.h.hosts.get(host).get("nodes").get(node).get(param, "")
                _node[node] = config

            self.status[host]["nodes"] = _node

        logger.info ("generating status file")



            #     if self.h.getNodeParamValue(host, node, "vendor") == "cn":
            #         if self.h.getNodeParamValue(host, node, "active") == "true":
            #             config_cn["active"] = "true"
            #         else:
            #             config_cn["active"] = ""
            #         _node[node] = config_cn
            #     else:
            #         if self.h.getNodeParamValue(host, node, "active") == "true":
            #             config_vendor["active"] = "true"
            #         else:
            #             config_vendor["active"] = ""

            #         _node[node] = config_vendor
            # self.status[host]["nodes"] = _node

    def writeConfig(self, outputFile="status.json"):
        with open(outputFile, "w") as outfile:
            json.dump(self.status, outfile, indent=4)

        logger.info("status file: " + outputFile + " created.")


def main(hostFile, vendorFile, statusFile):
    a = StatusFile(hostFile=hostFile, vendorFile=vendorFile)
    a.createStatusFile()
    a.writeConfig(outputFile=statusFile)

    b = Hosts(hostFile)
    logger.info (b.getHosts())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hostFile", default="hosts.json", help="specify host file")
    parser.add_argument("--vendorFile", default="vendorNodes.json", help="specify vendor file")
    parser.add_argument("--statusFile", default="status.json", help="specify status file")
    args = parser.parse_args()

    print ("hostFile:", args.hostFile)
    print ("vendorFile:", args.vendorFile)
    print ("statusFile:", args.statusFile)

    main(args.hostFile, args.vendorFile, args.statusFile)