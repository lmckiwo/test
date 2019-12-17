import paramiko
import socket
import logging
import logger_setup
import time

mod_name = 'ATIC.paramikoWrapper'
logger = logging.getLogger(mod_name)

class KeepalivesFilter (object):
    def filter(self, record):
        return record.msg.find('keepalive@openssh.com') < 0

paramiko.util.get_logger('paramiko.transport').addFilter(KeepalivesFilter())

def recv_all(channel):
    while not channel.recv_ready():
        time.sleep(0.1)
    stdout = ''
    while channel.recv_ready():
        stdout = channel.recv(1024)
    return stdout


class paramikoWrapper:
    def __init__(self, host, user, password, port=22):
        self.logger = logging.getLogger(mod_name + ".1")

        self.host = host
        self.port = port

        count = 1
        maxRetry = 3
        success = False
        while count <= maxRetry:
            try:
                self.logger.info("Try # " + str(count) + " to connect to " + host + ":" + str(port))
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.client.connect(host, username=user, password=password, port=port, timeout=10)
                self.logger.info ("[" + host + ":" + str(port) + "] - connected")
                self.channel = self.client.invoke_shell()

                break
                # self.channel = self.client.invoke_shell()
                # self.stdin = self.channel.makefile('wb')
                # self.stdout = self.channel.makefile('r')
            # except (TimeoutError, socket.timeout, paramiko.ssh_exception.NoValidConnectionsError, paramiko.ssh_exception.SSHException):
            #     self.logger.info ("[" + host + ":" + str(port) + "] - not connected")

            except paramiko.AuthenticationException:
                self.logger.error ("[" + host + ":" + str(port) + "] - bad password")
                break
            except Exception as ex:
                template = "An exception of type {0} occured. Arguments: \n {1!r}"
                message = template.format(type(ex).__name__, ex.args)
                self.logger.error (message)
                count += 1
                time.sleep(5)

        if count >= maxRetry:
            self.logger.error ("[" + host + ":" + str(port) + "] - not connected")
            self.logger.error ("Connection to " + host + " failed.")


        # else:
        #     print ("[" + host + ":" + str(port) + "] - connected")
        #     # status.writeStatus(self.car, self.node, "status", "online")

    def __del__(self):
        self.client.close()
        self.logger.info ("[" + self.host + ":" + str(self.port) + "] closed.")
        # status.writeStatus(self.car, self.node, "status", "offline")

    def isConnected(self):
        """
        This will check if the connection is still availlable.

        Return (bool) : True if it's still alive, False otherwise.
        """
        try:
            # read prompt
            # recv_all(channel)

            self.channel.send('pwd\n')
            stdout = recv_all(self.channel)

            # self.client.exec_command('pwd', timeout=5)
            return True
        except Exception as ex:
            # print ("Connection lost : %s" % e)
            # return False

            template = "An exception of type {0} occured. Arguments: \n {1!r}"
            message = template.format(type(ex).__name__, ex.args)
            self.logger.debug(message)
            # raise
            return False

    def run(self, command):
        self.logger.debug("executing command: " + command)
        # channel = self.client.invoke_shell()
        # read prompt
        # recv_all(channel)

        self.channel.send(command + '\n')
        stdout = recv_all(self.channel)

        # self.stdin, self.stdout, self.stderr = self.client.exec_command(command)

        # outval = self.stdout.read()
        # errval = self.stderr.read()

        # for line in self.stdout.read().splitlines():
        #     print('... ' + line.strip('\n'))
        return stdout, ""

