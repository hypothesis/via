import { useContext } from 'preact/hooks';

import { dismissToastMessage } from '../utils/toast-messages';
import { AppContext } from './AppContext';
import ToastMessages from './ToastMessages';

export default function VideoPlayerAppToastMessages() {
  const { toastMessages, setToastMessages } =
    useContext(AppContext).toastMessages;

  return (
    <div className="absolute z-2 top-0 w-full p-2">
      <ToastMessages
        messages={toastMessages}
        onMessageDismiss={id => dismissToastMessage(id, setToastMessages)}
      />
    </div>
  );
}
