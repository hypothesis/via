import {
  Scroll,
  ScrollContainer,
  ScrollContent,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { Ref } from 'preact';
import {
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
} from 'preact/hooks';

import { formatTimestamp } from '../utils/time';
import type { Segment, TranscriptData } from '../utils/transcript';

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

  /**
   * Callback invoked when the user selects a segment from the transcript.
   */
  onSelectSegment?: (segment: Segment) => void;
};

type TranscriptSegmentProps = {
  isCurrent: boolean;
  onSelect: () => void;
  time: number;
  text: string;
};

function TranscriptSegment({
  isCurrent,
  onSelect,
  time,
  text,
}: TranscriptSegmentProps) {
  return (
    <li
      className={classnames('flex flex-row p-1 hover:text-black', {
        'bg-grey-2': isCurrent,
        'text-grey-6': !isCurrent,
      })}
      data-is-current={isCurrent}
      data-testid="segment"
    >
      <button className="pr-5 hover:underline" onClick={onSelect}>
        {formatTimestamp(time)}
      </button>
      <p className="basis-64 grow" data-testid="transcript-text">
        {text}
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
  controlsRef,
  currentTime,
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
    scrollToCurrentSegment();
  }, [currentIndex, transcript, scrollToCurrentSegment]);

  useImperativeHandle(
    controlsRef || { current: null },
    () => ({
      scrollToCurrentSegment,
    }),
    [scrollToCurrentSegment]
  );

  return (
    <ScrollContainer borderless>
      <Scroll
        classes={
          // Make element positioned for use with `offsetRelativeTo`.
          'relative'
        }
        data-testid="scroll-container"
        elementRef={scrollRef}
      >
        <ScrollContent>
          <ul>
            {transcript.segments.map((segment, index) => (
              <TranscriptSegment
                key={index}
                isCurrent={index === currentIndex}
                onSelect={() => onSelectSegment?.(segment)}
                time={segment.start}
                text={segment.text}
              />
            ))}
          </ul>
        </ScrollContent>
      </Scroll>
    </ScrollContainer>
  );
}
