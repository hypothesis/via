export type VideoPlayerProps = {
  videoId: string;

  /** Set the current timestamp of the video. */
  time: number;

  /**
   * Callback invoked when the timestamp of the video changes.
   */
  onTimeChanged?: (timestamp: number) => void;

  /**
   * Callback invoked when the playing/paused state of the video changes.
   */
  onPlayingChanged?: (playing: boolean) => void;
};

/**
 * Component that wraps the YouTube video player.
 */
export default function VideoPlayer({
  videoId,
  time,
  onTimeChanged,
  onPlayingChanged,
}: VideoPlayerProps) {
  const encodedId = encodeURIComponent(videoId);
  const playerURL = `https://www.youtube.com/embed/${encodedId}?enablejsapi=1`;

  return (
    <div>
      <iframe src={playerURL} />
    </div>
  );
}
