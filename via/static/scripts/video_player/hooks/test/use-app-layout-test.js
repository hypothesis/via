import { mount } from 'enzyme';
import { useRef } from 'preact/hooks';

import { waitFor } from '../../../test-util/wait';
import { useAppLayout } from '../use-app-layout';

describe('useAppLayout', () => {
  let container;
  let lastAppLayout;
  let wrappers;

  // Create a fake component to mount in tests that uses the hook
  function FakeComponent() {
    const myRef = useRef();
    lastAppLayout = useAppLayout(myRef);
    return (
      <div
        ref={myRef}
        style={{ width: '100%', height: '100%' }}
        data-testid="appContainer"
      >
        <button>Hi</button>
      </div>
    );
  }

  function renderComponent() {
    const wrapper = mount(<FakeComponent />, { attachTo: container });
    wrappers.push(wrapper);
    return wrapper;
  }

  beforeEach(() => {
    container = document.createElement('div');
    container.setAttribute('id', 'container');
    container.style.width = '800px';
    container.style.height = '600px';
    document.body.append(container);

    wrappers = [];
    lastAppLayout = null;
  });

  afterEach(() => {
    wrappers.forEach(w => w.unmount());
    container.remove();
  });

  [
    { containerWidth: 200, expected: 'sm' },
    { containerWidth: 768, expected: 'sm' },
    { containerWidth: 856, expected: 'md' },
    { containerWidth: 875, expected: 'md' },
  ].forEach(({ containerWidth, expected }) => {
    it('should provide relative app size when component is rendered', () => {
      container.style.width = `${containerWidth}px`;
      renderComponent();
      assert.equal(lastAppLayout.appSize, expected);
    });

    it('should set video width in single-column layouts', () => {
      container.style.width = `${containerWidth}px`;
      renderComponent();

      if (expected === 'sm') {
        const expectedWidth = Math.min(
          containerWidth,
          (container.clientHeight / 2) * (16 / 9)
        );
        assert.approximately(lastAppLayout.videoWidth, expectedWidth, 1);
      } else {
        assert.isUndefined(lastAppLayout.videoWidth);
      }
    });
  });

  describe('updating app layout info when relative container size changes', () => {
    let wrapper;

    beforeEach(() => {
      container.style.width = '200px';
      wrapper = renderComponent();
    });

    for (const [width, expected] of [
      [866, 'sm'],
      [868, 'md'],
      [1000, 'md'],
      [1200, 'lg'],
      [1500, 'xl'],
      [400, 'sm'],
    ]) {
      it('should update the relative appSize', async () => {
        container.style.width = `${width}px`;
        await waitFor(() => {
          wrapper.update();
          return lastAppLayout.appSize === expected;
        }, 50 /* timeout */);
      });

      it('should update multicolumn value for relative appSize', async () => {
        container.style.width = `${width}px`;
        const shouldBeMulticolumn = expected !== 'sm';
        await waitFor(() => {
          wrapper.update();
          return lastAppLayout.multicolumn === shouldBeMulticolumn;
        }, 50 /* timeout */);
      });
    }
  });
});
