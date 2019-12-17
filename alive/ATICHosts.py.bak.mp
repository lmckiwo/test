from paramikoWrapper import paramikoWrapper
# from statusHandler import statusHandler
from collections import OrderedDict
from status import Hosts, Vendors, Status
import json
import socket
import subprocess, os
import logging
from time import sleep
import threading
import multiprocessing as mp


mod_name = 'ATIC.ATICHosts'
logger = logging.getLogger(mod_name)

VERSION = "4.0"

maxThread = 35

class ATICHosts(Hosts, Vendors):
    def __init__(self, hostFile="hosts.json", statusFile="status.json", vendorFile="vendorNodes.json"):
        self.manager = mp.Manager()
        self.mgrstatus = self.manager.dict()
        self.mgrremote = self.manager.dict()

        self.logger = logging.getLogger(mod_name + ".1")
        self.__version__ = VERSION
        Hosts.__init__(self, hostFile)
        Vendors.__init__(self, vendorFile)
        Status.__init__(self, statusFile)
        self.hostFile   = hostFile
        self.statusFile = statusFile
        self.remote={}
        # self.vendor=self._readJson(vendorFile)
        # self.status = statusHandler(self.mgrstatus, self.statusFile)
        # self.status = Status(self.statusFile)
        # status = self.status.stat.data


        # print ('atichosts',self.status.data['ATIC-006'])

        # constants
        self.defaultConn  = "host-us"
        self.CONNECTED    = "connected"
        self.NOTCONNECTED = "notConnected"
        self.ALIVE        = "online"
        self.DEAD         = "offline"
        self.UNKNOWN      = "UNK"
        self.OK           = "OK"
        self.NOK          = "NOK"

        self.NoSSH        = "NoSSH"
        self.noOutput     = "NoOutput"

        self._setDefault()

    def connect1(self):
        print ("connect to atic-005[wcm]")
        self._connect('ATIC-006', 'SMM', updateStatus=True)
        self._connect('ATIC-006', 'WCM', updateStatus=True)

    def _getVersion(self):
        return self.__version__

    def _getRemoteIndex(self, car, node):
        # creates the index value based on car and node combination
        return car + "-" + node

    def _isNodeForVendor(self, car, node, vendor):
        """ This returns true of vendor for a specific car, node is
            vendor

            The vendor name is stored as lowercase, but the vendor paramter is
            case insensitive.
        """
        if self.getNodeParamValue(car, node, "vendor") == vendor.lower():
            return True
        else:
            self.logger.debug("vendor for car " + car +" node " + node + " is " + self.getNodeParamValue(car, node, "vendor"))
            return False

    def _connect(self, car, node, stayConn=False, updateStatus=False):
        """
            syntax:
                _connect(self, car, node, stayConn=False, updateStatus=False)

            arguments:

                stayConn: if true, the connection will stay connected once the
                          control is returned to the calling method.

                updatestatus: if true, the status for the dashboard will be
                              updated.

            return: state
                    returns the connection state
                    values:
                        connected
                        notConnected
                        NoSSH

                    NoSSH means that the node is not SSH'able
        """

        if self.getNodeParamValue(car, node, "ssh"):
            if not self.isConnected(car, node):
                ipAddress = self.getConfigValue(car, self.defaultConn)
                port = self.getNodeParamValue(car, node, "port")
                username = self.getNodeParamValue(car, node, "username")
                password = self.getNodeParamValue(car, node, "password")

                if not self.nc(self.getHostIP(car), self.getHostNodePort(car, node)):
                    print ("hello", self.getHostIP(car), self.getHostNodePort(car, node))
                    return self.NoSSH

                self.logger.debug(__name__ + ": " + car + "[" + node + "] - " + ipAddress + \
                    ":" + port)
                # self.logger.debug(__name__ + ": ip address is " + self.getConfigValue(car, self.defaultConn))
                # self.logger.debug(__name__ + ": node username is  " + self.getNodeParamValue(car, node, "username"))
                # self.logger.debug(__name__ + ": node password is  ******** ")
                # self.logger.debug(__name__ + ": node port is  " + self.getNodeParamValue(car, node, "port"))
                self.remote[self._getRemoteIndex(car,node)] = paramikoWrapper(
                               ipAddress, username, password, port)

                if self.isConnected(car, node):
                    state = self.CONNECTED
                else:
                    state = self.NOTCONNECTED
                    try:
                        del self.remote[self._getRemoteIndex(car,node)]
                    except:
                        pass

                if not stayConn:
                    self._disconnect(car, node, False)

                if updateStatus:
                    self.logger.debug ("writing to status file: " + state)
                    self.status.writeStatus(car, node, "connected", state)

                    if state == self.CONNECTED:
                        self.status.writeStatus(car, node, "alive", self.ALIVE)
                        # return True

            else:
                if updateStatus:
                    self.logger.debug(car + "[" + node + "] already connected")
                    self.status.writeStatus(car, node, "alive", self.ALIVE)

                state = self.CONNECTED
        else:
            state = self.NoSSH

        return state

    def _disconnect(self, car, node, updateStatus=True):
        self.logger.debug("disconnecting from " + car + ":" + node)
        if self.getNodeParamValue(car, node, "ssh"):
            if self.isConnected(car, node):
                   self.remote[self._getRemoteIndex(car, node)].__del__()
                   self.remote.pop(self._getRemoteIndex(car, node), None)

        if updateStatus:
            self.status.writeStatus(car, node, "connected", self.NOTCONNECTED)

        return True

    def _getOS(self, host=None, node="SMM"):
        if host is None:
            hostOS = subprocess.Popen(['uname'], stdout=subprocess.PIPE).stdout.read().decode('utf-8').strip('\n')
            if str(hostOS.lower()).startswith("cygwin"):
                return "CYGWIN"
            if str(hostOS.lower()).startswith('linux'):
                return "Linux"
        else:
            retVal, output, err = self.runCommand(host, node, "uname")
            #out = self.runCommand(host, node, "uname", printOut=True)
            if not retVal:
                return err

            self.logger.debug("command output: " + output)
            if len(err) == 0:
                if str(output.lower()).startswith("cygwin"):
                    return "CYGWIN"
                if str(output.lower()).startswith("linux"):
                    return "Linux"

                return str(output.lower())

            else:
                return err

    def connectAll(self, reconnect=False, disconnect=False):
        threads = []
        for car in self.getHosts():
            for node in self.getNodes(car):
                if reconnect:
                    self.disconnectHost(car, node)

                if self._isNodeForVendor(car, node, "cn"):
                # self.h.data[car]["nodes"][node]["vendor"] == "cn":
                    self.logger.debug(__name__ + ": Attempting to connect to " + car + " node " + node)
                    # self._connect(car, node)
                    threads.append(
                        threading.Thread(target=self._connect, args=(car, node, disconnect)))
                    threads[-1].start()

        for t in threads:
            t.join()


    def disconnectAll(self, updateStatus=True):
        for car in self.getHosts():
            for node in self.getNodes(car):
                self.disconnectHost(car, node, updateStatus)

    def getAllConnectionState(self):
        for car in self.hosts:
            for node in self.hosts[car]["nodes"]:
                self.logger.info ("[" + self._getRemoteIndex(car, node) + "] ", end='')
                if self.isConnected(car, node):
                    state = self.CONNECTED
                    self.status.writeStatus(car, node, "status", state)
                else:
                    state = self.NOTCONNECTED
                    self.status.writeStatus(car, node, "status", state)

                self._updateACCStatus(car, node)

    def connectHost(self, car, node, force=False, disconnect=False):
        stat = statusHandler(self.statusFile)

        if force:
            self.disconnectHost(car, node)
            sleep(5)

        return self._connect(car, node, disconnect)

    def disconnectHost(self, car, node, updateStatus=True):
        return self._disconnect(car, node, updateStatus)

    # def getConnectionState(self, car, node):
    #     if self.isConnected(car, node):
    #         return True
    #     else:
    #         return False

    def _isRemoteIndexExists(self, car, node):
        if self._getRemoteIndex(car, node) in self.remote.keys():
            return True
        else:
            return False

    def isConnected(self, car, node):
        """
        syntax: isConnected(car, node)

        arguments:
            car: the car id as specified in the hosts json file
            node: the node belonging to the car as specified in the hosts json
                  file

        return value:
            boolean:
                if true, the node is connected
                if false, the node is not connected
        """

        if self._isRemoteIndexExists(car, node):
            if self.remote[self._getRemoteIndex(car, node)].isConnected():
                return True
            else:
                self.remote[self._getRemoteIndex(car, node)].__del__()
                del self.remote[self._getRemoteIndex(car, node)]
                return False
        else:
            return False


    def isNodeInHost(self, car, node):
        if node in self.getNodes(car):
            return True
        else:
            return False



    def __updateVendorNodesStatus__(self, car, node, vendor, gwNode="SMM"):
        (okay, value) = self.isVendorNodeAlive(car, node, vendor)
        if (okay):
            self.status.writeStatus(car, node, "alive", self.ALIVE)
        else:
            if (value) == "":
                if self.isConnected(car, gwNode):
                    self.status.writeStatus(car, node, "alive", self.DEAD)
                else:
                    self.status.writeStatus(car, node, "alive", self.UNKNOWN)
            else:
                self.status.writeStatus(car, node, "alive", self.UNKNOWN)

    def updateAllVendorNodesStatus(self, vendor, gwNode="SMM"):
        threads = []

        try:
            for car in self.getHosts():
                for node in self.getVendorNodes(vendor):
                    if not self.isNodeInHost(car, node) or \
                        not self._isNodeForVendor(car, node, vendor):
                        continue
                    # self.__updateAllVendorNodesStatus__(car, node, vendor)
                    threads.append(
                            threading.Thread(target=self.__updateVendorNodesStatus__,
                                             args=(car, node, vendor)
                            )
                    )
                    threads[-1].start()

                    while threading.active_count() >= maxThread:
                        sleep(5)
            # for t in threads:
            #     t.start()
            #     sleep(10)

            # for t in threads:
            #     t.join()

        # finally:
        #     threadLimiter.release()

        except Exception as e:
            self.logger.error("Unable to start thread {}".format(e))



    def __updateACCNodeStatus__(self, car, node):
        if self.isACCNodeAlive(car, node):
            self.logger.info(car + "[" + node + "] is alive")
            self.status.writeStatus(car, node, "alive", self.ALIVE)
        else:
            self.logger.info(car + "[" + node + "] is not alive")
            self.status.writeStatus(car, node, "alive", self.DEAD)

    def updateAllACCNodeStatus(self, vendor):
        threads = []
        for car in self.getHosts():
            self.logger.debug('updating car ' + car)
            for node in self.getNodes(car):
                self.logger.info('checking node ' + car + "[" + node + "]")
                if not self._isNodeForVendor(car, node, vendor):
                    self.logger.debug('node not in  ' + vendor)
                    continue

                # self.__updateAllACCNodeStatus__(car, node)
                threads.append(
                        threading.Thread(target=self.__updateACCNodeStatus__, args=(car, node))
                )

        for t in threads:
            t.start()

        for t in threads:
            t.join()

    def updateNodeStatus(self, car, node):
        if self._isNodeForVendor(car, node, 'cn'):
            self._connect(car, node, updateStatus=True)
            self.__updateACCNodeStatus__(car, node)
        else:
            self.__updateVendorNodesStatus__(car, node, "ENSCO")

    def updateCarStatus(self, car):
        result = self.CONNECTED
        if not self.isConnected(car, "SMM"):
            result = self._connect(car, "SMM", updateStatus=True, stayConn=True)

        # if result == self.CONNECTED:
        #     for node in self.getNodes(car):
        #         self.updateNodeStatus(car, node)
        # else:
        #     self.logger.error ("Unable to connect to " + car + "[SMM].")

        for node in self.getNodes(car):
            self.updateNodeStatus(car, node)


    def updateMPConnect(self, car):
        from multiprocessing import Pool, Process
        x=[[car,n] for n in self.getNodes(car) ]
        pool=Pool()
        pool.map(self._connect, x)

    def ping(self, ip, car=None, gwNode="SMM"):

        if car is None:
            theOS = self._getOS()
        else:
            theOS = self._getOS(host=car, node=gwNode)

        if theOS == "Linux":
            cmdPing = "ping -c1 "
        elif theOS == "CYGWIN":
            cmdPing = "ping -n 1 "
        else:
            self.logger.error("Unknown operating system: " + theOS + " for car " + car + " gwNode is " + gwNode)
            return False, self.UNKNOWN


        if car is None:
            self.logger.debug("Trying to ping " + ip)
            ret = os.system(cmdPing + ip + " > /dev/null")
            if ret != 0:
                return False, ""
            else:
                return True, ""
        else:
            self.logger.debug("Trying to ping " + ip + " in car " + car)
            if self.connectHost(car, gwNode):
                ret = self.runCommand(car, gwNode, cmdPing + ip, FalseIf=[" 100% packet loss"])
                if ret[0]:
                    return True, ""
                else:
                    if ret[2] == "noConn":
                        self.logger.error("ping failed because connection to car " + \
                            car + "[" + gwNode + "] is not connected.")
                    return False, ""
            else:
                return False, self.UNKNOWN



    def nc(self, ip, port, car=None):
        if car is not None:
            # TODO
            return False
        else:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((ip, int(port)))
                s.shutdown(2)
                return True
            except:
                return False

            # s.connect((self.hosts[car][self.defaultConn], int(self.hosts[car]["nodes"][node]["port"])))

    def runCommand2(self, car, node, command, TrueIf=[], FalseIf=[], printOut=False):
        def _returnVal(output, err, retVal):
            if printOut:
                self.logger.debug("returning output")
                return output.decode('utf-8'), err
            else:
                return retVal

        if not self.connectHost(car, node):
            self.logger.error("Unable to connect to host: " + car + "[" + node + "].")
            return False

        ip = self.getConfigValue(car, self.defaultConn)
        self.logger.debug("ip address for " + car + "[" + node +"] is " + ip)

        if ip is None or ip == "TBD":
            self.logger.info("ip address for " + car + "[" + node +"] is None or TBD")
            return False

        if not self.isConnected(car, node):
            self.logger.info(car + "[" + node + "] is not connected")
            return False

        output, err = self.remote[self._getRemoteIndex(car, node)].run(command)

        if len(err) != 0:
            return _returnVal(output, err, False)

        falseLink = []
        trueLink  = []

        if FalseIf != []:
            for pat in FalseIf:
                if pat in output.decode("ascii"):
                    falseLink.append(pat)

        self.logger.debug("falseList: {}".format(' '.join(falseLink)))

        if len(falseLink) != 0:
            return _returnVal(output, err, False)

        if TrueIf != []:
            for pat in TrueIf:
                if pat not in output.decode("ascii"):
                    trueLink.append(pat)

        self.logger.debug("trueList: {}".format(' '.join(trueLink)))

        if len(trueLink) != 0:
            return _returnVal(output, err, False)

        return _returnVal(output, err, True)

    def runCommand(self, car, node, command, TrueIf=[], FalseIf=[], gwNode="SMM"):
        '''
        return values: bool, output, err
        '''

        # if not self.connectHost(car, node):
        #     self.logger.error("Unable to connect to host: " + car + "[" + node + "].")
        #     return False, "", ""
        err = ""
        output = ""
        ip = self.getConfigValue(car, self.defaultConn)
        self.logger.debug("ip address for " + car + "[" + node +"] is " + ip)

        if ip is None or ip == "TBD":
            self.logger.info("ip address for " + car + "[" + node +"] is None or TBD")
            return False, "", ""

        if not self.isConnected(car, node):
            self.logger.info(car + "[" + node + "] is not connected")
            return False, "", "noConn"

#        # if self.connectHost(car, gwNode):
#        #     output, err = self.remote[self._getRemoteIndex(car, node)].run(command)
#        # else:
#        #     return False, "", "noConn"

        output, err = self.remote[self._getRemoteIndex(car, node)].run(command)

        if len(err) != 0:
            return False, output.decode('utf-8'), err

        if output == "":
            return False, "", self.noOutput

        falseLink = []
        trueLink  = []

        if FalseIf != []:
            for pat in FalseIf:
                if pat in output.decode("ascii"):
                    falseLink.append(pat)

        self.logger.debug("falseList: {}".format(' '.join(falseLink)))

        if len(falseLink) != 0:
            return False, output.decode("utf-8"), err

        if TrueIf != []:
            for pat in TrueIf:
                if pat not in output.decode("ascii"):
                    trueLink.append(pat)

        self.logger.debug("trueList: {}".format(' '.join(trueLink)))

        if len(trueLink) != 0:
            return False, output.decode("utf-8"), err

        return True, output.decode("utf-8"), err

    def isVendorNodeExistsForCar(self, car, vendor, node):
        ''' This method verifies if the node for the car exists in
            the json definition
        '''
        # check to make sure the vendor/node definition exists in json definition
        if not self.isVendorNodeExists(vendor=vendor, node=node):
            return False

        if self.isNodeInHost(car, node):
            return True
        else:
            return False


    def isVendorNodeAlive(self, car, node, vendor, gwNode="SMM"):
        ip = self.getVendorNodeIP(node, vendor)
        self.logger.debug("ip address for " + car + "[" + node +"] is " + ip)

        if ip is None or ip == "NA":
            return False, ""

        if not self.isVendorNodeExistsForCar(car, vendor, node):
            self.logger.warning ("Vendor node " + vendor + "[" + node + "] does not exist for car: " + car)
            return False, ""

        return self.ping(ip=ip, car=car, gwNode=gwNode)


    def isACCNodeAlive(self, car, node):
        self.logger.debug("running nc() for " + car + "[" + node +"]")
        ip = self.getHostIP(car)
        port = self.getHostNodePort(car, node)
        if ip != "" and port != "":
            return self.nc(ip, port)
        else:
            self.logger.error("ip address or port for car " + car + "[" + node +"] are not found")
            self.logger.error("ip address: " + ip)
            self.logger.error("port        " + port)
            return False

    def checkNetwork(self, car):
        connections = [self.defaultConn, "host-can", "wifi"]
        for conn in connections:
            if self.ping(self.hosts[car]["network"][conn]):
                self.status.writeStatus(car, "network", conn, self.ALIVE)
            else:
                self.status.writeStatus(car, "network", conn, self.DEAD)


    def printOutput(self, node, command, car=None):

        pass
