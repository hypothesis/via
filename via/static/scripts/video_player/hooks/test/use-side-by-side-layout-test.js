import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import { useSideBySideLayout } from '../use-side-by-side-layout';
import { TOOLBAR_WIDTH } from '../use-side-by-side-layout';

describe('useSideBySideLayout', () => {
  let container;
  let wrappers;
  let fakeLayoutDetail;

  // Create a fake component to mount in tests that uses the hook
  function FakeComponent() {
    const sideBySideEnabled = useSideBySideLayout(container);
    return (
      <div style="width:100%">
        <button>Hi</button>
        {sideBySideEnabled && <span data-testid="side-by-side-enabled" />}
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
    container.style.width = '1024px';
    container.style.paddingRight = '0px';
    document.body.append(container);

    wrappers = [];

    // Layout values here reflect dimensions of the sidebar reported in the
    // `hypothesis:layoutchange` event at time of authoring.
    fakeLayoutDetail = {
      sideBySideActive: false,
      sidebarLayout: {
        expanded: true,
        width: 461,
        toolbarWidth: 33,
        height: 0,
      },
    };
  });

  afterEach(() => {
    wrappers.forEach(w => w.unmount());
    container.remove();
  });

  function triggerEvent(detail = fakeLayoutDetail) {
    const event = new CustomEvent('hypothesis:layoutchange', {
      detail,
    });
    act(() => {
      document.body.dispatchEvent(event);
    });
  }

  function sideBySideState() {
    return (
      container.querySelector('[data-testid="side-by-side-enabled"]') !== null
    );
  }

  describe('initial render', () => {
    it('does not lay out side-by-side', () => {
      renderComponent();
      assert.isFalse(sideBySideState());
    });

    it('provides room for sidebar controls', () => {
      renderComponent();
      assert.equal(container.style.paddingRight, `${TOOLBAR_WIDTH}px`);
    });
  });

  describe('when sidebar opens', () => {
    [875, 876, 1024, 1268].forEach(bodyWidth => {
      it('applies side-by-side layout when there is enough space', () => {
        container.style.width = `${bodyWidth}px`;
        renderComponent();
        triggerEvent();

        assert.isTrue(sideBySideState());
      });
    });

    [450, 600, 874].forEach(bodyWidth => {
      it('allows sidebar to overlap content on narrow screens', () => {
        container.style.width = `${bodyWidth}px`;
        renderComponent();
        triggerEvent();

        assert.isFalse(sideBySideState());
      });
    });
  });

  describe('when window is resized', () => {
    it('recalculates side-by-side layout', () => {
      container.style.width = '450px';
      renderComponent();
      triggerEvent();

      assert.isFalse(sideBySideState());

      act(() => {
        container.style.width = '1450px';
        window.dispatchEvent(new Event('resize'));
      });
      assert.isTrue(sideBySideState());
    });
  });

  describe('when sidebar closes', () => {
    it('does not provide room for sidebar at right', () => {
      renderComponent();
      fakeLayoutDetail.sidebarLayout.expanded = false;
      triggerEvent();

      assert.isFalse(sideBySideState());
      assert.equal(container.style.paddingRight, `${TOOLBAR_WIDTH}px`);
    });
  });
});
