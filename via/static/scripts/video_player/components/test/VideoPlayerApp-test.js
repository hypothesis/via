import {
  mockImportedComponents,
  delay,
  waitForElement,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { useImperativeHandle } from 'preact/hooks';
import { act } from 'preact/test-utils';

import {
  videoPlayerConfig,
  transcriptsAPIResponse,
} from '../../../test-util/video-player-fixtures';
import { APIError } from '../../utils/api';
import { clipDurations } from '../../utils/transcript';
import VideoPlayerApp, { $imports } from '../VideoPlayerApp';

describe('VideoPlayerApp', () => {
  let fakeCallAPI;

  const transcriptData = {
    segments: [
      {
        start: 0,
        // nb. Duration is "too long" here, matching what we might get back
        // from YouTube. It should be normalized before passing to the
        // Transcript component.
        duration: 10,
        text: 'Hello',
      },
      {
        start: 5,
        duration: 7,
        text: 'World',
      },
    ],
  };

  function FakeHypothesisClient({ config }) {
    // Catch `contentReady` errors so tests don't fail with errors about
    // unhandled rejections.
    config.contentReady?.catch(() => {});
    return <div />;
  }
  FakeHypothesisClient.displayName = 'HypothesisClient';

  function FakeTranscript({ controlsRef }) {
    useImperativeHandle(
      controlsRef,
      () => ({
        scrollToBottom: sinon.stub(),
        scrollToCurrentSegment: sinon.stub(),
        scrollToTop: sinon.stub(),
      }),
      []
    );
    return <div />;
  }
  FakeTranscript.displayName = 'Transcript';

  function setFilter(wrapper, query) {
    const input = wrapper.find('FilterInput');
    act(() => {
      input.prop('setFilter')(query);
    });
    wrapper.update();
  }

  function getFilter(wrapper) {
    const transcript = wrapper.find('Transcript');
    return transcript.prop('filter');
  }

  let wrappers;
  let fakeLayoutInfo;
  let fakeUseAppLayout;
  let fakeUseSideBySideLayout;

  function createVideoPlayer(props = {}) {
    const wrapper = mount(
      <VideoPlayerApp
        videoId="1234"
        clientSrc="https://dummy.hypothes.is/embed.js"
        clientConfig={{}}
        // By default start with the transcript already loaded, instead of
        // using the API to fetch it.
        transcriptSource={transcriptData}
        {...props}
      />
    );
    wrappers.push(wrapper);
    return wrapper;
  }

  function createVideoPlayerUsingAPI() {
    return createVideoPlayer({
      transcriptSource: videoPlayerConfig.api.transcript,
    });
  }

  function findButton(wrapper, name) {
    return wrapper.find(`button[data-testid="${name}-button"]`);
  }

  beforeEach(() => {
    wrappers = [];
    fakeLayoutInfo = {
      appSize: 'lg',
      multicolumn: true,
      transcriptWidth: '100%',
    };
    fakeUseAppLayout = sinon.stub().returns(fakeLayoutInfo);
    fakeUseSideBySideLayout = sinon.stub().returns(false);
    fakeCallAPI = sinon.stub().rejects(new Error('Dummy API error'));

    $imports.$mock(mockImportedComponents());

    // Un-mock icons, so we get coverage for these very simple components
    // without dedicated tests.
    $imports.$restore({
      './icons': true,
    });

    $imports.$mock({
      './HypothesisClient': FakeHypothesisClient,
      './Transcript': FakeTranscript,
      '../hooks/use-app-layout': { useAppLayout: fakeUseAppLayout },
      '../hooks/use-side-by-side-layout': {
        useSideBySideLayout: fakeUseSideBySideLayout,
      },
      '../utils/api': {
        callAPI: fakeCallAPI,
      },
    });
  });

  afterEach(() => {
    wrappers.forEach(w => w.unmount());
    $imports.$restore();
  });

  describe('app layout', () => {
    context('multi-column layout for wider widths', () => {
      beforeEach(() => {
        fakeLayoutInfo.multicolumn = true;
      });
      it('renders a top bar with branding and filter input', () => {
        const wrapper = createVideoPlayer();

        const topBar = wrapper.find('[data-testid="top-bar"]');
        assert.isTrue(topBar.exists());
        assert.isTrue(topBar.find('[data-testid="hypothesis-logo"]').exists());
        assert.isTrue(topBar.find('FilterInput').exists());
      });

      it('renders a play/pause button', () => {
        const wrapper = createVideoPlayer();
        assert.isTrue(wrapper.find('[data-testid="play-button"]').exists());
      });
    });

    context('single-column layout for narrow widths', () => {
      beforeEach(() => {
        fakeLayoutInfo.multicolumn = false;
      });

      it('does not render a top bar', () => {
        const wrapper = createVideoPlayer();

        const topBar = wrapper.find('[data-testid="top-bar"]');
        assert.isFalse(topBar.exists());
      });

      it('renders filter input within transcript controls', () => {
        const wrapper = createVideoPlayer();
        const controls = wrapper.find('[data-testid="transcript-controls"]');
        assert.isTrue(controls.find('FilterInput').exists());
      });

      it('does not render a play/pause button', () => {
        const wrapper = createVideoPlayer();
        assert.isFalse(wrapper.find('[data-testid="play-button"]').exists());
      });
    });
  });

  describe('transcript loading', () => {
    beforeEach(() => {
      fakeCallAPI
        .withArgs(videoPlayerConfig.api.transcript)
        .resolves(transcriptsAPIResponse);
    });

    it('loads transcript via API', async () => {
      const wrapper = createVideoPlayerUsingAPI();
      assert.calledWith(fakeCallAPI, videoPlayerConfig.api.transcript);

      // App should initially be in a loading state.
      assert.isTrue(
        wrapper.exists('[data-testid="transcript-loading-spinner"]')
      );

      // Transcript should be displayed when loading completes.
      const transcript = await waitForElement(wrapper, 'Transcript');

      const expectedTranscript = {
        ...transcriptsAPIResponse.data.attributes,
        segments: clipDurations(
          transcriptsAPIResponse.data.attributes.segments
        ),
      };
      assert.deepEqual(transcript.prop('transcript'), expectedTranscript);
    });

    function findCopyButton(wrapper) {
      return wrapper.find('CopyButton');
    }

    it('disables toolbar buttons while transcript is loading', async () => {
      const wrapper = createVideoPlayerUsingAPI();
      const buttons = ['scroll-top', 'scroll-bottom', 'sync'];

      assert.isNull(findCopyButton(wrapper).prop('transcript'));
      for (const button of buttons) {
        assert.isTrue(findButton(wrapper, button).prop('disabled'));
      }

      await waitForElement(wrapper, 'Transcript');

      assert.isNotNull(findCopyButton(wrapper).prop('transcript'));
      for (const button of buttons) {
        assert.isFalse(findButton(wrapper, button).prop('disabled'));
      }
    });

    it('loads client while transcript is loading', async () => {
      const wrapper = createVideoPlayerUsingAPI();
      assert.isTrue(wrapper.exists('HypothesisClient'));
    });

    it('informs client via `contentReady` when content is loaded', async () => {
      const events = [];

      function FakeTranscript() {
        events.push('transcript-rendered');
        return <div />;
      }
      FakeTranscript.displayName = 'Transcript';

      $imports.$mock({
        './Transcript': FakeTranscript,
      });

      fakeCallAPI
        .withArgs(videoPlayerConfig.api.transcript)
        .callsFake(async () => {
          await delay(1);
          events.push('transcript-loaded');
          return transcriptsAPIResponse;
        });

      const wrapper = createVideoPlayerUsingAPI();

      // Get the promise we tell the client to wait for.
      const { contentReady } = wrapper.find('HypothesisClient').prop('config');
      assert.instanceOf(contentReady, Promise);
      contentReady.then(() => events.push('content-ready'));
      await waitForElement(wrapper, 'Transcript');

      assert.deepEqual(events, [
        'transcript-loaded',
        'transcript-rendered',
        'content-ready',
      ]);
    });

    it('informs client via `contentReady` when content fails to load', async () => {
      const error = new APIError(404);
      fakeCallAPI.withArgs(videoPlayerConfig.api.transcript).rejects(error);

      const wrapper = createVideoPlayerUsingAPI();
      const { contentReady } = wrapper.find('HypothesisClient').prop('config');

      let contentReadyError;
      try {
        await contentReady;
      } catch (e) {
        contentReadyError = e;
      }

      assert.instanceOf(contentReadyError, Error);
      assert.equal(contentReadyError.message, 'Transcript failed to load');
    });

    it('displays error if transcript failed to load', async () => {
      const error = new APIError(404);
      fakeCallAPI.withArgs(videoPlayerConfig.api.transcript).rejects(error);

      const wrapper = createVideoPlayerUsingAPI();
      const errorDisplay = await waitForElement(wrapper, 'TranscriptError');

      assert.equal(errorDisplay.prop('error'), error);
    });
  });

  it('plays and pauses video', () => {
    const wrapper = createVideoPlayer();

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
    const wrapper = createVideoPlayer();
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

  it('syncs timestamp from player to transcript', () => {
    const wrapper = createVideoPlayer();
    act(() => {
      wrapper.find('YouTubeVideoPlayer').prop('onTimeChanged')(20);
    });
    wrapper.update();

    const transcript = wrapper.find('Transcript');
    assert.equal(transcript.prop('currentTime'), 20);
  });

  it('updates player time when transcript segment is selected', () => {
    const wrapper = createVideoPlayer();
    act(() => {
      wrapper.find('Transcript').prop('onSelectSegment')(
        transcriptData.segments[1]
      );
    });
    wrapper.update();

    const player = wrapper.find('YouTubeVideoPlayer');
    assert.equal(player.prop('time'), transcriptData.segments[1].start);
  });

  it('clears filter when transcript segment is selected', () => {
    const wrapper = createVideoPlayer();
    setFilter(wrapper, 'foobar');

    assert.equal(getFilter(wrapper), 'foobar');

    act(() => {
      wrapper.find('Transcript').prop('onSelectSegment')(
        transcriptData.segments[1]
      );
    });
    wrapper.update();

    assert.equal(getFilter(wrapper), '');
  });

  it('scrolls to current segment when filter is cleared', () => {
    const wrapper = createVideoPlayer();
    setFilter(wrapper, 'foobar');

    const transcriptController = wrapper.find('Transcript').prop('controlsRef');
    setFilter(wrapper, '');

    assert.calledOnce(transcriptController.current.scrollToCurrentSegment);
  });

  [
    {
      button: 'sync',
      method: 'scrollToCurrentSegment',
    },
    {
      button: 'scroll-top',
      method: 'scrollToTop',
    },
    {
      button: 'scroll-bottom',
      method: 'scrollToBottom',
    },
  ].forEach(({ button, method }) => {
    it(`scrolls transcript when "${button}" button is clicked`, () => {
      const wrapper = createVideoPlayer();
      const transcriptController = wrapper
        .find('Transcript')
        .prop('controlsRef');
      assert.ok(transcriptController.current);

      findButton(wrapper, button).simulate('click');

      assert.calledOnce(transcriptController.current[method]);
    });
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
    const wrapper = createVideoPlayer();
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

  it('filters transcript when typing in search field', () => {
    const wrapper = createVideoPlayer();

    setFilter(wrapper, 'foobar');

    const transcript = wrapper.find('Transcript');
    assert.equal(transcript.prop('filter'), 'foobar');
  });

  it('dispatches dummy scroll event when filter changes, to update bucket bar', () => {
    const wrapper = createVideoPlayer();
    const onScroll = sinon.stub();
    document.body.addEventListener('scroll', onScroll, { once: true });

    setFilter(wrapper, 'foobar');

    assert.calledOnce(onScroll);
  });

  it('clears filter when Hypothesis client scrolls to a highlight', async () => {
    const wrapper = createVideoPlayer();
    const transcriptController = wrapper.find('Transcript').prop('controlsRef');

    setFilter(wrapper, 'foobar');

    // Simulate event emitted by client before it scrolls a highlight, which
    // may be in a hidden segment, into view.
    const event = new CustomEvent('scrolltorange');
    let ready;
    event.waitUntil = promise => {
      ready = promise;
    };
    act(() => {
      document.body.dispatchEvent(event);
    });

    // Wait for VideoPlayerApp to be re-rendered with filter cleared.
    assert.instanceOf(ready, Promise);
    await ready;

    wrapper.update();
    assert.equal(getFilter(wrapper), '');

    // Unlike when the user clears the filter directly, we shouldn't scroll
    // to the current segment, as this would conflict with the client trying
    // to scroll to a highlight.
    assert.notCalled(transcriptController.current.scrollToCurrentSegment);
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
    const wrapper = createVideoPlayer();
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
    const wrapper = createVideoPlayer();

    setFilter(wrapper, 'foobar');

    // If a "scrolltorange" event is dispatched at the body, but doesn't
    // have the expected even type, the video player should ignore it.
    document.body.dispatchEvent(new Event('scrolltorange'));
  });

  it('toggles automatic scrolling when "Auto-scroll" checkbox is changed', () => {
    const wrapper = createVideoPlayer();
    assert.isTrue(wrapper.find('Transcript').prop('autoScroll'));
    toggleAutoScroll(wrapper);
    assert.isFalse(wrapper.find('Transcript').prop('autoScroll'));
    toggleAutoScroll(wrapper);
    assert.isTrue(wrapper.find('Transcript').prop('autoScroll'));
  });

  it('configures client bucket bar and disables side-by-side mode', () => {
    const clientConfig = { openSidebar: true };
    const wrapper = createVideoPlayer({ clientConfig });
    const mergedConfig = wrapper.find('HypothesisClient').prop('config');

    assert.isTrue(mergedConfig.openSidebar);
    assert.equal(mergedConfig.bucketContainerSelector, '#bucket-container');
    assert.equal(mergedConfig.sideBySide.mode, 'manual');
    assert.isDefined(mergedConfig.sideBySide.isActive);
  });

  [true, false].forEach(sideBySideEnabled => {
    it('tells client if side-by-side is active', () => {
      fakeUseSideBySideLayout.returns(sideBySideEnabled);

      const wrapper = createVideoPlayer();
      const { sideBySide } = wrapper.find('HypothesisClient').prop('config');

      assert.equal(sideBySide.isActive(), sideBySideEnabled);
    });
  });

  it('appends hidden toast message when transcript is filtered', async () => {
    fakeCallAPI
      .withArgs(videoPlayerConfig.api.transcript)
      .resolves(transcriptsAPIResponse);

    const wrapper = createVideoPlayerUsingAPI();
    const transcript = await waitForElement(wrapper, 'Transcript');
    const getToastMessages = () =>
      wrapper.find('ToastMessages').prop('messages');

    // Toast messages are initially empty
    assert.equal(getToastMessages().length, 0);

    transcript.props().onFilterMatch('some text', 5);
    wrapper.update();

    const [toastMessage] = getToastMessages();
    assert.match(toastMessage, {
      type: 'success',
      message: '"some text" returned 5 results',
      visuallyHidden: true,
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
          transcriptSource={transcriptData}
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

    context('when interacting with input', () => {
      beforeEach(() => {
        // These tests need the actual input
        $imports.$restore({
          './FilterInput': true,
        });
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
