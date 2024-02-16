import { mount } from 'enzyme';

import HTMLVideoPlayer from '../HTMLVideoPlayer';

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

  it('should populate caption track', () => {
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

    const track = video.textTracks[0];

    // The `cues` property returns `null` unless the mode is set, although the
    // browser may still show the track.
    track.mode = 'showing';

    assert.equal(track.cues.length, 3);
  });
});
