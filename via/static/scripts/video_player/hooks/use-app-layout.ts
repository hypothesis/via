import type { RefObject } from 'preact';
import { useCallback, useLayoutEffect, useState } from 'preact/hooks';

import { SIDEBYSIDE_THRESHOLD, TOOLBAR_WIDTH } from './use-side-by-side-layout';

/* Relative application container size */
export type AppSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl';

/**
 * Return a string representing the relative size of `appContainer` that can
 * be used to make decisions about app layout and sizing of components. This
 * would typically be something handled by media queries, but it is an element
 * (`body`) width that needs to be queried, not the viewport. We could replace
 * this with container queries once browser support is sufficient.
 *
 * NB: This hook will not update if `appContainer.current` changes.
 */
export function useAppLayout(
  appContainer: RefObject<HTMLDivElement | null>
): AppSize {
  const [appSize, setAppSize] = useState<AppSize>('sm');

  const updateWidth = useCallback(() => {
    const containerWidth = appContainer.current?.clientWidth;
    /* istanbul ignore next */
    if (!containerWidth) {
      return;
    }

    let containerSize: AppSize = 'sm';
    if (containerWidth > 1376) {
      containerSize = '2xl';
    } else if (containerWidth > 1024) {
      containerSize = 'xl';
    } else if (containerWidth > SIDEBYSIDE_THRESHOLD) {
      containerSize = 'lg';
    } else if (containerWidth >= SIDEBYSIDE_THRESHOLD - TOOLBAR_WIDTH) {
      containerSize = 'md';
    }
    setAppSize(containerSize);
  }, [appContainer]);

  useLayoutEffect(() => {
    const element = appContainer.current;
    /* istanbul ignore if */
    if (!element) {
      return () => {};
    }
    const observer = new ResizeObserver(() => updateWidth());
    observer.observe(element);
    updateWidth();
    return () => observer.disconnect();
  }, [updateWidth, appContainer]);

  return appSize;
}
