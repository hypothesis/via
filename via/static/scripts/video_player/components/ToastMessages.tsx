import { Callout } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';

export type ToastMessage = {
  id: string;
  type: 'error' | 'success' | 'notice';
  message: ComponentChildren;
  visuallyHidden?: boolean;
  isDismissed?: boolean;
};

type ToastMessageItemProps = {
  message: ToastMessage;
  onDismiss: (id: string) => void;
};

/**
 * An individual toast message: a brief and transient success or error message.
 * The message may be dismissed by clicking on it. `visuallyHidden` toast
 * messages will not be visible but are still available to screen readers.
 */
function ToastMessageItem({ message, onDismiss }: ToastMessageItemProps) {
  // Capitalize the message type for prepending; Don't prepend a message
  // type for "notice" messages
  const prefix =
    message.type !== 'notice'
      ? `${message.type.charAt(0).toUpperCase() + message.type.slice(1)}: `
      : '';

  return (
    <Callout
      classes={classnames({
        'sr-only': message.visuallyHidden,
      })}
      status={message.type}
      onClick={() => onDismiss(message.id)}
      variant="raised"
    >
      <strong>{prefix}</strong>
      {message.message}
    </Callout>
  );
}

export type ToastMessagesProps = {
  messages: ToastMessage[];
  onMessageDismiss: (id: string) => void;
};

/**
 * A collection of toast messages. These are rendered within an `aria-live`
 * region for accessibility with screen readers.
 */
export default function ToastMessages({
  messages,
  onMessageDismiss,
}: ToastMessagesProps) {
  // The `ul` containing any toast messages is absolute-positioned and the full
  // width of the viewport. Each toast message `li` has its position and width
  // constrained by `container` configuration in tailwind.
  return (
    <ul aria-live="polite" aria-relevant="additions" className="w-full">
      {messages.map(message => (
        <li
          className={classnames('relative w-full container', {
            // Add a bottom margin to visible messages only. Typically, we'd
            // use a `space-y-2` class on the parent to space children.
            // Doing that here could cause an undesired top margin on
            // the first visible message in a list that contains (only)
            // visually-hidden messages before it.
            // See https://tailwindcss.com/docs/space#limitations
            'mb-2': !message.visuallyHidden,
            // Slide in from right in narrow viewports; fade in larger
            // viewports to toast message isn't flying too far
            'motion-safe:animate-slide-in-from-right lg:animate-fade-in':
              !message.isDismissed,
            // Only ever fade in if motion-reduction is preferred
            'motion-reduce:animate-fade-in': !message.isDismissed,
            'animate-fade-out': message.isDismissed,
          })}
          key={message.id}
        >
          <ToastMessageItem message={message} onDismiss={onMessageDismiss} />
        </li>
      ))}
    </ul>
  );
}
