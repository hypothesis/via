'use strict';

// Listen for `webviewerloaded` event to configure the viewer after its files
// have been loaded but before it is initialized.
//
// PDF.js >= v2.10.377 fires this event at the parent document if it is embedded
// in a same-origin iframe. See https://github.com/mozilla/pdf.js/pull/11837.
try {
  parent.document.addEventListener('webviewerloaded', onViewerLoaded);
} catch (err) {
  // Parent document is cross-origin. The event will be fired at the current
  // document instead.
  document.addEventListener('webviewerloaded', onViewerLoaded);
}

function onViewerLoaded() {
  // Prevent loading of default viewer PDF.
  PDFViewerApplicationOptions.set('defaultUrl', '');

  // Read configuration rendered into template as global vars.
  const proxyPdfUrl = window.PROXY_PDF_URL;
  const pdfUrl = window.PDF_URL;
  const clientEmbedUrl = window.CLIENT_EMBED_URL;

  // Wait for the PDF viewer to be fully initialized and then load the Hypothesis client.
  const app = PDFViewerApplication;
  app.initializedPromise.then(() => {
    // Disable range requesting, since Canvas signs their file URLs with a one-time
    // token, making subsequent attempts fail
    PDFViewerApplicationOptions.set('disableRange', true);

    // Load the Hypothesis client.
    const embedScript = document.createElement('script');
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
      url: proxyPdfUrl,

      // Make sure `PDFViewerApplication.url` returns the original URL, as this
      // is the URL associated with annotations.
      originalUrl: pdfUrl,
    });
  });
}
