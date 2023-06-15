import {
  Button,
  Checkbox,
  CopyIcon,
  Input,
  LogoIcon,
} from '@hypothesis/frontend-shared';
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
  clientConfig: baseClientConfig,
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
  const multicolumn = appSize !== 'sm';

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

  const bucketContainerId = 'bucket-container';
  const clientConfig = useMemo(() => {
    return {
      ...baseClientConfig,
      bucketContainerSelector: '#' + bucketContainerId,
    };
  }, [baseClientConfig]);

  return (
    <div
      data-testid="app-container"
      className={classnames(
        // Constrain height of interface to viewport height
        'flex flex-col h-[100vh] min-h-0'
      )}
    >
      <div
        data-testid="top-bar"
        className={classnames(
          // Match height of sidebar's top-bar
          'h-[40px] min-h-[40px]',
          'w-full flex items-center gap-x-3 px-2 border-b',
          // Background is one shade darker than sidebar top-bar
          'bg-grey-0'
        )}
      >
        <a
          href="https://web.hypothes.is"
          target="_blank"
          rel="noreferrer"
          title="Hypothesis"
        >
          <LogoIcon />
        </a>
        <div data-testid="filter-container" className="grow text-right">
          <Input
            data-testid="filter-input"
            aria-label="Transcript filter"
            classes={classnames(
              // Match height of search input in sidebar
              'h-[32px]',
              // TODO: Temporary prevention of sidebar controls overlapping
              'mr-[22px]',
              {
                // Adapt width to match width of transcript
                'max-w-[480px]': appSize === '2xl',
                'max-w-[450px]': appSize === 'xl',
                'max-w-[410px]': appSize === 'lg',
                'max-w-[380px]': appSize === 'md',
              }
            )}
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
        </div>
      </div>

      <main
        data-testid="app-layout"
        className={classnames('w-full flex min-h-0', {
          // Stack video over transcript.
          'flex-col': !multicolumn,
          // Video and transcript side-by-side, using up remaining vertical
          // space in app-container (i.e. 100vh minus top-bar)
          'flex-row grow h-full': multicolumn,
        })}
        ref={appContainerRef}
      >
        <div
          data-testid="embedded-video-container"
          className={classnames(
            'flex flex-col',
            {
              // Allow video to grow with available horizontal space in
              // multicolumn layouts (NB: It will take up full width in
              // single-column)
              grow: multicolumn,
            },
            {
              // Adapt spacing around video for different app sizes
              'p-0': appSize === 'sm',
              'p-1': appSize === 'md',
              'p-2': appSize === 'lg',
              'py-2 px-3': appSize === 'xl',
              'py-2 px-4': appSize === '2xl',
            }
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
          data-testid="transcript-container"
          className={classnames(
            'flex flex-col bg-grey-0 border-x',
            {
              // Make transcript fill available vertical space in single-column
              // layouts
              'min-h-0 grow': !multicolumn,
              // TODO: This is a stopgap measure to prevent controls from being
              // interfered with (overlaid) by sidebar controls and toolbar
              'mr-[30px]': multicolumn,
            },
            {
              // Adapt transcript width for different app sizes
              'w-[480px]': appSize === '2xl',
              'w-[450px]': appSize === 'xl',
              'w-[410px]': appSize === 'lg',
              'w-[380px]': appSize === 'md',
            }
          )}
        >
          <div
            data-testid="transcript-controls"
            className={classnames(
              // Same height as top-bar
              'h-[40px]',
              'bg-grey-1 flex items-center',
              // TODO: This is a stopgap measure to prevent the right side of the
              // transcript controls from being inpinged on by sidebar controls
              'pr-2'
            )}
          >
            <Button
              classes="text-l"
              icon={playing ? PauseIcon : PlayIcon}
              onClick={() => setPlaying(playing => !playing)}
              data-testid="play-button"
            >
              {playing ? 'Pause' : 'Play'}
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
          <div
            className={classnames(
              'relative',

              // Override flex-basis for transcript. Otherwise this container will
              // be sized to accomodate all transcript elements.
              'min-h-0'
            )}
          >
            <Transcript
              autoScroll={autoScroll}
              transcript={transcript}
              controlsRef={transcriptControls}
              currentTime={timestamp}
              filter={trimmedFilter}
              onSelectSegment={segment => setTimestamp(segment.start)}
            />
            <div
              id={bucketContainerId}
              className={classnames(
                // Position bucket bar along right edge of transcript, with a
                // small gap to avoid buckets touching the border.
                //
                // The bucket bar width is currently copied from the client.
                'absolute right-1 top-0 bottom-0 w-[23px]',

                // Make the bucket bar fill this container.
                'flex flex-column'
              )}
            />
          </div>
          <div data-testid="transcript-footer" className="px-2 py-4">
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
      </main>
    </div>
  );
}
