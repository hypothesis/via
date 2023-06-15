import { render } from 'preact';
import { useRef } from 'preact/hooks';
import { act } from 'preact/test-utils';

import { waitFor } from '../../../test-util/wait';
import { useAppLayout } from '../use-app-layout';

describe('useAppLayout', () => {
  let container;
  let appSize;

  function findElementByTestId(testId) {
    return container.querySelector(`[data-testid=${testId}]`);
  }

  // Create a fake component to mount in tests that uses the hook
  function FakeComponent() {
    const myRef = useRef();
    appSize = useAppLayout(myRef);
    return (
      <div
        ref={myRef}
        data-app-size={appSize}
        style="width:100%"
        data-testid="appContainer"
      >
        <button>Hi</button>
      </div>
    );
  }

  function renderComponent() {
    act(() => {
      render(<FakeComponent />, container);
    });

    return findElementByTestId('appContainer');
  }

  beforeEach(() => {
    container = document.createElement('div');
    container.setAttribute('id', 'container');
    document.body.append(container);
  });

  afterEach(() => {
    container.remove();
  });

  [
    { containerWidth: 200, expected: 'sm' },
    { containerWidth: 768, expected: 'sm' },
    { containerWidth: 769, expected: 'md' },
    { containerWidth: 875, expected: 'md' },
  ].forEach(({ containerWidth, expected }) => {
    it('should provide relative app size when component is rendered', () => {
      container.style.width = `${containerWidth}px`;

      renderComponent();
      assert.equal(appSize, expected);
    });
  });

  it('should update app size if relative size of container changes', async () => {
    container.style.width = '200px';

    const appContainerEl = renderComponent();
    assert.equal(appSize, 'sm');

    const steps = [
      [800, 'md'],
      [1000, 'lg'],
      [1200, 'xl'],
      [1500, '2xl'],
      [400, 'sm'],
    ];
    for (const [width, expected] of steps) {
      appContainerEl.style.width = `${width}px`;
      await waitFor(() => appSize === expected, /* timeout */ 50);
    }
  });
});
