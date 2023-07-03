import { useRef } from 'preact/hooks';

/** Wrap a function type to add `undefined` to the return types. */
type MayReturnUndefined<R, T extends (...a: any) => R> = (
  ...a: Parameters<T>
) => R | undefined;

/**
 * Wrap a callback to give it a stable reference.
 *
 * Returns a wrapper around `callback`. The wrapper has the same value across
 * renders, but always forwards to the latest value of `callback` when invoked.
 * If the most recent value of `callback` is undefined, the wrapper will do
 * nothing when called. Because the `callback` may have been undefined, the
 * wrapper may also return undefined.
 *
 * This is useful if you want to use a callback as an event handler inside
 * a `useEffect` or `useMemo` hook  without re-running the effect or
 * re-computing the memoed value on each change.
 */
export function useStableCallback<R, F extends (...a: any) => R>(
  callback: F | undefined
): MayReturnUndefined<R, F> {
  const wrapper = useRef({
    callback,
    call: (...args: unknown[]) => wrapper.current.callback?.(...args),
  });

  // On each render, save the last callback value.
  wrapper.current.callback = callback;

  return wrapper.current.call as unknown as MayReturnUndefined<R, F>;
}
