#!/usr/bin/env python
import socket, threading
import string, re
import datetime

from utils import *
from channels import *


class irc:
    def __init__(self, delegate):
        self._socket = socket.socket()
        self._channels = channels(self)
        self._bot = delegate;

        self.ident = None
        self.password = None
        self.nick = None
        self.realname = None

        self.server = None
        self.serverPort = None


    def connectToServer(self, server, port):
        print color.b_blue + 'Connecting to server: ' + color.clear + server + ':' + str(port)
        self.server = server
        self.serverPort = port
        self._socket.connect((server, port))
    

    def getMessageType(self,msg):
        # Add the ascii character 1 to the regex using %c
        if re.match("^:.*? PRIVMSG (&|#|\+|!).* :%cACTION .*%c$" % (1,1), msg):
            return "CHANNEL_ACTION_MSG"
        elif re.match("^:.*? PRIVMSG .* :%cACTION .*%c$" % (1,1), msg):
            return "ACTION_MSG"
        elif re.match("^:.*? PRIVMSG .* :%c.*%c$" % (1,1), msg):
            return "CTCP_REQUEST"
        elif re.match("^:.*? NOTICE .* :%c.*%c$" % (1,1), msg):
            return "CTCP_REPLY"
        elif re.match("^:.*? PRIVMSG (&|#|\+|!).* :.*$", msg):
            return "CHANNEL_MSG"
        elif re.match("^:.*? PRIVMSG .*:.*$", msg):
            return "QUERY_MSG"
        elif re.match("^:.*? NOTICE .* :.*$", msg):
            return "NOTICE_MSG"
        elif re.match("^:.*? INVITE .* .*$", msg):
            return "INVITE_NOTICE"
        elif re.match("^:.*? JOIN .*$", msg):
            return "JOIN_NOTICE"
        elif re.match("^:.*? TOPIC .* :.*$", msg):
            return "TOPICCHANGE_NOTICE"
        elif re.match("^:.*? NICK :.*$", msg):
            return "NICKCHANGE_NOTICE"
        elif re.match("^:.*? KICK .* .*$", msg):
            return "KICK_NOTICE"
        elif re.match("^:.*? PART .*$", msg):
            return "PART_NOTICE"
        elif re.match("^:.*? MODE .* .*$", msg):
            return "MODECHANGE_NOTICE"
        elif re.match("^:.*? QUIT :.*$", msg):
            return "QUIT_NOTICE"
        elif re.match("^PING.*?$", msg):
            return "PING"

        return "GENERIC_MESSAGE"

    def getMessageData(self, msg, type):
        msgComponents = string.split(msg)
        messageData = {}

        prefix = None
        command = None
        params = None


        if msgComponents[0][0] == ":":
            prefix = msgComponents[0]

            username = None
            nick = None
            hostmask = None
            server = None

            if "!" in prefix and "@" in prefix:
                split = string.split(prefix,"!")
                nick = split[0]

                split = string.split(split[1],"@")
                hostmask = split[1]
                username = split[0]
                print "nickuserhost: " + nick + " " + username + " " + hostmask
            else:
                if type == "MODECHANGE_NOTICE":
                    nick = prefix
                    print "nick: " + nick
                else:
                    server = prefix
                    print "server: " + server


    def parseRawMessage(self, msg):
        msg = string.rstrip(msg)
        messageType = self.getMessageType(msg)
        messageData = self.getMessageData(msg,messageType)
        if self._bot.debug: print color.cyan + str(datetime.datetime.now()) + " " + color.green + messageType + " " + color.clear + msg
        else: print msg
        
        msgComponents = string.split(msg)
        if re.match("^.* 366 %s .*:End of /NAMES.*$" % re.escape(self.nick), msg):
            self._channels.joinedTo(msgComponents[3])
        if (messageType == "KICK_NOTICE") and re.match("^.*%s.*$" % re.escape(self.nick), msg):
            self._channels.kickedFrom(msgComponents[2])

        if (messageType == "PING") and len(msgComponents) == 2:
            self.sendPingReply(msgComponents[1])

        if messageType == "NOTICE_MSG" and re.match("^:NickServ!.*? NOTICE %s :.*identify via \x02/msg NickServ identify.*$" % re.escape(self.nick), msg):
            print color.purple + 'Identify request recieved.' + color.clear
            if self.password:
                self.sendMSG(('identify %s' % self.password),'NickServ')
            else:
                print color.red + 'No password specified, not authenticating.' + color.clear

        if (messageType == "MODECHANGE_NOTICE"):
            if (msg == ":" + self.nick + " MODE " + self.nick + " :+i"):
                print color.b_cyan + "Overcast IRC Bot - Connected to irc server\n" + color.clear
                for channel, data in self._bot.channels.items():
                    self._channels.join(channel)

            #:McSpider!~McSpider@192.65.241.17 MODE ##mcspider +o Overcast1
            if re.match("^:.*? MODE .* \+o %s$" % re.escape(self.nick), msg):
                channel = msgComponents[2]
                print color.b_purple + "Oped in channel: " + color.clear + channel
                self._channels.setOpedInChannel(channel,True)
            if re.match("^:.*? MODE .* \-o %s$" % re.escape(self.nick), msg):
                channel = msgComponents[2]
                print color.b_purple + "De-Oped in channel: " + color.clear + channel
                self._channels.setOpedInChannel(channel,False)


        self._bot.parseMessage(msgComponents, messageType)


    def read(self):
        readbuffer = ""
        while 1:
            readbuffer = readbuffer+self._socket.recv(1024)
            if not readbuffer: break

            temp = string.split(readbuffer, "\n")
            readbuffer = temp.pop( )
            
            for msg in temp:
                msg.strip()
                t = threading.Thread(target = self.parseRawMessage, args = (msg,))
                startThread(t)

    def disconnect(self):
        # Check if the socket is still receving data, and if it is shut it down
        if self._socket.recv(128): self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()

    def quit(self,message="Going, going, gone."):
        print color.b_cyan + 'Overcast IRC Bot - Quitting\n' + color.clear
        self.sendRaw("QUIT :%s \r\n" % message)


    def authUser(self, username, nick, realname, password):
        print color.blue + 'IRC Login Info: ' + color.clear + username + ' | ' + realname + ' | ' + password 
        print color.blue + 'IRC Nick: ' + color.clear + nick + '\n'

        self.sendRaw('USER %s %s %s \r\n' % (username, " 0 * :", realname))
        self.sendRaw('NICK %s\r\n' % nick)

        self.ident = username
        self.nick = nick
        self.realname = realname
        self.password = password


    def sendRaw(self, message):
        #print color.blue + 'Sending raw string: ' + color.clear + message
        self._socket.send(message)

    def sendMSG(self, message, recipient):
        if recipient == None:
            print color.red + 'No message recipient specified! ' + color.clear
        print color.blue + 'Sending message: ' + color.clear + message + color.blue + ' Recipient: '+ color.clear + recipient
        self._socket.send("PRIVMSG %s :%s\r\n" % (recipient, message))

    def sendNoticeMSG(self, message, recipient):
        if recipient == None:
            print color.red + 'No message recipient specified! ' + color.clear
        print color.blue + 'Sending notice message: ' + color.clear + message + color.blue + ' Recipient: '+ color.clear + recipient
        self._socket.send("NOTICE %s :%s\r\n" % (recipient, message))

    def sendActionMSG(self, message, recipient):
        if recipient == None:
            print color.red + 'No message recipient specified! ' + color.clear
        print color.blue + 'Sending action message: ' + color.clear + message + color.blue + ' Recipient: '+ color.clear + recipient
        self._socket.send("PRIVMSG %s :%cACTION %s%c\r\n" % (recipient, 1, message, 1))

    def sendPingReply(self, server): 
        print color.blue + 'Sending ping reply: ' + color.clear + server
        self.sendRaw("PONG %s\r\n" % server)


