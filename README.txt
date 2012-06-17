OVERVIEW

   This is a supybot plugin that watches recent change list of MediaWiki
   instance and announces them to a channel(s).

KNOWN PROBLEMS

 * If one sets url to e.g. http://example.com/wiki/, then the API has to reside
   at http://example.com/wiki/api.php and pages accessed through
   http://example.com/wiki/Page_Name. This is generally not the case (wikipedia
   being a counterexample). Solution is to use two urls for configuration, some
   more elegant variation thereof, or automatically figuring out the urls of pages
   via API.

 * Only one wiki instance can be watched. I was too lazy to properly implement
   possibility of M channels watching N wikis.
