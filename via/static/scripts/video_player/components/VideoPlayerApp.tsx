import { Button, Input } from '@hypothesis/frontend-shared';
import { useRef, useState } from 'preact/hooks';

import type { TranscriptData } from '../utils/transcript';
import HypothesisClient from './HypothesisClient';
import Transcript from './Transcript';
import type { TranscriptControls } from './Transcript';
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
  const transcriptControls = useRef<TranscriptControls | null>(null);

  const [filter, setFilter] = useState('');

  return (
    <div className="w-full flex flex-row m-2">
      <div className="mr-2">
        <YouTubeVideoPlayer
          videoId={videoId}
          play={playing}
          time={timestamp}
          onPlayingChanged={setPlaying}
          onTimeChanged={setTimestamp}
        />
      </div>
      <div className="w-2/5 h-[90vh] flex flex-col bg-grey-0 border">
        <div className="p-1 bg-grey-1 border-b flex flex-row">
          <Button
            classes="text-xl"
            onClick={() => setPlaying(playing => !playing)}
            data-testid="play-button"
          >
            {playing ? '⏸' : '⏵'}
          </Button>
          <Button
            onClick={() => transcriptControls.current!.scrollToCurrentSegment()}
            data-testid="sync-button"
          >
            Sync
          </Button>
          <div className="flex-grow" />
          <Input
            aria-label="Filter transcript"
            data-testid="filter-input"
            onInput={e =>
              setFilter((e.target as HTMLInputElement).value.trim())
            }
            placeholder="Search..."
          />
        </div>
        <Transcript
          transcript={transcript}
          controlsRef={transcriptControls}
          currentTime={timestamp}
          filter={filter}
          onSelectSegment={segment => setTimestamp(segment.start)}
        />
      </div>
      <HypothesisClient src={clientSrc} config={clientConfig} />
    </div>
  );
}
