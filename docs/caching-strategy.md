# Caching strategy

## Short `max-age`, long `stale-while-revalidate`

One strategy we are using for caching the Python calls is to provide both a
`max-age` and `stale-while-revalidate` value.

Setting a `max-age` informs the consumer to not come back at all during the
period as the content is known 'good'. Setting a `stale-while-revalidate` as well
tells the consumer that they can safely use the content in their cache _while_ they check for updates.

### An example user journey

This should result in the following sort of behavior:

 * User requests a resource for the first time
    * __Result:__ Cache is populated
 * User requests the same resource very quickly
    * __Result:__ User does not even make a second request due to `max-age`
 * User requests the same resource after the `max-age` has expired but before
   the `stale-while-revalidate` has expired
   * __Result:__
     * User is immediately served the old cached content
     * _Then asynchronously_ the content is checked for validity
     * The cache updated as necessary
 * User requests the same resource very quickly after receiving the previous copy is found 'stale'
   * __Result:__ User is returned the updated content retrieved asynchronously last time


This means the user may see a stale version on the second try if the content has changed,
but can quickly fix this simply checking again.

### How this works to our advantage

In a very crude overview the proxy works by:

 1. A Python call to determine the type (PDF or not) - Slowish
 2. A call through NGINX to serve the content - Fastish

If this call is made repeatedly the flow is:

 1. Python call #1
 2. NGINX call #1 (user journey 1 complete)
 3. Python call #2
 4. NGINX call #2 (user journey 2 complete)
 5. Python call #3
 6. NGINX call #3 (user journey 3 complete)


Using the `stale-while-revalidate` the sequence from the users point of view becomes

 1. Python call #1
 2. NGINX call #1 (user journey 1 complete)
 3. NGINX call #2 (user journey 2 complete _with contents of Python call #1_)
 4. Python call #2 (async)
 5. NGINX call #3 (user journey 3 complete _with contents of Python call #2_)
 6. Python call #3 (async)

With the caveat that the content is always one call out of date, this effectively
means the Python call is made after the NGINX call.

## Different timeouts on different calls

The different calls have different time-outs as we can rely on some checks to
effectively invalidate others.

#### Static content (CSS, images, JavaScript, HTML, ...)

 * When served under `/` the timeout is 60s
 * When served under `/static/<salt>` marked as immutable
 * This means whatever serves links to immutable assets:
    * Must use `request.static_url()` to generate URLs for them
    * Must change for new assets to be picked up

#### `content_type()` view (redirect)

* `max-age`: PDF: 5m, HTML 60s
* PDFs should be relatively static, and take a while to update and change
* HTML could be served from a wiki or other volatile source

#### `pdf()`  view (html)

* `max-age`: 0
* This is the jumping off point from where we link to static assets
* As these assets are marked immutable, this must change to pick them up
