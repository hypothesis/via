import { render } from 'preact';
import { useState } from 'preact/hooks';

import { useNextRender } from '../next-render';

describe('useNextRender', () => {
  it('resolves promise after next render', async () => {
    const container = document.createElement('div');
    let nextRenderPromise;

    function Widget() {
      const [count, setCount] = useState(0);
      const nextRender = useNextRender();
      const onClick = () => {
        setCount(c => c + 1);
        nextRenderPromise = nextRender.wait();
      };
      return (
        <button type="button" onClick={onClick}>
          {count}
        </button>
      );
    }

    render(<Widget />, container);

    const button = container.querySelector('button');
    assert.equal(button.textContent, '0');

    button.click();
    const nextRender1 = nextRenderPromise;
    await nextRender1;
    assert.equal(button.textContent, '1');

    // `nextRender.wait()` after a render create a new promise. Subsequent calls
    // should return the same promise until the re-render completes.
    button.click();
    const nextRender2 = nextRenderPromise;
    assert.notStrictEqual(nextRender1, nextRender2);
    button.click();

    const nextRender3 = nextRenderPromise;
    assert.strictEqual(nextRender3, nextRender2);

    await nextRender2;
    assert.equal(button.textContent, '3');
  });
});
