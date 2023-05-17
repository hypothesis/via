import { mount } from 'enzyme';

import Transcript from '../Transcript';

describe('Transcript', () => {
  const transcript = {
    segments: [
      {
        time: 5,
        text: 'Hello and welcome',
      },
      {
        time: 10,
        text: 'To this video about',
      },
      {
        time: 20,
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
});
