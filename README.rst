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
*rename* it to *MediaWikiRecentChanges*. Load it and set the 'url' and
'announce' parameters - see the configuration documentation for details
(*config help* command).

KNOWN BUGS
----------

* If one sets url to e.g. http://example.com/wiki/, then the API has to reside
  at http://example.com/wiki/api.php and pages accessed through
  http://example.com/wiki/Page_Name. This is generally not the case (wikipedia
  being a counterexample). Solution is to use two urls for configuration, some
  more elegant variation thereof, or automatically figuring out the urls of
  pages via API.

* Only one wiki instance can be watched. I was too lazy to properly implement
  possibility of M channels watching N wikis.

* It would probably be better if the bot stored timestamp of the last seen
  change so that we couldn't see them multiple times on plugin reload or bot
  restart.

LICENSE
-------

`WTFPL <http://sam.zoy.org/wtfpl/>`_.
