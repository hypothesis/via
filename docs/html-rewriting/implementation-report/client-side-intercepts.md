# Implementation report: Client side intercepts

## Time

This has had a half day and then some, but a lot of that wasn't really related
to developing the JS as such, but trying to work out why we _couldn't_. 

That said, you can get something which monkey patches and works for a lot of
scripts very quickly. It just doesn't solve the whole issue at all.

Subsequent work added more sophisticated mocking of built in methods, and this
certainly exceeded the half day.

## Subjective experience

This is going to be a total slog of CORS, cookies and security issues. As a
result this is always going to be mixed mode working between front and
back-end. I can't see nice tickets where a front-end only, or back-end task
could be separated. 

This is very 80/20, and the first part is going without much effort, and
actually enables a lot of scripts. Some of the rest could be very hard or
impossible to progress.

Javascript is well documented of course, but my feeling is we are quickly
going to run into different browser differences. There is also a case of the
surface area we are trying to cover. Modern browsers are absurdly complex. We
patched out two things initially and I was up to 5 before I stopped. There are
more and some of what I'm doing doesn't work.

It's very hard to know what the hell is going on in general in a modern
website. The BBC doesn't work, but it also loads an obfusticated Javascript
which expands to being 55,000 lines long when reformatted. They often load a
lot of scripts (which load other scripts) and anything failing anywhere could,
or could not, be related to rendering errors.

_(edit) The BBC was eventually fixed by patching `window.location`, but good
luck working that out without just randomly trying it._

All we can generally say is that fixing something is more likely to make the
page render correctly.

### Development environment issues

We weren't really setup for Javascript dev and it shows. 

The first major problem we had was very aggressive caching making development
very difficult. There is now a flag to disable this.

The second was a wall of CORS issues. In the original "solution" we turned on
a couple of CORS headers for local dev and left it at that. This was both
unnecessary and insufficient. 

We don't need this in live as all requests come from the same domain (NGINX).
The dev NGINX has been updated to work this way too by proxying the content
running on the app outside the service.

## Non subject experience

 * It's going to be an essential component for any good solution
 * It works for many scripts (for example Youtube videos now play)
 * It fails for many scripts
 * This doesn't help us yet with Javascript templating and single page app
 type stuff. I'm not sure if anything can. (Maybe a post page load complete
 hook to do JS rewriting in page?)
 * Many of requests I saw were actually attempts to report previous 
 javascript errors to Sentry and the like. This means when comparing the 
 original and proxied site, there are often many more calls to proxy than the
 original
 * Sites often make continuous connections as they work (youtube.com) meaning 
 a page left open will create continuous demand on NGINX
 * I'm not sure there's a bottom to this well

