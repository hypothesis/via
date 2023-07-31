import { CopyIcon, IconButton } from '@hypothesis/frontend-shared';

import type { ToastMessageAppender } from '../hooks/use-toast-messages';
import { formatTranscript } from '../utils/transcript';
import type { TranscriptData } from '../utils/transcript';

export type CopyButtonProps = {
  transcript: TranscriptData | null;
  appendToastMessage: ToastMessageAppender;
};

/**
 * Toolbar button that copies the transcript to the clipboard.
 */
export default function CopyButton({
  transcript,
  appendToastMessage,
}: CopyButtonProps) {
  const copyTranscript = async () => {
    const formattedTranscript = transcript
      ? formatTranscript(transcript.segments)
      : '';
    try {
      await navigator.clipboard.writeText(formattedTranscript);
      appendToastMessage({
        type: 'success',
        message: 'Transcript copied',
      });
    } catch (err) {
      appendToastMessage({
        type: 'error',
        message: 'Failed to copy transcript',
      });
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
