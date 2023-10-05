import { waitFor } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { useRef } from 'preact/hooks';

import { useAppLayout } from '../use-app-layout';

describe('useAppLayout', () => {
  let container;
  let wrappers;

  // Create a fake component to mount in tests that uses the hook
  function FakeComponent() {
    const myRef = useRef();
    const { appSize, multicolumn } = useAppLayout(myRef);
    return (
      <div
        ref={myRef}
        data-app-size={appSize}
        data-app-multicolumn={multicolumn}
        style="width:100%"
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
    document.body.append(container);

    wrappers = [];
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
      const appContainerEl = renderComponent().find(
        '[data-testid="appContainer"]'
      );
      assert.equal(appContainerEl.prop('data-app-size'), expected);
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
          const appContainerEl = wrapper.find('[data-testid="appContainer"]');
          return appContainerEl.prop('data-app-size') === expected;
        }, 50 /* timeout */);
      });

      it('should update multicolumn value for relative appSize', async () => {
        container.style.width = `${width}px`;
        const shouldBeMulticolumn = expected !== 'sm';
        await waitFor(() => {
          wrapper.update();
          const appContainerEl = wrapper.find('[data-testid="appContainer"]');
          return (
            appContainerEl.prop('data-app-multicolumn') === shouldBeMulticolumn
          );
        }, 50 /* timeout */);
      });
    }
  });
});
