import { mount } from 'enzyme';

import HTMLVideoPlayer from '../HTMLVideoPlayer';

function waitForTrackLoad(trackEl) {
  if (trackEl.readyState === HTMLTrackElement.LOADED) {
    return Promise.resolve();
  }
  return new Promise((resolve, reject) => {
    trackEl.addEventListener('load', resolve, { once: true });
    trackEl.addEventListener(
      'error',
      () => reject(new Error('Caption track failed to load')),
      { once: true },
    );
  });
}

describe('HTMLVideoPlayer', () => {
  let players;

  const createPlayer = (props = {}) => {
    const player = mount(<HTMLVideoPlayer {...props} />);
    players.push(player);
    return player;
  };

  beforeEach(() => {
    players = [];
  });

  afterEach(() => {
    players.forEach(player => player.unmount());
  });

  it('should render video', () => {
    const wrapper = createPlayer({ videoURL: 'test-video.mp4' });
    const video = wrapper.find('video');
    assert.equal(video.prop('src'), 'test-video.mp4');

    const videoEl = video.getDOMNode();

    // We stub, rather than spy on, `play` here because the real method will
    // trigger an async error if the user has not interacted with the document.
    const playStub = sinon.stub(videoEl, 'play');
    const pauseStub = sinon.stub(videoEl, 'pause');

    wrapper.setProps({ play: true });
    assert.calledOnce(playStub);

    wrapper.setProps({ play: false });
    assert.calledOnce(pauseStub);
  });

  it('should invoke callback when video is paused/un-paused', () => {
    const onPlayingChanged = sinon.stub();
    const wrapper = createPlayer({
      videoURL: 'test-video.mp4',
      onPlayingChanged,
    });
    const video = wrapper.find('video').getDOMNode();

    video.dispatchEvent(new Event('play'));
    assert.calledWith(onPlayingChanged, true);

    video.dispatchEvent(new Event('pause'));
    assert.calledWith(onPlayingChanged, false);
  });

  it('should invoke callback when video time changes', () => {
    const onTimeChanged = sinon.stub();
    const wrapper = createPlayer({ videoURL: 'test-video.mp4', onTimeChanged });
    const video = wrapper.find('video').getDOMNode();

    video.dispatchEvent(new Event('timeupdate'));
    assert.calledWith(onTimeChanged, video.currentTime);
  });

  it('should seek video if `time` prop is out of sync with `currentTime`', () => {
    const wrapper = createPlayer({ videoURL: 'test-video.mp4', time: 0 });
    const video = wrapper.find('video').getDOMNode();

    const currentTimeSpy = sinon.spy(video, 'currentTime', ['set']);
    wrapper.setProps({ time: 5 });

    assert.calledWith(currentTimeSpy.set, 5);
  });

  it('should populate caption track', async () => {
    const transcript = {
      segments: [
        {
          start: 1,
          duration: 3,
          text: 'One',
        },
        {
          start: 4,
          duration: 3,
          text: 'Two',
        },
        {
          start: 7,
          duration: 3,
          text: 'Three',
        },
      ],
    };

    const wrapper = createPlayer({ videoURL: 'test-video.mp4', transcript });
    const video = wrapper.find('video').getDOMNode();
    assert.equal(video.textTracks.length, 1);

    // The track is rendered with a loadable `src` from the start. Chrome only
    // shows the captions toggle for tracks that exist when the video
    // initializes and never fail to load.
    const trackEl = wrapper.find('track').getDOMNode();
    assert.match(trackEl.getAttribute('src'), /^blob:/);

    const track = video.textTracks[0];

    // The `cues` property returns `null` unless the mode is set, although the
    // browser may still show the track.
    track.mode = 'showing';

    await waitForTrackLoad(trackEl);
    assert.equal(trackEl.readyState, HTMLTrackElement.LOADED);
    assert.equal(track.cues.length, 3);
    assert.deepEqual(
      Array.from(track.cues).map(cue => cue.text),
      ['One', 'Two', 'Three'],
    );
  });

  it('should render an empty caption track without a transcript', async () => {
    const wrapper = createPlayer({ videoURL: 'test-video.mp4' });
    const video = wrapper.find('video').getDOMNode();
    const trackEl = wrapper.find('track').getDOMNode();
    assert.match(trackEl.getAttribute('src'), /^blob:/);

    const track = video.textTracks[0];
    track.mode = 'showing';

    await waitForTrackLoad(trackEl);
    assert.equal(trackEl.readyState, HTMLTrackElement.LOADED);
    assert.equal(track.cues.length, 0);
  });

  it('should revoke caption track URL on unmount', () => {
    const revokeObjectURL = sinon.spy(URL, 'revokeObjectURL');
    try {
      const wrapper = createPlayer({
        videoURL: 'test-video.mp4',
        transcript: { segments: [{ start: 1, duration: 3, text: 'One' }] },
      });
      const vttURL = wrapper.find('track').getDOMNode().src;

      wrapper.unmount();

      assert.calledWith(revokeObjectURL, vttURL);
    } finally {
      revokeObjectURL.restore();
    }
  });

  [true, false].forEach(allowDownload => {
    it('should disable download controls if `allowDownload` is false', () => {
      const wrapper = createPlayer({
        videoURL: 'test-video.mp4',
        transcript: { segments: [] },
        allowDownload,
      });
      const video = wrapper.find('video').getDOMNode();

      if ('controlsList' in video) {
        assert.deepEqual(
          Array.from(video.controlsList.values()),
          allowDownload ? [] : ['nodownload'],
        );
      }

      const contextEvent = new Event('contextmenu', { cancelable: true });
      video.dispatchEvent(contextEvent);
      assert.equal(contextEvent.defaultPrevented, !allowDownload);
    });
  });
});
