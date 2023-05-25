import { Button, Checkbox, Input } from '@hypothesis/frontend-shared';
import { useEffect, useMemo, useRef, useState } from 'preact/hooks';

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
 * Type of "scrolltorange" event emitted by the client when it is about to
 * scroll a highlight into view.
 */
type ScrollToRangeEvent = CustomEvent<Range> & {
  waitUntil(ready: Promise<void>): void;
};

function isScrollToRangeEvent(e: Event): e is ScrollToRangeEvent {
  return (
    e instanceof CustomEvent &&
    'waitUntil' in e &&
    typeof e.waitUntil === 'function'
  );
}

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

  // Whether transcript automatically scrolls to stay in sync with video
  // position.
  const [autoScroll, setAutoScroll] = useState(true);

  const [playing, setPlaying] = useState(false);
  const transcriptControls = useRef<TranscriptControls | null>(null);

  const [filter, setFilter] = useState('');
  const trimmedFilter = useMemo(() => filter.trim(), [filter]);

  // Listen for the event the Hypothesis client dispatches before it scrolls
  // a highlight into view. If a filter is currently active, clear it first
  // to ensure the highlight is visible.
  const pendingRender = useRef<() => void>();
  useEffect(() => {
    if (trimmedFilter.length === 0) {
      return () => {};
    }

    const listener = (e: Event) => {
      setFilter('');

      if (!isScrollToRangeEvent(e)) {
        return;
      }

      // Make the client wait for the transcript to re-render after the clearing
      // the filter, before it attempts to scroll the highlight into view.
      const renderDone = new Promise<void>(
        resolve => (pendingRender.current = resolve)
      );
      e.waitUntil(renderDone);
    };
    document.body.addEventListener('scrolltorange', listener);
    return () => {
      document.body.removeEventListener('scrolltorange', listener);
    };
  }, [trimmedFilter]);

  // Notify Hypothesis client on next render after clearing a filter.
  if (pendingRender.current) {
    pendingRender.current();
    pendingRender.current = undefined;
  }

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
            title={playing ? 'Pause' : 'Play'}
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
            aria-label="Transcript filter"
            data-testid="filter-input"
            onInput={e => setFilter((e.target as HTMLInputElement).value)}
            placeholder="Search..."
            value={filter}
          />
        </div>
        <Transcript
          autoScroll={autoScroll}
          transcript={transcript}
          controlsRef={transcriptControls}
          currentTime={timestamp}
          filter={trimmedFilter}
          onSelectSegment={segment => setTimestamp(segment.start)}
        />
        <div className="pl-2">
          <Checkbox
            checked={autoScroll}
            data-testid="autoscroll-checkbox"
            onChange={e =>
              setAutoScroll((e.target as HTMLInputElement).checked)
            }
          >
            <div className="p-2 select-none">Auto-scroll</div>
          </Checkbox>
        </div>
      </div>
      <HypothesisClient src={clientSrc} config={clientConfig} />
    </div>
  );
}
