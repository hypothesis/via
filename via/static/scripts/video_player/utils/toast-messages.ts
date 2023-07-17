import type { StateUpdater } from 'preact/hooks';

import type { ToastMessage } from '../components/ToastMessages';
import { generateHexString } from './generate-hex-string';

export type ToastMessageData = Omit<ToastMessage, 'id'>;

type ToastMessagesUpdater = StateUpdater<ToastMessage[]>;

export const appendToastMessage = (
  toastMessageData: ToastMessageData,
  setToastMessages: ToastMessagesUpdater
) => {
  const id = generateHexString(10);
  setToastMessages(messages => [...messages, { ...toastMessageData, id }]);
};

export const dismissToastMessage = (
  id: string,
  setToastMessages: ToastMessagesUpdater
) =>
  setToastMessages(messages => messages.filter(message => message.id !== id));
