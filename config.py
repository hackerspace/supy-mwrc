###
# Copyright (c) 2012, Martin Milata
# Published under WTFPL.
###

import re

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('MediaWikiRecentChanges', True)


MediaWikiRecentChanges = conf.registerPlugin('MediaWikiRecentChanges')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(MediaWikiRecentChanges, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))

class NameSpaces(registry.Value):
    """Value must be list of namespace numbers separated by commas, or the
    string 'all' for all namespaces. (Main namespace should be the number 0,
    which is the default.)"""
    def set(self, s):
        if s == 'all':
            self.setValue([])
            return

        try:
            L = re.split(r'\s*,\s*', s)
            L = map(int, L)
            self.setValue(L)
        except ValueError:
            self.error()

    def setValue(self, v):
        if not all(map(lambda n: n >= 0, v)):
            self.error()
        super(NameSpaces, self).setValue(v)

    def __str__(self):
        values = self()
        if values == []:
            return "all"
        else:
            return ', '.join(map(str, values))

class CommaSeparatedListOfNonNegativeIntegers(registry.SeparatedListOf):
    """Value must be list of integers separated by commas."""
    Value = registry.NonNegativeInteger
    def splitter(self, s):
        return re.split(r'\s*,\s*', s)
    def joiner(self, L):
        return ', '.join(map(str, L))
    def set(self, s):
        L = self.splitter(s)
        try:
            for (i, s) in enumerate(L):
                v = self.Value(int(s), '')
                L[i] = v()
            self.setValue(L)
        except ValueError:
            self.error()


conf.registerGlobalValue(MediaWikiRecentChanges, 'url',
    #XXX#registry.String('http://en.wikipedia.org/wiki/', """URL of the MediaWiki
    registry.String('http://wiki.base48.cz/', """URL of the MediaWiki
    instance (e.g. http://en.wikipedia.org/wiki/)."""))
conf.registerGlobalValue(MediaWikiRecentChanges, 'namespaces',
    NameSpaces([0], """Comma separated list of
    namespace numbers that should be watched for changes. Default is '0' for
    main namespace. Empty list means all namespace."""))
conf.registerGlobalValue(MediaWikiRecentChanges, 'showMinor',
    registry.Boolean(False, """Whether to show edits marked as minor."""))
conf.registerGlobalValue(MediaWikiRecentChanges, 'limit',
    registry.PositiveInteger(5, """Maximal number of changes to show each
    time."""))
conf.registerGlobalValue(MediaWikiRecentChanges, 'waitPeriod',
    #XXX#registry.PositiveInteger(1800, """Number of seconds to wait between each
    registry.PositiveInteger(200, """Number of seconds to wait between each
    check."""))
conf.registerChannelValue(MediaWikiRecentChanges, 'announce',
    registry.Boolean(False, """Announce changes on this channel."""))
conf.registerGlobalValue(MediaWikiRecentChanges, 'lastChange',
    registry.NonNegativeInteger(0, """This variable is used to store the time
    of the last retrieved update. This is an ugly hack and you should not
    change this unless you are debugging the plugin;)"""))



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
