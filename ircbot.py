# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 01:22:34 2015
@author: thebored
Got original code: http://ubuntuforums.org/showthread.php?t=1493702
"""

import socket, time
import sqlite3 as lite
from IRCHandlers import *

class BotNet:
    def __init__(self):
        testy = {'master':'master', 'debugging?':True, 'debugging_level':5, 'testing?':True, 'nick':'botler', 'user':'The botler did it', 'server':'localhost', 'port':6667, 'delay?':True, 'testing_channels':['#boring'], 'testing_server':'localhost', 'testing_port':6667, 'channels':['#gamahcode'], 'server':'irc.geekshed.net', 'port':6667}
        self.bot_confs = [testy]
        self.bots = []
        self.debugging = True
        self.testing = True   
        for bot_conf in self.bot_confs:
            self.add_bot(bot_conf)

    def add_bot(self, bot_conf):
        new_bot = BoredBot(bot_conf, self)
        new_bot.start()
        self.debug("STARTED A NEW BOT:\t" + str(bot_conf) + '\n\n')
        self.bots.append(new_bot)
        self.debug("ADDED A NEW BOT:\t" + str(bot_conf) + '\n\n')

    def debug(self, msg):
        print(msg)

    def start(self):
        self.running = True
        while self.running:
            for bot in self.bots:
                if bot.running:
                    textData = bot.receiveText()
                    bot.handleMessage(textData)                

    def stop(self):
        self.running = False

class BoredBot:
    def __init__(self, bot_conf, bot_net):
        self.bot_conf = bot_conf
        self.bot_net = bot_net #ref to the parent botnet
        self.debugging = self.bot_conf['debugging?']  #True #tell me when you do stuff
        self.debugging_level = self.bot_conf['debugging_level'] #how useless of data?
        self.testing = self.bot_conf['testing?'] #use test server, or production
        self.delay = self.bot_conf['delay?']    #add on delay(pretend to type)
        
        """Initialize a bot"""
        self.nick = self.bot_conf['nick'] #nick'botler'
        self.bangName = '!' + self.nick   #!<botnick> often at beginning of commands
        self.user = self.bot_conf['user'] #nick'botler'
        self.master = self.bot_conf['master'] #obey me
        
        if self.testing:    #are we testing?
            self.joinup = self.bot_conf['testing_channels'] #['#boring']   #join these channels
            self.server = self.bot_conf['testing_server']       #server host
            self.port = self.bot_conf['testing_port']             #server IP
        else:
            self.joinup = self.bot_conf['channels'] #['#gamahcode']   #join these channels
            self.server = self.bot_conf['server']       #server host
            self.port = self.bot_conf['port']             #server IP      

        """ 
        all received msgs are passed to each self.handlers' .receivemsg()
        all sent msgs are passed to each self.sentHandlers' .sentmsg()
        """
        log = LogHandler(self)  #just use the same log handler in both places
        self.handlers = [PONGHandler(self), OneLinerHandler(self), QuoteHandler(self), log, QuitHandler(self), RejoinHandler(self), SysHandler(self)]
        self.sentHandlers = [log]

        self.db = lite.connect('irc.db')    #use this for storing shit in
        
        """Connect to an IRC server, set nick/user, join chans, start run"""
        self.irc = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.irc.connect( ( self.server, self.port ) )
        self.debug("connected...", 1)   #lets assume it all worked :D
        self.textSend('NICK ' + self.nick )      #set nick
        self.textSend('USER ' + self.user) #set user string
        self.motd = self.receiveText()
        self.debug (self.motd)    #print the motd
        time.sleep(2)        #give enough time to connect before continuing
        self.joinChans(self.joinup)              #join all the chans

    def debug(self, message, level=10):
        """If debugging is on, and the debug level is high enough print the message"""
        if self.debugging_level >= level:
            if self.debugging:
                print (message)

    def err(self, message):
        """Do any error msgs"""
        print ('\t\t' + message.upper())

    def delayText(self, message):
        """Delay a realistic amount based on amount of text being sent"""
        if self.delay:                           #if delaying, sleep
            realisticDelay = len(message) * .03  #use length of message
            self.debug('Giving realistic delay of ' + str(realisticDelay) + 's', 5)
            time.sleep(realisticDelay)
        return message

    def textSend(self, textData):
        """Take a string, do any typing delay, encode to bytes, and send"""
        self.irc.send((self.delayText(textData) + '\r\n').encode())  #always end line with \r\n
        self.debug("\n\ttextSent:\t'%s'" % (textData), 3)
        for handler in self.sentHandlers:    #pass sent msg to handlers that care
            handler.sentmsg(textData)

    def receiveText(self):
        """Get 4096bytes from socket buffer, and return it decoded to string"""
        textData = self.irc.recv(4096).decode()  #get 4k, decode bytes to string
        self.debug('\ntextDecoded: ' + textData, 4)
        return textData


    def joinChans(self, chanlist):
        """Join a passed list of one or more chans"""
        for chan in chanlist:
            self.textSend ('JOIN ' + chan)

    def start(self):
        """Begin self.running loop. Get text, pass to the message handlers."""
        self.debug ("starting bot(turning on self.running)!", 1)
        self.running = True  #Don't stop until self.stop()

    def stop(self):
        """Stop Cleanly: Quit server and stop self.running loop"""
        self.textSend('QUIT')
        self.running = False

    def handleMessage(self, textData):
        """Take a msg string, handle any commands, PONG server etc."""
        for handler in self.handlers:
            handler.receivemsg(textData)
        time.sleep(0.2) #chill for a bit. no need to loop the cpu to death

botnet = BotNet()    #Create an instance of BoredBot
botnet.start()                     #Start the Botnet

"""TO DO: !help(handler describe), create a IRCProtocolHandler that combines ping/pong, and get RFC stuff
    PluginSystem: the handlers are each a file in plugin directory. each file in dir is try:ed to imp.ort 
    To control a botnet, since every bot is running the same code, any bot can query/control the rest.
    If bots are on seperate machines, a botchannel or PMs should be used to communicate
    Plugins: data miner, markov chain, dcc dir bot 
"""