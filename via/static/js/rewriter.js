/* Javascript interceptions for rewriting HTML pages */

class URLRewriter {
  // Partial port of via3.services.rewriter.url.URLRewriter

  constructor(settings) {
    this.baseUrl = settings.baseUrl;
    this.baseScheme = this._urlScheme(this.baseUrl);
    this.urlTemplates = settings.urlTemplates;
  }

  _urlScheme(url) {
    if (url.startsWith("https:")) {
      return "https";
    } else if (url.startsWith("http:")) {
      return "http";
    }
    return null;
  }

  makeAbsolute(url) {
    if (url.startsWith("//")) {
      return this.baseScheme + ":" + url;
    }

    return new URL(url, this.baseUrl).toString();
  }

  canProxy(url) {
    return url.startsWith("https:") || url.startsWith("http:");
  }

  proxyStatic(url) {
    // We don't URL escape the paths that go direct through NGINX
    return this._templateRewrite(url, this.urlTemplates.PROXY_STATIC, false);
  }

  rewriteJS(url) {
    return this._templateRewrite(url, this.urlTemplates.REWRITE_JS);
  }

  rewriteHTML(url) {
    return this._templateRewrite(url, this.urlTemplates.REWRITE_HTML);
  }

  rewriteCSS(url) {
    return this._templateRewrite(url, this.urlTemplates.REWRITE_CSS);
  }

  _templateRewrite(url, template, encode = true) {
    console.log("Rewrite incoming URL", url);

    let absoluteUrl = this.makeAbsolute(url);
    console.log("  > (absolute)", url);

    if (!this.canProxy(absoluteUrl)) {
      console.log("  > (can't proxy)");
      return absoluteUrl;
    }

    if (encode) {
      absoluteUrl = encodeURIComponent(absoluteUrl);
      console.log("  > (encoded)", absoluteUrl);
    }

    const finalUrl = template.replace("__URL__", absoluteUrl);
    console.log("  > (final)", finalUrl);

    return finalUrl;
  }
}

function monkeyPatch(urlRewriter) {
  console.log("Initializing Via DOM API monkey-patching");

  const origFetch = window.fetch;
  window.fetch = (url, ...args) => {
    console.log("Via: Triggered fetch patch", url, args);
    return origFetch.call(null, urlRewriter.proxyStatic(url), ...args);
  };

  const origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url, ...args) {
    console.log("Via: Triggered XMLHttpRequest patch", method, url, args);
    return origOpen.call(this, method, urlRewriter.proxyStatic(url), ...args);
  };

  const origReplaceState = history.replaceState;
  history.replaceState = function(state, title, url) {
    console.log("Via: Tried to replace history", state, title, url);
    origReplaceState.call(history, state, title, urlRewriter.rewriteHTML(url));
    //return pushState.apply(history, arguments);
  };
  const origPushState = history.pushState;
  history.pushState = function(state, title, url) {
    console.log("Via: Tried to change history", state, title, url);
    origPushState.call(history, state, title, urlRewriter.rewriteHTML(url));
    //return pushState.apply(history, arguments);
  };
}

monkeyPatch(new URLRewriter(VIA_REWRITER_SETTINGS));

// Initialize proxy for "unforgeable" window properties (mainly `location`).
//
// Since these properties cannot be monkey-patched, we instead use server-side
// rewriting to wrap the page's JS in an IIFE which defines alternative `window`
// and `location` globals that refer to proxies set up here. These proxies
// can then intercept reads/writes to the unforgeable properties and modify
// their behavior.
const baseURL = new URL(VIA_REWRITER_SETTINGS.baseUrl);
const locationProxy = new Proxy(window.location, {
  get(target, prop, receiver) {
    if (prop in baseURL) {
      return baseURL[prop];
    }
    return Reflect.get(target, prop);
  }
});

// nb. We don't use `window` as the target here because that prevents us
// us from returning custom values for certain properties (eg. `window.window`)
// which are non-writable and non-configurable.
window.viaWindowProxy = new Proxy({}, {
  get(target, prop, receiver) {
    switch (prop) {
      case  "location":
        return locationProxy;
      case "window":
        return window.viaWindowProxy;
      default:
        break;
    }

    const val = Reflect.get(window, prop);

    // Calls to many `window` methods fail if `this` is a proxy rather than
    // the real window. Therefore we bind the returned function to the real `window`.
    //
    // TODO - Explain the regexp test.
    if (typeof val === 'function' && val.name.match(/^[a-z]+/)) {
      return val.bind(window);
    } else {
      return val;
    }
  },

  // Calls `window` property setters fail if `this` is a proxy rather than the
  // real window. Therefore we set the property on the real `window`.
  set(target, prop, value) {
    return Reflect.set(window, prop, value);
  },
});
