import { AspectRatio } from '@hypothesis/frontend-shared';
import { useEffect, useRef } from 'preact/hooks';

import type { TranscriptData } from '../utils/transcript';
import { transcriptToCues } from '../utils/transcript';

/**
 * Common props for different video player components.
 */
export type VideoPlayerProps = {
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

export type HTMLVideoPlayerProps = VideoPlayerProps & {
  /**
   * URL for video. Must be in a format supported by the browser's
   * `<video>` element.
   */
  videoURL: string;

  /**
   * Transcript for video.
   *
   * This is used to generate a caption `<track>` for the video.
   */
  transcript?: TranscriptData;

  /**
   * Whether to enable download controls for the video.
   *
   * Defaults to true.
   */
  allowDownload?: boolean;
};

/**
 * Video player built on the browser's native `<video>` element.
 */
export default function HTMLVideoPlayer({
  allowDownload,
  videoURL,
  transcript,
  play = false,
  time,
  onTimeChanged,
  onPlayingChanged,
}: HTMLVideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  // Play/pause video when `play` prop changes.
  useEffect(() => {
    const video = videoRef.current!;
    if (play) {
      video.play();
    } else {
      video.pause();
    }
  }, [play]);

  // Seek video when `time` prop is out of sync with current play time by
  // more than some threshold.
  useEffect(() => {
    if (time === undefined) {
      return;
    }

    const video = videoRef.current!;
    const delta = Math.abs(video.currentTime - time);
    if (delta < 1.0) {
      return;
    }
    video.currentTime = time;
  }, [time]);

  // Populate caption track for the video.
  const trackRef = useRef<HTMLTrackElement>(null);
  useEffect(() => {
    const trackEl = trackRef.current;
    if (!trackEl || !transcript) {
      return () => {};
    }

    const cues = transcriptToCues(transcript);
    for (const cue of cues) {
      trackEl.track.addCue(cue);
    }

    return () => {
      for (const cue of cues) {
        trackEl.track.removeCue(cue);
      }
    };
  }, [transcript]);

  const controlsList = !allowDownload ? 'nodownload' : undefined;

  return (
    <AspectRatio>
      <video
        ref={videoRef}
        controls
        // Disable UI controls to download videos if requested. This is only
        // a "soft" block since the video URL can easily be obtained via
        // developer tools.
        controlsList={controlsList}
        onContextMenu={e => {
          if (!allowDownload) {
            e.preventDefault();
          }
        }}
        src={videoURL}
        onTimeUpdate={event => {
          const video = event.target as HTMLVideoElement;
          onTimeChanged?.(video.currentTime);
        }}
        onPlay={() => onPlayingChanged?.(true)}
        onPause={() => onPlayingChanged?.(false)}
      >
        <track default kind="captions" ref={trackRef} />
      </video>
    </AspectRatio>
  );
}
