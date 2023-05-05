function pad(value: number): string {
  return value.toString().padStart(2, '0');
}

/**
 * Format a video timestamp.
 *
 * The timestamp is formatted as `m:ss` for times < 1 hour or `h:mm:ss` for
 * times over 1 hour. This matches how transcript timestamps are formatted on
 * youtube.com.
 *
 * @param time - Time in seconds since the start of the video
 */
export function formatTimestamp(time: number): string {
  if (!isFinite(time) || time < 0) {
    return '';
  }
  const totalSeconds = Math.floor(time);
  const hours = Math.floor(totalSeconds / (60 * 60));
  const mins = Math.floor(totalSeconds / 60) % 60;
  const secs = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}:${pad(mins)}:${pad(secs)}`;
  } else {
    return `${mins}:${pad(secs)}`;
  }
}
