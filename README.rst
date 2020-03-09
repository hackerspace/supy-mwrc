====================================================
MediaWiki recent changes tracking plugin for supybot
====================================================

OVERVIEW
--------

This is a supybot plugin that watches recent change list of MediaWiki instance
and announces them to a channel(s).

INSTALLATION
------------

Copy (or symlink) the git repository to your bot's plugin/ directory and
*rename* it to *MediaWikiRecentChanges*. Load it and set the 'apiUrl',
'pageUrl' and 'announce' parameters - see the configuration documentation for
details (*config help* command).

KNOWN BUGS
----------

* Only one wiki instance can be watched. I was too lazy to properly implement
  possibility of M channels watching N wikis.

LICENSE
-------

`WTFPL <http://sam.zoy.org/wtfpl/>`_.
