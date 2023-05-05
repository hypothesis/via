import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import VideoPlayerApp from '../VideoPlayerApp';

describe('VideoPlayerApp', () => {
  const transcriptData = {
    segments: [
      {
        time: 0,
        text: 'Hello',
      },
      {
        time: 5,
        text: 'World',
      },
    ],
  };

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

    const playButton = wrapper.find('button[data-testid="play-button"]');
    assert.equal(playButton.text(), '⏵');

    playButton.simulate('click');

    player = wrapper.find('YouTubeVideoPlayer');
    assert.isTrue(player.prop('play'));
    assert.equal(playButton.text(), '⏸');
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
    assert.equal(player.prop('time'), transcriptData.segments[1].time);
  });
});
