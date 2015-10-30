# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 07:00:09 2015

@author: thebored
"""


class IRCHandler(object):
    """
    Handlers that respond to others use receivemsg. Handlers that watch what is
    being sent use sentmsg to watch what the bot is sending(think log handler)
    The base handler has some methods that come in handy when working with msgs
    Just implement the receivemsg to handle received msg, 
    and sentmsg to watch what the bot itself is doing(including the other handlers)
    Also note self.bot is a ref to the bot. this lets it be controlled from inside
    the handlers. Also, with self.bot.handlers, the other handlers can be used 
    """
    def __init__(self, bot):
        self.bot = bot

    def description(self):
        return "No Desciption"

    def receivemsg(self, msg):
        return None
        
    def sentmsg(self, sentmsg):
        return None
        
    def privmsg(self, destination, msg):
        """Takes destination nick/chan and message, forms and sends privmsg"""
        self.bot.textSend('PRIVMSG ' + destination +  ' :' + msg)    #dont forget :

    def replyto(self, msg, reply):
         """Takes a privmsg and reply, and sends reply to appropriate chan/pm"""
         if self.isPrivMsg(msg): #make sure its a privmsg!
             self.privmsg(self.chanFrom(msg), reply)  #send msg to sender chan/pm

    def isPrivMsg(self, msg):   #note:PRIVMSG are not just pms, it includes chans
        splitMsg = msg.split()
        if len(splitMsg) < 2:
            return False
        if splitMsg[1].find('PRIVMSG') != -1:
            return True
        else:
            return False 
            
    def chanFrom(self, msg):  
        """if a privmsg, get the channel(or nick if a pm) it's from
        :thebored!~thebored@localhost.lake PRIVMSG #boring :chan msg
        :thebored!~thebored@localhost.lake PRIVMSG botler :pm message
        Notice, the chan can be extracted from msg[2] for a chan msg. but for
        pms it needs to be parsed from msg[0]"""
        if self.isPrivMsg(msg):
            if self.isPrivate(msg): #if private/pm, send directly to sender
                return 'thebored' #FUCKIN CHANGE TIS BIG EROOR
            else:   #if its in a chan, use the place the messag was sent
                return msg.split()[2]
        else:
            return None     #if not a chan/priv msg its a server
            
    def isPrivate(self, msg):
        if (msg.split()[2] == self.bot.nick):
            return True
        else:
            return False
            
    def senderOf(self, msg):    #if privmsg, get the sender info
        if self.isPrivMsg(msg):
            self.bot.debug("\t\t\tThis was a PRIVMSG FROM %s" %  msg.split()[0], 5)
            return msg.split()[0] #like :thebored!~thebored@localhost.lake
        else:
            return None
    
    def nick_of(self, nick_host):
        """Take the host string, return the nick"""
        ##like :thebored!~thebored@localhost.lake -> thebored
        return nick_host.split('!~')[0].lstrip(':')
        
    def isCommandFromGod(self, msg):
        """Takes a msg, returns True if it is from self.bot.master"""
        #if the first word has 1 occurance of <nick>!~
        #like :thebored!~thebored@localhost.lake(some reason :<nick>!~ is broken)
        if self.isPrivMsg(msg):
            if (self.senderOf(msg).find(self.bot.master + '!~') != -1):
                #self.debug('Received message from ' + self.bot.master + ' the god.')
                return True
            else:
                return False
        else:
           return False


class PONGHandler(IRCHandler):
    """PONG: PONG back the servers PING to stay connected"""
    def receivemsg(self, msg):
        if msg.split()[0].find('PING') != -1:   #if first word is PING
            self.bot.textSend ('PONG ' + msg.split() [1])   #PONG back

class OneLinerHandler(IRCHandler):
    """OneLiner: A collection of one line responses to prompts/commands"""
    def receivemsg(self, msg):
        if self.isPrivMsg(msg):
            if msg.find('hi ' + self.bot.nick) != -1:
                self.replyto(msg, 'hi there. go fuck yourself.')
            if msg.find('!cheeseit') != -1: #chumps
                self.replyto(msg,'Time to catch the next pimpmobile')
            if msg.find('!dildos') != -1: #why not?
                self.replyto(msg,'B==D ' + msg.split()[4])

class QuoteHandler(IRCHandler):
    """quote: Send random line from a Quotes table in the  bot's .db"""
    def receivemsg(self, msg):
        if msg.find('!quote') != -1:
            with self.bot.db:    
                cur = self.bot.db.cursor()
                cur.execute("SELECT * FROM Quotes ORDER BY RANDOM() LIMIT 1")
                row = cur.fetchone() #fetch the row 
                self.bot.debug('Fetched Random Quote: ' + str(row), 3)
                self.replyto(msg, ('"%s"' % row[1]))    #send the quote

    def addQuote(self, quote, added_by):
        with self.bot.db:
            cur = self.bot.db.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS Quotes(Id INTEGER PRIMARY KEY, Quote TEXT, Added_by TEXT)")
            cur.execute("INSERT INTO Quotes(Quote, Added_by) VALUES (?, ?)", (quote, added_by))
            self.bot.debug("Added a Quote to the DB!: %s added by %s" % (quote, added_by), 2)

class QuitHandler(IRCHandler):
    """quit: Makes the bot quit the server on with '!<botname> quit' command"""
    def receivemsg(self, msg):
        if self.isCommandFromGod(msg):
            if msg.find(self.bot.bangName + ' quit') != -1:
                self.replyto(msg, "Screw you guys, I'm going home.")
                self.bot.stop()

class JoinHandler(IRCHandler):
    """join: Make the bot rejoin its self.joinup list of chans with !rejoin"""
    def receivemsg(self, msg):
        if self.isCommandFromGod(msg):
            if msg.find('!rejoin') != -1:
                self.bot.joinChans(self.bot.joinup)
            if msg.find('!join') != -1:
                self.bot.joinChans([msg.split()[3]])

class LogHandler(IRCHandler):
    """logger: log all msgs to an sqllite file db"""
    def receivemsg(self, msg):
        self.log(msg)
    def sentmsg(self, msg):
        self.log(msg)
    def log(self, msg):
        self.bot.debug("\tSQL:\t'%s'" % (msg), 8)
        with self.bot.db:
            cur = self.bot.db.cursor()
            chan = self.chanFrom(msg)
            cur.execute("CREATE TABLE IF NOT EXISTS IRCLog (Id INTEGER PRIMARY KEY, Msg TEXT, Chan TEXT)")
            cur.execute("INSERT INTO IRCLog (Msg, Chan) VALUES (?, ?)", (msg, chan))
            self.bot.debug("Added a msg to the DB Log!: '%s added from %s'" % (msg, chan), 2)

from datetime import timedelta

class SysHandler(IRCHandler):
    """sys: A collection of Linux sysinfo commands with '!sys <info>'"""
    def receivemsg(self, msg):
        #stole the uptime code from
        #http://planzero.org/blog/2012/01/26/system_uptime_in_python,_a_better_way
        if msg.find('!sys uptime') != -1:    #reply with linux system uptime  
            self.bot.debug('\tReceived !sys uptime command', 3)
            try: #Try to open
                uptime = open('/proc/uptime', 'r')
            except IOError:  #Not on linux, or something. fucked up
                self.bot.err('/dev/uptime file no-worky!')
            else:
                with uptime as f:
                    uptime_seconds = float(f.readline().split()[0])
                    uptime_string = str(timedelta(seconds = uptime_seconds))
                    self.replyto(msg, uptime_string) #reply uptime to sender
        if msg.find('!sys os') != -1:    #Reply with os version
            self.bot.debug('\tReceived !sys os command', 3)
            try:
                os_version = open('/proc/version', 'r')
            except IOError:
                self.bot.err('/dev/version file no-worky!')
            else:
                with os_version as f:
                    os_info = str(f.readline())
                    self.replyto(msg, os_info)
        if msg.find('!sys meminfo') != -1:   #Reply with meminfo
            self.bot.debug('\tReceived !sys meminfo command', 3)
            try:
                meminfo = open('/proc/meminfo', 'r')
            except IOError:
                self.bot.err('/dev/meminfo file no-worky!')
            else:
                with meminfo as f:
                    for line in f.readlines():
                        line = str(line)
                        if line.find('Mem') != -1:
                            self.replyto(msg, line)
        if msg.find('!sys cpuinfo') != -1:   #Reply with cpuinfo
            self.bot.debug('\tReceived !sys cpuinfo command', 3)
            try:
                cpuinfo = open('/proc/cpuinfo', 'r')
            except IOError:
                self.bot.err('/dev/cpuinfo file no-worky!')
            else:
                with cpuinfo as f:
                    for line in f.readlines():
                        line = str(line)
                        if line.find('model name') != -1:
                            self.replyto(msg, line.split(':', 1)[1])
                            break    #Get out of the for loop. Dont print >once
