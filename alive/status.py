import json
from collections import OrderedDict
from sys import exit
import logging

mod_name = 'ATIC.' + __name__
mod_logger = logging.getLogger(mod_name)


class readJson(object):
    def __init__(self, dataFile):
        self.logger = logging.getLogger(mod_name + ".readJson")
        self.data = self._readJson(dataFile)
        self.dataFile = dataFile

    def _readJson(self, jsonFile):
        try:
            with open(jsonFile, "r") as s:
                return json.load(s, object_pairs_hook=OrderedDict)
        except FileNotFoundError:
                self.logger.error("File " + jsonFile + " not found.")
                exit(1)

    def getKeys(self, data, exclude=None):
        if isinstance(data, dict):
            return [x for x in data.keys() if x != exclude]
        else:
            self.logger.debug("Nothing is returned")
            return []

    def safeGet(self, element, *keys):
        """
        Check if *keys (nested) exists in `element` (dict).
        """
        if not isinstance(element, dict):
            raise AttributeError('safeGet() expects dict as first argument.')

        if len(keys) == 0:
            raise AttributeError('safeGet() expects at least two arguments, ' +
                                 ' one given.')

        _element = element
        for key in keys:
            try:
                _element = _element[key]
            except KeyError:
                self.logger.info("Nothing is returned")
                return ""
        return _element

    def read(self):
        try:
           self.data = self._readJson(self.dataFile)
           return True
        except:
            return False

    def write(self):
        try:
            with open (self.dataFile, 'w') as outfile:
                json.dump(self.data, outfile, indent=4)
            return True
        except:
            return False


class Hosts(readJson):
    def __init__(self, hostFile="hosts.json"):
        self.logger = logging.getLogger(mod_name + ".Hosts")
        readJson.__init__(self, hostFile)
        self.hosts = self.data

        # class constants
        self.default         = "default"
        self.configParamType = "config"
        self.nodeParamType   = "nodes"

        # self.setConfigDefault()
        # self.setNodeDefault()


    def _setDefault(self):
        self.setConfigDefault()
        self.setNodeDefault()

    def getHosts(self):
        return self.getKeys(self.hosts, self.default)

    def getConfigParams(self, host):
        """ Returns the list of parameters available for a given host """

        return self.safeGet(self.hosts, host, self.configParamType).keys()

    def getNodes(self, host):
        """ Returns the list of nodes for a given host """
        if self.safeGet(self.hosts, host, self.nodeParamType):
            return self.safeGet(self.hosts, host, self.nodeParamType).keys()
        else:
            return ""

    def getConfigValue(self, host, param):
        """ Returns the value of the parameter for a given host. """
        return self.safeGet(self.hosts, host, self.configParamType, param)

    def getNodeParams(self, host, node):
        """ Returns the list of parameter for a given node and host """
        if self.safeGet(self.hosts, host, self.nodeParamType, node):
            return self.safeGet(self.hosts, host, self.nodeParamType, node).keys()
        else:
            return ""

    def getNodeParamValue(self, host, node, param):
        """ Returns the value of a given parameter for a given node for a
            given Host """
        return self.safeGet(self.hosts, host, self.nodeParamType, node, param)

    def getHostIP(self, host, apn="host-us"):
        return self.safeGet(self.hosts, host, self.configParamType, apn)

    def getHostNodePort(self, host, node):
        return self.safeGet(self.hosts, host, self.nodeParamType, node, "port")

    def setHostConfigParamValue(self, car, param, value, writeFile=False):
        """ This method will update the dictionary of the parameter in config
            section of data """

        self.hosts[car][self.configParamType][param]=value
        if writeFile:
            self.write()


    def setHostNodeParamValue(self, car, node, param, value, writeFile=False):
        self.hosts[car][self.nodeParamType][node][param]=value
        if writeFile:
            self.write()

    def setConfigDefault(self):
        for host in self.getHosts():
            for param in self.getConfigParams('default'):
                if param not in self.getConfigParams(host):
                    self.setHostConfigParamValue(host, param, self.getConfigValue('default', param))

    def setNodeDefault(self):
        for dNode in self.getNodes('default'):
            for host in self.getHosts():
                if dNode in self.getNodes(host):
                    for param in self.getNodeParams('default', dNode):
                        if param not in self.getNodeParams(host, dNode):
                            self.setHostNodeParamValue(host, dNode, param, self.getNodeParamValue('default', dNode, param))

    def isNodeActive(self, host, node):
        if self.getNodeParamValue(host, node, "active").lower() == "true":
            return True
        else:
            return False

    def isHostActive(self, host):
        if self.getConfigValue(host, "active").lower() == "true":
            return True
        else:
            return False

    def getVendorName(self, host, node):
        return self.getNodeParamValue(host, node, "vendor").upper()
    
class Vendors(readJson):
    def __init__(self, vendorFile="vendorNodes.json"):
        self.logger = logging.getLogger(mod_name + ".Vendors")

        readJson.__init__(self, vendorFile)
        self.vendors = self.data

        # class constants
        self.nodeParamType = "nodes"
        self.default       = "default"

    def getVendors(self):
        return self.getKeys(self.vendors)


    def getVendorNodes(self, vendor):
        return self.safeGet(self.vendors, vendor, self.nodeParamType).keys()

    def getVendorNodeIP(self, node, vendor):
        if self.isVendorExists(vendor):
            if self.isVendorNodeExists(vendor=vendor, node=node):
                return self.safeGet(self.vendors, vendor, self.nodeParamType, node)
            else:
                return ""
        return ""


    def isVendorExists(self, vendor):
        """This method checks to make see if the Vendor specified exists in
           json file. """

        if vendor in self.getVendors():
            return True
        else:
            return False

    def isVendorNodeExists(self, vendor, node):
        """ This method checks to make see if the node exist for Vendor specified
           json file.

           It will also check to make sure the vendor specified exists
        """
        if self.isVendorExists(vendor):
            if node in self.getVendorNodes(vendor):
                self.logger.debug(vendor + "[" + node + "] exists")
                return True
            else:
                self.logger.debug(vendor + "[" + node + "] does not exist")
                return False
        else:
            return False


class Status(Hosts):
    def __init__(self, statusFile="status.json"):
        self.logger = logging.getLogger(mod_name + ".Status")

        Hosts.__init__(self, statusFile)
        self.status = self.data
        self.statusFile = statusFile

        # class constants
        self.default         = "default"
        self.configParamType = "config"
        self.nodeParamType   = "nodes"

    def setNodeParamValue(self, car, node, param, value):
        if self.safeGet(self.status, car, self.nodeParamType, node, param):
            self.status[car][self.nodeParamType][node][param]=value
            self.write()
            return True
        else:
            return False
