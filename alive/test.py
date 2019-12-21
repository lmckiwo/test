import unittest
import logging
from time import sleep
from shutil import copy2
from copy import deepcopy
# import MockSSH
# from mock_F5 import commands

mod_name = 'ATIC'
mod_logger = logging.getLogger(mod_name)
logging.disable(logging.NOTSET)

testFilesLocation = "../test/"

class TestStatus(unittest.TestCase):
    def setUp(self):
        from status import readJson, Hosts, Vendors, Status

        copy2(testFilesLocation + "status.json.test.orig", testFilesLocation + "status.json.test")
        copy2(testFilesLocation + "hosts2.json.test.orig", testFilesLocation + "hosts2.json.test")

        self.json = readJson(testFilesLocation + "hosts.json.test")
        self.hosts = Hosts(testFilesLocation + "hosts.json.test")
        self.hosts2 = Hosts(testFilesLocation + "hosts2.json.test")
        self.vendors = Vendors(testFilesLocation + "vendorNodes.json.test")
        self.status = Status(statusFile=testFilesLocation + 'status.json.test')

        self.testHost1 = "HOST-001"
        self.testHost2 = "HOST-002"
        self.testBadHost = "BADHOST"
        self.node1 = "HOST1"
        self.node2 = "HOST2"
        self.node3 = "HOST3"
        self.badNode = "blah"

        self.badPort = "1234"


    # def tearDown(self):
    #     self.atic.disconnectAll()
    #     sleep(5)

    def test_readJson(self):
        data = self.json._readJson(testFilesLocation + "status.json.test")
        if data:
            self.assertTrue
        else:
            self.assertFalse


        # print (data.status_code)
        with self.assertRaises(SystemExit) as cm:
            data = self.json._readJson(testFilesLocation + "badfile.json")

        the_exception = cm.exception
        self.assertEqual(the_exception.code, 1)


    def test_getKeys(self):
        self.assertEqual(self.json.getKeys(self.json.data), ['default', 'HOST-001', 'HOST-002', 'QA-001', 'BAD-HOST'])
        self.assertEqual(self.json.getKeys(self.json.data, exclude='default'), ['HOST-001', 'HOST-002', 'QA-001', 'BAD-HOST'])
        self.assertEqual(self.json.getKeys(self.json.data, "blah"), ['default', 'HOST-001', 'HOST-002', 'QA-001', 'BAD-HOST'])

    def test_safeGet(self):
        self.assertEqual(self.json.safeGet(self.json.data, self.testHost1, "nodes", self.node1, "active"), "true")
        self.assertEqual(self.json.safeGet(self.json.data, self.testHost1, "config", "wifi"), "")

        target = sorted(['ensco-unit', 'ensco-name', 'CN-id', 'host-can', 'host-us'])
        source = sorted(self.json.safeGet(self.json.data, self.testHost1, "config").keys())

        self.assertEqual(source, target)

        # self.assertEqual(self.hosts.safeGet(self.hosts.data, self.testHost1, "config").keys(), ['ensco-unit', 'ensco-name', 'CN-id', 'host-can', 'host-us', 'wifi'])
        # self.assertNotEqual(self.json.safeGet(self.json.data, self.testHost1, "config").keys(), ['ensco-unit', 'ensco-name', 'CN-id', 'host-can', 'host-us'])

    ##########################
    # HOSTS                  #
    ##########################
    def test_getHosts(self):
        self.assertEqual(self.hosts.getHosts(), ['HOST-001', 'HOST-002', 'QA-001', 'BAD-HOST'])

    def test_getConfigParams(self):
        self.assertEqual(sorted(self.hosts.getConfigParams(self.testHost1)), sorted(['ensco-unit', 'ensco-name', 'CN-id', 'host-can', 'host-us']))

    def test_getNodes(self):
        self.assertEqual(sorted(self.hosts.getNodes(self.testHost1)), sorted(['HOST1', 'HOST2', 'HOST3', 'HOST4', 'HOST5', 'VENDORHOST1', 'VENDORHOST2', 'VENDORHOST3']))

    def test_getConfigValue(self):
        self.assertEqual(self.hosts.getConfigValue(self.testHost1, "wifi"), "")

    def test_getNodeParams(self):
        self.assertEqual(sorted(self.hosts.getNodeParams(self.testHost1, self.node1)), sorted(['active', 'username', 'port']))

    def test_getNodeParamValue(self):
        self.assertEqual(self.hosts.getNodeParamValue(self.testHost1, self.node1, "active"), "true")


    def test_getHostIP(self):
        self.assertEqual(self.hosts.getHostIP(self.testHost1), "4.3.4.119")
        self.assertEqual(self.hosts.getHostIP(self.testHost1, apn="host-us"), "4.3.4.119")
        self.assertEqual(self.hosts.getHostIP(self.testHost1, apn="host-can"), "1.2.3.99")

    def test_getHostNodePort(self):
        self.assertEqual(self.hosts.getHostNodePort(self.testHost1, self.node1), "2500")
        self.assertEqual(self.hosts.getHostNodePort(self.testHost1, self.node3), "")
        self.assertEqual(self.hosts.getHostNodePort(self.testBadHost, self.node1), "")
        self.assertEqual(self.hosts.getHostNodePort(self.testHost1, self.badNode), "")

    def test_setHostConfigParamValue(self):
        self.hosts2.hosts = self.hosts2._readJson(testFilesLocation + "hosts2.json.test")

        self.assertEqual(self.hosts2.getConfigValue(self.testHost1, "host-us"), "4.3.4.119")
        self.hosts2.setHostConfigParamValue(self.testHost1, "host-us", "blah")
        self.assertEqual(self.hosts2.getConfigValue(self.testHost1, "host-us"), "blah")
        self.hosts2.hosts = self.hosts2._readJson(testFilesLocation + "hosts2.json.test")
        self.assertEqual(self.hosts2.getConfigValue(self.testHost1, "host-us"), "4.3.4.119")

        # update hosts file
        self.hosts2.setHostConfigParamValue(self.testHost1, "host-us", "blah", writeFile=True)
        self.assertEqual(self.hosts2.getConfigValue(self.testHost1, "host-us"), "blah")
        self.hosts2.hosts = self.hosts2._readJson(testFilesLocation + "hosts2.json.test")
        self.assertEqual(self.hosts2.getConfigValue(self.testHost1, "host-us"), "4.3.4.119")


    def test_setHostNodeParamValue(self):

        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "username"), "root")
        self.hosts2.setHostNodeParamValue(self.testHost1, self.node1, "username", "blah")
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "username"), "blah")
        self.hosts2.hosts = self.hosts2._readJson(testFilesLocation + "hosts2.json.test")
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "username"), "root")

        # update hosts file
        self.hosts2.setHostNodeParamValue(self.testHost1, self.node1, "username", "blah", writeFile=True)
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "username"), "blah")
        self.hosts2.hosts = self.hosts2._readJson(testFilesLocation + "hosts2.json.test")
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "username"), "blah")

    def test_setConfigDefault(self):

        self.assertEqual(self.hosts2.getConfigValue(self.testHost1, "wifi"), "")
        self.hosts2.setConfigDefault()
        self.assertEqual(self.hosts2.getConfigValue(self.testHost1, "wifi"), "NA")

        self.hosts2.hosts = self.hosts2._readJson(testFilesLocation + "hosts2.json.test")
        self.assertEqual(self.hosts2.getConfigValue(self.testHost1, "wifi"), "")

    def test_setNodeDefault(self):

        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "username"), "root")
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "password"), "")
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "port"), "2500")
        self.hosts2.setNodeDefault()
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "username"), "root")
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "password"), "password")
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "port"), "2500")

        self.hosts2.hosts = self.hosts2._readJson(testFilesLocation + "hosts2.json.test")
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "username"), "root")
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "password"), "")
        self.assertEqual(self.hosts2.getNodeParamValue(self.testHost1, self.node1, "port"), "2500")


    ##########################
    # VENDORS                #
    ##########################

    def test_getVendors(self):
        self.assertEqual(sorted(self.vendors.getVendors()), sorted(['VENDOR1', 'VENDOR2']))


    def test_getVendorNodes(self):
        self.assertEqual(sorted(self.vendors.getVendorNodes('VENDOR1')), sorted(['VENDORHOST1', 'VENDORHOST2', 'VENDORHOST3', 'VENDORHOST4', 'VENDORHOST5', 'VENDORHOST6', 'VENDORHOST7', 'VENDORHOST8']))

    def test_getVendorNodeIP(self):
        self.assertEqual(self.vendors.getVendorNodeIP(vendor="VENDOR1", node="VENDORHOST1"), "192.206.233.190")
        # self.assertEqual(self.vendors.getVendorNodeIP(node="VENDORHOST1", vendor="VENDOR1"), "192.206.233.190")
        self.assertEqual(self.vendors.getVendorNodeIP(node="VENDORHOST11", vendor="VENDOR1"), "")

    def test_isVendorExists(self):
        self.assertTrue(self.vendors.isVendorExists("VENDOR1"))
        self.assertTrue(self.vendors.isVendorExists("VENDOR2"))
        self.assertFalse(self.vendors.isVendorExists("VENDOR11"))

    def test_isVendorNodeExists(self):
        self.assertTrue(self.vendors.isVendorNodeExists("VENDOR1", "VENDORHOST1"))
        self.assertTrue(self.vendors.isVendorNodeExists("VENDOR2", "TT"))
        self.assertFalse(self.vendors.isVendorNodeExists("VENDOR11", "VENDORHOST1"))
        self.assertFalse(self.vendors.isVendorNodeExists("VENDOR1", "VENDORHOST11"))


    ##########################
    # STATUS                 #
    ##########################

    def test_Status_getHosts(self):
        self.assertEqual(self.status.getHosts(), ['HOST-001', 'HOST-002', 'QA-001', 'BAD-HOST'])

    def test_Status_getConfigParams(self):
        self.assertEqual(sorted(self.status.getConfigParams(self.testHost1)), sorted(['active', 'host-us', 'host-can', 'wifi']))

    def test_Status_getNodes(self):
        self.assertEqual(sorted(self.status.getNodes(self.testHost1)), sorted(['HOST1', 'HOST2', 'HOST3', 'HOST4', 'HOST5', 'VENDORHOST1', 'VENDORHOST2', 'VENDORHOST3']))

    def test_Status_getConfigValue(self):
        self.assertEqual(self.status.getConfigValue(self.testHost1, "wifi"), "NA")

    def test_Status_getNodeParams(self):
        self.assertEqual(sorted(self.status.getNodeParams(self.testHost1, self.node1)), sorted(['vendor', 'active', 'c_connected', 'u_connected', 'alive']))

    def test_Status_getNodeParamValue(self):
        # copy2("status.json.test", "status.json")
        self.assertEqual(self.status.getNodeParamValue(self.testHost1, self.node1, "active"), "true")

    def test_read(self):
        mystuff = self.status.status
        self.assertTrue(self.status.read())
        self.assertEqual(self.status.status, mystuff)
        #self.assertFalse(self.status.read("blah"))

    def test_write(self):
        # copy2("status.json.test.orig", "status.json.test")
        self.assertTrue(self.status.read())
        mystuff = deepcopy(self.status.status)
        print("mystuff: ", mystuff[self.testHost1]["nodes"][self.node1]["active"])
        self.assertTrue(self.status.write())
        self.assertTrue(self.status.read())
        self.assertEqual(self.status.status, mystuff)

        self.status.setNodeParamValue(self.testHost1, self.node1, "active", "false")
        self.assertTrue(self.status.write())

        self.assertNotEqual(self.status.status, mystuff)
        # self.status.setNodeParamValue(self.testHost1, self.node1, "active", "true")
        # self.assertTrue(self.status.write(self.status.status, 'status.json'))
        # self.assertEqual(self.status.status, mystuff)


    def test_setNodeParamValue(self):
        self.assertEqual(self.status.getNodeParamValue(self.testHost1, self.node1, "active"), "true")
        self.assertTrue(self.status.setNodeParamValue(self.testHost1, self.node1, "active", "false"))

        self.assertTrue(self.status.write())

        # self.assertEqual(self.status.getNodeParamValue(self.testHost1, self.node1, "active"), "false")


class TestStatusHandler(unittest.TestCase):

    def setUp(self):
        # import createStatus
        from statusHandler import statusHandler

        self.testHost1 = "HOST-001"
        self.testHost2 = "QA-001"
        self.testHost3 = "BAD-HOST"
        self.testHost4 = "BAD-HOST1"
        self.badHost = "ATIC-00"
        self.node1 = "HOST1"
        self.node2 = "HOST2"
        self.node3 = "VENDORHOST1"
        self.node4 = "VENDORHOST7"
        self.badnode = "BAD"
        self.status = statusHandler(testFilesLocation + "status.json.test")
        copy2(testFilesLocation + "status.json.test.orig", testFilesLocation + "status.json.test")


    def test_ReadStatus(self):
        self.assertEqual(self.status.readStatus(self.testHost1, self.node1, "u_connected"), "")
        self.assertEqual(self.status.readStatus(self.testHost1, self.node1, "connected1"), self.status.UNDEF)
        self.assertEqual(self.status.readStatus(self.badHost, self.node1, "connected1"), self.status.UNDEF)
        self.assertEqual(self.status.readStatus(self.testHost1, self.badnode, "connected1"), self.status.UNDEF)


    def test_WriteStatus(self):
        self.assertTrue(self.status.writeStatus(self.testHost1, self.node1, "u_connected", "true"))
        self.assertFalse(self.status.writeStatus(self.testHost1, self.node1, "u_connected1", "true"))
        self.assertFalse(self.status.writeStatus(self.testHost1, self.badnode, "u_connected", "true"))
        self.assertFalse(self.status.writeStatus(self.badHost, self.node1, "u_connected", "true"))

class TestATICHosts(unittest.TestCase):
   # # @classmethod
   #  def setUpClass(cls):
   #      users = {'root': 'password'}
   #      cls.keypath = tempfile.mkdtemp()
   #      MockSSH.startThreadedServer(
   #          commands,
   #          prompt="[root@hostname:Active] testadmin # ",
   #          keypath=cls.keypath,
   #          interface="localhost",
   #          port=22,
   #          **users)

   #  # @classmethod
   #  def tearDownClass(cls):
   #      print ("tearDownClass")
   #      MockSSH.stopThreadedServer()
   #      shutil.rmtree(cls.keypath)

    def setUp(self):
        from ATICHosts import ATICHosts
        from statusHandler import statusHandler

        copy2(testFilesLocation + "hosts2.json.test.orig", testFilesLocation + "hosts.json.test")
        self.atic = ATICHosts(hostFile=testFilesLocation + 'hosts.json.test', \
                              vendorFile=testFilesLocation + 'vendorNodes.json.test', \
                              statusFile=testFilesLocation + 'status.json.test')
        self.testHost1 = "HOST-001"
        self.testHost2 = "QA-001"
        self.testHost3 = "BAD-HOST"
        self.badHost = "ATIC-00"
        self.node1 = "HOST1"
        self.node2 = "HOST2"
        self.node3 = "VENDORHOST1"
        self.node4 = "VENDORHOST7"
        self.status = statusHandler(statusFile=testFilesLocation + 'status.json.test')

    def tearDown(self):
        sleep(5)
        self.atic.disconnectAll()
        sleep(5)

    def test_getRemoteIndex(self):
        self.assertEqual(self.atic._getRemoteIndex(self.testHost1, self.node1), self.testHost1 + "-" + self.node1)

    def test_isNodeForVendor(self):
        self.assertTrue(self.atic._isNodeForVendor(self.testHost1, self.node1, "vendor0"))
        self.assertTrue(self.atic._isNodeForVendor(car=self.testHost1, node=self.node3, vendor="vendor1"))
        self.assertFalse(self.atic._isNodeForVendor(self.testHost1, self.node1, "vendor1"))
        self.assertFalse(self.atic._isNodeForVendor(self.testHost1, self.node3, "vendor0"))

        self.assertTrue(self.atic._isNodeForVendor(self.testHost1, self.node1, "VENDOR0"))
        self.assertTrue(self.atic._isNodeForVendor(self.testHost1, self.node3, "VENDOR1"))
        self.assertFalse(self.atic._isNodeForVendor(self.testHost1, self.node1, "Vendor1"))
        self.assertFalse(self.atic._isNodeForVendor(self.testHost1, self.node3, "VENDOR0"))

    def test_isNodeInHost(self):
        self.assertTrue(self.atic.isNodeInHost(self.testHost1, self.node1))
        self.assertFalse(self.atic.isNodeInHost(self.testHost2, self.node4))

    def test_isVendorExists(self):
        self.assertTrue(self.atic.isVendorExists("VENDOR1"))
        self.assertTrue(self.atic.isVendorExists("VENDOR2"))
        self.assertFalse(self.atic.isVendorExists("VENDOR11"))


    # def test_isVendorNodeAlive(self):
    #     (ok,res) = self.atic.isVendorNodeAlive(car=self.testHost2, node=self.node3, vendor="VENDOR1", gwNode="HOST2")
    #     print (ok, res)
    #     self.assertTrue(ok)
    #     (ok,res) = self.atic.isVendorNodeAlive(car=self.testHost2, node=self.node4, vendor="VENDOR1", gwNode="HOST2")
    #     self.assertFalse(ok)

    def test_isVendorNodeAlive(self):
        (ok,res) = self.atic.isVendorNodeAlive(car=self.testHost2, node=self.node3, vendor="VENDOR1", gwNode="HOST2")
        print ("VENDOR NODE ALIVE",ok, res)
        print("car is",self.testHost2, "node",self.node3, "vendor VENDOR1 gwNode HOST2")
        self.assertTrue(ok)
        (ok,res) = self.atic.isVendorNodeAlive(car=self.testHost2, node=self.node4, vendor="VENDOR1", gwNode="HOST2")
        self.assertFalse(ok)

    def test_isVendorNodeExistsForCar(self):
        self.assertFalse(self.atic.isVendorNodeExistsForCar(car=self.testHost2, vendor="VENDOR1", node=self.node4))
        self.assertTrue(self.atic.isVendorNodeExistsForCar(car=self.testHost2, vendor="VENDOR1", node=self.node3))
        self.assertFalse(self.atic.isVendorNodeExistsForCar(car=self.testHost2, vendor="TT", node=self.node3))
        self.assertTrue(self.atic.isVendorNodeExistsForCar(car=self.testHost1, vendor="VENDOR1", node=self.node3))


    def test_connect(self):
        # copy2('hosts.json.test', 'hosts.json')
        self.assertTrue(self.atic._connect(self.testHost2, self.node2))
        self.assertEqual(self.atic.status.readStatus(self.testHost2, self.node2, "connected"), self.atic.CONNECTED)
        self.assertTrue(self.atic._connect(self.testHost2, self.node2))
        self.assertEqual(self.atic.status.readStatus(self.testHost2, self.node2, "connected"), self.atic.CONNECTED)
        self.assertFalse(self.atic._connect(self.testHost3, self.node1))
        self.assertEqual(self.atic.status.readStatus(self.testHost3, self.node1, "connected"), self.atic.NOTCONNECTED)

    def test_isConnected(self):
        self.assertTrue(self.atic._connect(self.testHost2, self.node2))
        self.assertFalse(self.atic._connect(self.testHost3, self.node1))
        self.assertTrue(self.atic.isConnected(self.testHost2, self.node2))
        self.assertFalse(self.atic.isConnected(self.testHost1, self.node1))

    def test_disconnect(self):
        self.assertTrue(self.atic._connect(self.testHost2, self.node2))
        self.assertEqual(self.atic.status.readStatus(self.testHost2, self.node2, "connected"), self.atic.CONNECTED)
        self.atic._disconnect(self.testHost2, self.node2)
        self.assertFalse(self.atic.isConnected(self.testHost2, self.node2))

    def test_connectHost(self):
        self.assertFalse(self.atic.connectHost(self.testHost3, self.node1))
        self.assertEqual(self.atic.status.readStatus(self.testHost3, self.node1, "connected"), self.atic.NOTCONNECTED)
        self.assertTrue(self.atic.connectHost(self.testHost2, self.node2))
        self.assertEqual(self.atic.status.readStatus(self.testHost2, self.node2, "connected"), self.atic.CONNECTED)
        self.assertTrue(self.atic.connectHost(self.testHost2, self.node2))
        sleep(5)
        self.assertTrue(self.atic.connectHost(self.testHost2, self.node2, force=True))
        self.assertTrue(self.atic.isConnected(self.testHost2, self.node2))
        self.atic._disconnect(self.testHost2, self.node2)

    def test_disconnectHost(self):
        self.assertTrue(self.atic.connectHost(self.testHost2, self.node2))
        self.assertEqual(self.atic.status.readStatus(self.testHost2, self.node2, "connected"), self.atic.CONNECTED)
        self.assertTrue(self.atic.disconnectHost(self.testHost2, self.node2))
        self.assertEqual(self.atic.status.readStatus(self.testHost2, self.node2, "connected"), self.atic.NOTCONNECTED)
        self.assertTrue(self.atic.disconnectHost(self.testHost2, self.node2))
        self.assertEqual(self.atic.status.readStatus(self.testHost2, self.node2, "connected"), self.atic.NOTCONNECTED)

    def test_isRemoteIndexExists(self):
        self.assertTrue(self.atic.connectHost(self.testHost2, self.node2))
        self.assertEqual(self.atic.status.readStatus(self.testHost2, self.node2, "connected"), self.atic.CONNECTED)
        self.assertTrue(self.atic._isRemoteIndexExists(self.testHost2, self.node2))
        self.assertTrue(self.atic.disconnectHost(self.testHost2, self.node2))
        self.assertFalse(self.atic._isRemoteIndexExists(self.testHost2, self.node2))

    def test_ping(self):
#         self.assertTrue(self.atic.connectHost(car="QA-001", node="HOST2"))
        self.assertTrue(self.atic.ping("google.com"))
#         self.assertTrue(self.atic.ping(ip="127.0.0.1"))
#         self.assertFalse(self.atic.ping(ip="129.0.1.1"))
#         self.assertTrue(self.atic.ping(ip="192.168.2.23"))
#         self.assertTrue(self.atic.ping(car="QA-001", ip="192.168.2.23", gwNode="HOST2"))
#         self.assertTrue(self.atic.ping(car="QA-001", ip="127.0.0.1", gwNode="HOST2"))
#         self.assertFalse(self.atic.ping(car="QA-001", ip="131.4.0.1", gwNode="HOST2"))

    def test_runCommand(self):
        self.assertTrue(self.atic.connectHost(self.testHost2, self.node2))
        self.assertEqual(self.atic.status.readStatus(self.testHost2, self.node2, "connected"), self.atic.CONNECTED)
        self.assertTrue(self.atic._isRemoteIndexExists(self.testHost2, self.node2))
#         self.assertFalse(self.atic.runCommand(self.testHost2, self.node2, "ip a", TrueIf=['eth0', 'wlan0', 'lo', 'eth19']))
#         retVal, output, err = self.atic.runCommand(self.testHost2, self.node2, "ip a", TrueIf=['enp2s0', 'wlp3s0', 'lo', 'eth19'])
#         self.assertFalse(retVal)
#         # self.assertFalse(self.atic.runCommand(self.testHost2, self.node2, "ip a", TrueIf=['eth0', 'wlan0', 'lo', 'l1']))
#         retVal, output, err = self.atic.runCommand(self.testHost2, self.node2, "ip a", TrueIf=['enp2s0', 'wlp3s0', 'lo', 'l1'])
#         self.assertFalse(retVal)
#         retVal, output, err = self.atic.runCommand(self.testHost2, self.node2, "ip a", TrueIf=['enp2s0', 'wlp3s0', 'lo'])
#         self.assertTrue(retVal)
        retVal, output, err = self.atic.runCommand(self.testHost2, self.node2, "ping -c1 -w1 127.0.0.1", FalseIf=[' 100% packet loss'])
        self.assertTrue(retVal)

        retVal, output, err = self.atic.runCommand(self.testHost2, self.node2, "pwd", TrueIf=['/root'])
        self.assertTrue(retVal)

#     def test_getOS(self):
#         self.assertTrue(self.atic.connectHost(car="QA-001", node="HOST2"))

#         # comment out if not cygwin
#         self.assertEqual(self.atic._getOS(), "CYGWIN")

#         # comment out if not Linux
#         #self.assertEqual(self.atic._getOS(), "Linux")

#         self.assertEqual(self.atic._getOS(host='QA-001', node='HOST2'), "Linux")

#     def test_nc(self):
#         self.assertFalse(self.atic.nc("10.1.157.106", "8080"))
#         self.assertTrue(self.atic.nc("192.168.2.23", "22"))
#         if self.atic._getOS() == "CYGWIN":
#             self.assertFalse(self.atic.nc("127.0.0.1", "22"))
#         else:
#             self.assertTrue(self.atic.nc("127.0.0.1", "22"))

#     def test_isACCNodeAlive(self):
#         self.assertFalse(self.atic.isACCNodeAlive(self.testHost1, self.node1))
#         self.assertTrue(self.atic.isACCNodeAlive(self.testHost2, self.node2))

if __name__ == "__main__":
#     unittest.main()

    suite = unittest.TestSuite()
#     ## # suite.addTest(TestATICHosts("test_isNodeForVendor"))
#     ## # suite.addTest(TestATICHosts("test_isNodeInHost"))
#     ## # suite.addTest(TestATICHosts("test_isRemoteIndexExists"))
#     ## # suite.addTest(TestATICHosts("test_isVendorExists"))
    suite.addTest(TestATICHosts("test_isVendorNodeAlive"))
    # # suite.addTest(TestATICHosts("test_isVendorNodeExistsForCar"))

#     suite.addTest(TestStatus("test_readJson"))
#     ## suite.addTest(TestStatus("test_getKeys"))
#     ## # suite.addTest(TestStatus("test_safeGet"))
#     ## suite.addTest(TestStatus("test_getHosts"))
#     ## suite.addTest(TestStatus("test_getConfigParams"))
#     ## suite.addTest(TestStatus("test_getNodes"))
#     ## suite.addTest(TestStatus("test_getConfigValue"))
#     ## suite.addTest(TestStatus("test_getNodeParams"))
#     ## suite.addTest(TestStatus("test_getNodeParamValue"))

#     ## suite.addTest(TestStatus("test_getVendors"))
#     ## suite.addTest(TestStatus("test_getVendorNodes"))
#     ## suite.addTest(TestStatus("test_getVendorNodeIP"))
#     ## suite.addTest(TestStatus("test_isVendorExists"))
#     ## suite.addTest(TestStatus("test_isVendorNodeExists"))
#     ## suite.addTest(TestStatus("test_Status_getHosts"))
#     ## suite.addTest(TestStatus("test_Status_getConfigParams"))
#     ## suite.addTest(TestStatus("test_Status_getNodes"))
#     ## suite.addTest(TestStatus("test_Status_getConfigValue"))
#     ## suite.addTest(TestStatus("test_Status_getNodeParams"))
#     ## suite.addTest(TestStatus("test_Status_getNodeParamValue"))
#     ## suite.addTest(TestStatus("test_setNodeParamValue"))
#     ## suite.addTest(TestStatus("test_read"))
#     ## suite.addTest(TestStatus("test_write"))
#     ## suite.addTest(TestStatus("test_getHostIP"))
#     #suite.addTest(TestStatus("test_getHostNodePort"))




#     # suite.addTest(TestStatus("test_setHostConfigParamValue"))
#     # suite.addTest(TestStatus("test_setHostNodeParamValue"))
#     # suite.addTest(TestStatus("test_setConfigDefault"))
#     # suite.addTest(TestStatus("test_setNodeDefault"))



#     ## suite.addTest(TestStatusHandler("test_ReadStatus"))
#     ## suite.addTest(TestStatusHandler("test_WriteStatus"))



#     ## # suite.addTest(TestATICHosts("test_disconnectHost"))
#     ## # suite.addTest(TestATICHosts("test_runCommand"))
#     # suite.addTest(TestATICHosts("test_ping"))
#     #suite.addTest(TestATICHosts("test_nc"))
#     #suite.addTest(TestATICHosts("test_isACCNodeAlive"))
#     # suite.addTest(TestATICHosts("test_getOS"))

    runner = unittest.TextTestRunner()
    runner.run(suite)
