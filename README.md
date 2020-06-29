Via 3
=====

A proxy that serves up third party PDF files and HTML pages with the
[Hypothesis client](https://github.com/hypothesis/client) embedded, so you can
annotate them.

Installing Via 3 in a development environment
---------------------------------------------

### You will need

* Via 3 integrates with h and the Hypothesis client, so you will need to
  set up development environments for each of those before you can develop Via:

  * https://h.readthedocs.io/en/latest/developing/install/
  * https://h.readthedocs.io/projects/client/en/latest/developers/developing/

* For now, Via 3 also redirects to legacy Via to proxy HTML pages, so you'll
  need to set up a legacy Via development environment too:

  * https://github.com/hypothesis/via3

* [Git](https://git-scm.com/)

* [pyenv](https://github.com/pyenv/pyenv)
  Follow the instructions in the pyenv README to install it.
  The Homebrew method works best on macOS.

### Clone the git repo

    git clone https://github.com/hypothesis/via3.git

This will download the code into a `via3` directory in your current working
directory. You need to be in the `via3` directory from the remainder of the
installation process:

    cd via3

### Create the development data and settings

Create the environment variable settings needed to get Via 3 working nicely with other services (e.g. Google Drive):

    make devdata

### Start the development server

    make dev

The first time you run `make dev` it might take a while to start because it'll
need to install the application dependencies and build the assets.

This will start the server on port 9083 (http://localhost:9083), reload the
application whenever changes are made to the source code, and restart it should
it crash for some reason.

**That's it!** You’ve finished setting up your Via 3 development environment. Run
`make help` to see all the commands that're available for running the tests,
linting, code formatting, etc.

Updating the PDF viewer
-----------------------

Via 3 serves PDFs using [PDF.js](https://mozilla.github.io/pdf.js/). PDF.js is
vendored into the source tree and the viewer HTML is patched to load the Hypothesis
client. To update the PDF viewer, run `tools/update-pdfjs`.

How Via 3 works
---------------

Via 3 allows users to annotate arbitrary web pages or PDF files by proxying the
page or file and injecting the Hypothesis client. Users go to
<https://via3.hypothes.is/> and paste in a PDF or HTML URL (or visit
`https://via3.hypothes.is/<SOME_URL>` directly) and Via 3 responds with an
annotatable version.

### Via 3's architecture

Via 3 is composed of four separable components:

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

   The HTML proxy isn't implemented yet. Via 3 currently redirects to legacy Via for HTML proxying.

   The HTML proxy's job is to enable annotating of HTML pages by proxying the
   page and injecting the Hypothesis client into it.

   It also has to rewrite various elements of the page that would otherwise
   break because the page is being proxied.

### How Via 3 works in production

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

### How Via 3 works in development

In development NGINX runs in Docker Compose and is exposed at
http://localhost:9083/. This is defined in `docker-compose.yml`. The app's
`Dockerfile` isn't used in development, but the NGINX running in Docker Compose
in development does use the same `nginx.conf` file as the NGINX running in
Docker in production.

The Python WSGI server (Gunicorn) runs on the host (no Docker) and is exposed
at http://localhost:9082/.

NGINX is _not_ "in front of" Gunicorn in development. Rather, NGINX and
Gunicorn are "alongside" each other:

1. The front page of the app in development is http://localhost:9082/, which is
   served by Gunicorn directly without involving NGINX.

   Other URLs that're handled by the Pyramid app are also at
   `http://localhost:9082/*` and served by Gunicorn directly.

2. For requests that should be handled by NGINX directly (for example the
   `/proxy/static/*` URLs) the Pyramid app redirects the browser to
   `http://localhost:9083/*` URLs that're handled by the NGINX instance running
   in Docker Compose without further involving Python.

### But that means development is different from production!

That's true but the difference is small. In production requests that should be
handled by Gunicorn first go to NGINX which then proxies to Gunicorn. Whereas
in dev these requests go directly from the browser to Gunicorn. A small part of
the `nginx.conf` file that does the proxying to Gunicorn is used in production
but not in dev.

In practice this isn't really a problem and putting NGINX in front of Gunicorn
in development would likely create more issues than it would solve.

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
