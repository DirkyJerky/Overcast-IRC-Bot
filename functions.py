#!/usr/bin/env python
import os, sys
import string, re

import importlib
from utils import *
import datetime


class functions:
    def __init__(self, delegate):
        self.functionsList = []
        self.loadfunctions()
        self.bot = delegate
        self.globalCooldown = {}
        pass

    def loadfunctions(self):
        lib_path = os.path.abspath('./_functions/')
        sys.path.append(lib_path)

        for f in os.listdir(os.path.abspath("./_functions/")):
            functionName, ext = os.path.splitext(f)
            if ext == ".py":
                # print color.green + 'Imported module: ' + color.clear + functionName
                function = __import__(functionName)
                command_func = getattr(function, "function")
                instance = command_func()
                instance.name = functionName + ext
                self.functionsList.append(instance)

            self.functionsList = sorted(self.functionsList, key=lambda function: function.priority, reverse=True)

    def checkForFunction(self, msgComponents, messageType):
        msgSenderHostmask = msgComponents[0]
        msgSender = string.lstrip(string.split(msgSenderHostmask,"!")[0],":")

        # Global same sender message cooldown
        if msgSender in self.globalCooldown and (not (self.globalCooldown[msgSender] == None or datetime.datetime.now() > self.globalCooldown[msgSender])):
            print color.b_red + "Ignoring possible flood message" + color.clear
            return

        # Check functions
        for func in self.functionsList:
            # Handle channel messages
            privateMessage = (messageType == "QUERY_MSG") or (messageType == "ACTION_MSG")
            if ((messageType == "CHANNEL_MSG") or (messageType == "CHANNEL_ACTION_MSG") or privateMessage) and len(msgComponents) >= 3:
                messageRecipient = msgComponents[2]

                target = messageRecipient
                if privateMessage:
                    target = msgSender

                messageData = {"recipient":messageRecipient,"message":msgComponents[3:], "rawMessage":" ".join(msgComponents), "sender":msgSender, "senderHostmask":msgSenderHostmask, "messageType":messageType, "target":target}
                messageData["message"][0] = messageData["message"][0][1:]

                if "natural" in func.type:
                    funcExectuted = self.runFunction(func, messageData, "natural")
                    if funcExectuted and func.blocking:
                        return

                if "command" in func.type:
                    # Check if the message has a trigger and a subcommand
                    if len(msgComponents) >= 4:
                        messageCommand = msgComponents[3]
                        messageData["message"] = msgComponents[4:]
                        # any(re.match("^:%s.*?$" % (trigger), messageCommand, re.IGNORECASE) for trigger in self.bot.triggers)
                        if (messageRecipient in self.bot.channels) and any(messageCommand.lower() in ":" + trigger.lower() for trigger in self.bot.triggers) and len(msgComponents) >= 5:
                            messageCommand = msgComponents[4]
                            if messageCommand in func.commands:
                                if not func.restricted or (func.restricted and self.bot.isUserAuthed(messageData["sender"],messageData["senderHostmask"])):
                                    funcExectuted = self.runFunction(func, messageData, "command")
                                    if funcExectuted and func.blocking:
                                        return
                                else: self.notAllowedMessage(messageData["sender"],messageRecipient)
                        elif privateMessage:
                            if messageCommand[1:] in func.commands:
                                if not func.restricted or (func.restricted and self.bot.isUserAuthed(messageData["sender"],messageData["senderHostmask"])):
                                    funcExectuted = self.runFunction(func, messageData, "command")
                                    if funcExectuted and func.blocking:
                                        return
                                else: self.bot.notAllowedMessage(messageData["sender"],messageRecipient)

            # Handle status messages
            else:
                messageData = {"recipient":None,"message":msgComponents[3:], "rawMessage":" ".join(msgComponents), "sender":None, "senderHostmask":None, "messageType":messageType}
                if "status" in func.type:
                    funcExectuted = self.runFunction(func, messageData, "status")
                    if funcExectuted and func.blocking:
                        return

    def runFunction(self, func, messageData, type):
        # try:
        functionExecuted = func.main(self.bot, messageData, type)
        if functionExecuted and func.blocking:
            func.runCount = func.runCount + 1
            print color.blue + "Blocking %s function executed:" % type + color.clear + func.functionString
        elif functionExecuted:
            func.runCount = func.runCount + 1
            print color.blue + "%s function executed:" % type.capitalize() + color.clear + func.name

        if functionExecuted:
            self.globalCooldown[messageData["sender"]] = datetime.datetime.now() + datetime.timedelta(seconds = 1)
            return True
        return False
        # except Exception:
        #         print color.red + "Exception raised!"

