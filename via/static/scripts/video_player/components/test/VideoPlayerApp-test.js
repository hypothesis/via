import { mount } from 'enzyme';
import { useImperativeHandle } from 'preact/hooks';
import { act } from 'preact/test-utils';

import { mockImportedComponents } from '../../../test-util/mock-imported-components';
import VideoPlayerApp, { $imports } from '../VideoPlayerApp';

describe('VideoPlayerApp', () => {
  const transcriptData = {
    segments: [
      {
        start: 0,
        text: 'Hello',
      },
      {
        start: 5,
        text: 'World',
      },
    ],
  };

  function FakeTranscript({ controlsRef }) {
    useImperativeHandle(
      controlsRef,
      () => ({
        scrollToCurrentSegment: sinon.stub(),
      }),
      []
    );
    return <div />;
  }
  FakeTranscript.displayName = 'Transcript';

  beforeEach(() => {
    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      './Transcript': FakeTranscript,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('plays and pauses video', () => {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        transcript={transcriptData}
      />
    );
    let player = wrapper.find('YouTubeVideoPlayer');
    assert.isFalse(player.prop('play'));

    let playButton = wrapper.find('button[data-testid="play-button"]');
    assert.equal(playButton.text(), '⏵');
    assert.equal(playButton.prop('title'), 'Play');

    playButton.simulate('click');

    player = wrapper.find('YouTubeVideoPlayer');
    assert.isTrue(player.prop('play'));

    playButton = wrapper.find('button[data-testid="play-button"]');
    assert.equal(playButton.text(), '⏸');
    assert.equal(playButton.prop('title'), 'Pause');
  });

  it('updates play/pause button when player is paused', () => {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        transcript={transcriptData}
      />
    );
    act(() => {
      wrapper.find('YouTubeVideoPlayer').prop('onPlayingChanged')(true);
    });
    wrapper.update();

    const playButton = wrapper.find('button[data-testid="play-button"]');
    assert.equal(playButton.text(), '⏸');

    act(() => {
      wrapper.find('YouTubeVideoPlayer').prop('onPlayingChanged')(false);
    });
    wrapper.update();
    assert.equal(playButton.text(), '⏵');
  });

  it('syncs timestamp from player to transcript', () => {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        transcript={transcriptData}
      />
    );
    act(() => {
      wrapper.find('YouTubeVideoPlayer').prop('onTimeChanged')(20);
    });
    wrapper.update();

    const transcript = wrapper.find('Transcript');
    assert.equal(transcript.prop('currentTime'), 20);
  });

  it('updates player time when transcript segment is selected', () => {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        transcript={transcriptData}
      />
    );
    act(() => {
      wrapper.find('Transcript').prop('onSelectSegment')(
        transcriptData.segments[1]
      );
    });
    wrapper.update();

    const player = wrapper.find('YouTubeVideoPlayer');
    assert.equal(player.prop('time'), transcriptData.segments[1].start);
  });

  it('scrolls current transcript segment into view when "Sync" button is clicked', () => {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        transcript={transcriptData}
      />
    );
    const transcriptController = wrapper.find('Transcript').prop('controlsRef');
    assert.ok(transcriptController.current);

    wrapper.find('button[data-testid="sync-button"]').simulate('click');

    assert.calledOnce(transcriptController.current.scrollToCurrentSegment);
  });

  function setFilter(wrapper, query) {
    const input = wrapper.find('input[data-testid="filter-input"]');
    input.getDOMNode().value = query;
    input.simulate('input');
  }

  it('filters transcript when typing in search field', () => {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        transcript={transcriptData}
      />
    );

    setFilter(wrapper, 'foobar');

    const transcript = wrapper.find('Transcript');
    assert.equal(transcript.prop('filter'), 'foobar');
  });

  it('clears transcript filter when Hypothesis client scrolls to a highlight', async () => {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        transcript={transcriptData}
      />
    );

    setFilter(wrapper, 'foobar');

    // Simulate event emitted by client before it scrolls a highlight, which
    // may be in a hidden segment, into view.
    const scrollToRangeEvent = new CustomEvent('scrolltorange');
    let ready;
    scrollToRangeEvent.waitUntil = promise => {
      ready = promise;
    };
    document.body.dispatchEvent(scrollToRangeEvent);

    // Wait for VideoPlayerApp to be re-rendered with filter cleared.
    assert.instanceOf(ready, Promise);
    await ready;

    wrapper.update();
    const transcript = wrapper.find('Transcript');
    assert.equal(transcript.prop('filter'), '');
  });

  it('ignores "scrolltorange" events with wrong type', () => {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        transcript={transcriptData}
      />
    );

    setFilter(wrapper, 'foobar');

    // If a "scrolltorange" event is dispatched at the body, but doesn't
    // have the expected even type, the video player should ignore it.
    document.body.dispatchEvent(new Event('scrolltorange'));
  });

  it('toggles automatic scrolling when "Auto-scroll" checkbox is changed', () => {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        transcript={transcriptData}
      />
    );

    const toggleAutoScroll = () => {
      act(() => {
        const input = wrapper.find('input[data-testid="autoscroll-checkbox"]');

        input.getDOMNode().checked = !input.getDOMNode().checked;
        input.simulate('change');
      });
      wrapper.update();
    };

    assert.isTrue(wrapper.find('Transcript').prop('autoScroll'));
    toggleAutoScroll();
    assert.isFalse(wrapper.find('Transcript').prop('autoScroll'));
    toggleAutoScroll();
    assert.isTrue(wrapper.find('Transcript').prop('autoScroll'));
  });

  describe('keyboard shortcuts', () => {
    let wrappers;

    beforeEach(() => {
      wrappers = [];
    });

    afterEach(() => {
      wrappers.forEach(w => w.unmount());
    });

    function createVideoPlayer() {
      const wrapper = mount(
        <VideoPlayerApp
          videoId="1234"
          clientSrc="https://dummy.hypothes.is/embed.js"
          clientConfig={{}}
          transcript={transcriptData}
        />,
        { attachTo: document.body }
      );
      wrappers.push(wrapper);
      return wrapper;
    }

    function sendKey(wrapper, key, target = document.body) {
      act(() => {
        target.dispatchEvent(
          new KeyboardEvent('keyup', { key, bubbles: true })
        );
      });
      wrapper.update();
    }

    it('toggles video playback when "k" is pressed', () => {
      const wrapper = createVideoPlayer();
      sendKey(wrapper, 'k');
      assert.isTrue(wrapper.find('YouTubeVideoPlayer').prop('play'));
      sendKey(wrapper, 'k');
      assert.isFalse(wrapper.find('YouTubeVideoPlayer').prop('play'));
    });

    it('ignores shortcut keys when sent to input elements', async () => {
      const wrapper = createVideoPlayer();
      const inputField = wrapper
        .find('input[data-testid="filter-input"]')
        .getDOMNode();
      inputField.focus();

      sendKey(wrapper, 'k', inputField);

      assert.isFalse(wrapper.find('YouTubeVideoPlayer').prop('play'));
    });

    it('focuses search field when "/" is pressed', () => {
      const wrapper = createVideoPlayer();
      const inputField = wrapper
        .find('input[data-testid="filter-input"]')
        .getDOMNode();

      // nb. We are using `assert.isTrue` here rather than `assert.equal`
      // for less verbose errors if assert fails.
      assert.isTrue(document.activeElement !== inputField);

      sendKey(wrapper, '/');

      assert.isTrue(document.activeElement === inputField);

      sendKey(wrapper, 'Escape', inputField);

      assert.isFalse(document.activeElement === inputField);
    });

    it('syncs transcript when "s" is pressed', () => {
      const wrapper = createVideoPlayer();
      const transcriptController = wrapper
        .find('Transcript')
        .prop('controlsRef');

      sendKey(wrapper, 's');

      assert.calledOnce(transcriptController.current.scrollToCurrentSegment);
    });

    it('toggles auto-scroll when "a" is pressed', () => {
      const wrapper = createVideoPlayer();
      assert.isTrue(wrapper.find('Transcript').prop('autoScroll'));
      sendKey(wrapper, 'a');
      assert.isFalse(wrapper.find('Transcript').prop('autoScroll'));
    });
  });
});
