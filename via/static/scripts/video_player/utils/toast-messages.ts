import type { Signal } from '@preact/signals';

import type { ToastMessage } from '../components/ToastMessages';
import { generateHexString } from './generate-hex-string';

export type ToastMessageData = Omit<ToastMessage, 'id'>;

type ToastMessagesSignal = Signal<ToastMessage[]>;

export const appendToastMessage = (
  toastMessageData: ToastMessageData,
  toastMessages: ToastMessagesSignal
) => {
  const id = generateHexString(10);
  toastMessages.value = [...toastMessages.value, { ...toastMessageData, id }];
};

export const dismissToastMessage = (
  id: string,
  toastMessages: ToastMessagesSignal
) => {
  toastMessages.value = toastMessages.value.filter(
    message => message.id !== id
  );
};
