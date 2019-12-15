#!/usr/bin/python
#

import sys
import MockSSH

from twisted.python import log

from time import sleep
import tempfile

class command_ping(MockSSH.SSHCommand):
    name = "ping"

    def start(self):
        if len(self.args) == 1:
            self.ip = self.args[0]
            print(("IP is ", self.ip))
            self.writeln("PING " + self.ip + " (" + self.ip + ") 56(84) bytes of data.")
            self.writeln("64 bytes from lga25s60-in-f14.1e100.net (" + self.ip + "): icmp_seq=1 ttl=55 time=20.4 ms")
            self.writeln("")
            self.writeln("--- " + self.ip + " ping statistics ---")
            self.writeln("1 packets transmitted, 1 received, 0% packet loss, time 0ms")
            self.writeln("rtt min/avg/max/mdev = 18.911/18.911/18.911/0.000 ms")
            self.exit()
        else:
            self.writeln("Usage: ping [-aAbBdDfhLnOqrRUvV] [-c count] [-i interval] [-I interface]")
            self.writeln("            [-m mark] [-M pmtudisc_option] [-l preload] [-p pattern] [-Q tos]")
            self.writeln("            [-s packetsize] [-S sndbuf] [-t ttl] [-T timestamp_option]")
            self.writeln("            [-w deadline] [-W timeout] [hop1 ...] destination")
            self.exit()

class command_pwd(MockSSH.SSHCommand):
    name = "pwd"

    def start(self):
        self.writeln("/root")
        self.exit()

class command_passwd(MockSSH.SSHCommand):
    name = 'passwd'

    def start(self):
        self.passwords = []
        if len(self.args) == 1:
            self.username = self.args[0]
            self.writeln("Changing password for user %s." % self.username)
            self.write("New BIG-IP password: ")
            self.protocol.password_input = True
            self.callbacks = [self.ask_again, self.finish]
        else:
            self.writeln("MockSSH: Supported usage: passwd <username>")
            self.exit()

    def ask_again(self):
        self.write('Retype new BIG-IP password: ')

    def finish(self):
        self.protocol.password_input = False

        if self.passwords[0] != self.passwords[1]:
            self.writeln("Sorry, passwords do not match")
            self.writeln("passwd: Authentication token manipulation error")
            self.writeln("passwd: password unchanged")
            self.exit()
        else:
            self.writeln("Changing password for user %s." % self.username)
            self.writeln("passwd: all authentication tokens updated "
                         "successfully.")
            self.exit()

    def lineReceived(self, line):
        print('INPUT (passwd):', line)
        self.passwords.append(line.strip())
        self.callbacks.pop(0)()


commands = [command_passwd, command_pwd, command_ping]


def main():
    users = {'root': 'password'}

    log.startLogging(sys.stderr)

    #MockSSH.runServer(
#    MockSSH.startThreadedServer(
#        commands,
#        prompt="[root@hostname:Active] root # ",
#        interface='127.0.0.1',
#        port=22,
#        **users)

    users = {'root': 'password'}
    keypath = tempfile.mkdtemp()
    MockSSH.startThreadedServer(
        commands,
        prompt="[root@hostname:Active] testadmin # ",
        keypath=keypath,
        interface="localhost",
        port=22,
        **users)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("User interrupted")
        sys.exit(1)
