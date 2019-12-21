from paramikoWrapper import paramikoWrapper
from statusHandler import statusHandler
from collections import OrderedDict
from status import Hosts, Vendors
import json
import socket
import subprocess, os
import logging
from time import sleep
import threading

mod_name = 'ATIC.ATICHosts'
logger = logging.getLogger(mod_name)

VERSION = "4.2"

maxThread = 35

class ATICHosts(Hosts, Vendors):
    def __init__(self, hostFile="hosts.json", statusFile="status.json", vendorFile="vendorNodes.json"):
        self.logger = logging.getLogger(mod_name + ".1")
        self.__version__ = VERSION
        Hosts.__init__(self, hostFile)
        Vendors.__init__(self, vendorFile)
        self.hostFile   = hostFile
        self.statusFile = statusFile
        self.remote={}
        # self.vendor=self._readJson(vendorFile)
        self.status = statusHandler(self.statusFile)
        self.apnList={"host-us":["u_alive", "u_connected"], "host-can": ["c_alive", "c_connected"]}
        self.vendorList=self.getVendors()


        # constants
        self.defaultConn  = "host-us"
        self.usConn       = "host-us"
        self.canConn      = "host-can"
        self.wifi         = "wifi"
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

                    NoSSH means that the node is not SSH'able.  ie. no ip address
        """

        if self.getNodeParamValue(car, node, "ssh") == "true":
            if not self.isConnected(car, node):
                for apn in self.apnList:
                    print ("CHECKING APN", apn)
                    ipAddress = self.getHostIP(car, apn)
                    port = self.getHostNodePort(car, node)
                    if ipAddress != "NA":
                        print ("IP ADDRESS", ipAddress, port)
                        if not self.nc(ipAddress, port):
                            print (ipAddress, port, "NOT CONNECTED")
                            return self.NOTCONNECTED
                        print (ipAddress, port, "CONNECTED")
                    else:
                        continue

                    if ipAddress == "NA":
                        return self.NoSSH

                    # ipAddress = self.getConfigValue(car, apn)
                    # port = self.getNodeParamValue(car, node, "port")
                    username = self.getNodeParamValue(car, node, "username")
                    password = self.getNodeParamValue(car, node, "password")

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
                        self.status.writeStatus(car, node, self.apnList[apn][1], state)

                        if state == self.CONNECTED:
                            self.status.writeStatus(car, node, self.apnList[apn][0], self.ALIVE)

                    break

            else:
                if updateStatus:
                    self.logger.debug(car + "[" + node + "] already connected")
                    # self.status.writeStatus(car, node, self.apnList[apn][0], self.ALIVE)

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
            for apn in self.apnList:
                self.status.writeStatus(car, node, self.apnList[apn][1], self.NOTCONNECTED)

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


#TODO
    def __updateVendorNodeStatus__(self, car, node, vendor, gwNode="SMM"):
        (okay, value) = self.isVendorNodeAlive(car, node, vendor)
        if (okay):
            self.status.writeStatus(car, node, "alive", self.OK)
            if self.getNodeParamValue(car, node, "ssh") == "true":
                # if self.getNodeParamValue(car, node, "u_connected") == self.CONNECTED:
                #     apn = "host-us"
                # elif self.getNodeParamValue(car, node, "c_connected") == self.CONNECTED:
                #     apn = "host-can"
                # else:
                #     return

                for apn in self.apnList:
                    print("apn is", apn)
                    ip = self.getHostIP(car, apn=apn)
                    port = self.getNodeParamValue(car, node, "port")
                    print ("car is",car, "node is", node)
                    print ("ip and port",ip, port)
                    if ip != "" and port != "":
                        if not self.nc(ip, port):
                            self.status.writeStatus(car, node, self.apnList[apn][1], self.NOTCONNECTED)
                            continue
                        else:
                            self.status.writeStatus(car, node, self.apnList[apn][1], self.CONNECTED)

                # ip = self.getHostIP(car, apn=apn)
                # port = self.getNodeParamValue(car, node, "port")
                # if ip != "" and port != "":
                #     if not self.nc(ip, port):
                #         self.status.writeStatus(car, node, self.apnList[apn][1], self.NOTCONNECTED)
                #     else:
                #         self.status.writeStatus(car, node, self.apnList[apn][1], self.CONNECTED)

        else:
            if (value) == "":
                if self.isConnected(car, gwNode):
                    self.status.writeStatus(car, node, "alive", self.NOK)
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
                            threading.Thread(target=self.__updateVendorNodeStatus__,
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

        for apn in self.apnList:
            if self.isACCNodeAlive(car, node, apn):
                self.logger.info(car + "[" + node + "] is " + self.apnList[apn][0])
                self.status.writeStatus(car, node, self.apnList[apn][0], self.OK)
            else:
                if self.getHostIP(car, apn=apn) == "NA":
                    self.status.writeStatus(car, node, self.apnList[apn][0], self.UNKNOWN)
                else:
                    self.logger.info(car + "[" + node + "] is not " + self.apnList[apn][0])
                    self.status.writeStatus(car, node, self.apnList[apn][0], self.NOK)


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
        if not self.isNodeActive(car, node):
            return

        if self._isNodeForVendor(car, node, 'cn'):

            # self._connect(car, node, updateStatus=True)
#            if self.nc(self.getHostIP(car), self.getHostNodePort(car, node)):
#                self.status.writeStatus(car, node, "connected", self.OK)
#            else:
#                self.status.writeStatus(car, node, "connected", self.NOK)
            self.__updateACCNodeStatus__(car, node)
        else:
            v = self.getVendorName(car, node)
            if v in self.vendorList:
                self.__updateVendorNodeStatus__(car, node, v)
            else:
                return

    def updateCarStatus(self, car):
        if not self.isHostActive(car):
            return

        result = self.CONNECTED
        if not self.isConnected(car, "SMM"):
            self._connect(car, "SMM", updateStatus=True, stayConn=True)

        # if result == self.CONNECTED:
        #     for node in self.getNodes(car):
        #         self.updateNodeStatus(car, node)
        # else:
        #     self.logger.error ("Unable to connect to " + car + "[SMM].")

        for node in self.getNodes(car):
            if node in ["TGMS", "Gage/RPMS", "RQMS", "LOCD/GIS"]:
                self.status.writeStatus(car, node, "u_connected", "false")
                self.status.writeStatus(car, node, "c_connected", "false")

            self.updateNodeStatus(car, node)


    def ping(self, ip, car=None, gwNode="SMM"):

#         if car is None:
#             theOS = self._getOS()
#         else:
#             theOS = self._getOS(host=car, node=gwNode)

        theOS = "Linux"
        if theOS == "Linux":
            cmdPing = "ping -c2 -w1 "
        elif theOS == "CYGWIN":
            cmdPing = "ping -n 2 "
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
            # if self.connectHost(car, gwNode):
            if self._connect(car, gwNode, stayConn=True, updateStatus=True) == self.CONNECTED:
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
                s.settimeout(10)
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


    def isACCNodeAlive(self, car, node, apn="host-us"):
        self.logger.debug("running nc() for " + car + "[" + node +"]")
        ip = self.getHostIP(car, apn=apn)
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
