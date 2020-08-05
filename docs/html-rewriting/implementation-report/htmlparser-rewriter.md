# Implementation report: HTMLParser 

## Time

I've spent about a day on this, but honestly most of the `HTMLParser` specific
work was definitely under the half a day mark. This is benefiting from the 
previous work and shared code.

`HTMLParser` is very simple, which means you'll get as far as you are going to
get very quickly.

The original work for HTMLParser was performed in a non-streaming way. When the
work for [LXML](lxml-rewriter-streaming.md) was done to make it streaming the
work was back-ported here quite quickly.

## Subjective experience

`HTMLParser` is a parser only, and absolutely nothing else. It doesn't build a
document tree or really anything else. It pulls the document apart and gives 
you the individual parts (like a tag was opened and it's called 'div'). 
Despite that it's actually kind of easy to get to something going.

The docs are basically one page 
(https://docs.python.org/3/library/html.parser.html) and it's _nearly_ enough, 
but doesn't actually document all of the behavior. It's very light on details.
I think you'd have to turn to tutorials or guess yourself.

The basic level here means you are totally on your own trying to construct 
valid HTML output. I'm not convinced it's even possible to transparently 
reproduce the page you got. It feels like it's going to be an absolute
edge-case factory to me.

There are also various comparisons etc. online and they weren't very 
complimentary. Particularly around handling of non-valid HTML. Which we will 
probably encounter.

## Non subjective experience

 * `HTMLParser` is much slower than LXML for parsing
 * I don't think `HTMLParser` can transparently proxy a page, meaning we can't 
   leave the parts of the page we don't care about alone. There were parts of 
   the page which rendered goody, and I couldn't work out why.
 * It does handle self closing tags, unlike the `LXML` streaming solution
 * It also doesn't attempt to insert tags to fix pages - and advantage for us
 * It takes `HTMLParser` more time to parse the page than our whole `LXML` 
   solution, often by a decent margin
 * On the other hand, the difference between parsing the page and rewriting it
   is negligible. As HTMLParser does it all in one pass. LXML on the other hand
   has parse, rewrite, render (again, all of these together are quicker than 
   HTMLParser doing nothing)
 * HTMLParser seems to do something or other to entities. I don't know if this 
   is what it does when it sees unicode or not, but it just "does what it 
   likes". I think unicode will be hard here too.
 