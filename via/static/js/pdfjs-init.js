'use strict';

// Note: This file is not transpiled. For IE 11 compatibility, it must only
// use ES5 language features.
//
// This script can however assume that some ES2015+ library features, eg.
// Promises, will already have been polyfilled as PDF.js uses them.

// Listen for `webviewerloaded` event to configure the viewer after its files
// have been loaded but before it is initialized.
document.addEventListener('webviewerloaded', function(event) {
  var appOptions = window.PDFViewerApplicationOptions;
  var app = window.PDFViewerApplication;

  // Ensure that PDF.js viewer events such as "documentloaded" are dispatched
  // to the DOM. The client relies on this.
  appOptions.set('eventBusDispatchToDOM', true);

  // Disable preferences support, as otherwise this will result in `eventBusDispatchToDOM`
  // being overridden with the default value of `false`.
  appOptions.set('disablePreferences', true);

  // Prevent loading of default viewer PDF.
  appOptions.set('defaultUrl', '');

  // Read configuration rendered into template as global vars.
  var url = window.PDF_URL;
  var clientEmbedUrl = window.CLIENT_EMBED_URL;

  // Wait for the PDF viewer to be fully initialized and then load the Hypothesis client.
  //
  // This is required because the client currently assumes that `PDFViewerApplication`
  // is fully initialized when it loads. Note that "fully initialized" only means
  // that the PDF viewer application's components have been initialized. The
  // PDF itself will still be loading, and the client will wait for that to
  // complete before fetching annotations.
  //
  var pdfjsInitialized = new Promise(function (resolve) {
    // Poll `app.initialized` as there doesn't appear to be an event that
    // we can listen to.
    var timer = setInterval(function () {
      if (app.initialized) {
        clearTimeout(timer);
        resolve();
      }
    }, 20);
  });

  pdfjsInitialized.then(function () {
    // Prevent PDF.js' `Promise` polyfill, if it was used, from being
    // overwritten by the one that ships with Hypothesis (both from core-js).
    //
    // See https://github.com/hypothesis/via/issues/81#issuecomment-531121534
    if (typeof Promise === 'function' && typeof PromiseRejectionEvent === 'undefined') {
      window.PromiseRejectionEvent = function FakePromiseRejectionEvent(type, options) {
        // core-js doesn't actually use this, it just tests for `typeof PromiseRejectionEvent`
        console.warn('Tried to construct fake `PromiseRejectionEvent`');
      };
    }

    // Load the Hypothesis client.
    var embedScript = document.createElement('script');
    embedScript.src = clientEmbedUrl;
    document.body.appendChild(embedScript);

    // Load the PDF specified in the URL.
    //
    // This is done after the viewer components are initialized to avoid some
    // race conditions in `PDFViewerApplication` if the PDF finishes loading
    // (eg. from the HTTP cache) before the viewer is fully initialized.
    //
    // See https://github.com/mozilla/pdf.js/wiki/Frequently-Asked-Questions#can-i-specify-a-different-pdf-in-the-default-viewer
    // and https://github.com/mozilla/pdf.js/issues/10435#issuecomment-452706770
    app.open({
      // Load PDF through Via to work around CORS restrictions.
      url: url,

      // Make sure `PDFViewerApplication.url` returns the original URL, as this
      // is the URL associated with annotations.
      originalUrl: url,
    });
  });
});
