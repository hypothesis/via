// These tests use Preact directly, rather than via Enzyme, to simplify debugging.
import { render } from 'preact';

import { useStableCallback } from '../use-stable-callback';

describe('useStableCallback', () => {
  let container;
  let stableCallbackValues;

  beforeEach(() => {
    container = document.createElement('div');
    stableCallbackValues = [];
  });

  function Widget({ callback }) {
    const stableCallback = useStableCallback(callback);
    stableCallbackValues.push(stableCallback);
    return <button onClick={stableCallback}>Test</button>;
  }

  it('returns a wrapper with a stable identity', () => {
    render(<Widget callback={() => {}} />, container);
    render(<Widget callback={() => {}} />, container);

    assert.equal(stableCallbackValues.length, 2);
    assert.equal(stableCallbackValues[0], stableCallbackValues[1]);
  });

  it('returned wrapper forwards to the latest callback', () => {
    const stub = sinon.stub();
    render(<Widget callback={() => {}} />, container);
    render(<Widget callback={stub} />, container);

    assert.equal(stableCallbackValues.length, 2);
    stableCallbackValues.at(-1)('foo', 'bar', 'baz');

    assert.calledWith(stub, 'foo', 'bar', 'baz');
  });
});
