import { mount } from 'enzyme';
import { useCallback, useRef } from 'preact/hooks';

import { useScrollAnchor } from '../use-scroll-anchor';

const loremIpsum =
  'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.';

describe('useScrollAnchor', () => {
  // Scrollable test widget with children that have text wrapping onto
  // multiple lines. As the width of the container is varied, the
  // `useScrollAnchor` hook will need to adjust the scroll position to keep
  // the same child visible.
  function TestWidget({ width = 200, height = 200 }) {
    const container = useRef(null);
    const getChildren = useCallback(
      () => container.current.querySelectorAll('.child'),
      [],
    );

    useScrollAnchor(container, getChildren);

    return (
      <div
        data-testid="container"
        ref={container}
        style={{
          width: `${width}px`,
          height: `${height}px`,
          fontSize: '13px',

          // Hide scrollbars so the `clientWidth` of this element is the same
          // on all platforms.
          overflowY: 'hidden',
        }}
      >
        <div className="child">{loremIpsum}</div>
        <div className="child">{loremIpsum}</div>
        <div className="child">{loremIpsum}</div>
        <div className="child">{loremIpsum}</div>
        <div className="child">{loremIpsum}</div>
      </div>
    );
  }

  let wrappers;

  const renderWidget = props => {
    const wrapper = mount(<TestWidget {...props} />, {
      attachTo: document.body,
    });
    wrappers.push(wrapper);
    return wrapper;
  };

  /** Return Y offset of top of `child` from top of `container`. */
  function offsetFromTop(container, child) {
    const containerRect = container.getBoundingClientRect();
    const childRect = child.getBoundingClientRect();
    return childRect.top - containerRect.top;
  }

  function waitForEvent(element, event) {
    return new Promise(resolve => {
      element.addEventListener(event, resolve, { once: true });
    });
  }

  function waitForResize(element) {
    return new Promise(resolve => {
      const ro = new ResizeObserver(() => {
        resolve();
        ro.disconnect();
      });
      ro.observe(element);
    });
  }

  beforeEach(() => {
    wrappers = [];
  });

  afterEach(() => {
    wrappers.forEach(w => w.unmount());
  });

  it('disables built-in scroll anchoring', () => {
    const wrapper = renderWidget();
    assert.equal(
      wrapper.find('[data-testid="container"]').getDOMNode().style
        .overflowAnchor,
      'none',
    );
  });

  it('adjusts scroll position when container is resized', async () => {
    const wrapper = renderWidget({ width: 150 });
    const container = wrapper.find('[data-testid="container"]').getDOMNode();

    // Scroll down enough that, when we make the container wider below, the
    // content will shift.
    const scrolled = waitForEvent(container, 'scroll');
    container.scrollBy(0, 50);
    await scrolled;

    // Pick the second child for testing. This is the first child that fits
    // within the viewport and so the one which `useScrollAnchor` will pick as
    // a scroll anchor.
    const child = wrapper.find('.child').at(1).getDOMNode();
    const topOffset = Math.floor(offsetFromTop(container, child));
    const scrollOffset = Math.floor(container.scrollTop);

    // Make the container wider. The item contents will now wrap onto fewer
    // lines and so if the scroll position of the container is not updated by
    // `useScrollAnchor`, the content would shift.
    const resized = waitForResize(container);
    wrapper.setProps({ width: 200 });
    await resized;

    // Check that `useScrollAnchor` did adjust the `scrollTop` of the container
    // so as to keep the relative offset of the child the same.
    const topOffset2 = Math.floor(offsetFromTop(container, child));
    const scrollOffset2 = Math.floor(container.scrollTop);

    assert.notEqual(scrollOffset, scrollOffset2);
    assert.equal(topOffset, topOffset2);

    // Wait for a repaint. Otherwise we'll get a ResizeObserver loop error
    // when resizing a second time below.
    await new Promise(resolve => requestAnimationFrame(resolve));

    // Resize to zero width/height and trigger a scroll. This exercises code
    // paths for the case where no scroll anchor can be chosen.
    const resized2 = waitForResize(container);
    wrapper.setProps({ width: 0, height: 0 });
    container.dispatchEvent(new Event('scroll'));
    await resized2;
  });
});
