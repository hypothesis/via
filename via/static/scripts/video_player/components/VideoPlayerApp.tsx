import {
  Button,
  Checkbox,
  CopyIcon,
  IconButton,
  Input,
  LogoIcon,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { Ref } from 'preact';
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

type FilterInputProps = {
  elementRef: Ref<HTMLElement | undefined>;
  setFilter: (filter: string) => void;
  filter: string;
};

function FilterInput({ elementRef, setFilter, filter }: FilterInputProps) {
  return (
    <Input
      data-testid="filter-input"
      aria-label="Transcript filter"
      classes={classnames(
        // Match height of search input in sidebar
        'h-[32px]'
      )}
      elementRef={elementRef}
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
  );
}

function HypothesisLogo() {
  return (
    <a
      href="https://web.hypothes.is"
      target="_blank"
      rel="noreferrer"
      title="Hypothesis"
    >
      <LogoIcon data-testid="hypothesis-logo" />
    </a>
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
  const transcriptWidths = {
    sm: '100%',
    md: '380px',
    lg: '410px',
    xl: '450px',
    '2xl': '480px',
  };

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
      className="flex flex-col h-[100vh] min-h-0"
    >
      {multicolumn && (
        <div
          data-testid="top-bar"
          className={classnames(
            'h-[40px] min-h-[40px] w-full flex items-center gap-x-3',
            'px-2 border-b bg-grey-0'
          )}
        >
          <HypothesisLogo />
          <div className="grow" />
          <div
            data-testid="filter-container"
            className={classnames(
              'text-right',
              // TODO: Temporary prevention of sidebar controls overlapping
              'mr-[22px]'
            )}
            style={{ width: transcriptWidths[appSize] }}
          >
            <FilterInput
              elementRef={filterInputRef}
              setFilter={setFilter}
              filter={filter}
            />
          </div>
        </div>
      )}

      <main
        data-testid="app-layout"
        className={classnames('w-full flex min-h-0', {
          'flex-col': !multicolumn,
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
          className={classnames('flex flex-col bg-grey-0 border-x', {
            // Make transcript fill available vertical space in single-column
            // layouts
            'min-h-0 grow': !multicolumn,
            // TODO: This is a stopgap measure to prevent controls from being
            // interfered with (overlaid) by sidebar controls and toolbar
            'mr-[30px]': multicolumn,
          })}
          style={{ width: transcriptWidths[appSize] }}
        >
          <div
            data-testid="transcript-controls"
            className={classnames(
              // Same height as top-bar
              'h-[40px] min-h-[40px]',
              'bg-grey-1 flex items-center',
              // TODO: This is a stopgap measure to prevent the right side of the
              // transcript controls from being inpinged on by sidebar controls
              'pr-2',
              {
                'px-1.5': !multicolumn,
              }
            )}
          >
            {multicolumn && (
              <>
                <Button
                  icon={playing ? PauseIcon : PlayIcon}
                  onClick={() => setPlaying(playing => !playing)}
                  data-testid="play-button"
                  variant="custom"
                  classes="text-grey-7 hover:text-grey-9 font-semibold"
                >
                  {playing ? 'Pause' : 'Play'}
                </Button>
                <div className="grow" />
              </>
            )}
            {!multicolumn && (
              <>
                <HypothesisLogo />
                <div className="flex-grow ml-2.5">
                  <FilterInput
                    setFilter={setFilter}
                    elementRef={filterInputRef}
                    filter={filter}
                  />
                </div>
              </>
            )}

            <IconButton
              onClick={syncTranscript}
              data-testid="sync-button"
              icon={SyncIcon}
              title="Sync transcript to video"
              size="custom"
              classes="p-2"
            />
            <IconButton
              onClick={copyTranscript}
              data-testid="copy-button"
              title="Copy transcript"
              icon={CopyIcon}
              size="custom"
              classes="p-2"
            />
          </div>
          <div
            className={classnames(
              'relative',

              // Override flex-basis for transcript. Otherwise this container
              // will be sized to accomodate all transcript elements.
              'min-h-0',

              // Make the bucket bar fill this container.
              'flex flex-col'
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
          <div
            data-testid="transcript-footer"
            className="p-2 bg-grey-1 border-b h-[40px] min-h-[40px] flex items-center"
          >
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
