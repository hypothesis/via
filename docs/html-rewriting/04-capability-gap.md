# What is missing from our solution?

## Overview

This page attempts to give a feeling for how many sites are "usable" in the new
solution, with the original Via given as a comparison.

After this a brief attempt was made to try and assess why pages were not 
working in order to see what we might need to do to close the gap between the
prototype and a "perfect" rewriting solution. 

### What counts as usable?

 * The main text is visible and not obscured in any place
 * No obnoxious scrolling to find or read the content (horizontal or vertical)
 * The main content is not hard to distinguish from surrounding content (where
  it is normally easy)

# A visual inspection of pages gives us ~84% usable

## Examples were examined from the top 100 domains by LMS usage

The top 1000 domains were gathered by usage in LMS assignments. A random URL
was then chosen for each domain which we hope represents that domain.

This allows us to extrapolate somewhat to how many sites in actual usage this
might represent.

Sites were filtered if they were broken or unretrievable. The top 100 of those 
remaining were inspected visually to see if they were usable.

Some comparatives with original flavour Via. The percentages are percentage 
count of the top 100 and top 1000.

## Quantitative

The percentages here show the number of times a domain was used from the 
examplar URL tested in the total for the top 100 and 1000.   

So a very populate site may be 1% of the top 100 sites, but represent 5% of the
usages in LMS for example.

| State  | Product   | Sites | Count | % Top 100  | % Top 1000 |
|--------|-----------|-------|-------|--------|--------|
| Ok     | Prototype | **84**    | 1712  | **82.59%** | 46.84% |
| Ok     | Via       | 96    | 1975  | 95.27% | 54.04% |
| Broken | Prototype | 14    | 327   | 15.77% |  8.95% |
| Broken | Via       | 3     | 80    |  3.86% |  2.19% |
| Other  | Prototype | 2     | 34    |  1.64% |  0.93% |
| Other  | Via       | 1     | 18    |  0.87% |  0.49% |

Sites marked "Other" failed for reasons outside of the product. 

## Qualitative

These results include an assessment of whether rendering was "better" than the
rendering produced by Via. This helps capture sites which might be "usable" in
both, but rendered more faithfully by one or the other.

| Rendering    | Sites | Description |
|--------------|-------| -------------
| Better       | 9     | Both render the page, we render it better (small errors)
| Same         | 77    | Similar rendering 
| Worse        | 2     | Both render the page, we render it worse (small errors)
| Newly broken | 11    | Usable in Via, unusable in the prototype
| Other        | 1     | n/a - Site broken

We a similar but slightly more nuanced story. Even though our rewriting fails
completely more often, **when it does work it is usually mildly better**. The 
differences here were usually adverts or small images showing up that were 
missing in Via.

**Of note**: Via is seriously broken in dev. I don't know why (SSL?) but it 
renders absolute gibberish for a lot of sites.

## These results don't hold up over time

Having run these comparisons a number of times, and say we quite frequently get
a slightly different result without changing anything. This is due to:

 * The sites coming and going
 * Transient net "weather" effecting our connections
 * Logical, but sufficiently complex interactions appearing random - e.g. 
 visiting sites in the "wrong" order has caused some to fail due to cookie
 contamination. It might be logical, but it doesn't feel it

## Improvements after this inspection have mixed results

Further work on the Javascript advanced the art somewhat causing some of the 
more complex sites to work correctly. A not very thorough test of the other
sites found it caused some of them to break instead.

The new approach relies on spotting things with regexes, which is fragile in
a way intercepting and monkey patching fetch isn't. 

Due to the cost of retesting, I didn't get a complete number. My gut feel is:

 * We probably fixed more than we broke
 * If we could get the best of both we are getting competetive with original Via

# Site specific issues

## [Medium⬈](https://medium.com/@Bhasingursifath/graffiti-art-or-vandalism-4ecda1f780ab)

Certain sites (like Medium) construct URLs based on the scheme of the window. 
In dev we are running with `http` not `https` and so the wrong URL is
constructed. This isn't the reason Medium is failing, but it could be for 
other sites.

Medium like other sites seems to be sensitive the results of `window.location` 

## [NPR⬈](https://www.npr.org/2017/03/21/520820142/soy-marr-n)

The initial response from NPR is a redirect. We need to handle this as a
redirect ourselves, or the base doesn't match the content etc.

Then it sets cookies with javascript. We don't do anything about this and it's
a total mess. We are leaking state between sites as well.

Finally it calls `window.location` to change the URL, which need to intercept
somehow. This is apparently done in Via by actually regexing the JS content to
insert a custom function which intercepts the call. This has side effects, as
the regexing sometimes rewrites things it shouldn't.

# Non-site specific issues

Some random things that are failing or won't work. Not sure these are the
causes of anything:

 * Web workers won't register on the wrong domain
 * Anything that relies on the window location to do routing, like single page
 apps
 * We aren't currently rewriting in page CSS so inline fonts will probably fail
 
## Super complex sites with no obvious failure reason

A surprisingly large number of sites seem to load fine, and then spot something
is wrong and hide their content 
(e.g. [www.fastcompany.com⬈](https://www.fastcompany.com/3024273/infographics-lie-heres-how-to-spot-the-bs?)).
In general quite a few of these aren't throwing any errors or failing to
retrieve any content. They just inspect the general state and decide they don't
like it.

It turns out many of these sites are sensitive to `window.location` return 
values, but this was guessed at rather than determined. We are mostly working
experimentally at this point. In the general case this will be a power of 
guesswork and investigation to work out why. Which is to say, we honestly 
don't know what the gap we are missing is yet.

## GDPR / cookie / privacy prompts have a good and a horrible solution

Quite a few of our errors relate to popups and interupts asking for various
types of permissions.

The good fix for these is to get cookies working correctly, but this won't fix
all sites as some have forms and other mechanisms which end up redirecting you
to the wrong site, usually with cookies there to prevent a repeat. 

Of the sites I investigated I found that if you manually capture and inject
the right cookies, we can avoid all of these prompts.

This is a bad solution for a number of reasons:

 * It probably violates terms of use on the sites
 * It's legally iffy
 * It's a maintenance headache (how to we store and update these?)
 * Re-using tokens across many requests could get us banned
 
It could be a tool in the tool box for very stubbon websites.

## It's costly to work out if we've made things better or worse

Currently our only way of working out if we've made all sites (rather than just
the one we are looking at) better or worse is to visually inspect them all. 

It's slow and error prone, and the results don't hold up over time. This is 
because sites behave differently on different days. 

In general I suspect this pattern of increased complexity and not knowing 
if we are close or far from the end is likely to continue. 

This approach of patching could be one tweak away from being perfect, or 
fundamentally flawed. I doubt you could know until you conclusively got it 
working for every site (which there is no way to be sure of).

# List of missing capabilities

 * **Client side cookie rewriting solution** - Required 
 * **Location interception** - Required - We have something here, but it causes
 errors
 * **Inline JS rewriting** - Required (as above, same solution but needs to be
 applied inline)
 * **CSS inline rewriting** - Nice to have (makes fonts always work)
 * **???** - Unknown, unknowns - We do not know what is required to fix 
 remaining sites, the above could do it, or not?

Unlisted in the above is making everything we have work correctly and be
robust. So we "have" many capabilities but also not really: they aren't
finished. For example there have been updates to the Python side which I
haven't crossed over into the JS side. 