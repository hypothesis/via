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
};

type TranscriptSegmentProps = {
  isCurrent: boolean;
  time: number;
  text: string;
};

function TranscriptSegment({ time, text }: TranscriptSegmentProps) {
  // TODO - Use appropriate semantic elements here
  return (
    <div>
      <div>{time}</div>
      <p>{text}</p>
    </div>
  );
}

export default function Transcript({
  currentTime,
  transcript,
}: TranscriptProps) {
  // TODO - Use appropriate semantic elements here
  return (
    <div>
      {transcript.segments.map((segment, index) => (
        <TranscriptSegment
          key={index}
          isCurrent={
            currentTime >= segment.time &&
            (index === transcript.segments.length - 1 ||
              currentTime < transcript.segments[index + 1].time)
          }
          time={segment.time}
          text={segment.text}
        />
      ))}
    </div>
  );
}
