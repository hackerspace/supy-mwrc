###
# Copyright (c) 2012, Martin Milata
# Published under WTFPL.
###

import json
import time
import urllib
import urllib2
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

def timestamp_to_iso(ts):
    st = time.gmtime(ts)
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', st)

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

        self.conf_last_change = 0
        self.conf_channels = ['#test48']

    # freenode seems to send ping every 2 minutes
    def __call__(self, irc, msg):
        self.__parent.__call__(irc, msg)
        irc = callbacks.SimpleProxy(irc, msg)
        now = time.time()

        if now > self.last_update + self.pluginConf.waitPeriod():
            self.log.debug('__call__: updating')
            self.last_update = now
            # run this in separate thread?
            self.check_recent_changes(irc)
        else:
            self.log.debug('__call__: not updating')
            pass

    # XXX: keep a command for unconditionally listing changes?
    # catch and print exceptions here? web.py / strError
    # XXX: help string
    def wikichanges(self, irc, msg, args):
        """
        takes no arguments

        Show recent changes of the wiki.
        """
        self.check_recent_changes(irc)
    wikichanges = wrap(wikichanges)

    def resetlastchange(self, irc, msg, args):
        self.conf_last_change = 0
        irc.replySuccess()
    resetlastchange = wrap(resetlastchange)

    def check_recent_changes(self, irc):
        # XXX compare times first

        url = self.build_query_url()
        self.log.debug(url)
        fh = urllib2.urlopen(url)
        json_response = fh.read()

        response = json.loads(json_response)
        messages = []
        for change in response['query']['recentchanges']:
            # skip if we've already seen this change
            if iso_to_timestamp(change['timestamp']) <= self.conf_last_change:
                continue

            if change['type'] == 'edit':
                msg = u'User {user} modified {url}'
            elif change['type'] == 'new':
                msg = u'User {user} created {url}'
            else:
                self.log.warning('Ignoring unknown change type: %s',
                    change['type'])
                continue

            msg = msg.format(user=change['user'],
                url=self.build_title_url(change['title'])
            )

            if change['comment']:
                msg = u'{0} - {1}'.format(msg, change['comment'])

            msg = msg.encode('utf-8')
            messages.append(msg)
            #irc.reply(msg, prefixNick=False)

        try:
            new_last_change = max(map(lambda change: iso_to_timestamp(change['timestamp']),
                response['query']['recentchanges']
            ))
            self.conf_last_change = new_last_change
        except:
            pass

        messages = messages[::-1]
        for channel in self.conf_channels:
            for msg in messages:
                irc.reply(msg, prefixNick=False, to=channel)
            self.log.debug('Sent %s changes to channel %s', len(messages), channel)

    def build_query_url(self):
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
        if self.conf_last_change:
            query['rcstart'] = self.conf_last_change + 1
        if not self.pluginConf.showMinor():
            query['rcshow'] = '!minor'
        query['rclimit'] = self.pluginConf.limit()

        url_parts[4] = urllib.urlencode(query)
        return urlparse.urlunparse(url_parts)

    def build_title_url(self, title):
        url_parts = list(urlparse.urlparse(self.pluginConf.url()))

        if not url_parts[2].endswith('/'):
            url_parts[2] += '/'
        url_parts[2] += title.replace(' ', '_')

        return urlparse.urlunparse(url_parts)


Class = MediaWikiRecentChanges


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
