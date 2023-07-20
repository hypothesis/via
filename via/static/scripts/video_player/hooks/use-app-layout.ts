import type { RefObject } from 'preact';
import { useMemo, useLayoutEffect, useState } from 'preact/hooks';

import { SIDEBYSIDE_THRESHOLD, TOOLBAR_WIDTH } from './use-side-by-side-layout';

/* Relative application container size */
export type AppSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl';

export type AppLayoutInfo = {
  /* Relative size of app container element */
  appSize: AppSize;

  multicolumn: boolean;

  /* Width for the column containing the transcript as a CSS dimension */
  transcriptWidth: string;

  /**
   * Maximum width for the video, or `undefined` if it should use the full
   * width of the video player's column.
   */
  videoWidth?: number;
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
  const [containerWidth, setContainerWidth] = useState<number | null>(null);
  const [containerHeight, setContainerHeight] = useState<number | null>(null);

  const layoutInfo = useMemo(() => {
    let containerSize: AppSize = 'sm';
    const minimumMulticolumn = SIDEBYSIDE_THRESHOLD - TOOLBAR_WIDTH;

    const width = containerWidth ?? window.innerWidth;
    const height = containerHeight ?? window.innerHeight;

    if (width > 1376) {
      containerSize = 'xl';
    } else if (width > 1024) {
      containerSize = 'lg';
    } else if (width >= minimumMulticolumn) {
      containerSize = 'md';
    }
    const multicolumn = containerSize !== 'sm';

    // In single-column layout, limit the video width so as to make it half the
    // window height. This ensures that there is enough space for the transcript,
    // even if the window is short.
    const videoAspectRatio = 16 / 9;
    const videoWidth = !multicolumn
      ? Math.min(width, (height / 2) * videoAspectRatio)
      : undefined;

    return {
      appSize: containerSize,
      multicolumn,
      transcriptWidth: transcriptWidths[containerSize],
      videoWidth,
    };
  }, [containerWidth, containerHeight]);

  useLayoutEffect(() => {
    const element = appContainer.current;
    /* istanbul ignore if */
    if (!element) {
      return () => {};
    }

    const updateWidth = () => {
      const containerWidth = element.clientWidth;
      const containerHeight = element.clientHeight;

      /* istanbul ignore next */
      if (!containerWidth || !containerHeight) {
        return;
      }

      setContainerWidth(containerWidth);
      setContainerHeight(containerHeight);
    };

    const observer = new ResizeObserver(() => updateWidth());
    observer.observe(element);
    updateWidth();
    return () => observer.disconnect();
  }, [appContainer]);

  return layoutInfo;
}
