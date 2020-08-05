# URL Rewriting

## Overview

Many individual sounding problems like:

 * Handling form submissions
 * Showing images
 * Solving certain CORS issues 
 * Catching links in pages
 
Often boil down to two solutions: 

 * Taking a URL from attribute in a tag and changing it
 * Doing many complex things with Javascript
 
### This page discusses rewriting URLs in attributes

The lessons here are general but are presented through the medium of our 
specific solution.

### In a nutshell

The decision of what and how to rewrite a particular URL is determined by:

 * Content type - We will handle CSS differently from Jpegs
 * Context - Often used to imply content type, but potentially interesting on it's own
 * URL type - Different styles of URLs require different approaches
 
We use the context to apply rules and tell what kind of rewriting to do.

## Part 1 - We use a ruleset based on context and actions to determine what to rewrite

The system currently uses context object which contains:

 * URL extension (e.g. `js` or `png`)
 * Tag name
 * Attribute name
 * The value of the `rel` attribute - To descriminate between different types of `link` tag
 
We then use a rule to match that context to an action like `rewrite_html` or 
`proxy_static`. These different rules tell us to rewrite the URL in a specific 
way. 

This list of context is not exhaustive, and could need to be extended.

### We support six different URL rewriting actions

 * `NONE` - Don't do anything at all
 * `MAKE_ABSOLUTE` - Convert the URL to be absolute
 * `PROXY_STATIC` - Proxy the content from us, but leave it unchanged
 * `REWRITE_HTML` - Rewrite the URL so it will go through our HTML rewriting
 * `REWRITE_CSS` - Rewrite the URL so it will go through our CSS rewriting
 * `REWRITE_JS` - Rewrite the URL so it will go through our JS rewriting

Currently `MAKE_ABSOLUTE` is not used, as it's pretty much handled by putting in
an appropriate `<base>` tag and letting the browser do it.

### Our rules are stored in YAML

As an example here are some of our rules, which are applied on a first match
basis:

```yaml
rules:
  - match: {ext: [png, jpg, jpeg, gif, svg]}
    action: NONE

  - match: {tag: a, attr: href}
    action: REWRITE_HTML

  - match: {tag: link, rel: stylesheet}
    action: REWRITE_CSS
```

For example, `<a href="my_dog.png">` would match both of the first rules, but
the image one would apply first, meaning we would take no action.

### We only use certain attributes as a filter and optimisation

This is largely an optimisation, but also prevents perverse situations. An `id`
attribute could for example, end in something which would cause us to think it
was CSS.

The current list of "interesting" tag attribute combinations is shown below.
This shows an attribute is _capable_ of being rewritten, not that we necessarily
need to.

```
"a": {"href", "src"},
"link": {"href"},
"img": {"src", "srcset", "data-src"},
"image": {"src", "srcset", "data-src"},
"form": {"action"},
"iframe": {"src"},
"script": {"src"},
"blockquote": {"cite"},
"input": {"src"},
"head": {"profile"},
```

Note that the `data-src` is likely a custom addition for a certain javascript
library, but it's common enough to include. There are probably an unknowable
number more like this.

----

## Part 2 - Once we've decided to rewrite we act differently based on URL

### Different URLs have to be handled differently

These can come in many flavours:

 * Relative - Very common, mostly fixed with appropriate `<base>` tag
 * Absolute - Not a problem in general unless we need to intercept
 * Scheme unspecified - URLS can be specified as `//example.com/path` which causes the scheme to picked up from context
 * Non HTTP scheme - `data` or `ftp` etc. We leave these alone
 * Embedded - URLs in streams of other data, like inline styles
 * Specific syntax - Certain attributes (like `srcset`) have a specific syntax of their own 

### Relative, absolute and scheme unspecified can all be normalised

For these types of URL we can fill in the missing parts and carry on. This is
the bread and butter case.

All missing parts are taken from the original URL. If we need to run this through
the app or NGINX, the resultant URL is modified again.

### URLs embedded in `style` tags require full CSS rewriting

To rewrite arbitrary CSS in tags we can leverage whatever solution we have for
rewriting CSS and apply it. 

This is also true of inline CSS, Javascript and events added to tags (e.g. `onclick`). We don't
currently do this.

### We can write parsers for `srcset` but don't really need to

Images don't seem to require proxying so far, so there's no need to rewrite
these tags, but doing so requires writing a specialised parser. We've done this
and it works, but it complicates things a lot.

### Everything else is ignored

Any URL which doesn't start with `http://` or `https://` will be left alone.

The most common cases are:

 * `data` - The image is inline already, no rewrite required
 * `emailto` - Again no rewrite required
 * `ftp` - We can't really rewrite this either
 * Custom schemes - Product specific schemes like [the Steam browser protocol](https://developer.valvesoftware.com/wiki/Steam_browser_protocol)

----

## Summary

* We look for certain attributes on certain tags (filter + optimisation)
* We then convert them to a context based on tag name, attribute, rel and extension
* We map this context to an action based on a ruleset
* If we decide to rewrite we modify the URL depending on it's type
* Many URLs are not mappable