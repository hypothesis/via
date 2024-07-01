import { useCallback, useEffect, useState } from 'preact/hooks';

// `hypothesis:layoutchange` is triggered on the host document `body` element by
// the client's `annotator`. Types are copied from the `client` project. See
// https://github.com/hypothesis/client/blob/16e37788fdc52fd7e7b8eb9c0eece6a993334424/src/annotator/events.ts
type SidebarLayout = {
  /** Whether sidebar is open or closed */
  expanded: boolean;
  /** Current width of sidebar in pixels */
  width: number;
  /** Current height of sidebar in pixels */
  height: number;
  /** Width of controls (toolbar, bucket bar) on the edge of the sidebar */
  toolbarWidth: number;
};

type LayoutChangeEventDetail = {
  sideBySideActive: boolean;
  sidebarLayout: SidebarLayout;
};

type LayoutChangeEvent = CustomEvent & { detail: LayoutChangeEventDetail };

// Minimum body width at which laying out side-by-side should be considered
export const SIDEBYSIDE_THRESHOLD = 875;
// The sidebar reports its toolbar width as 33px. This is a custom padding
// amount that allows this app to nestle up more cloesly to the sidebar when
// closed.
export const TOOLBAR_WIDTH = 22;

/**
 * Adjust the available space to the right of app content to make room for
 * the sidebar when plausible. This mimics the client's "side-by-side" mode,
 * tuned specifically for this application.
 *
 * Side-by-side layout will be re-computed whenever sidebar state via the
 * `hypothesis:layoutchange` event changes meaningfully, or when the window
 * is resized.
 *
 * @param [container] test seam
 * @return Whether side-by-side is currently active or not
 */
export function useSideBySideLayout(container = document.body): boolean {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sufficientSpace, setSufficientSpace] = useState(
    container.clientWidth >= SIDEBYSIDE_THRESHOLD,
  );
  const [sidebarWidth, setSidebarWidth] = useState(0);
  const sideBySideActive = sufficientSpace && sidebarOpen;

  const updateSidebarState = useCallback((e: Event) => {
    const sidebarInfo: LayoutChangeEventDetail = (e as LayoutChangeEvent)
      .detail;
    const layout = sidebarInfo.sidebarLayout;

    setSidebarOpen(layout.expanded);
    setSidebarWidth(layout.width);
  }, []);

  // Make room for the sidebar at the right of the app layout when applicable.
  // Otherwise, provide some room for the sidebar's controls. Padding is used
  // here (versus margin) because it is part of an element's dimensions
  // (`clientWidth`) and thus easier to compute with.
  useEffect(() => {
    if (sideBySideActive) {
      // prettier-ignore
      container.style.paddingRight = `${
        sidebarWidth - (TOOLBAR_WIDTH / 2)
      }px`;
    } else {
      container.style.paddingRight = `${TOOLBAR_WIDTH}px`;
    }
  }, [container, sidebarWidth, sideBySideActive]);

  useEffect(() => {
    const onResize = () => {
      setSufficientSpace(container.clientWidth >= SIDEBYSIDE_THRESHOLD);
    };

    document.body.addEventListener(
      'hypothesis:layoutchange',
      updateSidebarState,
    );
    window.addEventListener('resize', onResize);
    return () => {
      document.body.removeEventListener(
        'hypothesis:layoutchange',
        updateSidebarState,
      );
      window.removeEventListener('resize', onResize);
    };
  }, [container, updateSidebarState]);

  return sideBySideActive;
}
