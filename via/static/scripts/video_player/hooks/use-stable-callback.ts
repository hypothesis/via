import { useRef } from 'preact/hooks';

/**
 * Return a function which wraps a callback to give it a stable value.
 *
 * The wrapper has a stable value across renders, but always forwards to the
 * callback from the most recent render. This is useful if you want to use a
 * callback inside a `useEffect` or `useMemo` hook without re-running the effect
 * or re-computing the memoed value when the callback changes.
 */
export function useStableCallback<R, A extends any[], F extends (...a: A) => R>(
  callback: F
): F {
  const wrapper = useRef({
    callback,
    call: (...args: A) => wrapper.current.callback(...args),
  });

  // On each render, save the last callback value.
  wrapper.current.callback = callback;

  return wrapper.current.call as F;
}
