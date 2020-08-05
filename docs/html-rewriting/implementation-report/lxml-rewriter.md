# Implementation report: LXML in-memory solution

## Time

The time spent on this is definitely more than half a day, but that's a bit 
unfair, as that's on me for taking this further than it needed. It also suffers
from being the first and incurred some first movers disadvantage:

 * I was using this to learn what did or didn't need to be rewritten
 * I had to work out how to inject the client (not in LXML, just what code 
 we need from via to make it happen)
 * Some extra work to make the harness helpful for testing

Initial progress was good and I managed to move onto more esoteric issues 
quite quickly.

## Subjective experience

LXML is good, but quite old school. The docs (https://lxml.de/index.html) are
thorough but hard to navigate. It constantly lends the feeling you can do 
whatever you want, but it might take some figuring out. The API reference 
(https://lxml.de/api/index.html) is actually Javadoc (chuckle).

The code is reasonably easy to debug and work out what is wrong. It's actually
Python for a while before it hits `libxml` so you don't just hit a wall of 
C bindings.

It has lots of handy functions for doing certain things. The problem is if the
functions don't do what you want, you have to it yourself. For example there is
a function for making all URLs in a page absolute and iterating over them 
(god yes), but it doesn't understand newer places links can be like img data
tags. It's a timesaver still, but it's resulted in me not knowing exactly what
I'm rewriting or not.

A particular unpleasantness is the myriad of parsing functions and subtle
differences between what you get back. There are `DocumentTrees`,
`ElementTrees`, `Elements`, `HTMLElements`, `Nodes`, `TextNodes`. Many of these
are children of each other or have significant differences, but it's not
obvious to me why.

My gut feel is, if you can carve out the small part of the functionality you
need and stick to it, it will be fine to maintain. There are lots of docs and
tutorials, but they often cover the same types of examples.

## Non subjective experience

* It's pretty fast (50ms for rewriting a whole page)
* LXML attempts to "fix" broken pages by inserting extra tags, this can really
 mess things up
* Encoding is going to be a headache. The docs suggest using
 [`bs4.UnicodeDammit`](https://www.crummy.com/software/BeautifulSoup/bs4/doc/),
 but it's unacceptably slow. 10 seconds slow.
 * Many of the functions return fragment type objects which don't consider the
 document a document. I can't work out how to get it to preserve the doc-type
 declaration as a result, which lead to lots of weirdness
