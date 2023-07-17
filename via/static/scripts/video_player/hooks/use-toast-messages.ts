import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

import type { ToastMessage } from '../components/ToastMessages';

export type ToastMessageData = Omit<ToastMessage, 'id'> & {
  autoDismiss?: boolean;
};

export type ToastMessagesStore = {
  toastMessages: ToastMessage[];
  appendToastMessage: (toastMessage: ToastMessageData) => void;
  dismissToastMessage: (id: string) => void;
};

const noop = () => {};

export const ToastMessagesContext = createContext<ToastMessagesStore>({
  toastMessages: [],
  appendToastMessage: noop,
  dismissToastMessage: noop,
});

export function useToastMessages(): ToastMessagesStore {
  return useContext(ToastMessagesContext);
}
