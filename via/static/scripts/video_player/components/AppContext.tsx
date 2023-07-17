import { createContext } from 'preact';
import type { StateUpdater } from 'preact/hooks';

import type { ToastMessage } from './ToastMessages';

export type ToastMessagesState = {
  toastMessages: ToastMessage[];
  setToastMessages: StateUpdater<ToastMessage[]>;
};

export type AppStore = {
  toastMessages: ToastMessagesState;
};

export const AppContext = createContext<AppStore>({
  toastMessages: {
    toastMessages: [],
    setToastMessages: () => {},
  },
});
