import { mount } from 'enzyme';

import {
  $imports,
  default as YouTubeVideoPlayer,
  PlayerState,
} from '../YouTubeVideoPlayer';

// Capture `setTimeout` for use in bypassing Sinon's fake timers.
const globalSetTimeout = setTimeout;

function delay(ms) {
  return new Promise(resolve => globalSetTimeout(resolve, ms));
}

describe('YouTubeVideoPlayer', () => {
  let clock;
  let fakeYT;
  let fakeLoadYouTubeIFrameAPI;
  let fakePlayer;

  beforeEach(() => {
    clock = sinon.useFakeTimers();

    fakePlayer = {
      getCurrentTime: sinon.stub().returns(0),
      getPlayerState: sinon.stub().returns(PlayerState.UNSTARTED),
      pauseVideo: sinon.stub(),
      playVideo: sinon.stub(),
      seekTo: sinon.stub(),
    };

    fakeYT = {
      Player: sinon.stub().returns(fakePlayer),
    };

    fakeLoadYouTubeIFrameAPI = sinon.stub().resolves(fakeYT);

    $imports.$mock({
      '../utils/youtube': {
        loadYouTubeIFrameAPI: fakeLoadYouTubeIFrameAPI,
      },
    });

    sinon.stub(console, 'error');
  });

  afterEach(() => {
    $imports.$restore();
    console.error.restore();
    clock.restore();
  });

  /** Simulate initialization of the YouTube IFrame Player API. */
  async function initPlayer() {
    await delay(0);
    const { events } = fakeYT.Player.args[0][1];
    events.onReady();
    emitPlayerStateChange(PlayerState.UNSTARTED);
  }

  /**
   * Simulate playback state changing.
   *
   * @param {YT.PlayerState} state
   */
  function emitPlayerStateChange(state) {
    const { events } = fakeYT.Player.args[0][1];
    events.onStateChange({ data: state });
  }

  /**
   * Simulate the video time changing as a result of the video playing or
   * the user seeking the video.
   *
   * See https://issuetracker.google.com/issues/283097094.
   *
   * @param {number} timestamp
   */
  function emitPlayerProgressChange(timestamp) {
    const { events } = fakeYT.Player.args[0][1];
    events.onVideoProgress({ data: timestamp });
  }

  it('creates video player iframe', () => {
    const wrapper = mount(<YouTubeVideoPlayer videoId="abcdef" />);
    const iframe = wrapper.find('iframe');
    assert.isTrue(iframe.exists());
    const origin = encodeURIComponent(window.origin);
    assert.equal(
      iframe.prop('src'),
      `https://www.youtube.com/embed/abcdef?enablejsapi=1&origin=${origin}`
    );
  });

  it('reports error if YouTube IFrame Player API fails to load', async () => {
    fakeLoadYouTubeIFrameAPI.rejects(new Error('Failed to load'));
    const wrapper = mount(<YouTubeVideoPlayer videoId="abcdef" />);

    await delay(0);

    wrapper.update();

    assert.isTrue(wrapper.exists('[data-testid="load-error"]'));
    assert.include(
      wrapper.text(),
      'There was an error loading this video. Try reloading the page.'
    );
  });

  it('reports initial playback state after player loads', async () => {
    const onPlayingChanged = sinon.stub();
    mount(
      <YouTubeVideoPlayer
        videoId="abcdef"
        onPlayingChanged={onPlayingChanged}
      />
    );

    await initPlayer();

    assert.calledWith(onPlayingChanged, false);
  });

  it('calls `onPlayingChanged` callback when playing state changes', async () => {
    const onPlayingChanged = sinon.stub();
    mount(
      <YouTubeVideoPlayer
        videoId="abcdef"
        onPlayingChanged={onPlayingChanged}
      />
    );

    await initPlayer();
    onPlayingChanged.resetHistory();

    emitPlayerStateChange(PlayerState.PLAYING);
    assert.calledWith(onPlayingChanged, true);

    emitPlayerStateChange(PlayerState.PAUSED);
    assert.calledWith(onPlayingChanged, false);
  });

  it('calls `onTimeChanged` callback when video progress changes', async () => {
    const onTimeChanged = sinon.stub();
    mount(
      <YouTubeVideoPlayer videoId="abcdef" onTimeChanged={onTimeChanged} />
    );
    await initPlayer();

    emitPlayerProgressChange(30);
    assert.calledWith(onTimeChanged, 30);

    emitPlayerProgressChange(40);
    assert.calledWith(onTimeChanged, 40);
  });

  it('does not attempt to report play time if `onTimeChanged` not passed', async () => {
    mount(<YouTubeVideoPlayer videoId="abcdef" />);
    await initPlayer();

    fakePlayer.getCurrentTime.returns(30);
    clock.tick(1000);
    assert.notCalled(fakePlayer.getCurrentTime);
  });

  it('starts/stops video when `play` prop changes', async () => {
    const wrapper = mount(<YouTubeVideoPlayer videoId="abcdef" play={false} />);
    await initPlayer();

    wrapper.setProps({ play: true });
    assert.calledOnce(fakePlayer.playVideo);

    wrapper.setProps({ play: false });
    assert.calledOnce(fakePlayer.pauseVideo);
  });

  it('seeks video when `time` prop changes by more than 1s from current position', async () => {
    const wrapper = mount(<YouTubeVideoPlayer videoId="abcdef" time={0} />);
    await initPlayer();

    wrapper.setProps({ time: 0.5 });
    assert.notCalled(fakePlayer.seekTo);

    wrapper.setProps({ time: 3.0 });
    assert.calledWith(fakePlayer.seekTo, 3.0, true);
  });
});
