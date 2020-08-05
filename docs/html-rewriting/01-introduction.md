# Via HTML Rewriting Investigation

## Abstract

Original Via rewrites web pages to allow us to insert the client into them for
users who do not have the browser plugin installed. It rewrites pages well but
is a resource hog and crashes causing support requirements.

During the course of the sprint many different rewriting techniques were 
attempted. At their best they achieved rough parity of rewriting accuracy with
original Via. However, no single solution achieved this consistently.

It is unknown how much effort would be required to do consistently reach an 
acceptable level of accuracy. The effort required to do so is likely to be 
significant, unpredictable and on-going. This will create a cost to the 
business and require involvement of members of multiple teams.

Other solutions should be considered along-side maintaining our own home grown 
HTML rewriting solution. 

## Overview

Originally this document was conceived of as a comparison between techniques
for creating our own HTML rewriter, but overtime it became obvious that only 
certain techniques would work, and many were required at once.

This document therefore is more of a guide to those decisions and background
on the rewriting problem.

### We want a more reliable rewriter

We want:

 * Something which doesn't crash
 * Doesn't use a large amount of CPU, threads, memory or other resources
 * Is on a supported platform (i.e. not Python 2.7)
 * Is easy to maintain
 * Has good accuracy when rewriting pages
 
We want this because:

 * We don't want to waste developer time
 * We need to be able to scale up to more users
 * Slow and crashing services give a bad user experience

### This document is intended to be read on it's own

This document presents the high level outcomes and decisions. In many cases it
links to more detail on items, but reading this detail is not required to 
understand the summary. 

If you are in a hurry do not follow any links. 

### The approach to this document has changed

Originally this was conceived of as a comparison between a number of techniques
to see which were stronger or weaker in certain circumstances. It was predicted
that there would be many routes to a solution and the job would be to pick the
best.

This largely hasn't happened. Instead it has become relatively obvious that 
there aren't really many different alternatives (of those explored) for two 
main reasons:

 * Certain techniques can be clearly ruled out based on one or two short 
   comings
 * Any good solution will likely require many of the components together
 
The document which was originally in mind, and therefore the data gathered for
it, skewed towards comparing the techniques in various ways. These data will
be presented for the sake of completeness, but are much less relevant now.

# We have answers to some questions

## Can we write a 'good enough' HTML rewriter with a low amount of effort?

> No

Our hope was that we could get a rough version that might work for many pages
with lower fidelity. In reality pages tend to work or not in a fairly binary
way. This means lower effort invested results in fewer pages working, not a 
lower quality over many working pages.

There does not appear to be a simple solution that does not have an 
unacceptably high page failure rate. 

A very non scientific guess of percentage usable pages vs. effort:

 * 60% - Adding the base tag alone - Extremely low effort
 * 80% - The above + back-end HTML rewriting and static proxying - Medium effort
 * 85% - The above + simple Javascript intercepts - Medium effort
 * 90%+ - The above + Cookies and complex Javascript rewriting - High effort

90% sounds like a high number, but it translates to our product failing on one
in ten sites a customer tries it on. This isn't good at all.

This problem has also characteristics that make it [mentally as well
 as technically difficult](extras/the-brain-trap.md).

## Would our own rewriter more reliable than old Via?

> Likely, but unproven

Our product is smaller, and simpler, and so is likely to have less ability to
fail. The stack of Python, Pyramid and NGINX is well understood and deployed
in our other apps. So there are reasons to believe this will be reliable.

However... we are beholden to making large number of calls to third parties.
These parties can return any data, at any speed they like. Some of the 
instability may be inherent in making connections to third parties.

We also have _no evidence_ to show we would be any more reliable. The safest
assumption here is that until proven, we should assume we won't be.

## Would our own rewriter have lower resource consumption than old Via?

> We don't know

A similar story. There are reasons to believe we will be. The basis of Via
(`pywb`) is a library which is attempting to do far more than we use it for.
It also appears to handle all rewriting and webserving responsibilities in
python.

`pywb` might be a very good rewriter, but it's unlikely it's as good a 
webserver as the combination of NGINX and gunicorn. On the other hand, certain
python web frameworks (like Tornado) are optimised for many asynchronous IO 
bound operations. 

So Python is unlikely to compete with the functions performed by NGINX, but 
there are frameworks that are faster for this for the non-NGINX portions than 
Pyramid. For all we know `pywb` could have more in common with Tornado than 
Pyramid. Our experience suggests otherwise, but we don't know for sure.

I also have not deeply investigated how `pywb` works, as it wasn't the focus
of this investigation.

## Would our own new rewriter easy to maintain?

> No

The prototype is already starting to get very complicated. In includes the
following components:

 * NGINX proxying static content
 * Backend system for streaming content with cookie rewriting
 * Backend HTML rewriting
 * Backend CSS rewriting
 * Backend JS rewriting
 * Javascript intercepts
 * Javascript intercepts based on the backend rewriting
 
Some components like Javascript cookie rewriting are missing.

Each of these components can be quite complicated and much of the complexity 
arises from the interactions between these components, the rulesets
governing them, and the web at large.

There is often a long chain of consequence between the cause of a bug and it's
presentation. Bugs which are separated in time, and through long causal chains
are usually the hardest to solve.

It's hard to think about, and I don't believe this will get easier as it 
matures. The problem domain is inherantly complex. There is a limit to how much
code nicety can reduce this.

Testing will be extremely difficult or not very informative of real
performance. I suspect we will have many "fix one page, break another ten" 
style situations.

## How much effort would be required to take the current prototype ready?

> We don't know

A rough effort estimate:

 * Getting the current code cut down to a single solution - Small
 * Getting the current code production ready (no tests) - Medium
 * Getting basic test coverage - Medium / Large
 * Getting effective test coverage - Large / Unknown
 * Getting acceptable rewrite accuracy - Unknown
 
The uncertainties dominate the effort assessment in two main areas: getting 
effective testing and getting accuracy up to a usable level.

Testing is difficult as it's not clear how we can effectively test that a page
"works" from a user point of view. That a piece of content is visible in the
content of an HTML request does not mean it is visible to the user and vice
versa. 

Sites with complex content loading are often the ones which fail the most. 
Manual testing is too slow and expensive to cover the gap.
 
Improving accuracy to an "acceptable" level is hard in a number of ways:

 * What is "acceptable"?
 * Given the difficulty of testing, how can we be sure we have hit the required
   level?
 * What is missing to get us from where we are to where we need to be?
 
For more details on what is missing from the prototype solution see 
[Capability gap](04-capability-gap.md). The long and short is, we could be very
close or very far away, and it's likely to continue to be difficult to know.

## Would this solution generalise to the web? 
_Given it's only testing on URLs from LMS_
> Yes

There is nothing easier or simpler about the LMS problem than the general 
problem.

There are requirements of the general solution that do not apply to the LMS
solution, but you tend to get those accidentally:

 * We don't need in page navigation to work - _But_ it's easy to do for the 
   most part
 * We don't need adverts to work - _But_ by the time you've got everything else
   working you tend to have this

# The current technological solution

To create a successful rewriter a number of problems have to be overcome

 * [Rewriting HTML](02-individual-rewriting-tasks.md) - Details on tasks which
   have to be overcome to create a rewriter
 * [Rewriting URLs](03-rewriting-urls.md) - A focus on how we rewrite URLs as a
   lense for discussing URL rewriting (mostly in the context of tag attributes)

This section provides an overview of the attempts and conclusions of trying
to solve these problems.

## A number of different techniques were tried

Backend rewriters

* A "null" streaming and non-streaming solution - For speed comparison only
* [LXML based non-streaming rewriter](implementation-report/lxml-rewriter.md) - Dismissed for 
  inserting tags into pages
* [LXML streaming rewriter](implementation-report/lxml-rewriter-streaming.md) - Dismissed for inserting 
  tags into pages
* [HTMLParser streaming rewriter](implementation-report/htmlparser-rewriter.md)

As addons to a back-end rewriter

* NGINX - A required component regardless
* [Javascript client side interceptions](implementation-report/client-side-intercepts.md) - A required component regardless

## Techniques that were not tried

* Pure NGINX rewriting - Dismissed as impossible based on complexity of LXML 
  solution
* Pure Javascript rewriting - Not attempted in the time
* [Beautiful Soup⬈](https://pypi.org/project/beautifulsoup4/) - More for 
  extraction, unlikely to be able to cleanly proxy the page
* [html5lib⬈](https://pypi.org/project/html5lib/) - Non streaming, HTML5 
  compliant parser. Very slow. Non streaming
* [gumbo⬈](https://pypi.org/project/gumbo/) / 
  [html5-parser⬈](https://html5-parser.readthedocs.io/en/latest/) - Non 
  streaming, HTML5 compliant parser. Faster, but unmaintained and requires 
  C compilation

### Streaming parsing is much better for user experience

With Javascript interception and NGINX as required components, the major choice
for HTML parsing comes down to speed and user experience.

By streaming content we can start delivering bytes to a user as soon as we can
while we are still receiving more content.

It's more complex, and overall the process is a bit slower, but the first
content shows up to the user faster. Therefore the user experience is that the
solution is much faster.

It was generally observed that:

 * A fixed overhead is un-avoidable for connection and SSL
 * A streaming parser _can_ rewrite broken pages more faithfully (by being 
   dumb)
 * The difference is mostly observable on large pages
 * Streaming should have much better memory characteristics
 
For more details see [Speed comparisons](comparisons/speed.md).

### Streaming comes with significant downsides too

Many parsers are not available to us as they have no streaming support (e.g.
`html5lib`).

Generally the complexity of our coding is higher to retrieve, process and 
respond with data in a streaming way. The real downsides come with types of
coding and behavior which become impossible, rather than more difficult.

For example, in a traditional in-memory setting, if the connection failed half
way through, it's possible to restart the connection and get the content again.
This isn't possible in streaming context, as part of the original content will
already have been sent to the client.

In general it's not clear how errors would be handled, as we mostly have to
return a status code _before_ we start sending content.

### Streaming is probably worth it

The upsides probably outweigh the down, and if we find they don't it's easy to
switch from one mode of working to the other. 

### The result was HTMLParser streaming with NGINX and Javascript intercepts

The final stack looks something like this:

 * A streaming system which begins outputting content as it is being retrieved
 * HTMLParser at the center of HTML rewriter
 * A solution agnostic URL rewriter with rules of when to apply it
 * Custom CSS and JS rewriters based on regexes
 * Javascript patches and intercepts
 * NGINX to proxy the content for CORS reasons
 
The major "choice" here is `HTMLParser` over `LXML`. It is 100% down to the 
fact that `HTMLParser` does not insert extra tags.
 
# Conclusions

## A rewriter is possible, but the effort required is large and uncertain

Original Via proves that a rewriter is possible, but it also suggests this may
come at significant complexity.

I feel like we are close to a solution with comparable accuracy of rewriting,
at significantly lower complexity but 
[there are reasons to be skeptical](extras/the-brain-trap.md) of this belief. 

The difficulty around testing makes it difficult to know, at any given point, 
what our true accuracy level is.  

## Do we want to become a rewriter company?

As a complicated and absorbing task, maintaining the rewriter is likely to 
attact developer time. This effort will be on-going as more sites are found 
that do not work, or previously working sites stop. 

Using a third party solution has downsides, but it offloads the work of 
maintaining this component. 

As one of the main motivators for this work is to save developer time spent 
managing original Via during outages, this could be a success without victory.

## The task is not to rewrite HTML

The task is to allow the user to annotate a given page. All of this work is 
in service to writing a small piece of Javascript into the page. The complexity
arises as the entire web is setup to prevent this as a security problem.

We should investigate removing and reducing the barriers to using the browser
extension in an LMS context or other solutions which meet the need.

## The trends are not in our favour

There are a number of trends in websites and the web in general: most do not 
favour us:

 * **Standards compliance** (For) - Generally in our favour, although Google 
 specific embrace and extend tactics like AMP might buck the trend
 * **Security** (Against) - The central problem and highest risk. We stand a 
 non-trival chance of being legislated away
 * **Complexity** (Against) - Generally sites and browser interactions are 
 becoming more complex, with more different ways of interacting with a browser 
 being added
 * **Interactivity** (Against) - Sites are becoming more dynamic. Typically the
 pages we do the best on have the least Javascript

## We may have to do this regardless

A number of circumstances could add up to a situation where this work is 
inevitable:

 * No workable browser plugin solution for LMS users can be found
 * An updated Via (`pywb`) has the same poor operability as the current one
 * No alternative 3rd party rewriters with the right characteristics can be 
   found
 * The new solution is proven to scale significantly better 

# Next steps

## Get a production-lite version of the HTML rewriter live

The best way for people to evaluate the performance of the current solution is
to see it in action. I believe this is the most direct way to evaluate the 
solution and develop a "good enough/not good enough" decision.

I would suggest:

 * Stripping out alternative exploratory code (leaving only the best solution)
 * A pass over the code to bring it up to our automated standards (lint)
 * Add a convenient way for non-developers to try any given page
 * Not adding tests at this time
 * Not redirecting any user traffic (this is internal only)
 
We would of course have to back-fill any testing before redirecting any real 
user traffic to the solution.

## Investigate a solution based on up to date `pywb`

Some of our bug bears with `pywb` and hence Via are due to the fact it is badly
out of date. We should investigate how many could be solved by a solution based
on an up to date version.

At a minimum the updated `pywb`:

 * Supports Python 3
 * No longer proxies flash based video

## Work the problem from other angles (browser plugins etc.)

This work was constrained to the question of alternative ways of implementing
a custom HTML rewriting solution. 

It did not address or consider the larger questions of:

 * How does this compare with other existing off the shelf solutions?
 * Are there solutions which don't involve rewriting HTML?