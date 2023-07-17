import type { ComponentChildren } from 'preact';
import { createContext } from 'preact';
import type { StateUpdater } from 'preact/hooks';
import { useState } from 'preact/hooks';

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

export type AppProviderProps = {
  children: ComponentChildren;
};

export default function AppProvider({ children }: AppProviderProps) {
  const [toastMessages, setToastMessages] = useState<ToastMessage[]>([]);

  return (
    <AppContext.Provider
      value={{
        toastMessages: {
          toastMessages,
          setToastMessages,
        },
      }}
    >
      {children}
    </AppContext.Provider>
  );
}
