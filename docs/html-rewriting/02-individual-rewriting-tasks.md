# Rewriting tasks

## Overview

This page describes components, discovered over the investigation, which are
required for a complete solution to rewriting HTML pages.

Not all of these have been implemented fully or successfully and this
list is not exhaustive.

# General issues

## User-Agent

Having an absent or unexpected `User-Agent` string can cause sites to block you
as a robot or return a degraded version of the site.

The easiest method is to send the user agent which the browser sent to us:

 * It's guaranteed to be a real agent string
 * It means any browser specific tweaks would be appropriate (go away IE6 etc.) 

## Cookies

Cookies are vast and complicated problem, but there are number ok high level 
take aways:

### Services use and check cookies

 * Some services won't return the right content without a specific cookie 
 (GDPR, privacy etc.)
 * Some appear to detect missing or broken ones and bounce you about
 * The core of any authenticated resource
 
### Cookies cause problems by themselves

 * Most cookies are set without a domain, which means they pick up our domain
 * That's "good" in that we are allowed to see them and use them
 * It's bad because: 
   * Without doing anything about it we end up with huge numbers of cookies
   * This can result in so many cookies that sites refuse to process the header
   * This **very obviously presents a security problem** as we will pass cookie 
   data from one domain to another

### Cookies are more complicated than I really understand

There are quite a lot of complexity around various different additional options
such as same-site and secure settings which may be relevant, but I don't
really understand.

### Required fixes

 * We must rewrite cookies so that they are only associated with the relevant site
 * We cannot modify their names as the client side won't find them
 * This can be achieved by setting a path which matches the site only on our proxy
 * So if our urls look like `rewrite/http/example.com/path` we can set the path 
 accordingly and the browser will scope the cookies appropriately
 * This must happen both client and server side

# Page content rewrites

## Tag attributes

In general the main job is rewriting URLS in tag attributes. See [details of
rewriting URLs](03-rewriting-urls.md).

## Images sources (`src, srcset`)

Images are pretty well behaved and can be mostly left alone.

In times gone by sites would often block you for 
["hot linking"](https://en.wikipedia.org/wiki/Inline_linking).
This doesn't seem as common any more, but at least one site was checking
the `Referer` header.

We can't set the right one, but we can disable it. This can be achieved in 
two ways:

 * [Add a tag to stop the browser](https://stackoverflow.com/questions/5033300/stop-link-from-sending-referrer-to-destination)
 * Drop the header in NGINX

`srcsets` are a new spec with it's own special syntax. To handle this you need
to write your own parser for it. Seeing as we don't rewrite images, it's mostly
fine.

## Form submissions

We obviously can capture and pass on form submissions, but there is a big 
question of whether we _should_. 

Some pages rely on this to submit details for GDPR or other policy acceptance
however this **obviously presents a privacy problem** where we may be privy
to passwords or other sensitive content.

## JS content

_Whatever is said here goes for inline `script` blocks as well._

There are two major problems with Javascript:

 * Getting it in the first place due to CORS issues
 * Things it gets up to after you have loaded it
 
For CORS to work it generally requires us to proxy the content so the origin
matches the page. As long as we are running from the same origin we don't 
need CORS headers, as no cross origin request is taking place.

The scope of things Javascript can get up to is long, and covered in the next
section.

# Client side events

There are a number of javascript calls that need to be mocked or otherwise worked
around for pages to work well. This is the most uncertain portion at the moment
and doesn't include

## Get/set cookie

Javascript can and does set cookies a lot. Any that end up on the default domain
can cause problems mentioned above. Cookie interception has to:

 * First prevent build up and cross contamination of cookies (blocking all would do)
 * Map cookies to the path (or some other method) to ensure the right cookies get through

## xhr/fetch

Javascript often creates URLs on the fly which are not detectable with regexes etc.

These are then used to make fetch requests. If these requests are for more javascript
or other CORS sensitive resources, they will fail without being proxied.

## History events

Various calls like `pushState`, `replaceState` can end up changing the URL
either just visually, or actually cause a page reload.

This is a problem for two reasons:

 * It causes an error to attempt to replace the domain this way
 * This can cause script failures and therefore missing content
 * It provides a way to escape our wrapping

## window.location

Window location is relevant in two main ways:

 * Setting it which causes page reload and escape
 * Reading from it causing errors
 
Window location is difficult to patch as it's a protected variable and cannot
be trivially redefined.

A solution to reading in particular appears to be the key to fixing a lot of 
single page app style pages, which use the current location to determine which
content to show. In this case we would need to return the original URL.

## More?

The general trend for the client side seems to be finding out about something
new every time a page fails. This list is not exhaustive

# Nice to haves

## Web workers

Web workers will not load cross domain. It's not clear if this is a content
blocking issue, but it raises errors in the console.

## CSS content

_Whatever is said here goes for inline styles and `style` attributes as well._

CSS is generally well behaved with the exception of fonts which suffer from 
CORS issues and so must be proxied in order to work.

## JSON manifests and contents

Certain sites read a `manifest.json` which will be blocked on CORS if we don't
proxy it. Not sure this is a content blocking issue.

The content also contains URLs which might need to be rewritten to work 
correctly.