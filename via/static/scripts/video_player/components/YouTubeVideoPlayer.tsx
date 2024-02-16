import { AspectRatio, useStableCallback } from '@hypothesis/frontend-shared';
import { useEffect, useMemo, useRef, useState } from 'preact/hooks';

import { loadYouTubeIFrameAPI } from '../utils/youtube';
import type { VideoPlayerProps } from './HTMLVideoPlayer';

/**
 * Playback state values.
 *
 * This is a copy of the `YT.PlayerState` global that is available when the
 * YouTube IFrame API script has loaded, but it works in the test environment
 * where we don't actually load that script.
 *
 * See https://developers.google.com/youtube/iframe_api_reference#Events.
 */
export const PlayerState = {
  UNSTARTED: -1,
  ENDED: 0,
  PLAYING: 1,
  PAUSED: 2,
  BUFFERING: 3,
  CUED: 4,
};

export type YouTubeVideoPlayerProps = VideoPlayerProps & {
  /** ID of the YouTube video to load. */
  videoId: string;
};

function isPlaying(state: YT.PlayerState) {
  return state === PlayerState.PLAYING || state === PlayerState.BUFFERING;
}

/**
 * Additional events that the YouTube player supports, which are missing from
 * {@link YT.Events}.
 */
interface PlayerEvents extends YT.Events {
  /**
   * Undocumented event that is emitted when the video progress changes,
   * either as a result of the video playing or the user seeking the video.
   *
   * The `data` payload is the current timestamp of the video.
   *
   * See https://issuetracker.google.com/issues/283097094
   */
  onVideoProgress: (event: { data: number }) => void;
}

/**
 * Component that wraps the YouTube video player.
 *
 * See https://developers.google.com/youtube/iframe_api_reference.
 */
export default function YouTubeVideoPlayer({
  onPlayingChanged,
  onTimeChanged,
  play = true,
  videoId,
  time,
}: YouTubeVideoPlayerProps) {
  const [loadError, setLoadError] = useState(null);

  // See https://developers.google.com/youtube/player_parameters#Manual_IFrame_Embeds
  const playerURL = useMemo(() => {
    const encodedId = encodeURIComponent(videoId);
    const url = new URL(`https://www.youtube.com/embed/${encodedId}`);
    url.searchParams.set('enablejsapi', '1'); // Enable `YT.Player` API
    url.searchParams.set('origin', window.origin);

    // Make the "More videos" overlay show only videos from the same channel.
    //
    // Ideally we would be able to turn this off entirely. YT doesn't allow
    // that, but it does at least allow us to avoid showing suggestions from
    // other channels.
    url.searchParams.set('rel', '0');
    return url.toString();
  }, [videoId]);

  const playerController = useRef<YT.Player>();

  // Wrap callbacks to avoid re-running effects when they change.
  const noop = () => {};
  const onPlayingChangedCallback = useStableCallback(onPlayingChanged ?? noop);
  const onTimeChangedCallback = useStableCallback(onTimeChanged ?? noop);

  const videoFrame = useRef(null);

  // Initialize the controller that allows us to interact with the player.
  useEffect(() => {
    loadYouTubeIFrameAPI()
      .then(YT => {
        // Instantiate the player controller. Note that some methods (eg.
        // `playVideo`) are not available until the `onReady` callback fires.
        const player = new YT.Player(videoFrame.current!, {
          events: {
            onReady: () => {
              playerController.current = player;

              // Report initial state when the video loads.
              onPlayingChangedCallback(isPlaying(player.getPlayerState()));
            },

            onStateChange: event => {
              if (event.data === PlayerState.UNSTARTED) {
                return;
              }
              onPlayingChangedCallback(isPlaying(event.data));
            },

            onVideoProgress: event => {
              onTimeChangedCallback(event.data);
            },
          } as PlayerEvents,
        });
      })
      .catch(err => {
        console.error('Error loading video:', err);
        setLoadError(err);
      });
  }, [onPlayingChangedCallback, onTimeChangedCallback]);

  // Play/pause video when `play` prop changes.
  useEffect(() => {
    const player = playerController.current;
    if (!player) {
      return;
    }
    if (play) {
      player.playVideo();
    } else {
      player.pauseVideo();
    }
  }, [play]);

  // Seek video when `time` prop is out of sync with current play time by
  // more than some threshold.
  useEffect(() => {
    const player = playerController.current;
    if (!player || typeof time !== 'number') {
      return;
    }
    const timeDelta = Math.abs(player.getCurrentTime() - time);
    if (timeDelta < 1.0) {
      return;
    }
    player.seekTo(time, true /* allowSeekahead */);
  }, [time]);

  return (
    <AspectRatio>
      <iframe
        allow="autoplay; fullscreen"
        title="Video player"
        src={playerURL}
        ref={videoFrame}
      />
      {loadError && (
        <p data-testid="load-error">
          <b>There was an error loading this video. Try reloading the page.</b>
        </p>
      )}
    </AspectRatio>
  );
}
