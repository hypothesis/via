import {
  Scroll,
  ScrollContainer,
  ScrollContent,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useEffect, useRef } from 'preact/hooks';

import { formatTimestamp } from '../utils/time';

export type Segment = {
  /**
   * True if this segment corresponds to the section of the video that is
   * currently playing.
   */
  isCurrent: boolean;

  /**
   * Time at which this segment starts, as an offset in seconds from the start
   * of the video.
   */
  time: number;

  /** Text of this part of the video. */
  text: string;
};

export type TranscriptData = {
  segments: Segment[];
};

export type TranscriptProps = {
  transcript: TranscriptData;

  /**
   * The current timestamp of the video player, as an offset in seconds from
   * the start of the video.
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
      className={classnames(
        'flex flex-row p-1 hover:text-black',
        isCurrent && 'bg-grey-2',
        !isCurrent && 'text-grey-6'
      )}
      data-is-current={isCurrent}
      data-testid="segment"
    >
      <button className="w-20 hover:underline" onClick={() => onSelect()}>
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
  currentTime,
  onSelectSegment,
  transcript,
}: TranscriptProps) {
  const scrollRef = useRef<HTMLElement | null>(null);

  const currentIndex = transcript.segments.findIndex(
    (segment, index) =>
      currentTime >= segment.time &&
      (index === transcript.segments.length - 1 ||
        currentTime < transcript.segments[index + 1].time)
  );

  useEffect(() => {
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
  }, [currentIndex, transcript]);

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
                time={segment.time}
                text={segment.text}
              />
            ))}
          </ul>
        </ScrollContent>
      </Scroll>
    </ScrollContainer>
  );
}
