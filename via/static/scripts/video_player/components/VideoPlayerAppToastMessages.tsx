import { useToastMessages } from '../hooks/use-toast-messages';
import ToastMessages from './ToastMessages';

export default function VideoPlayerAppToastMessages() {
  const { toastMessages, dismissToastMessage } = useToastMessages();

  return (
    <div className="absolute z-2 top-0 w-full p-2">
      <ToastMessages
        messages={toastMessages}
        onMessageDismiss={dismissToastMessage}
      />
    </div>
  );
}
