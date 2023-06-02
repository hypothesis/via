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

  let wrappers;

  // TODO - Convert existing tests to use this helper to render the player.
  function createVideoPlayer(props = {}) {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        transcript={transcriptData}
        {...props}
      />
    );
    wrappers.push(wrapper);
    return wrapper;
  }

  beforeEach(() => {
    wrappers = [];

    $imports.$mock(mockImportedComponents());

    // Un-mock icons, so we get coverage for these very simple components
    // without dedicated tests.
    $imports.$restore({
      './icons': true,
    });

    $imports.$mock({
      './Transcript': FakeTranscript,
    });
  });

  afterEach(() => {
    wrappers.forEach(w => w.unmount());
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
    assert.equal(playButton.text().trim(), 'Play');

    playButton.simulate('click');

    player = wrapper.find('YouTubeVideoPlayer');
    assert.isTrue(player.prop('play'));

    playButton = wrapper.find('button[data-testid="play-button"]');
    assert.equal(playButton.text().trim(), 'Pause');
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
    assert.equal(playButton.text().trim(), 'Pause');

    act(() => {
      wrapper.find('YouTubeVideoPlayer').prop('onPlayingChanged')(false);
    });
    wrapper.update();
    assert.equal(playButton.text().trim(), 'Play');
  });

  it('copies transcript to clipboard when "Copy" button is pressed', async () => {
    const fakeClipboard = {
      writeText: sinon.stub().resolves(),
    };
    const clipboardStub = sinon
      .stub(navigator, 'clipboard')
      .get(() => fakeClipboard);

    try {
      const wrapper = mount(
        <VideoPlayerApp
          videoId="1234"
          clientSrc="https://dummy.hypothes.is/embed.js"
          clientConfig={{}}
          transcript={transcriptData}
        />
      );

      await wrapper.find('button[data-testid="copy-button"]').prop('onClick')();

      assert.calledWith(fakeClipboard.writeText, 'Hello\nWorld');
    } finally {
      clipboardStub.restore();
    }
  });

  it('logs a warning if accessing clipboard fails', async () => {
    const copyError = new Error('Not allowed');
    const fakeClipboard = {
      writeText: sinon.stub().rejects(copyError),
    };
    const clipboardStub = sinon
      .stub(navigator, 'clipboard')
      .get(() => fakeClipboard);
    const warnStub = sinon.stub(console, 'warn');

    try {
      const wrapper = mount(
        <VideoPlayerApp
          videoId="1234"
          clientSrc="https://dummy.hypothes.is/embed.js"
          clientConfig={{}}
          transcript={transcriptData}
        />
      );

      try {
        await wrapper
          .find('button[data-testid="copy-button"]')
          .prop('onClick')();
      } catch {
        /* ignored */
      }

      assert.calledWith(console.warn, 'Failed to copy transcript', copyError);
    } finally {
      clipboardStub.restore();
      warnStub.restore();
    }
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

  it('syncs transcript when "Sync" button is clicked', () => {
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

  const toggleAutoScroll = wrapper => {
    act(() => {
      const input = wrapper.find('input[data-testid="autoscroll-checkbox"]');

      input.getDOMNode().checked = !input.getDOMNode().checked;
      input.simulate('change');
    });
    wrapper.update();
  };

  const togglePlaying = wrapper => {
    wrapper.find('button[data-testid="play-button"]').simulate('click');
  };

  it('syncs transcript when transitioning from paused to playing if auto-scroll is active', () => {
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

    // When auto-scroll is active (default state) transcript should sync as
    // soon as playback starts.
    togglePlaying(wrapper);
    assert.calledOnce(transcriptController.current.scrollToCurrentSegment);
    transcriptController.current.scrollToCurrentSegment.resetHistory();

    togglePlaying(wrapper); // Pause video

    // If auto-scroll is disabled when the play button is clicked, it shouldn't
    // sync.
    toggleAutoScroll(wrapper);
    togglePlaying(wrapper);
    assert.notCalled(transcriptController.current.scrollToCurrentSegment);
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
    const event = new CustomEvent('scrolltorange');
    let ready;
    event.waitUntil = promise => {
      ready = promise;
    };
    document.body.dispatchEvent(event);

    // Wait for VideoPlayerApp to be re-rendered with filter cleared.
    assert.instanceOf(ready, Promise);
    await ready;

    wrapper.update();
    const transcript = wrapper.find('Transcript');
    assert.equal(transcript.prop('filter'), '');
  });

  it('does not defer scrolling if there is no filter', () => {
    createVideoPlayer();

    // Simulate event emitted by client before it scrolls a highlight.
    const event = new CustomEvent('scrolltorange');
    event.waitUntil = sinon.stub();
    document.body.dispatchEvent(event);

    // Since there is no filter active, `ScrollToRangeEvent.waitUntil` will not
    // be called, and the Hypothesis client will scroll immediately.
    assert.notCalled(event.waitUntil);
  });

  it('pauses playback when Hypothesis client scrolls to a highlight', () => {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        transcript={transcriptData}
      />
    );
    wrapper.find('button[data-testid="play-button"]').simulate('click');

    const event = new CustomEvent('scrolltorange');
    event.waitUntil = () => {}; // Dummy
    act(() => {
      document.body.dispatchEvent(event);
    });
    wrapper.update();

    const player = wrapper.find('YouTubeVideoPlayer');
    assert.isFalse(player.prop('play'));
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

    assert.isTrue(wrapper.find('Transcript').prop('autoScroll'));
    toggleAutoScroll(wrapper);
    assert.isFalse(wrapper.find('Transcript').prop('autoScroll'));
    toggleAutoScroll(wrapper);
    assert.isTrue(wrapper.find('Transcript').prop('autoScroll'));
  });

  it('configures bucket bar container for client', () => {
    const clientConfig = { openSidebar: true };
    const wrapper = createVideoPlayer({ clientConfig });
    const mergedConfig = wrapper.find('HypothesisClient').prop('config');
    assert.deepEqual(mergedConfig, {
      openSidebar: true,
      bucketBarContainer: '#bucket-container',
    });
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
