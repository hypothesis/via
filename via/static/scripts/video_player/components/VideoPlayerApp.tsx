import {
  Button,
  Checkbox,
  CopyIcon,
  IconButton,
  LogoIcon,
  Spinner,
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
import { useSideBySideLayout } from '../hooks/use-side-by-side-layout';
import { callAPI } from '../utils/api';
import type { APIMethod, APIError, JSONAPIObject } from '../utils/api';
import { useNextRender } from '../utils/next-render';
import { appendToastMessage } from '../utils/toast-messages';
import type { TranscriptData } from '../utils/transcript';
import { formatTranscript, mergeSegments } from '../utils/transcript';
import { AppContext } from './AppContext';
import FilterInput from './FilterInput';
import HypothesisClient from './HypothesisClient';
import type { ToastMessage } from './ToastMessages';
import Transcript from './Transcript';
import type { TranscriptControls } from './Transcript';
import TranscriptError from './TranscriptError';
import VideoPlayerAppToastMessages from './VideoPlayerAppToastMessages';
import YouTubeVideoPlayer from './YouTubeVideoPlayer';
import { PauseIcon, PlayIcon, SyncIcon } from './icons';

export type VideoPlayerAppProps = {
  /** ID of the YouTube video to load. */
  videoId: string;

  /** URL of the boot script for the Hypothesis client. */
  clientSrc: string;

  /** JSON-serializable configuration for the Hypothesis client. */
  clientConfig: object;

  /**
   * The data source for the transcript. Either an API to call when the player
   * loads, or pre-fetched data (mostly useful in tests).
   */
  transcriptSource: APIMethod | TranscriptData;
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

function isTranscript(value: any): value is TranscriptData {
  return (
    typeof value === 'object' && value !== null && Array.isArray(value.segments)
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
  transcriptSource,
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

  const { appSize, multicolumn, transcriptWidth } =
    useAppLayout(appContainerRef);
  const sideBySideActive = useSideBySideLayout();

  // Fetch transcript when app loads.
  const [transcript, setTranscript] = useState<
    TranscriptData | APIError | null
  >(isTranscript(transcriptSource) ? transcriptSource : null);

  // Notify client once the transcript is rendered, and ready to anchor
  // annotations.
  const [contentReady, resolveContentReady, rejectContentReady] =
    useMemo(() => {
      let reject: (err: Error) => void;
      let resolve: () => void;
      const promise = new Promise<void>((resolve_, reject_) => {
        resolve = resolve_;
        reject = reject_;
      });
      return [promise, resolve!, reject!];
    }, []);
  if (isTranscript(transcript)) {
    resolveContentReady();
  } else if (transcript instanceof Error) {
    rejectContentReady(new Error('Transcript failed to load'));
  }

  useEffect(() => {
    if (isTranscript(transcriptSource)) {
      return;
    }
    callAPI<JSONAPIObject<TranscriptData>>(transcriptSource)
      .then(response => {
        const transcript = response.data.attributes;

        // Group segments together for better readability.
        transcript.segments = mergeSegments(transcript.segments, 3);

        setTranscript(transcript);
      })
      .catch(err => setTranscript(err));
  }, [transcriptSource]);
  const isLoading = transcript === null;

  // Listen for the event the Hypothesis client dispatches before it scrolls
  // a highlight into view.
  const nextRender = useNextRender();
  const pendingScrollToHighlight = useRef(false);
  useEffect(() => {
    const listener = (e: Event) => {
      if (!isScrollToRangeEvent(e)) {
        return;
      }

      pendingScrollToHighlight.current = true;

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
    () => transcriptControls.current?.scrollToCurrentSegment(),
    []
  );

  // After clearing the filter, scroll the current segment into view, unless
  // we cleared the filter to allow the client to scroll to a highlight.
  const isFilterEmpty = trimmedFilter.length === 0;
  const prevFilterEmpty = useRef(isFilterEmpty);
  useEffect(() => {
    if (
      isFilterEmpty &&
      !prevFilterEmpty.current &&
      !pendingScrollToHighlight.current
    ) {
      syncTranscript();
    }
    prevFilterEmpty.current = isFilterEmpty;
    pendingScrollToHighlight.current = false;
  }, [isFilterEmpty, syncTranscript]);

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

  const [toastMessages, setToastMessages] = useState<ToastMessage[]>([]);

  const copyTranscript = async () => {
    const formattedTranscript = isTranscript(transcript)
      ? formatTranscript(transcript.segments)
      : '';
    try {
      await navigator.clipboard.writeText(formattedTranscript);
    } catch (err) {
      appendToastMessage(
        {
          type: 'error',
          message: 'Failed to copy transcript',
        },
        setToastMessages
      );
    }
  };

  const bucketContainerId = 'bucket-container';
  const prevSideBySideActive = useRef(sideBySideActive);
  prevSideBySideActive.current = sideBySideActive;
  const clientConfig = useMemo(() => {
    return {
      ...baseClientConfig,
      bucketContainerSelector: '#' + bucketContainerId,
      contentReady,
      sideBySide: {
        mode: 'manual',
        // Using a ref here to make sure the `isActive` callback reference is
        // kept, and only its return value changes
        isActive: () => prevSideBySideActive.current,
      },
    };
  }, [baseClientConfig, contentReady]);

  return (
    <AppContext.Provider
      value={{
        toastMessages: {
          toastMessages,
          setToastMessages,
        },
      }}
    >
      <div
        data-testid="app-container"
        className={classnames('flex flex-col h-[100vh] min-h-0 relative')}
      >
        {multicolumn && (
          <div
            data-testid="top-bar"
            className={classnames(
              'h-[40px] min-h-[40px] w-full flex items-center gap-x-3',
              'pl-2 border-b bg-grey-0'
            )}
          >
            <HypothesisLogo />
            <div className="grow" />
            <div
              data-testid="filter-container"
              className={classnames(
                'text-right',
                // Put space to the right of the filter input so it is not
                // overlaid by sidebar controls. NB: Cannot use margin because it
                // gets "consumed" in side-by-side mode
                'pr-4'
              )}
              style={{ width: transcriptWidth }}
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
            'flex-col grow': !multicolumn,
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
                'py-2 px-3': appSize === 'lg',
                'py-2 px-4': appSize === 'xl',
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
            data-testid="transcript-and-controls-container"
            className={classnames('flex flex-col bg-grey-0 border-x', {
              // Make transcript fill available vertical space in single-column
              // layouts
              'min-h-0 grow': !multicolumn,
            })}
            style={{ width: transcriptWidth }}
          >
            <div
              data-testid="transcript-controls"
              className={classnames(
                // Same height as top-bar
                'h-[40px] min-h-[40px]',
                'bg-grey-1 flex items-center',
                {
                  // Provide the correct right alignment with the sidebar
                  // Multicolumn needs more right-hand space to avoid interference
                  // by sidebar controls
                  'px-1.5': !multicolumn,
                  'pr-4': multicolumn,
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
                disabled={!isTranscript(transcript)}
                icon={SyncIcon}
                title="Sync transcript to video"
                size="custom"
                classes="p-2"
              />
              <IconButton
                onClick={copyTranscript}
                data-testid="copy-button"
                disabled={!isTranscript(transcript)}
                title="Copy transcript"
                icon={CopyIcon}
                size="custom"
                classes="p-2"
              />
            </div>
            <div
              className={classnames(
                'relative grow',
                'min-h-0',
                'flex flex-col',
                {
                  // Ensure that this container uses all available vertical space
                  // on narrow screens
                  'h-full': !multicolumn,
                }
              )}
              data-testid="transcript-container"
            >
              <VideoPlayerAppToastMessages />
              {isLoading && (
                <div className="flex justify-center p-8">
                  <Spinner data-testid="transcript-loading-spinner" size="md" />
                </div>
              )}
              {isTranscript(transcript) && (
                <Transcript
                  autoScroll={autoScroll}
                  transcript={transcript}
                  controlsRef={transcriptControls}
                  currentTime={timestamp}
                  filter={trimmedFilter}
                  onSelectSegment={segment => {
                    // Clear the filter before jumping to a segment, so the user
                    // can easily read the text that comes before and after it.
                    //
                    // Note that we always show the current segment, regardless
                    // of whether a filter is applied.
                    setFilter('');

                    setTimestamp(segment.start);
                  }}
                >
                  <div
                    data-testid="bucket-bar-channel"
                    className={classnames(
                      // Provide a backdrop for bucket bar buttons. 20px of this
                      // is overlaid by the sidebar's semi-transparent bucket
                      // channel.
                      'bg-gradient-to-r from-white to-grey-1 border-l w-[40px]'
                    )}
                  />
                </Transcript>
              )}
              {transcript instanceof Error && (
                <TranscriptError error={transcript} />
              )}
              <div
                id={bucketContainerId}
                className={classnames(
                  // Position bucket bar along right edge of transcript, with a
                  // small gap to avoid buckets touching the border.
                  //
                  // The bucket bar width is currently copied from the client.
                  'absolute right-1.5 bottom-0 w-[23px]',

                  // Make the bucket bar fill this container.
                  'flex flex-column',

                  {
                    'top-0': !multicolumn,
                    // Leave room for sidebar toolbar buttons at top of buckets
                    // in multi-column layouts
                    'h-[calc(100%-24px)]': multicolumn,
                  }
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
    </AppContext.Provider>
  );
}
