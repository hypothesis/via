import { useRef } from 'preact/hooks';

export type NextRender = {
  /** Return a promise which resolves after the next render of the current component. */
  wait(): Promise<void>;
};

/**
 * Hook which enables waiting until the next re-render of the current component
 * completes.
 *
 * A simple timeout could be used instead, but this hook is designed to be
 * robust to whatever approach is used to schedule renders (next microtask, next
 * animation frame etc.) in the current environment.
 */
export function useNextRender(): NextRender {
  const resolveNextRender = useRef<{
    promise: Promise<void>;
    resolve: () => void;
  }>();

  // Preact renders synchronously, so we can resolve the promise now and
  // the DOM will be updated by the time any code waiting on the promise runs.
  //
  // If this wasn't the case, we'd have to use `useLayoutEffect` instead.
  if (resolveNextRender.current) {
    resolveNextRender.current.resolve();
    resolveNextRender.current = undefined;
  }

  const controller = useRef({
    wait() {
      if (!resolveNextRender.current) {
        let resolve = () => {}; // Dummy initializer to avoid TS error.
        const promise = new Promise<void>(r => {
          resolve = r;
        });
        resolveNextRender.current = { promise, resolve };
      }
      return resolveNextRender.current.promise;
    },
  });
  return controller.current;
}
