import { useContext } from 'preact/hooks';

import { AppContext } from '../components/AppProvider';
import type { ToastMessage } from '../components/ToastMessages';
import { generateHexString } from '../utils/generate-hex-string';

type ToastMessageData = Omit<ToastMessage, 'id'>;

type ToastMessages = {
  toastMessages: ToastMessage[];
  appendToastMessage: (toastMessageData: ToastMessageData) => void;
  dismissToastMessage: (od: string) => void;
};

export function useToastMessages(): ToastMessages {
  const { toastMessages, setToastMessages } =
    useContext(AppContext).toastMessages;
  const appendToastMessage = (toastMessageData: ToastMessageData) => {
    const id = generateHexString(10);
    setToastMessages(messages => [...messages, { ...toastMessageData, id }]);
  };
  const dismissToastMessage = (id: string) =>
    setToastMessages(messages => messages.filter(message => message.id !== id));

  return {
    toastMessages,
    appendToastMessage,
    dismissToastMessage,
  };
}
