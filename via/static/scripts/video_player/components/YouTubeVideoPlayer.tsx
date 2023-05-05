import { useEffect, useRef, useState } from 'preact/hooks';

import { loadYouTubeIFrameAPI } from '../utils/youtube';

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

export type YouTubeVideoPlayerProps = {
  /** ID of the YouTube video to load. */
  videoId: string;

  /**
   * Whether the video is playing or paused.
   *
   * Note that even if this is set to `true` when the component is mounted, the
   * browser may prevent automatic playback of the video until the user has
   * interacted with the page.
   */
  play?: boolean;

  /**
   * Current play time of the video, expressed as a number of seconds since
   * the start.
   */
  time?: number;

  /**
   * Callback invoked at a regular interval (eg. 1 second) when the timestamp
   * of the video changes.
   */
  onTimeChanged?: (timestamp: number) => void;

  /**
   * Callback invoked when the playing/paused state of the video changes.
   */
  onPlayingChanged?: (playing: boolean) => void;
};

function isPlaying(state: YT.PlayerState) {
  return state === PlayerState.PLAYING || state === PlayerState.BUFFERING;
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
  const encodedId = encodeURIComponent(videoId);
  const encodedOrigin = encodeURIComponent(window.origin);

  // See https://developers.google.com/youtube/player_parameters#Manual_IFrame_Embeds
  const playerURL = `https://www.youtube.com/embed/${encodedId}?enablejsapi=1&origin=${encodedOrigin}`;

  const playerController = useRef<YT.Player>();

  const onPlayingChangedCallback = useRef<(playing: boolean) => void>();
  onPlayingChangedCallback.current = onPlayingChanged;

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
              onPlayingChangedCallback.current?.(
                isPlaying(player.getPlayerState())
              );
            },

            onStateChange: event => {
              if (event.data === PlayerState.UNSTARTED) {
                return;
              }
              onPlayingChangedCallback.current?.(isPlaying(event.data));
            },
          },
        });
      })
      .catch(err => {
        console.error('Error loading video:', err);
        setLoadError(err);
      });
  }, []);

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

  // Report current video position periodically.
  useEffect(() => {
    if (!play) {
      return () => {};
    }
    const poller = setInterval(() => {
      const player = playerController.current;
      if (!player || !onTimeChanged) {
        return;
      }
      onTimeChanged(Math.round(player.getCurrentTime()));
    }, 1000);
    return () => {
      clearInterval(poller);
    };
  }, [onTimeChanged, play]);

  return (
    <div>
      <iframe
        allow="autoplay; fullscreen"
        className="w-[640px] h-[360px] pb-2"
        title="Video player"
        src={playerURL}
        ref={videoFrame}
      />
      {loadError && (
        <p data-testid="load-error">
          <b>There was an error loading this video. Try reloading the page.</b>
        </p>
      )}
    </div>
  );
}
