import type { RefObject } from 'preact';
import { useCallback, useLayoutEffect, useState } from 'preact/hooks';

type AppSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl';

/**
 * Watch for resizes on `element` and invoke `onSizeChanged` callback
 */
export function observeElementSize(
  element: Element,
  onSizeChanged: (width: number, height: number) => void
): () => void {
  const observer = new ResizeObserver(() =>
    onSizeChanged(element.clientWidth, element.clientHeight)
  );
  observer.observe(element);
  return () => observer.disconnect();
}

/**
 * Return a string representing the relative size of `appContainer`
 */
export function useAppLayout(appContainer: RefObject<HTMLDivElement | null>) {
  const [appSize, setAppSize] = useState<AppSize>('sm');

  const updateWidth = useCallback(() => {
    const containerWidth = appContainer.current?.clientWidth;
    if (!containerWidth) {
      return;
    }

    let containerSize: AppSize = 'sm';
    if (containerWidth > 1376) {
      containerSize = '2xl';
    } else if (containerWidth > 1024) {
      containerSize = 'xl';
    } else if (containerWidth > 875) {
      containerSize = 'lg';
    } else if (containerWidth > 768) {
      containerSize = 'md';
    }

    setAppSize(containerSize);
  }, [appContainer]);

  useLayoutEffect(() => {
    const cleanup = observeElementSize(appContainer.current!, updateWidth);
    updateWidth();
    return cleanup;
  }, [updateWidth, appContainer]);

  return appSize;
}
