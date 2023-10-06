import type { ToastMessage } from '@hypothesis/frontend-shared';
import { useCallback, useState } from 'preact/hooks';

export type ToastMessageData = Omit<ToastMessage, 'id'>;

export type ToastMessageAppender = (toastMessageData: ToastMessageData) => void;

export type ToastMessages = {
  toastMessages: ToastMessage[];
  appendToastMessage: ToastMessageAppender;
  dismissToastMessage: (id: string) => void;
};

// Keep a global incremental counter to use as unique toast message ID
let toastMessageCounter = 0;

export function useToastMessages(): ToastMessages {
  const [toastMessages, setToastMessages] = useState<ToastMessage[]>([]);
  const appendToastMessage = useCallback(
    (toastMessageData: ToastMessageData) => {
      toastMessageCounter++;
      const id = `${toastMessageCounter}`;
      setToastMessages(messages => [...messages, { ...toastMessageData, id }]);
    },
    []
  );
  const dismissToastMessage = useCallback(
    (id: string) =>
      setToastMessages(messages =>
        messages.filter(message => message.id !== id)
      ),
    []
  );

  return { toastMessages, appendToastMessage, dismissToastMessage };
}
