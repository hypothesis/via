import { Button, Checkbox, CopyIcon, Input } from '@hypothesis/frontend-shared';
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'preact/hooks';

import type { TranscriptData } from '../utils/transcript';
import { formatTranscript } from '../utils/transcript';
import HypothesisClient from './HypothesisClient';
import Transcript from './Transcript';
import type { TranscriptControls } from './Transcript';
import YouTubeVideoPlayer from './YouTubeVideoPlayer';
import { PauseIcon, PlayIcon, SyncIcon } from './icons';

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
  const filterInputRef = useRef<HTMLInputElement>();

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

  const syncTranscript = useCallback(
    () => transcriptControls.current!.scrollToCurrentSegment(),
    []
  );

  // If we transition from paused to playing while autoscroll is active,
  // immediately scroll the current segment into view. Without this, the
  // transcript will not scroll until playback reaches the next segment.
  useEffect(() => {
    if (autoScroll && playing) {
      syncTranscript();
    }
  }, [autoScroll, playing, syncTranscript]);

  // Handle app-wide keyboard shortcuts.
  useEffect(() => {
    const keyListener = (e: KeyboardEvent) => {
      // Disable single letter shortcuts if focused element is a text input.
      const enableSingleKey = !['input', 'select', 'textarea'].includes(
        (e.target as Element).tagName.toLowerCase()
      );
      const matchesKey = (key: string) => enableSingleKey && e.key === key;

      // Shortcuts that match the YouTube player, or perform a similar action.
      // See https://support.google.com/youtube/answer/7631406.
      if (matchesKey('k')) {
        setPlaying(playing => !playing);
      } else if (matchesKey('/')) {
        const input = filterInputRef.current;
        if (input) {
          input.focus();
          input.select();
        }
      }

      // Custom shortcuts for our video player app.
      if (matchesKey('s')) {
        syncTranscript();
      } else if (matchesKey('a')) {
        setAutoScroll(autoScroll => !autoScroll);
      }
    };
    document.body.addEventListener('keyup', keyListener);
    return () => {
      document.body.removeEventListener('keyup', keyListener);
    };
  }, [syncTranscript]);

  const copyTranscript = async () => {
    const formattedTranscript = formatTranscript(transcript.segments);
    try {
      await navigator.clipboard.writeText(formattedTranscript);
    } catch (err) {
      // TODO: Replace this with a toast message in the UI.
      console.warn('Failed to copy transcript', err);
    }
  };

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
        <div className="p-1 bg-grey-1 border-b flex flex-col">
          <Input
            aria-label="Transcript filter"
            data-testid="filter-input"
            elementRef={filterInputRef}
            onKeyUp={e => {
              // Allow user to easily remove focus from search input.
              if (e.key === 'Escape') {
                (e.target as HTMLElement).blur();
              }
            }}
            onInput={e => setFilter((e.target as HTMLInputElement).value)}
            placeholder="Search..."
            value={filter}
          />
          <div className="flex flex-row">
            <Button
              classes="text-l"
              onClick={() => setPlaying(playing => !playing)}
              data-testid="play-button"
            >
              {playing ? (
                <>
                  <PauseIcon /> Pause
                </>
              ) : (
                <>
                  <PlayIcon /> Play
                </>
              )}
            </Button>
            <div className="flex-grow" />
            <Button
              onClick={copyTranscript}
              data-testid="copy-button"
              title="Copy transcript"
            >
              <CopyIcon />
            </Button>
            <Button
              onClick={syncTranscript}
              data-testid="sync-button"
              title="Sync"
            >
              <SyncIcon />
            </Button>
          </div>
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
