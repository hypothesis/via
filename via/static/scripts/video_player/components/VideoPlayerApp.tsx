import { Button, Input } from '@hypothesis/frontend-shared';
import { useState } from 'preact/hooks';

import HypothesisClient from './HypothesisClient';
import Transcript from './Transcript';
import type { TranscriptData } from './Transcript';
import YouTubeVideoPlayer from './YouTubeVideoPlayer';

export type VideoPlayerAppProps = {
  videoId: string;
  clientSrc: string;
  clientConfig: object;
  transcript: TranscriptData;
};

/**
 * Video annotation application.
 *
 * This displays a video alongside its transcript, and loads the Hypothesis
 * client so the user can annotate the transcript.
 */
export default function VideoPlayerApp({
  videoId,
  clientSrc,
  clientConfig,
  transcript,
}: VideoPlayerAppProps) {
  // Current play time of the video, in seconds since the start.
  const [timestamp, setTimestamp] = useState(0);
  const [playing, setPlaying] = useState(false);

  return (
    <div className="w-full">
      <YouTubeVideoPlayer
        videoId={videoId}
        play={playing}
        time={timestamp}
        onPlayingChanged={setPlaying}
        onTimeChanged={setTimestamp}
      />
      <Button onClick={() => setPlaying(playing => !playing)}>
        {playing ? 'Pause' : 'Play'}
      </Button>
      <Input
        value={timestamp}
        onChange={e =>
          setTimestamp(parseInt((e.target as HTMLInputElement).value))
        }
      />
      <Transcript transcript={transcript} currentTime={timestamp} />
      <HypothesisClient src={clientSrc} config={clientConfig} />
    </div>
  );
}
