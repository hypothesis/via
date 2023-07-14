import type { RefObject } from 'preact';
import { useCallback, useLayoutEffect, useRef, useState } from 'preact/hooks';

import { SIDEBYSIDE_THRESHOLD, TOOLBAR_WIDTH } from './use-side-by-side-layout';

/* Relative application container size */
export type AppSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl';

export type AppLayoutInfo = {
  /* Relative size of app container element */
  appSize: AppSize;
  multicolumn: boolean;
  /* Width for the column containing the transcript as a CSS dimension */
  transcriptWidth: string;
};

const transcriptWidths = {
  sm: '100%',
  md: '380px',
  lg: '410px',
  xl: '450px',
};

/**
 * Return app layout info based on the size of the `appContainer` element. We
 * could replace this with container queries once browser support is sufficient.
 *
 * NB: This hook will not update if `appContainer.current` changes.
 */
export function useAppLayout(
  appContainer: RefObject<HTMLDivElement | null>
): AppLayoutInfo {
  const lastContainerSize = useRef<AppSize>('sm');
  const [layoutInfo, setLayoutInfo] = useState<AppLayoutInfo>({
    appSize: 'sm',
    multicolumn: false,
    transcriptWidth: transcriptWidths.sm,
  });

  const updateWidth = useCallback(() => {
    const containerWidth = appContainer.current?.clientWidth;
    /* istanbul ignore next */
    if (!containerWidth) {
      return;
    }

    let containerSize: AppSize = 'sm';
    const minimumMulticolumn = SIDEBYSIDE_THRESHOLD - TOOLBAR_WIDTH;

    if (containerWidth > 1376) {
      containerSize = 'xl';
    } else if (containerWidth > 1024) {
      containerSize = 'lg';
    } else if (containerWidth >= minimumMulticolumn) {
      containerSize = 'md';
    }
    if (lastContainerSize.current !== containerSize) {
      lastContainerSize.current = containerSize;
      setLayoutInfo({
        appSize: containerSize,
        multicolumn: containerSize !== 'sm',
        transcriptWidth: transcriptWidths[containerSize],
      });
    }
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

  return layoutInfo;
}
