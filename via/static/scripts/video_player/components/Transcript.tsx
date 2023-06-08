import { Scroll, ScrollContainer } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { Ref } from 'preact';
import {
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
} from 'preact/hooks';

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
};

export type TranscriptProps = {
  /**
   * Whether to automatically scroll the transcript as the video plays to keep
   * the segment corresponding to `currentTime` in view.
   */
  autoScroll?: boolean;

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
   * CSS highlight used to highlight spans of text specified by {@link matches}.
   */
  highlight?: Highlight;

  /** Offsets within the segment text to highlight. */
  matches?: MatchOffset[];

  isCurrent: boolean;
  onSelect: () => void;
  time: number;
  text: string;
};

function TranscriptSegment({
  hidden = false,
  highlight,
  matches,
  isCurrent,
  onSelect,
  time,
  text,
}: TranscriptSegmentProps) {
  const contentRef = useRef<HTMLParagraphElement>(null);

  // Highlight the text within the segment that matches the current filter
  // query.
  useEffect(() => {
    if (!highlight || !matches) {
      return () => {};
    }

    const ranges = matches.map(({ start, end }) => {
      const textNode = contentRef.current!.childNodes[0];
      const range = new Range();

      // FIXME - If the Hypothesis client has inserted highlights, these will
      // break up the single text node child into multiple children.
      if (textNode instanceof Text && textNode.length >= end) {
        range.setStart(textNode, start);
        range.setEnd(textNode, end);
      }

      return range;
    });
    ranges.forEach(r => highlight.add(r));

    return () => {
      ranges.forEach(r => highlight.delete(r));
    };
  }, [highlight, matches]);

  const timestamp = formatTimestamp(time);

  return (
    <li
      className={classnames(
        'flex gap-x-3 p-1.5',
        // Various tranparencies of a dark color are used for backgrounds to
        // avoid obscuring scroll-hint shadows
        'border-y hover:bg-slate-9/[.08]',
        {
          'bg-slate-9/[.08] border-grey-4/50 shadow-inner': isCurrent,
          // Non-current entries have a bottom border only (subtle dotted)
          'odd:bg-slate-9/[.03] border-t-transparent border-b-grey-2 border-b-dotted':
            !isCurrent,
          hidden,
        }
      )}
      data-is-current={isCurrent}
      data-testid="segment"
    >
      <button
        aria-label={timestamp}
        onClick={onSelect}
        className={classnames(
          // TODO: Use shared Button to get these styles for free
          'flex transition-colors focus-visible-ring rounded-sm',
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
        className={classnames('grow peer-hover:text-stone-900', {
          'text-stone-600': !isCurrent,
          'text-stone-800': isCurrent,
        })}
        data-testid="transcript-text"
        ref={contentRef}
      >
        {text}
        {
          // Add a trailing space at the end of each segment to avoid the last
          // word of a segment being joined with the first word of the next
          // segment in annotation quotes.
          ' '
        }
      </p>
    </li>
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

    // Scroll container such that the middle of the current segment is centered
    // in the container. Note that we don't use `currentSegment.scrollIntoView`
    // here because that may scroll the whole document, which we don't want.
    const currentSegmentOffset = offsetRelativeTo(
      currentSegment,
      scrollContainer
    );
    const scrollTarget =
      currentSegmentOffset +
      currentSegment.clientHeight / 2 -
      scrollContainer.clientHeight / 2;

    scrollContainer.scrollTo({
      left: 0,
      top: scrollTarget,
      behavior: 'smooth',
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
    }),
    [scrollToCurrentSegment]
  );

  // Use CSS highlights to highlight text in segments that matches the current
  // filter query.
  const highlight = useMemo(() => {
    if (typeof Highlight !== 'function') {
      return undefined;
    }
    return new Highlight();
  }, []);

  useEffect(() => {
    if (!highlight) {
      return () => {};
    }

    // nb. This assumes there is only one `Transcript` component mounted
    // at a time.
    CSS.highlights.set('transcript-filter-match', highlight);
    return () => {
      CSS.highlights.delete('transcript-filter-match');
    };
  }, [highlight]);

  const filterMatches = useMemo(() => {
    // Ignore filter unless it is at least 2 chars long. Single-char filters
    // are ignored to delay filtering until user has typed enough chars to
    // usefully filter the transcript.
    if (filter.length < 2) {
      return null;
    }
    return filterTranscript(transcript.segments, filter);
  }, [filter, transcript]);

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
        <ul>
          {transcript.segments.map((segment, index) => (
            <TranscriptSegment
              key={index}
              hidden={
                filterMatches
                  ? !filterMatches.has(index) && index !== currentIndex
                  : false
              }
              highlight={highlight}
              isCurrent={index === currentIndex}
              matches={filterMatches?.get(index)}
              onSelect={() => onSelectSegment?.(segment)}
              time={segment.start}
              text={segment.text}
            />
          ))}
        </ul>
      </Scroll>
    </ScrollContainer>
  );
}
