import { useCallback, useState } from 'preact/hooks';

import type { ToastMessage } from '../components/ToastMessages';
import { generateHexString } from '../utils/generate-hex-string';

export function useToastMessages() {
  const [toastMessages, setToastMessages] = useState<ToastMessage[]>([]);
  const appendToastMessage = useCallback(
    (toastMessageData: Omit<ToastMessage, 'id'>) => {
      const id = generateHexString(10);
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

export type ToastMessageAppender = ReturnType<
  typeof useToastMessages
>['appendToastMessage'];
