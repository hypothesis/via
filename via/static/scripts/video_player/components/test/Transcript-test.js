/* global Highlight */
import { mount } from 'enzyme';

import Transcript from '../Transcript';

describe('Transcript', () => {
  const transcript = {
    segments: [
      {
        start: 5,
        text: 'Hello and welcome',
      },
      {
        start: 10,
        text: 'To this video about',
      },
      {
        start: 20,
        text: 'how to use Hypothesis',
      },
    ],
  };

  it('renders segments', () => {
    const wrapper = mount(
      <Transcript transcript={transcript} currentTime={5} />
    );
    const segments = wrapper.find('[data-testid="segment"]');
    assert.equal(segments.length, 3);

    assert.equal(segments.at(0).text(), '0:05Hello and welcome');
    assert.isTrue(segments.at(0).prop('data-is-current'));

    assert.equal(segments.at(1).text(), '0:10To this video about');
    assert.isFalse(segments.at(1).prop('data-is-current'));

    assert.equal(segments.at(2).text(), '0:20how to use Hypothesis');
    assert.isFalse(segments.at(2).prop('data-is-current'));
  });

  it('renders segments if none is current', () => {
    const wrapper = mount(
      <Transcript transcript={transcript} currentTime={0} />
    );
    const segments = wrapper.find('[data-testid="segment"]');
    assert.isFalse(segments.at(0).prop('data-is-current'));
  });

  it('invokes callback when segment is clicked', () => {
    const selectSegment = sinon.stub();
    const wrapper = mount(
      <Transcript
        transcript={transcript}
        currentTime={5}
        onSelectSegment={selectSegment}
      />
    );
    const timestamp = wrapper
      .find('[data-testid="segment"]')
      .at(1)
      .find('button');

    timestamp.simulate('click');

    assert.calledWith(selectSegment, transcript.segments[1]);
  });

  it('scrolls current segment into view', () => {
    const wrapper = mount(
      <Transcript transcript={transcript} currentTime={5} />
    );
    const scrollContainer = wrapper.find('div[data-testid="scroll-container"]');
    const scrollTo = sinon.spy(scrollContainer.getDOMNode(), 'scrollTo');

    wrapper.setProps({ currentTime: 10 });

    assert.calledWith(scrollTo, {
      left: 0,
      top: 0,
      behavior: 'smooth',
    });
  });

  it('does not scroll transcript while user is selecting text', () => {
    const wrapper = mount(
      <Transcript transcript={transcript} currentTime={5} />,
      {
        attachTo: document.body,
      }
    );
    try {
      const scrollContainer = wrapper.find(
        'div[data-testid="scroll-container"]'
      );
      const scrollTo = sinon.spy(scrollContainer.getDOMNode(), 'scrollTo');

      const segment = wrapper.find('[data-testid="segment"]').at(1);
      window.getSelection().selectAllChildren(segment.getDOMNode());

      wrapper.setProps({ currentTime: 10 });

      assert.notCalled(scrollTo);
    } finally {
      wrapper.unmount();
    }
  });

  it("scrolls transcript when controller's `scrollToCurrentSegment` method is called", () => {
    const controlsRef = { current: null };
    const wrapper = mount(
      <Transcript
        controlsRef={controlsRef}
        transcript={transcript}
        currentTime={5}
      />
    );
    const scrollContainer = wrapper.find('div[data-testid="scroll-container"]');
    const scrollTo = sinon.spy(scrollContainer.getDOMNode(), 'scrollTo');

    assert.ok(controlsRef.current);
    controlsRef.current.scrollToCurrentSegment();

    assert.calledWith(scrollTo, {
      left: 0,
      top: 0,
      behavior: 'smooth',
    });
  });

  it('does not hide segments when there is no filter', () => {
    const wrapper = mount(
      <Transcript transcript={transcript} currentTime={0} />
    );
    const segments = wrapper.find('li[data-testid="segment"]');
    assert.equal(segments.length, 3);
    segments.forEach(s => assert.isFalse(s.hasClass('hidden')));
  });

  it('hides segments that do not match current filter', () => {
    const wrapper = mount(
      <Transcript transcript={transcript} currentTime={5} filter="video" />
    );
    const segments = wrapper.find('li[data-testid="segment"]');

    // First segment is not hidden because it matches the current time.
    assert.isFalse(segments.at(0).hasClass('hidden'));

    // Second segment is not hidden because it matches the filter.
    assert.isFalse(segments.at(1).hasClass('hidden'));

    // Third segment is hidden because it does not match the filter.
    assert.isTrue(segments.at(2).hasClass('hidden'));
  });

  if (typeof Highlight === 'function') {
    it('registers and unregisters custom highlight', () => {
      sinon.stub(CSS.highlights, 'set');
      sinon.stub(CSS.highlights, 'delete');

      try {
        const wrapper = mount(
          <Transcript transcript={transcript} currentTime={5} filter="video" />
        );
        assert.calledWith(
          CSS.highlights.set,
          'transcript-filter-match',
          sinon.match.instanceOf(Highlight)
        );

        wrapper.unmount();

        assert.calledOnce(CSS.highlights.delete);
        assert.calledWith(CSS.highlights.delete, 'transcript-filter-match');
      } finally {
        CSS.highlights.set.restore();
        CSS.highlights.delete.restore();
      }
    });

    it("works in browsers that don't support CSS Custom Highlights", () => {
      const highlightStub = sinon
        .stub(window, 'Highlight')
        .get(() => undefined);
      try {
        const wrapper = mount(
          <Transcript transcript={transcript} currentTime={5} filter="video" />
        );
        wrapper.unmount();
      } finally {
        highlightStub.restore();
      }
    });
  }
});
