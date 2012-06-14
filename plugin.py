###
# Copyright (c) 2012, Martin Milata
# Published under WTFPL.
###

import json
import time
import urllib
import urlparse

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

def iso_to_timestamp(s):
    st = time.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
    return int(time.mktime(st))

class MediaWikiRecentChanges(callbacks.Plugin):
    """
    Announces recent changes of a MediaWiki instance. You need to set the
    'url' config variable to the one you want to watch and the enable the
    'announce' parameters for channels where you want the change notifications
    to appear.
    """

    def __init__(self, irc):
        self.__parent = super(MediaWikiRecentChanges, self)
        self.__parent.__init__(irc)
        self.pluginConf = conf.supybot.plugins.MediaWikiRecentChanges
        # after loading the plugin, do not do update immediately
        self.last_update = time.time()
        # What should i use here? ideal behaviour would be to save state and
        # remember the timestamp of the last change. Using zero here means the
        # bot will announce changes on every startup. Using time.time() would
        # mean that the bot will announce only changes made after the plugin
        # was loaded, provided that the clocks of bothost and wiki are
        # synchronized and in the same timezone (=problem)...
        self.last_change = 0

    # freenode seems to send ping every 2 minutes
    def __call__(self, irc, msg):
        self.__parent.__call__(irc, msg)
        irc = callbacks.SimpleProxy(irc, msg)
        now = time.time()

        if now > self.last_update + self.pluginConf.waitPeriod():
            self.log.debug('MWRC: updating')
            self.last_update = now
            # run this in separate thread?
            self.announceNewChanges(irc)
        else:
            self.log.debug('MWRC: not updating')
            pass

    def wikichanges(self, irc, msg, args):
        try:
            changes = self.getRecentChanges()
        except Exception as e:
            irc.reply('Error: ' + utils.web.strError(e))
        else:
            for change in changes:
                irc.reply(change[1], prefixNick=False)
    wikichanges = wrap(wikichanges)

    #def resetlastchange(self, irc, msg, args):
    #    self.last_change = 0
    #    irc.replySuccess()
    #resetlastchange = wrap(resetlastchange)

    def getRecentChanges(self):
        url = self.buildQueryURL()
        #self.log.debug(url)
        json_response = utils.web.getUrl(url)

        response = json.loads(json_response)
        messages = []
        for change in response['query']['recentchanges']:
            if change['type'] == 'edit':
                msg = u'User {user} modified {url}'
            elif change['type'] == 'new':
                msg = u'User {user} created {url}'
            else:
                self.log.warning('Ignoring unknown change type: %s',
                    change['type'])
                continue

            msg = msg.format(user=change['user'],
                url=self.buildTitleURL(change['title'])
            )

            if change['comment']:
                msg = u'{0} - {1}'.format(msg, change['comment'])

            msg = msg.encode('utf-8')
            change_ts = iso_to_timestamp(change['timestamp'])
            messages.append((change_ts, msg))

        return messages[::-1]

    def announceNewChanges(self, irc):
        changes = self.getRecentChanges()
        self.log.debug('Changes total: %s', len(changes))
        self.log.debug('Ts: %s %s', self.last_change, map(lambda ch: ch[0],
            changes))
        changes = filter(lambda change: change[0] > self.last_change, changes)
        self.log.debug('Changes filtered: %s', len(changes))

        try:
            self.last_change = max(map(lambda change: change[0], changes))
        except ValueError:
            pass

        messages = map(lambda change: change[1], changes)
        chans = 0
        for channel in irc.state.channels.keys():
            if self.pluginConf.announce.get(channel)():
                chans += 1
                for msg in messages:
                    irc.reply(msg, prefixNick=False, to=channel)
        self.log.info('Sent %s changes to %s channels', len(messages), chans)

    def buildQueryURL(self):
        url_parts = list(urlparse.urlparse(self.pluginConf.url()))

        if not url_parts[2].endswith('/'):
            url_parts[2] += '/'
        url_parts[2] += 'api.php'

        query = {
            'action': 'query',
            'list'  : 'recentchanges',
            'format': 'json',
            'rcprop': 'user|comment|timestamp|title',
            'rctype': 'edit|new',
        }
        if self.pluginConf.namespaces():
            query['rcnamespace'] = '|'.join(map(str,
                self.pluginConf.namespaces()))
        if not self.pluginConf.showMinor():
            query['rcshow'] = '!minor'
        query['rclimit'] = self.pluginConf.limit()

        url_parts[4] = urllib.urlencode(query)
        return urlparse.urlunparse(url_parts)

    def buildTitleURL(self, title):
        url_parts = list(urlparse.urlparse(self.pluginConf.url()))

        if not url_parts[2].endswith('/'):
            url_parts[2] += '/'
        url_parts[2] += title.replace(' ', '_')

        return urlparse.urlunparse(url_parts)


Class = MediaWikiRecentChanges


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79: