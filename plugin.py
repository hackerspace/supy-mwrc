###
# Copyright (c) 2012, Martin Milata
# Published under WTFPL.
###

import json
import time
import urllib.request, urllib.parse, urllib.error

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.ircmsgs as ircmsgs
import supybot.schedule as schedule
import supybot.callbacks as callbacks

def iso_to_timestamp(s):
    st = time.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
    return int(time.mktime(st))

filename = conf.supybot.directories.data.dirize('MediaWikiRecentChanges.last')

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
        self.irc = irc
        self.pluginConf = conf.supybot.plugins.MediaWikiRecentChanges
        self.last_change = self.loadTimeStamp()
        self.scheduleNextCheck()

    def die(self):
        # remove scheduler event
        try:
            schedule.removeEvent('mwrcEvent')
        except KeyError:
            pass
        self.__parent.die()

    def scheduleNextCheck(self):
        def event():
            self.log.debug('MWRC: Firing scheduler event')
            try:
                self.announceNewChanges(self.irc)
            finally:
                self.scheduleNextCheck()

        self.log.debug('MWRC: Scheduling next check')
        schedule.addEvent(event,
            time.time() + self.pluginConf.waitPeriod(),
            'mwrcEvent'
        )

    @wrap
    def wikichanges(self, irc, msg, args):
        """takes no arguments

        Prints latest changes on MediaWiki instance.
        """
        try:
            changes = self.getRecentChanges()
        except Exception as e:
            irc.reply('Error: ' + utils.web.strError(e))
        else:
            for change in changes:
                irc.reply(change[1], prefixNick=False)

    def getRecentChanges(self):
        url = self.buildQueryURL()
        #self.log.debug(url)
        json_response = utils.web.getUrl(url)

        response = json.loads(json_response)
        messages = []
        for change in response['query']['recentchanges']:
            if change['type'] == 'edit':
                msg = 'User {user} modified {url}'
            elif change['type'] == 'new':
                msg = 'User {user} created {url}'
            else:
                self.log.warning('Ignoring unknown change type: %s',
                    change['type'])
                continue

            msg = msg.format(user=change['user'],
                url=self.buildTitleURL(change['title'])
            )

            if change['comment']:
                msg = '{0} - {1}'.format(msg, change['comment'])

            change_ts = iso_to_timestamp(change['timestamp'])
            messages.append((change_ts, msg))

        return messages[::-1]

    def announceNewChanges(self, irc):
        try:
            changes = self.getRecentChanges()
        except Exception as e:
            self.log.error('MWRC: Cannot retrieve recent changes: %s' %
                           utils.web.strError(e))
            return

        changes = [change for change in changes if change[0] > self.last_change]

        try:
            self.last_change = max([change[0] for change in changes])
            self.saveTimeStamp(self.last_change)
        except ValueError:
            pass

        messages = [change[1] for change in changes]
        chans = 0
        for channel in list(irc.state.channels.keys()):
            if self.pluginConf.announce.get(channel)():
                chans += 1
                for msg in messages:
                    irc.queueMsg(ircmsgs.privmsg(channel, msg))

    def buildQueryURL(self):
        url_parts = list(urllib.parse.urlparse(self.pluginConf.apiUrl()))

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

        url_parts[4] = urllib.parse.urlencode(query)
        return urllib.parse.urlunparse(url_parts)

    def buildTitleURL(self, title):
        template = self.pluginConf.pageUrl()
        return template.format(page=title.replace(' ', '_'))

    def loadTimeStamp(self):
        try:
            with open(filename, 'r') as f:
                contents = f.read()
            return int(contents, 10)
        except Exception as e:
            self.log.error('MWRC: cannot load last change timestamp: %s' % e)
        return 0

    def saveTimeStamp(self, last_change):
        try:
            with open(filename, 'w') as f:
                f.write(str(last_change))
        except Exception as e:
            self.log.error('MWRC: cannot save last change timestamp: %s' % e)


Class = MediaWikiRecentChanges


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
