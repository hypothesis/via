import { mount } from 'enzyme';

import Transcript, { $imports } from '../Transcript';

describe('Transcript', () => {
  let FakeTextHighlighter;
  let fakeTextHighlighter;

  let container;
  let wrappers;

  const transcript = {
    segments: [
      {
        start: 5,
        duration: 5,
        text: 'Hello and welcome',
      },
      {
        start: 10,
        duration: 10,
        text: 'To this video about',
      },
      {
        start: 20,
        duration: 4,
        text: 'how to use Hypothesis',
      },
    ],
  };

  beforeEach(() => {
    wrappers = [];
    container = document.createElement('div');
    document.body.append(container);

    fakeTextHighlighter = {
      highlightSpans: sinon.stub(),
      removeHighlights: sinon.stub(),
    };
    FakeTextHighlighter = sinon.stub().returns(fakeTextHighlighter);

    $imports.$mock({
      '../utils/highlighter': {
        TextHighlighter: FakeTextHighlighter,
      },
    });
  });

  afterEach(() => {
    container.remove();
    wrappers.forEach(w => w.unmount());
  });

  function createTranscript(props = {}) {
    const wrapper = mount(<Transcript transcript={transcript} {...props} />);
    wrappers.push(wrapper);
    return wrapper;
  }

  it('renders segments', () => {
    const wrapper = mount(
      <Transcript transcript={transcript} currentTime={5} />
    );
    const segments = wrapper.find('[data-testid="segment"]');
    assert.equal(segments.length, 3);

    const renderedSegments = [];
    for (let i = 0; i < segments.length; i++) {
      const segment = segments.at(i);
      const start = segment.find('p').prop('data-time-start');
      const end = segment.find('p').prop('data-time-end');
      renderedSegments.push({
        text: segment.text(),
        isCurrent: segment.prop('data-is-current'),
        startTime: start ? parseFloat(start) : undefined,
        endTime: end ? parseFloat(end) : undefined,
      });
    }

    assert.deepEqual(renderedSegments, [
      {
        text: 'Hello and welcome ',
        isCurrent: true,
        startTime: 5,
        endTime: 10,
      },
      {
        text: 'To this video about ',
        isCurrent: false,
        startTime: 10,
        endTime: 20,
      },
      {
        text: 'how to use Hypothesis ',
        isCurrent: false,
        startTime: 20,
        endTime: 24,
      },
    ]);
  });

  it('renders segments if none is current', () => {
    const wrapper = createTranscript({ currentTime: 0 });
    const segments = wrapper.find('[data-testid="segment"]');
    assert.isFalse(segments.at(0).prop('data-is-current'));
  });

  it('invokes `onSelectSegment` callback when segment timestamp is clicked', () => {
    const selectSegment = sinon.stub();
    const wrapper = createTranscript({
      currentTime: 5,
      onSelectSegment: selectSegment,
    });
    const timestamp = wrapper
      .find('[data-testid="segment"]')
      .at(1)
      .find('button');

    timestamp.simulate('click');

    assert.calledWith(selectSegment, transcript.segments[1]);
  });

  it('invokes `onSelectSegment` callback when segment text is clicked', () => {
    let wrapper;

    try {
      const selectSegment = sinon.stub();
      const wrapper = mount(
        <Transcript
          transcript={transcript}
          currentTime={5}
          onSelectSegment={selectSegment}
        />,
        { attachTo: container }
      );
      const timestamp = wrapper.find('[data-testid="segment"]').at(1).find('p');

      // Click on segment text with no selection. This should select the segment.
      timestamp.simulate('pointerdown');
      timestamp.simulate('pointerup');
      assert.calledWith(selectSegment, transcript.segments[1]);
      selectSegment.resetHistory();

      // Click on segment text, clearing existing selection in the process.
      // This should be ignored.
      window.getSelection().selectAllChildren(document.body);
      timestamp.simulate('pointerdown');
      window.getSelection().empty();
      timestamp.simulate('pointerup');
      assert.notCalled(selectSegment);

      // Click on segment text, creating a new selection in the process.
      // This should be ignored.
      timestamp.simulate('pointerdown');
      window.getSelection().selectAllChildren(document.body);
      timestamp.simulate('pointerup');
      assert.notCalled(selectSegment);
    } finally {
      wrapper?.unmount();
    }
  });

  it('scrolls current segment into view', () => {
    let wrapper;
    try {
      wrapper = mount(<Transcript transcript={transcript} currentTime={5} />, {
        // Render into document so transcript has a non-zero height.
        attachTo: container,
      });
      const scrollContainer = wrapper.find(
        'div[data-testid="scroll-container"]'
      );
      const scrollTo = sinon.spy(scrollContainer.getDOMNode(), 'scrollTo');
      const segment = wrapper.find('[data-testid="segment"]').at(1);
      const expectedTop =
        segment.getDOMNode().offsetTop -
        scrollContainer.getDOMNode().clientHeight * (1 / 4);

      wrapper.setProps({ currentTime: 10 });

      assert.calledWith(scrollTo, {
        left: 0,
        top: expectedTop,
      });
    } finally {
      wrapper?.unmount();
    }
  });

  it('does not scroll to current segment if `autoScroll` is disabled', () => {
    const wrapper = createTranscript({ autoScroll: false, currentTime: 5 });
    const scrollContainer = wrapper.find('div[data-testid="scroll-container"]');
    const scrollTo = sinon.spy(scrollContainer.getDOMNode(), 'scrollTo');

    wrapper.setProps({ currentTime: 10 });

    assert.notCalled(scrollTo);
  });

  it('does not scroll transcript while user is selecting text', () => {
    const wrapper = mount(
      <Transcript transcript={transcript} currentTime={5} />,
      {
        attachTo: container,
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

  describe('scrolling methods', () => {
    const longTranscript = {
      segments: Array(20)
        .fill(0)
        .map((_, i) => ({
          start: i * 10,
          text: `Text of segment ${i}`,
        })),
    };

    function createLongTranscript() {
      const controlsRef = { current: null };
      const wrapper = mount(
        <Transcript
          controlsRef={controlsRef}
          transcript={longTranscript}
          currentTime={50}
        />,
        { attachTo: container }
      );
      const scrollContainer = wrapper.find(
        'div[data-testid="scroll-container"]'
      );
      const scrollTo = sinon.spy(scrollContainer.getDOMNode(), 'scrollTo');

      return { controlsRef, scrollContainer, scrollTo, wrapper };
    }

    beforeEach(() => {
      container.style.height = '400px';
    });

    it('scrolls to current segment when `scrollToCurrentSegment` is called', () => {
      const { controlsRef, scrollTo, scrollContainer, wrapper } =
        createLongTranscript();

      assert.ok(controlsRef.current);
      controlsRef.current.scrollToCurrentSegment();

      const currentSegment = wrapper.find('[data-testid="segment"]').at(5);
      assert.isTrue(currentSegment.prop('data-is-current'));
      assert.calledOnce(scrollTo);

      // Calculate expected position that puts segment towards, but not at,
      // the top of the container.
      const expectedTop =
        currentSegment.getDOMNode().offsetTop -
        scrollContainer.getDOMNode().clientHeight * (1 / 4);
      const actualTop = scrollTo.args[0][0].top;
      assert.approximately(actualTop, expectedTop, 5);
    });

    it('scrolls to first segment when `scrollToTop` is called', () => {
      const { controlsRef, scrollTo } = createLongTranscript();

      assert.ok(controlsRef.current);
      controlsRef.current.scrollToTop();

      assert.calledWith(scrollTo, {
        left: 0,
        top: 0,
      });
    });

    it('scrolls to last segment when `scrollToTop` is called', () => {
      const { controlsRef, scrollContainer, scrollTo } = createLongTranscript();

      assert.ok(controlsRef.current);
      controlsRef.current.scrollToBottom();

      assert.calledWith(scrollTo, {
        left: 0,
        top: scrollContainer.getDOMNode().scrollHeight,
      });
    });
  });

  it('does not hide segments when there is no filter', () => {
    const wrapper = createTranscript({ currentTime: 0 });
    const segments = wrapper.find('li[data-testid="segment"]');
    assert.equal(segments.length, 3);
    segments.forEach(s => assert.isFalse(s.hasClass('hidden')));
  });

  it('hides segments that do not match current filter', () => {
    const wrapper = createTranscript({ currentTime: 5, filter: 'video' });
    const segments = wrapper.find('li[data-testid="segment"]');

    // First segment is not hidden because it matches the current time.
    assert.isFalse(segments.at(0).hasClass('hidden'));

    // Second segment is not hidden because it matches the filter.
    assert.isFalse(segments.at(1).hasClass('hidden'));

    // Third segment is hidden because it does not match the filter.
    assert.isTrue(segments.at(2).hasClass('hidden'));
  });

  it('highlights filter matches in segment text', () => {
    const filter = 'video';
    const wrapper = createTranscript({ currentTime: 5, filter });
    const segments = wrapper.find('TranscriptSegment');
    const segmentText = transcript.segments[1].text;
    const expectedSpans = [
      {
        start: segmentText.indexOf(filter),
        end: segmentText.indexOf(filter) + filter.length,
      },
    ];
    assert.deepEqual(segments.at(1).prop('matches'), expectedSpans);

    const highlightCalls = fakeTextHighlighter.highlightSpans.getCalls();
    assert.equal(
      highlightCalls.length,
      1 // Number of segments with matches
    );

    const [element, spans] = highlightCalls[0].args;
    assert.equal(element.tagName, 'P');
    assert.deepEqual(spans, expectedSpans);

    wrapper.unmount();

    assert.calledOnce(fakeTextHighlighter.removeHighlights);
    assert.calledWith(fakeTextHighlighter.removeHighlights, element);
  });
});
