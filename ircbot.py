# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 01:22:34 2015
@author: thebored
Got original code: http://ubuntuforums.org/showthread.php?t=1493702
"""
#need time to do delays(time.sleep())
import socket, time
#need something to store quotes/log in.
import sqlite3 as lite
#you need the IRCHandlers.py file to get handlers to do things with things. all of them.
from IRCHandlers import *

class BotNet:
    """
    Spawn/contain/control invidual bot. Each nick on each server is a
    seperate bot, unless a handler stitches them together by sending stuff to
    other bots through the botnet ref each bot get when initialized. Since
    botnet.bots is a list of all the bots you, and each bot has a ref list of
    all its handlers, everythings can converse with everything else directly.
    """
    def __init__(self, bot_confs):
        testy = {'master':'master', 'debugging?':True, 'debugging_level':5, 'testing?':True, 'nick':'botler', 'user':'The botler did it', 'server':'localhost', 'port':6667, 'delay?':True, 'testing_channels':['#boring'], 'testing_server':'localhost', 'testing_port':6667, 'channels':['#gamahcode'], 'server':'irc.geekshed.net', 'port':6667}
        self.bot_confs = [testy] #list of dicts containing the configuration of each bot
        self.bots = []  #list of bot in the net. the central trunk of the data tree
        #debugging statements go to console not irc
        self.debugging = True   #whether the botnet is being debugged.
                                #note: each bot is debugged seperately, from the botnet
        """Ok. This is a little artbitrary, but I assign a value 0-10 for how
        important of a step is being documented. So here are the general levels
        """
        self.debugging_level = 10
        self.testing = True     #what configuration should be used
                                #don't test buggy bots on public servers
                                #easy option(no conf!): apt-get install ircd
        #for each bot conf given, spawn a bot
        for bot_conf in self.bot_confs:
            self.add_bot(bot_conf)

    def add_bot(self, bot_conf):
        """Spawn, start, and add a bot to the self.bots list"""
        new_bot = BoredBot(self, bot_conf)
        new_bot.start()
        self.debug("STARTED A NEW BOT:\t" + str(bot_conf) + '\n\n')
        self.bots.append(new_bot)
        self.debug("ADDED A NEW BOT:\t" + str(bot_conf) + '\n\n')

    def debug(self, msg, level=5):
        """If debugging is on, and the debug level is high enough print the message"""
        if self.debugging_level >= level:
            if self.debugging:
                print (msg)

    def start(self):
        self.running = True
        while self.running:
            for bot in self.bots:
                if bot.running:
                    text_data = bot.receive_text()
                    bot.handle_message(text_data)                

    def stop(self):
        self.running = False

class BoredBot:
    def __init__(self, bot_net, bot_conf):
        self.bot_conf = bot_conf
        self.bot_net = bot_net #ref to the parent botnet
        self.debugging = self.bot_conf['debugging?']  #True #tell me when you do stuff
        self.debugging_level = self.bot_conf['debugging_level'] #how useless of data?
        self.testing = self.bot_conf['testing?'] #use test server, or production
        self.delay = self.bot_conf['delay?']    #add on delay(pretend to type)
        
        """Initialize a bot"""
        self.nick = self.bot_conf['nick'] #nick'botler'
        self.bang_name = '!' + self.nick   #!<botnick> often at beginning of commands
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
        all received msgs are passed to each self.handlers' .receive_msg()
        all sent msgs are passed to each self.sentHandlers' .sentmsg()
        """
        log = LogHandler(self)  #just use the same log handler in both places
        self.handlers = [PONGHandler(self), OneLinerHandler(self), QuoteHandler(self), log, QuitHandler(self), JoinHandler(self), SysHandler(self)]
        self.sent_handlers = [log]

        self.db = lite.connect('irc.db')    #use this for storing shit in
        
        """Connect to an IRC server, set nick/user, join chans, start run"""
        self.irc = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.irc.connect( ( self.server, self.port ) )
        self.debug("connected...", 1)   #lets assume it all worked :D
        self.text_send('NICK ' + self.nick )      #set nick
        self.text_send('USER ' + self.user) #set user string
        self.motd = self.receive_text()
        self.debug (self.motd)    #print the motd
        time.sleep(3)        #give enough time to connect before continuing
        self.join_chans(self.joinup)              #join all the chans

    def debug(self, message, level=5):
        """If debugging is on, and the debug level is high enough print the message"""
        if self.debugging_level >= level:
            if self.debugging:
                print (message)

    def err(self, message):
        """Do any error msgs"""
        print ('\t\t' + message.upper())

    def delay_text(self, message):
        """Delay a realistic amount based on amount of text being sent"""
        if self.delay:                           #if delaying, sleep
            realistic_delay = len(message) * .03  #use length of message
            self.debug('Giving realistic delay of ' + str(realistic_delay) + 's', 3)
            time.sleep(realistic_delay)
        return message

    def text_send(self, text_data):
        """Take a string, do any typing delay, encode to bytes, and send"""
        self.irc.send((self.delay_text(text_data) + '\r\n').encode())  #always end line with \r\n
        self.debug("\n\ttextSent:\t'%s'" % (text_data), 1)
        for handler in self.sent_handlers:    #pass sent msg to handlers that care
            handler.sent_msg(text_data)

    def receive_text(self):
        """Get 4096bytes from socket buffer, and return it decoded to string"""
        text_data = self.irc.recv(4096).decode()  #get 4k, decode bytes to string
        self.debug('\ntext decoded: ' + text_data, 2)
        return text_data


    def join_chans(self, chan_list):
        """Join a passed list of one or more chans"""
        for chan in chan_list:
            self.text_send ('JOIN ' + chan)

    def start(self):
        """Begin self.running loop. Get text, pass to the message handlers."""
        self.debug("starting bot(turning on self.running)!", 0)
        self.running = True  #Don't stop until self.stop()

    def stop(self):
        """Stop Cleanly: Quit server and stop self.running loop"""
        self.debug('Stopping the bot: nick:%s\tserver:%s\t' % (self.nick, self.server), 0)
        self.text_send('QUIT')
        self.running = False

    def handle_message(self, text_data):
        """Take a msg string, handle any commands, PONG server etc."""
        for handler in self.handlers:
            handler.receive_msg(text_data)
        time.sleep(0.2) #chill for a bit. no need to loop the cpu to death

botnet = BotNet()    #Create an instance of BoredBot
botnet.start()                     #Start the Botnet
