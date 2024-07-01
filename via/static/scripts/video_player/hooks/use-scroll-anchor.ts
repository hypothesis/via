import { useEffect } from 'preact/hooks';
import type { MutableRef } from 'preact/hooks';

function rectIsEmpty(rect: DOMRect) {
  return rect.width <= 0 || rect.height <= 0;
}

/**
 * Return true if `rectB` is fully contained within `rectA`
 */
export function rectContains(rectA: DOMRect, rectB: DOMRect) {
  if (rectIsEmpty(rectA) || rectIsEmpty(rectB)) {
    return false;
  }

  return (
    rectB.left >= rectA.left &&
    rectB.right <= rectA.right &&
    rectB.top >= rectA.top &&
    rectB.bottom <= rectA.bottom
  );
}

/**
 * Automatically adjust the scroll offset of `scrollRef` when the element is
 * resized, so that the same content remains at the top of the viewport.
 *
 * This works by selecting a _scroll anchor_ when the container is scrolled, and
 * noting its position relative to the top of the container. When the container
 * is resized, the scroll position is adjusted to keep the scroll anchor in the
 * same position relative to the top of the container.
 *
 * A known limitation is that the scroll anchoring will break if the scroll
 * container's height becomes small enough that no child fits fully within its
 * viewport.
 *
 * @param scrollRef - The scrollable container element
 * @param getChildren - Callback that returns the children of the container that
 *   should be used as candidates for a scroll anchor
 */
export function useScrollAnchor(
  scrollRef: MutableRef<HTMLElement | null>,
  getChildren: (element: HTMLElement) => NodeListOf<HTMLElement>,
) {
  useEffect(() => {
    /* istanbul ignore next */
    if (!scrollRef.current) {
      return undefined;
    }

    const scrollElement = scrollRef.current!;

    // Turn off the browser's own scroll anchoring, so it doesn't interfere with
    // ours.
    scrollElement.style.overflowAnchor = 'none';

    // Element selected as the scroll anchor, and its offset from the top of
    // the scrollable element.
    let scrollAnchor: { element: HTMLElement; offset: number } | null = null;

    const observer = new ResizeObserver(() => {
      if (!scrollAnchor) {
        return;
      }

      const scrollRect = scrollElement.getBoundingClientRect();
      const relativeOffset =
        scrollAnchor.element.getBoundingClientRect().top - scrollRect.top;
      const delta = relativeOffset - scrollAnchor.offset;
      scrollElement.scrollBy(0, delta);
    });
    observer.observe(scrollElement);

    const updateScrollAnchor = () => {
      const scrollRect = scrollElement.getBoundingClientRect();
      const newScrollAnchor = Array.from(getChildren(scrollElement)).find(
        child => rectContains(scrollRect, child.getBoundingClientRect()),
      );

      if (!newScrollAnchor) {
        scrollAnchor = null;
      } else {
        const offset =
          newScrollAnchor.getBoundingClientRect().top - scrollRect.top;
        scrollAnchor = {
          element: newScrollAnchor,
          offset,
        };
      }
    };
    scrollElement.addEventListener('scroll', updateScrollAnchor);

    // Set initial scroll anchor.
    updateScrollAnchor();

    return () => {
      observer.disconnect();
      scrollElement.removeEventListener('scroll', updateScrollAnchor);
    };
  }, [scrollRef, getChildren]);
}
