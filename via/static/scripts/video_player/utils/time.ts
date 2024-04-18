function pad(value: number): string {
  return value.toString().padStart(2, '0');
}

function formatTimePiece(
  value: number,
  singular: string,
  plural: string
): string {
  if (value === 1) {
    return `${value} ${singular}`;
  } else {
    return `${value} ${plural}`;
  }
}

/**
 * Format a video timestamp.
 *
 * The timestamp is formatted as `m:ss` for times < 1 hour or `h:mm:ss` for
 * times over 1 hour. This matches how transcript timestamps are formatted on
 * youtube.com.
 *
 * @param time - Time in seconds since the start of the video
 * @param format - Format to use
 *   "digits" - A short "mm:ss" or "hh:mm:ss" timestamp, suitable for display
 *   "description" - A verbose "H hours, M minutes, S seconds" format, useful
 *     for screen readers or contexts where the meaning of the text would not
 *     be obvious in the "digits" format
 */
export function formatTimestamp(
  time: number,
  format: 'digits' | 'description' = 'digits'
): string {
  if (!isFinite(time) || time < 0) {
    return '';
  }
  const totalSeconds = Math.floor(time);
  const hours = Math.floor(totalSeconds / (60 * 60));
  const mins = Math.floor(totalSeconds / 60) % 60;
  const secs = totalSeconds % 60;

  switch (format) {
    case 'digits':
      if (hours > 0) {
        return `${hours}:${pad(mins)}:${pad(secs)}`;
      } else {
        return `${mins}:${pad(secs)}`;
      }
    case 'description': {
      const formatted = [];
      if (hours > 0) {
        formatted.push(formatTimePiece(hours, 'hour', 'hours'));
      }
      if (mins > 0) {
        formatted.push(formatTimePiece(mins, 'minute', 'minutes'));
      }
      if (secs > 0 || (hours === 0 && mins === 0)) {
        formatted.push(formatTimePiece(secs, 'second', 'seconds'));
      }
      return formatted.join(', ');
    }
    /* istanbul ignore next */
    default:
      return '';
  }
}
