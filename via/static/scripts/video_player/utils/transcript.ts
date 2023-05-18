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
 * Filter a transcript against a user-supplied query.
 *
 * Returns a map of indices of matching segments to locations of match within
 * the segment.
 */
export function filterTranscript(
  transcript: Segment[],
  query: string
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
