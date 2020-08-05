# Implementation report: LXML streaming solution

## Time

Again, hard to pin down. It wasn't hard, but non LXML specific plumbing had to
be in place to get this working. I'd say it was quite quick to work with, apart
from documentation quirks (see below). 

## Subjective experience

The basics are well documented for the 
["target" parser](https://lxml.de/parsing.html#the-target-parser-interface) 
(the most streamy of the various parsers). But the specifics are woefully
under documented. 

The docs say "you can pass a target object to the parser" and provide an 
example, but the example is a subset of the total methods supported. Finding
out the rest proved mostly impossible from the docs. I was forced to implement
a class with `__attr__` magic method and observe which methods were called.

Annoyingly the methods are almost all present and handling doctypes is easy,
but undocumented.

## Non-subjective experience

### Most of the caveats of the  HTMLParser solution remain

 * We are using a very low level parser (no objects representing tags or anything) 
 * This means we have to translate the page more thoroughly for things we don't even care about
 * It's far from a transparent rewrite

### They are extremely similar with a few differences

 * LXML is faster, and seems to handle encoding better
 * It's speed is comparable with the non-streaming LXML
 * Self closing tags are experienced as two events (open and close) - This is 
 bad and causes us to emit rubbish
 * LXML attempts to fix the page by adding closing tags for missing things - 
  this is kind of a disaster for us

