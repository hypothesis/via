import { mount } from 'enzyme';
import { useRef } from 'preact/hooks';

import { waitFor } from '../../../test-util/wait';
import { useAppLayout } from '../use-app-layout';

describe('useAppLayout', () => {
  let container;
  let wrappers;

  // Create a fake component to mount in tests that uses the hook
  function FakeComponent() {
    const myRef = useRef();
    const appSize = useAppLayout(myRef);
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
    { containerWidth: 769, expected: 'md' },
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

  it('should update app size if relative size of container changes', async () => {
    container.style.width = '200px';

    const wrapper = renderComponent();
    const appContainerEl = wrapper.find('[data-testid="appContainer"]');
    assert.equal(appContainerEl.prop('data-app-size'), 'sm');

    const steps = [
      [800, 'md'],
      [1000, 'lg'],
      [1200, 'xl'],
      [1500, '2xl'],
      [400, 'sm'],
    ];
    for (const [width, expected] of steps) {
      container.style.width = `${width}px`;

      await waitFor(() => {
        wrapper.update();
        const appContainerEl = wrapper.find('[data-testid="appContainer"]');
        return appContainerEl.prop('data-app-size') === expected;
      }, /* timeout */ 50);
    }
  });
});
