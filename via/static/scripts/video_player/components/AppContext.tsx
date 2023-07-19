import type { Signal } from '@preact/signals';
import { createContext } from 'preact';

import type { ToastMessage } from './ToastMessages';

export type AppStore = {
  toastMessages: Signal<ToastMessage[]>;
};

export const AppContext = createContext<AppStore>({
  toastMessages: {},
} as AppStore);
