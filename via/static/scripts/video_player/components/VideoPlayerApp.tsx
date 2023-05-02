import { useState } from 'preact/hooks';

import HypothesisClient from './HypothesisClient';
import Transcript from './Transcript';
import type { TranscriptData } from './Transcript';
import VideoPlayer from './VideoPlayer';

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
  // Current play time of the video
  const [timestamp, setTimestamp] = useState(0);

  return (
    <div className="w-full">
      <VideoPlayer
        videoId={videoId}
        time={timestamp}
        onTimeChanged={setTimestamp}
      />
      <Transcript transcript={transcript} currentTime={timestamp} />
      <HypothesisClient src={clientSrc} config={clientConfig} />
    </div>
  );
}
