import { Button, Checkbox, CopyIcon, Input } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'preact/hooks';

import { useAppLayout } from '../hooks/use-app-layout';
import { useNextRender } from '../utils/next-render';
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
  const appContainerRef = useRef<HTMLDivElement | null>(null);
  const appSize = useAppLayout(appContainerRef);

  // Listen for the event the Hypothesis client dispatches before it scrolls
  // a highlight into view.
  const nextRender = useNextRender();
  useEffect(() => {
    const listener = (e: Event) => {
      if (!isScrollToRangeEvent(e)) {
        return;
      }

      // If a filter is currently active, clear it first to ensure the highlight
      // is visible.
      let didChangeFilter;
      setFilter(prevFilter => {
        didChangeFilter = prevFilter !== '';
        return '';
      });

      // Pause playback to prevent transcript quickly scrolling away from the
      // highlight back to the current location, if autoscroll is active.
      setPlaying(false);

      if (didChangeFilter) {
        // Wait until component is re-rendered with filter cleared, before
        // scrolling to highlight.
        e.waitUntil(nextRender.wait());
      }
    };
    document.body.addEventListener('scrolltorange', listener);
    return () => {
      document.body.removeEventListener('scrolltorange', listener);
    };
  }, [nextRender]);

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

  const multicolumn = appSize !== 'sm';

  return (
    <div
      data-app-size={appSize}
      data-multicolumn={multicolumn}
      className={classnames('w-full flex', {
        'flex-col min-h-0 h-[100vh]': !multicolumn,
        'flex-row': multicolumn,
      })}
      ref={appContainerRef}
    >
      <div
        className={classnames(
          // This column will grow in width per the parent flex container and
          // allow the contained media (video) to scale with available space.
          // The column flex layout established here ensures this container fills
          // the full height of the parent flex container
          'flex flex-col p-3',
          { grow: multicolumn }
        )}
      >
        <YouTubeVideoPlayer
          videoId={videoId}
          play={playing}
          time={timestamp}
          onPlayingChanged={setPlaying}
          onTimeChanged={setTimestamp}
        />
      </div>
      <div
        className={classnames(
          // Full-height column with a width allowing comfortable line lengths
          'flex flex-col',
          {
            'w-[480px]': appSize === '2xl',
            'w-[450px]': appSize === 'xl',
            'w-[410px]': appSize === 'lg',
            'w-[380px]': appSize === 'md',
            // TODO: This is a stopgap measure to prevent controls from being
            // interfered with (overlaid) by sidebar controls and toolbar
            'mr-[30px] h-[100vh]': multicolumn,
            'min-h-0 grow': !multicolumn,
          },
          'bg-grey-0 border-x'
        )}
      >
        <div
          className={classnames(
            'p-1 bg-grey-1',
            // TODO: This is a stopgap measure to prevent the right side of the
            // search input from being inpinged on by sidebar controls
            'pr-2'
          )}
          data-testid="search-bar"
        >
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
        <div className="px-2 py-4">
          <Checkbox
            checked={autoScroll}
            data-testid="autoscroll-checkbox"
            onChange={e =>
              setAutoScroll((e.target as HTMLInputElement).checked)
            }
          >
            <div className="select-none">Auto-scroll</div>
          </Checkbox>
        </div>
      </div>
      <HypothesisClient src={clientSrc} config={clientConfig} />
    </div>
  );
}
