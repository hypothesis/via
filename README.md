Via
===

A proxy that serves up third party PDF files and HTML pages with the
[Hypothesis client](https://github.com/hypothesis/client) embedded, so you can
annotate them.

Installing Via in a development environment
-------------------------------------------

### You will need

* Via integrates with h and the Hypothesis client, so you will need to set up
  development environments for each of those before you can develop Via:

  * https://h.readthedocs.io/en/latest/developing/install/
  * https://h.readthedocs.io/projects/client/en/latest/developers/developing/

* Via redirects to Via HTML to proxy HTML pages, so you'll need to set up a
  Via HTML development environment too:

  * https://github.com/hypothesis/viahtml

* [Git](https://git-scm.com/)

* [pyenv](https://github.com/pyenv/pyenv)
  Follow the instructions in the pyenv README to install it.
  The Homebrew method works best on macOS.

### Clone the git repo

    git clone https://github.com/hypothesis/via.git

This will download the code into a `via` directory in your current working
directory. You need to be in the `via` directory from the remainder of the
installation process:

    cd via

### Create the development data and settings

Create the environment variable settings needed to get Via working nicely with other services (e.g. Google Drive):

    make devdata

### Start the development server

    make dev

The first time you run `make dev` it might take a while to start because it'll
need to install the application dependencies and build the assets.

This will start NGINX running on http://localhost:9083 and reverse proxying to
Gunicorn on http://localhost:9082, reload the application whenever changes are
made to the source code, and restart it should it crash for some reason.

**You should use NGINX (http://localhost:9083) as your main entry point** to
Via in development. This is how it's used in production, and if you visit
Gunicorn directly you'll get CORS (Cross Origin Resource Sharing) errors from
your browser.

**That's it!** You’ve finished setting up your Via development environment. Run
`make help` to see all the commands that're available for running the tests,
linting, code formatting, etc.

Configuration
-------------

Environment variables:

| Name             | Purpose | Example |
|------------------|---------|---------|
| `CHECKMATE_URL` | The URL of the URL Checkmate instance to use | `https://checkmate.example.com` |
| `CHECKMATE_API_KEY` | API key to authenticate with Checkmate |
| `CHECKMATE_ALLOW_ALL` | Whether to bypass Checkmate's allow-list (and use only the blocklist) | `true`
| `CHECKMATE_IGNORE_REASONS` | Comma-separated list of Checkmate block reasons to ignore | `publisher-blocked,high-io` |
| `CLIENT_EMBED_URL` | The URL of the client's embed script | `https://hypothes.is/embed.js`
| `ENABLE_FRONT_PAGE` | Show a front page at the root URL | `true` |
| `GOOGLE_API_KEY` | The API key to use to authenticate with the Google Drive API |
| `GOOGLE_DRIVE_CREDENTIALS` | Service account credentials in JSON to authenticate with the Google Drive API |
| `GOOGLE_DRIVE_IN_PYTHON` | Process Google Drive in Python (requires `GOOGLE_DRIVE_CREDENTIALS`) |
| `NEW_RELIC_*` | Various New Relic settings. See New Relic's docs for details |
| `NGINX_SECURE_LINK_SECRET` | The NGINX secure links signing secret. This is used by Via's Python endpoints to generate the signed URLs required by its NGINX-implemented `/proxy/static/` endpoint. All instances of Via must have this setting |
| `NGINX_SERVER` | The URL of Via's NGINX server for proxying PDF files | `https://via.hypothes.is`
| `SENTRY_*` | Various Sentry settings. See Sentry's docs for details |
| `SIGNED_URLS_REQUIRED` | Require URLs to Via's Python endpoints to be signed so that Via can only be used by something that has the URL signing secret. Public instances of Via should _not_ enable this. Private instances of Via (e.g. the LMS app's instance of Via) _should_ enable this | `true`
| `VIA_HTML_URL` | The URL of the Via HTML instance to redirect to for proxying HTML pages | `https://viahtml.hypothes.is/proxy`
| `VIA_SECRET` | The secret that must be used to sign URLs to Via's Python endpoints if `SIGNED_URLS_REQUIRED` is on |

Updating the PDF viewer
-----------------------

Via serves PDFs using [PDF.js](https://mozilla.github.io/pdf.js/). PDF.js is
vendored into the source tree and the viewer HTML is patched to load the Hypothesis
client. To update the PDF viewer, run `make update-pdfjs`.

How Via works
-------------

Via allows users to annotate arbitrary web pages or PDF files by proxying the
page or file and injecting the Hypothesis client. Users go to
<https://via.hypothes.is/> and paste in a PDF or HTML URL (or visit
`https://via.hypothes.is/<SOME_URL>` directly) and Via responds with an
annotatable version.

### Via's architecture

Via is composed of four separable components:

1. A **top-level component** that responds to requests to the top-level
   `/<THIRD_PARTY_URL>` endpoint by deciding whether the URL is a PDF file or
   not and redirecting the browser to either the PDF viewer component or the
   HTML proxying component accordingly.

   This component is implemented in Python / Pyramid.

   The Pyramid app sends a GET request to the third-party URL but only
   downloads the response headers not the body. It looks at the Content-Type
   header to determine whether the body is a PDF file or not.

   If it's a PDF file then it redirects to the PDF viewer component:
   `/pdf/<THIRD_PARTY_URL>`.

   If it's an HTML file then it redirects to the HTML proxy component.

   The Pyramid app also handles various other bits and bobs such as serving up
   the front page, handling special `via.*` query params, serving static files
   such as PDF.js's assets, etc etc.

2. A **PDF viewer component** that renders a modified version of PDF.js with the Hypothesis client embedded.

   This is what enables users to annotate PDF files.

   The PDF viewer is also implemented in Python / Pyramid (and JavaScript served by the Pyramid app).

   The PDF viewer responds to requests to `/pdf/<THIRD_PARTY_URL>` by rendering
   a version of [PDF.js](https://mozilla.github.io/pdf.js/) with the Hypothesis
   client embedded, and configuring PDF.js to download the PDF file from the
   static file proxy component.

3. A **static files proxy component** that simply proxies static files to get around CORS.

   This component is implemented in NGINX (in the [nginx.conf](nginx/nginx.conf) file) for efficiency.

   This component responds to requests to the `/proxy/static/<THIRD_PARTY_URL>`
   endpoint, such as PDF.js's download requests for PDF files.

   Many PDF hosts use
   [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) headers to
   prevent JavaScript cross-origin requests (such as requests from our copy of
   PDF.js) from downloading the file.
   See [Can I load a PDF from another server (cross domain request)?](https://github.com/mozilla/pdf.js/wiki/Frequently-Asked-Questions#can-i-load-a-pdf-from-another-server-cross-domain-request)
   in the PDF.js FAQ.

   To get around this we proxy the PDF file through our own server so that
   browsers no longer see PDF.js's download request as a cross-origin request.

   In the future we'll also use this component to proxy some static resources
   of web pages for the same reason.

4. A **rewriting HTML proxy component** that proxies HTML pages and injects the Hypothesis client.

   This is what enables users to annotate web pages.

   The HTML proxy isn't implemented yet. Via currently redirects to legacy Via for HTML proxying.

   The HTML proxy's job is to enable annotating of HTML pages by proxying the
   page and injecting the Hypothesis client into it.

   It also has to rewrite various elements of the page that would otherwise
   break because the page is being proxied.

### How Via works in production

In production both NGINX and Gunicorn (the WSGI server for the Python / Pyramid
app) run inside a single Docker container defined by the app's `Dockerfile`.

NGINX runs on port 9083 in the Docker container, which is exposed to the
outside world.

Gunicorn runs on a UNIX socket that is accessible to NGINX within the Docker
container but is not directly accessible to the outside world.

NGINX is "in front of" Gunicorn in production:

1. All requests from user's browsers first go to NGINX on the Docker container's port 9083.

2. If the request is to a URL that NGINX handles directly (such as a
   `/proxy/static/*` URL) then NGINX just responds directly.

3. If the request is to one of the URLs that should be handled by the Pyramid
   app then NGINX proxies to Gunicorn on a UNIX socket.

### How Via works in development

In development NGINX runs in Docker Compose and is exposed at
http://localhost:9083/. This is defined in `docker-compose.yml`. The app's
`Dockerfile` isn't used in development, but the NGINX running in Docker Compose
in development does use the same `nginx.conf` file as the NGINX running in
Docker in production.

The Python WSGI server (Gunicorn) runs on the host (no Docker) and is exposed
at http://localhost:9082/. The NGINX running on `:9083` proxies to the Gunicorn
on `:9082`.

### WhiteNoise

The Pyramid app uses [WhiteNoise](http://whitenoise.evans.io/) to serve static
files in a CDN-friendly (caching-friendly) way. WhiteNoise serves the Python
app's static files in an efficient way and with the appropriate caching headers,
compression, etc.

WhiteNoise is a piece of [WSGI middleware](https://www.python.org/dev/peps/pep-3333/#middleware-components-that-play-both-sides)
that wraps our Pyramid WSGI app. Rather than proxying to Pyramid directly
Gunicorn actually proxies to WhiteNoise which either responds directly (if the
request is for a static file) or proxies to Pyramid.

### See also

* [Caching strategy](docs/caching-strategy.md)
