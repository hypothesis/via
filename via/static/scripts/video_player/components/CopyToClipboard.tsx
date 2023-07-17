import { CopyIcon, IconButton } from '@hypothesis/frontend-shared';

import { useToastMessages } from '../hooks/use-toast-messages';
import type { TranscriptData } from '../utils/transcript';
import { formatTranscript } from '../utils/transcript';

export type CopyToClipboardProps = {
  transcript?: TranscriptData;
};

export default function CopyToClipboard({ transcript }: CopyToClipboardProps) {
  const { appendToastMessage } = useToastMessages();
  const copyTranscript = async () => {
    const formattedTranscript = transcript
      ? formatTranscript(transcript.segments)
      : '';

    try {
      await navigator.clipboard.writeText(formattedTranscript);
      appendToastMessage({
        type: 'success',
        message: 'Transcript copied to clipboard',
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
