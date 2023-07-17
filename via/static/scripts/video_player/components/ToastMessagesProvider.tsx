import type { ComponentChildren } from 'preact';
import { useReducer } from 'preact/hooks';

import type { ToastMessageData } from '../hooks/use-toast-messages';
import { ToastMessagesContext } from '../hooks/use-toast-messages';
import { generateHexString } from '../utils/generate-hex-string';
import type { ToastMessage } from './ToastMessages';
import ToastMessages from './ToastMessages';

const toastMessageReducer = (
  state: ToastMessage[],
  action:
    | { type: 'append'; toastMessage: ToastMessage }
    | { type: 'dismiss'; id: string }
    | { type: 'remove'; id: string }
) => {
  switch (action.type) {
    case 'append':
      return [...state, action.toastMessage];
    case 'dismiss':
      for (const message of state) {
        if (message.id === action.id) {
          message.isDismissed = true;
          break;
        }
      }

      return state;
    case 'remove':
      return state.filter(message => message.id !== action.id);
    default:
      return state;
  }
};

export type ToastMessagesProviderProps = {
  children: ComponentChildren;
};

export default function ToastMessagesProvider({
  children,
}: ToastMessagesProviderProps) {
  const [toastMessages, dispatch] = useReducer(toastMessageReducer, []);
  const dismissToastMessage = (id: string) => {
    dispatch({ type: 'dismiss', id });

    // Wait for transition to finish, then remove message
    setTimeout(() => {
      dispatch({ type: 'remove', id });
    }, 500);
  };
  const appendToastMessage = ({
    autoDismiss = true,
    ...rest
  }: ToastMessageData) => {
    const id = generateHexString(10);
    dispatch({
      type: 'append',
      toastMessage: { ...rest, id },
    });

    if (autoDismiss) {
      setTimeout(() => dismissToastMessage(id), 5000);
    }
  };

  return (
    <ToastMessagesContext.Provider
      value={{
        toastMessages,
        appendToastMessage,
        dismissToastMessage,
      }}
    >
      <div className="absolute z-2 right-0 top-[80px] w-full">
        <ToastMessages
          messages={toastMessages}
          onMessageDismiss={dismissToastMessage}
        />
      </div>
      {children}
    </ToastMessagesContext.Provider>
  );
}
