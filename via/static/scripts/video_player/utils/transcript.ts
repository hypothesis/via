export type Segment = {
  /**
   * Time at which this segment starts, as an offset in seconds from the start
   * of the video.
   */
  start: number;

  /** Text of this part of the video. */
  text: string;
};

/**
 * Data for a transcript of a video.
 */
export type TranscriptData = {
  segments: Segment[];
};
