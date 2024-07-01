export type Segment = {
  /**
   * Time at which this segment starts, as an offset in seconds from the start
   * of the video.
   */
  start: number;

  /**
   * How long this segment lasts.
   *
   * Note that for transcripts from some services (eg. YouTube), `start +
   * duration` for a segment may be greater than the `start` value of the next
   * segment. This is because the `duration` field represents how long the
   * subtitle should be presented on screen, rather than how long the
   * corresponding audio actually lasts. Segments can be "clipped" using
   * {@link clipDurations} to ensure they don't overlap.
   */
  duration: number;

  /** Text of this part of the video. */
  text: string;
};

/**
 * Data for a transcript of a video.
 */
export type TranscriptData = {
  segments: Segment[];
};

/**
 * Generate a {@link VTTCue} list from a transcript.
 *
 * This can be used to create cues for use with an HTML media element.
 */
export function transcriptToCues(transcript: TranscriptData): VTTCue[] {
  return transcript.segments.map(
    seg => new VTTCue(seg.start, seg.start + seg.duration, seg.text),
  );
}

/**
 * Escape characters in `str` which have a special meaning in a regex pattern.
 *
 * Taken from https://stackoverflow.com/a/6969486.
 */
function escapeRegExp(str: string) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
}

/**
 * Location of a query match within the text of a segment.
 */
export type MatchOffset = {
  start: number;
  end: number;
};

/** Perform a case-insensitive search for `query` in `text`. */
function findMatches(text: string, query: string): Array<MatchOffset> {
  const pattern = new RegExp(escapeRegExp(query), 'ig');
  const matches: MatchOffset[] = [];

  let match;
  while ((match = pattern.exec(text)) !== null) {
    matches.push({ start: match.index, end: match.index + match[0].length });
  }

  return matches;
}

/**
 * Clip the `duration` field of segments so that segment time ranges do not
 * overlap.
 */
export function clipDurations(transcript: Segment[]): Segment[] {
  return transcript.map((segment, index) => {
    const { start, text } = segment;
    const nextSegment: Segment | undefined = transcript[index + 1];
    const duration = nextSegment
      ? Math.min(segment.duration, nextSegment.start - start)
      : segment.duration;
    return { start, duration, text };
  });
}

/**
 * Filter a transcript against a user-supplied query.
 *
 * Returns a map of indices of matching segments to locations of match within
 * the segment.
 */
export function filterTranscript(
  transcript: Segment[],
  query: string,
): Map<number, MatchOffset[]> {
  const result = new Map<number, MatchOffset[]>();
  for (const [index, segment] of transcript.entries()) {
    const matches = findMatches(segment.text, query);
    if (matches.length > 0) {
      result.set(index, matches);
    }
  }
  return result;
}

/**
 * Format a transcript as plain text.
 */
export function formatTranscript(transcript: Segment[]): string {
  return transcript.map(seg => seg.text).join('\n');
}

/**
 * Merge every group of `n` consecutive segments into a single transcript
 * segment.
 *
 * This is useful for transcript sources like YouTube where each entry is short,
 * typically just a few words, and so the transcript can be more readable if
 * segments are grouped.
 */
export function mergeSegments(segments: Segment[], n: number): Segment[] {
  return segments.reduce((merged, segment, idx) => {
    if (idx % n !== 0) {
      const last = merged[merged.length - 1];
      last.text += ' ' + segment.text;
      last.duration = segment.start + segment.duration - last.start;
    } else {
      // Copy segment so we can modify in subsequent iterations.
      merged.push({ ...segment });
    }
    return merged;
  }, [] as Segment[]);
}
