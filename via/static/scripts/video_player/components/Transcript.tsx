import {
  Scroll,
  ScrollContainer,
  useStableCallback,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren, Ref } from 'preact';
import {
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
} from 'preact/hooks';

import { useScrollAnchor } from '../hooks/use-scroll-anchor';
import { TextHighlighter } from '../utils/highlighter';
import { formatTimestamp } from '../utils/time';
import type { MatchOffset, Segment, TranscriptData } from '../utils/transcript';
import { filterTranscript } from '../utils/transcript';

/**
 * Interface for interacting with the transcript view, beyond what is available
 * by setting props.
 */
export type TranscriptControls = {
  /**
   * Scroll the view so the segment corresponding to {@link TranscriptProps.currentTime}
   * is visible.
   */
  scrollToCurrentSegment: () => void;

  scrollToTop: () => void;
  scrollToBottom: () => void;
};

export type TranscriptProps = {
  /**
   * Whether to automatically scroll the transcript as the video plays to keep
   * the segment corresponding to `currentTime` in view.
   */
  autoScroll?: boolean;

  /** Other content to render in scrolling container after the transcript
   * segments.
   */
  children?: ComponentChildren;

  transcript: TranscriptData;

  /**
   * Ref that is set to a controller for the transcript component after it
   * mounts.
   */
  controlsRef?: Ref<TranscriptControls>;

  /**
   * The current timestamp of the video player, as an offset in seconds from
   * the start of the video.
   *
   * When the current time's associated transcript segment changes, the new
   * segment will automatically be scrolled into view.
   */
  currentTime: number;

  /** Query string to filter the transcript. */
  filter?: string;

  /**
   * Callback invoked when the user selects a segment from the transcript.
   */
  onSelectSegment?: (segment: Segment) => void;
};

type TranscriptSegmentProps = {
  /**
   * Mark the segment as hidden.
   *
   * When segments do not match the current filter, we continue to render
   * them but hidden with CSS. This avoids losing highlights created by the
   * Hypothesis client.
   */
  hidden?: boolean;

  /**
   * Highlighter used to highlight matches listed in {@link matches}.
   */
  highlighter: TextHighlighter;

  /** Spans within the segment text to highlight. */
  matches?: MatchOffset[];

  isCurrent: boolean;
  onSelect: () => void;
  segment: Segment;
};

function hasSelection() {
  return Boolean(window.getSelection()?.toString());
}

function TranscriptSegment({
  hidden = false,
  highlighter,
  matches,
  isCurrent,
  onSelect,
  segment,
}: TranscriptSegmentProps) {
  const contentRef = useRef<HTMLParagraphElement>(null);

  // Highlight the text within the segment that matches the current filter
  // query. The highlights are created manually, rather than using a Preact
  // component, to avoid damaging highlights added by the Hypothesis client.
  useEffect(() => {
    const contentEl = contentRef.current;
    if (!matches || !contentEl) {
      return () => {};
    }

    highlighter.highlightSpans(contentEl, matches);
    return () => {
      highlighter.removeHighlights(contentEl);
    };
  }, [highlighter, matches]);

  const hadSelectionOnPointerDown = useRef(false);
  const timestamp = useMemo(
    () => formatTimestamp(segment.start),
    [segment.start]
  );

  // Add a trailing space at the end of each segment to avoid the last word of a
  // segment being joined with the first word of the next segment in annotation
  // quotes.
  const text = segment.text + ' ';

  const stableOnSelect = useStableCallback(onSelect);

  return useMemo(
    () => (
      <li
        className={classnames(
          'flex gap-x-3 p-1.5 rounded',
          // Margin needed to provide space for box shadow on current item
          'mb-1',
          {
            'bg-white shadow-md': isCurrent,
            hidden,
          }
        )}
        data-is-current={isCurrent}
        data-testid="segment"
      >
        <button
          aria-label={timestamp}
          onClick={stableOnSelect}
          className={classnames(
            // TODO: Use shared Button to get these styles for free
            'flex transition-colors focus-visible-ring rounded',
            // `peer` allows Tailwind styling based on sibling state
            'peer',
            'font-medium hover:underline',
            {
              // Colors are one tick lighter than segment text
              'text-stone-700': isCurrent,
              'text-stone-500': !isCurrent,
              'hover:text-stone-800': true,
            },
            // Workaround for a Firefox issue that prevented annotating across
            // multiple segments [1]. Buttons have a default `user-select: none`
            // style in FF and selections that include elements with this style
            // are split into multiple ranges. The Hypothesis client in turn only
            // uses the first range from a selection (see [2]).
            //
            // [1] https://github.com/hypothesis/via/issues/930
            // [2] https://github.com/hypothesis/client/issues/5485
            'select-text',

            // The timestamp is rendered using a CSS ::before pseudo-element
            // so that it does not appear in the selection captured by the Hypothesis
            // client, when creating an annotation that spans multiple segments.
            //
            // We use a combination of padding and margin to create the space
            // between the timestamp and transcript. The padding region enlarges
            // the clickable area of the timestamp button. The margin region enlarges
            // the area in which a user can start a selection of the transcript text.
            // Without it selecting the left edge of the transcript is fiddly.
            'before:content-[attr(data-timestamp)]',
            // Style and position timestamp text
            'before:px-1 before:pt-[1px] before:text-right before:text-[.8em]'
          )}
          data-timestamp={timestamp}
        />
        <p
          className={classnames(
            'grow peer-hover:text-stone-900',
            {
              'text-stone-600': !isCurrent,
              'text-stone-800': isCurrent,
            },

            // Avoid buckets overlapping highlighted text.
            'pr-3'
          )}
          data-testid="transcript-text"
          // Add attributes used by the client to create media time selectors.
          //
          // The precision of these is currently not as good as it could be
          // because of the grouping of segments from the transcript returned
          // by the API. We could improve this in future by rendering each
          // segment of the original transcript as a separate element within this
          // paragraph.
          data-time-start={segment.start}
          data-time-end={segment.start + segment.duration}
          ref={contentRef}
          // We have a "click" handler here, but don't set a role because
          // this is a secondary way to focus the transcript. The timestamp
          // button is the primary control for this action.
          onPointerDown={() => {
            hadSelectionOnPointerDown.current = hasSelection();
          }}
          onPointerUp={() => {
            // Allow the user to easily select a segment by clicking it, but
            // don't seek the video if they are selecting or de-selecting text
            // to annotate.
            if (!hadSelectionOnPointerDown.current && !hasSelection()) {
              stableOnSelect();
            }
          }}
        >
          {
            // To avoid highlights from the Hypothesis client or filter matching
            // being disrupted, it is important that the content here is a single
            // text string which does not change after the initial render.
            text
          }
        </p>
      </li>
    ),
    [
      hidden,
      isCurrent,
      segment.duration,
      segment.start,
      stableOnSelect,
      text,
      timestamp,
    ]
  );
}

/**
 * Return the offset of `element` from the top of a positioned ancestor `parent`.
 *
 * @param parent - Positioned ancestor of `element`
 */
function offsetRelativeTo(element: HTMLElement, parent: HTMLElement): number {
  let offset = 0;
  while (element !== parent && parent.contains(element)) {
    offset += element.offsetTop;
    element = element.offsetParent as HTMLElement;
  }
  return offset;
}

export default function Transcript({
  autoScroll = true,
  children,
  controlsRef,
  currentTime,
  filter = '',
  onSelectSegment,
  transcript,
}: TranscriptProps) {
  const scrollRef = useRef<HTMLElement | null>(null);

  const currentIndex = transcript.segments.findIndex(
    (segment, index) =>
      currentTime >= segment.start &&
      (index === transcript.segments.length - 1 ||
        currentTime < transcript.segments[index + 1].start)
  );

  const scrollToCurrentSegment = useCallback(() => {
    const scrollContainer = scrollRef.current!;
    const currentSegment = scrollContainer.querySelector(
      '[data-is-current=true]'
    ) as HTMLElement | null;
    if (!currentSegment) {
      return;
    }

    // Don't scroll the transcript container while the user is making a
    // selection inside it, as this will likely cause the wrong text to be
    // selected.
    const selection = window.getSelection();
    const selectedRange = selection?.rangeCount
      ? selection.getRangeAt(0)
      : null;
    if (
      selectedRange &&
      !selectedRange.collapsed &&
      scrollContainer.contains(selectedRange.startContainer)
    ) {
      return;
    }

    // Scroll the container such that the current segment is positioned towards
    // the top. We allow more space below than above, on the assumption that the
    // user is likely to want to read forwards further than they want to read
    // back from the current position.
    const currentSegmentOffset = offsetRelativeTo(
      currentSegment,
      scrollContainer
    );

    const scrollTarget =
      currentSegmentOffset - scrollContainer.clientHeight * (1 / 4);

    scrollContainer.scrollTo({
      left: 0,
      top: scrollTarget,
    });
  }, []);

  useEffect(() => {
    if (autoScroll) {
      scrollToCurrentSegment();
    }
  }, [autoScroll, currentIndex, transcript, scrollToCurrentSegment]);

  useImperativeHandle(
    controlsRef || { current: null },
    () => ({
      scrollToCurrentSegment,
      scrollToTop: () => scrollRef.current!.scrollTo({ left: 0, top: 0 }),
      scrollToBottom: () =>
        scrollRef.current!.scrollTo({
          left: 0,
          top: scrollRef.current!.scrollHeight,
        }),
    }),
    [scrollToCurrentSegment]
  );

  // Create highlighter for filter matches. This will use either CSS custom
  // highlights or `<mark>` if not available.
  const highlighter = useMemo(
    () => new TextHighlighter('transcript-filter-match'),
    []
  );

  const filterMatches = useMemo(() => {
    // Ignore filter unless it is at least 2 chars long. Single-char filters
    // are ignored to delay filtering until user has typed enough chars to
    // usefully filter the transcript.
    if (filter.length < 2) {
      return null;
    }
    return filterTranscript(transcript.segments, filter);
  }, [filter, transcript]);

  // Adjust the scroll position when the transcript container is resized, so the
  // user doesn't lose their place. See
  // https://github.com/hypothesis/via/issues/1021.
  const getScrollChildren = useCallback(
    (element: HTMLElement) => element.querySelectorAll('li'),
    []
  );
  useScrollAnchor(scrollRef, getScrollChildren);

  const noop = () => {};
  const stableOnSelectSegment = useStableCallback(onSelectSegment ?? noop);
  const segments = useMemo(
    () => (
      <ul
        className={classnames(
          'grow shadow-r-inner p-2',
          // Transparency is necessary to avoid obscuring scroll shadows
          'bg-grey-3/30'
        )}
      >
        {transcript.segments.map((segment, index) => (
          <TranscriptSegment
            key={index}
            hidden={
              filterMatches
                ? !filterMatches.has(index) && index !== currentIndex
                : false
            }
            highlighter={highlighter}
            isCurrent={index === currentIndex}
            matches={filterMatches?.get(index)}
            onSelect={() => stableOnSelectSegment(segment)}
            segment={segment}
          />
        ))}
      </ul>
    ),
    [
      currentIndex,
      filterMatches,
      highlighter,
      stableOnSelectSegment,
      transcript.segments,
    ]
  );

  return (
    <ScrollContainer borderless>
      <Scroll
        classes={classnames(
          // Make element positioned for use with `offsetRelativeTo`.
          'relative',
          'border-y'
        )}
        data-testid="scroll-container"
        elementRef={scrollRef}
      >
        <div className="flex min-h-full">
          {segments}
          {children}
        </div>
        <div
          className="sr-only"
          aria-live="polite"
          role="status"
          data-testid="search-status"
        >
          {filterMatches && filter && (
            <>
              {filter} returned {filterMatches.size} results
            </>
          )}
        </div>
      </Scroll>
    </ScrollContainer>
  );
}
