import { CopyIcon, IconButton } from '@hypothesis/frontend-shared';

import { formatTranscript } from '../utils/transcript';
import type { TranscriptData } from '../utils/transcript';

export type CopyButtonProps = {
  transcript: TranscriptData | null;
};

/**
 * Toolbar button that copies the transcript to the clipboard.
 */
export default function CopyButton({ transcript }: CopyButtonProps) {
  const copyTranscript = async () => {
    const formattedTranscript = transcript
      ? formatTranscript(transcript.segments)
      : '';
    try {
      await navigator.clipboard.writeText(formattedTranscript);
    } catch (err) {
      // TODO: Replace this with a toast message in the UI.
      console.warn('Failed to copy transcript', err);
    }
  };

  return (
    <IconButton
      onClick={copyTranscript}
      data-testid="copy-button"
      disabled={!transcript}
      title="Copy transcript"
      icon={CopyIcon}
      size="custom"
      classes="p-2"
    />
  );
}
