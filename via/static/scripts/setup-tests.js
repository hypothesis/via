import { assert } from 'chai';
import { configure } from 'enzyme';
import { Adapter } from 'enzyme-adapter-preact-pure';
import 'preact/debug';
import sinon from 'sinon';

// Expose sinon assertions and add extra assert methods.
sinon.assert.expose(assert, { prefix: null });

// Expose these globally, to avoid dependency on outdated karma-chai and
// karma-sinon plugins
globalThis.assert = assert;
globalThis.sinon = sinon;

// Configure Enzyme for UI tests.
configure({ adapter: new Adapter() });

// Ensure that uncaught exceptions between tests result in the tests failing.
// This works around an issue with mocha / karma-mocha, see
// https://github.com/hypothesis/client/issues/2249.
let pendingError = null;
let pendingErrorNotice = null;

/* istanbul ignore next */
window.addEventListener('error', event => {
  pendingError = event.error;
  pendingErrorNotice = 'An uncaught exception was thrown between tests';
});
/* istanbul ignore next */
window.addEventListener('unhandledrejection', event => {
  pendingError = event.reason;
  pendingErrorNotice = 'An uncaught promise rejection occurred between tests';
});

afterEach(() => {
  /* istanbul ignore if */
  if (pendingError) {
    console.error(pendingErrorNotice);
    throw pendingError;
  }
});
