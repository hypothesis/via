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

  * https://github.com/hypothesis/via

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

### Run the services with Docker Compose

Start the services that Via 3 requires (currently just NGINX) using Docker
Compose:

    make services

### Start the development server

    make dev

The first time you run `make dev` it might take a while to start because it'll
need to install the application dependencies and build the assets.

This will start the server on port 9082 (http://localhost:9082), reload the
application whenever changes are made to the source code, and restart it should
it crash for some reason.

**That's it!** You’ve finished setting up your Via 3 development environment. Run
`make help` to see all the commands that're available for running the tests,
linting, code formatting, etc.

### Updating the PDF viewer

Via 3 serves PDFs using [PDF.js](https://mozilla.github.io/pdf.js/). PDF.js is
vendored into the source tree and the viewer HTML is patched to load the Hypothesis
client. To update the PDF viewer, run `tools/update-pdfjs`.

## How the app is setup

Content is served by two main items:

 * NGINX on port 9083 (http://localhost:9083 in dev)
 * A python app on port 9082 (http://localhost:9082 in dev)

The python app consists of two parts:

 * A conventional Pyramid app
 * A [Whitenoise](http://whitenoise.evans.io/en/stable/) wrapper that serves static content

## See also

* [Caching strategy](docs/caching-strategy.md)
