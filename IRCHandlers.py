# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 07:00:09 2015

@author: thebored
"""


class IRCHandler(object):
    """
    Handlers that respond to others use receive_msg. Handlers that watch what is
    being sent use sent_msg to watch what the bot is sending(think log handler)
    The base handler has some methods that come in handy when working with msgs
    Just implement the receive_msg to handle received msg,
    and sent_msg to watch what the bot itself is doing(including the other handlers)
    Also note self.bot is a ref to the bot. this lets it be controlled from inside
    the handlers. Also, with self.bot.handlers, the other handlers can be used
    """
    def __init__(self, bot):
        self.bot = bot

    def description(self):
        """Return a description for the handler. Useful for !list/!help"""
        return "No Desciption"

    def receive_msg(self, msg):
        """Take every line/msg received and see if it needs to do something"""
        return None

    def sent_msg(self, sent_msg):
        """Take every line/msg sent by the bot and see if it needs to do something"""
        return None

    def priv_msg(self, destination, msg):
        """Takes destination nick/chan and message, forms and sends privmsg"""
        self.bot.text_send('PRIVMSG ' + destination +  ' :' + msg)    #dont forget :

    def reply_to(self, msg, reply):
         """Takes a privmsg and reply, and sends reply to appropriate chan/pm"""
         if self.is_priv_msg(msg): #make sure its a privmsg!
             self.priv_msg(self.chan_from(msg), reply)  #send msg to sender chan/pm

    def is_priv_msg(self, msg):
        """"
        Take a line, and see if it is a PRIVMSG
        Includes private chat, and channel msgs. Anything with PRIVMSG.
        To see if a private chat message(not in a channel), use .is_private()        
        """
        split_msg = msg.split()
        if len(split_msg) < 2:  #maybe change to 3?
            return False
        if split_msg[1].find('PRIVMSG') != -1:
            return True
        else:
            return False

    def chan_from(self, msg):
        """
        if a privmsg, get the channel(or nick if a pm) it's from
        :thebored!~thebored@localhost.lake PRIVMSG #boring :chan msg
        :thebored!~thebored@localhost.lake PRIVMSG botler :pm message
        Notice, the chan can be extracted from msg[2] for a chan msg. but for
        pms it needs to be parsed from msg[0]
        """
        if self.is_priv_msg(msg):
            if self.is_private(msg): #if private/pm, send directly to sender
                return self.nick_of(self.sender_of(msg))
            else:   #if its in a chan, use the place the message was sent
                return msg.split()[2]
        else:
            return None     #if not a chan/priv msg its a server

    def is_private(self, msg):
        """
        Take a msg, and see if it is a private chat message
        If it is a PRIVMSG, and the destination wasnt a channel, its private
        :thebored!~thebored@localhost.lake PRIVMSG botler :pm message
        """
        if self.is_priv_msg(msg):
            if (msg.split()[2] == self.bot.nick):
                return True
            else:
                return False
        else:
            return False

    def sender_of(self, msg):
        """
        Take a msg, check if it's a privmsg, and return the sender info/host
        like :thebored!~thebored@localhost.lake not just nick like thebored
        """
        if self.is_priv_msg(msg):
            self.bot.debug("\t\t\tThis was a PRIVMSG FROM %s" %  msg.split()[0], 5)
            return msg.split()[0]
        else:
            return None

    def nick_of(self, nick_host):
        """
        Take the host string, return the nick
        like :thebored!~thebored@localhost.lake -> thebored
        """
        return nick_host.split('!~')[0].lstrip(':')

    def is_authenticated(self, msg):
        """Takes a msg, returns True if it is from self.bot.master"""
        if self.is_priv_msg(msg):
            sending_nick = self.nick_of(self.sender_of(msg))
            if (sending_nick.find(self.bot.master) != -1):
                self.bot.debug('Received message from ' + self.bot.master + ' the god.', 3)
                return True
            else:
                self.bot.debug('Received message from %s not the god %s' % (sending_nick, self.bot.master), 3)
                return False
        else:
            self.bot.debug('Received message but its not a privmsg', 4)
            return False


class PONGHandler(IRCHandler):
    """PONG: PONG back the servers PING to stay connected"""
    def receive_msg(self, msg):
        if msg.split()[0].find('PING') != -1:   #if first word is PING
            self.bot.text_send ('PONG ' + msg.split() [1])   #PONG back

class OneLinerHandler(IRCHandler):
    """OneLiner: A collection of one line responses to prompts/commands"""
    def receive_msg(self, msg):
        if self.is_priv_msg(msg):
            if msg.find('hi ' + self.bot.nick) != -1:
                self.reply_to(msg, 'hi there. go fuck yourself.')
            if msg.find('!cheeseit') != -1: #chumps
                self.reply_to(msg,'Time to catch the next pimpmobile')
            if msg.find('!dildos') != -1: #why not?
                self.reply_to(msg,'B==D ' + msg.split()[4])

class QuoteHandler(IRCHandler):
    """quote: Send random line from a Quotes table in the  bot's .db"""
    def receive_msg(self, msg):
        if msg.find('!quote') != -1:
            with self.bot.db:
                cur = self.bot.db.cursor()
                cur.execute("SELECT * FROM Quotes ORDER BY RANDOM() LIMIT 1")
                row = cur.fetchone()                    #fetch the row
                self.bot.debug('Fetched Random Quote: %s' % str(row), 3)
                self.reply_to(msg, ('"%s"' % row[1]))    #send the quote

    def add_quote(self, quote, added_by):
        """Take a quote, and the nick adding it, and add it to the Quotes db"""
        with self.bot.db:
            cur = self.bot.db.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS Quotes(Id INTEGER PRIMARY KEY, Quote TEXT, Added_by TEXT)")
            cur.execute("INSERT INTO Quotes(Quote, Added_by) VALUES (?, ?)", (quote, added_by))
            self.bot.debug("Added a Quote to the DB!: %s added by %s" % (quote, added_by), 2)

class QuitHandler(IRCHandler):
    """quit: Makes the bot quit the server on with '!<botname> quit' command"""
    def receive_msg(self, msg):
        if self.is_authenticated(msg):
            if msg.find(self.bot.bang_name + ' quit') != -1:
                self.reply_to(msg, "Screw you guys, I'm going home.")
                self.bot.stop()

class JoinHandler(IRCHandler):
    """join: Make the bot rejoin its self.joinup list of chans with !rejoin"""
    def receive_msg(self, msg):
        if self.is_authenticated(msg):
            if msg.find('!rejoin') != -1:
                self.bot.join_chans(self.bot.join_up)
            if msg.find('!join') != -1:
                self.bot.join_chans([msg.split()[3]])

class LogHandler(IRCHandler):
    """logger: log all msgs to an sqllite file db"""
    def receive_msg(self, msg):
        self.log(msg)
    def sent_msg(self, msg):
        self.log(msg)
    def log(self, msg):
        self.bot.debug("\tSQL:\t'%s'" % (msg), 8)
        with self.bot.db:
            cur = self.bot.db.cursor()
            chan = self.chan_from(msg)
            cur.execute("CREATE TABLE IF NOT EXISTS IRCLog (Id INTEGER PRIMARY KEY, Msg TEXT, Chan TEXT)")
            cur.execute("INSERT INTO IRCLog (Msg, Chan) VALUES (?, ?)", (msg, chan))
            self.bot.debug("Added a msg to the DB Log!: '%s added from %s'" % (msg, chan), 2)

from datetime import timedelta

class SysHandler(IRCHandler):
    """sys: A collection of Linux sysinfo commands with '!sys <info>'"""
    def receive_msg(self, msg):
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
                    self.reply_to(msg, uptime_string) #reply uptime to sender
        if msg.find('!sys os') != -1:    #Reply with os version
            self.bot.debug('\tReceived !sys os command', 3)
            try:
                os_version = open('/proc/version', 'r')
            except IOError:
                self.bot.err('/dev/version file no-worky!')
            else:
                with os_version as f:
                    os_info = str(f.readline())
                    self.reply_to(msg, os_info)
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
                            self.reply_to(msg, line)
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
                            self.reply_to(msg, line.split(':', 1)[1])
                            break    #Get out of the for loop. Dont print >once
