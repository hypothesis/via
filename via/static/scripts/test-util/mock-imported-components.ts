import type { FunctionComponent } from 'preact';

/**
 * Return true if an imported `value` "looks like" a Preact function component.
 *
 * This check can have false positives (ie. match values which are not really components).
 * That's OK because typical usage in a test is to first mock all components with
 * `$imports.$mock(mockImportedComponents())` and then mock other things with
 * `$imports.$mock(...)`. The more specific mocks will override the generic
 * component mocks.
 */
function isComponent(value: unknown) {
  return (
    typeof value === 'function' &&
    value.name.match(/^[A-Z]/) &&
    // Check that function is not an ES class. Note this only works with real
    // ES classes and may not work with ones transpiled to ES5.
    !value.toString().match(/^class\b/)
  );
}

/**
 * Return the display name of a component, minus the names of any wrappers
 * (eg. `withServices(OriginalName)` becomes `OriginalName`).
 *
 * @param component - A Preact component
 */
function getDisplayName(component: FunctionComponent): string {
  let displayName =
    component.displayName || component.name || 'UnknownComponent';

  const wrappedComponentMatch = displayName.match(/\([A-Z][A-Za-z0-9]+\)/);
  if (wrappedComponentMatch) {
    displayName = wrappedComponentMatch[0].slice(1, -1);
  }

  return displayName;
}

/**
 * Helper for use with `babel-plugin-mockable-imports` that mocks components
 * imported by a file. This will only mock components that are local to the
 * package; it will not mock external components. This is to aid in catching
 * integration issues, at the slight cost of unit isolation.
 *
 * Mocked components will have the same display name as the original component,
 * minus any wrappers (eg. `Widget` and `withServices(Widget)` both become
 * `Widget`). They will render only their children, as if they were just a
 * `Fragment`.
 *
 * @example
 *   import ComponentUnderTest, { $imports } from '../component-under-test';
 *
 *   beforeEach(() => {
 *     $imports.$mock(mockImportedComponents());
 *
 *     // Add additional mocks or overrides here.
 *   });
 *
 *   afterEach(() => {
 *     $imports.$restore();
 *   });
 *
 * @return A function that can be passed to `$imports.$mock`.
 */
export function mockImportedComponents() {
  return (source: string, symbol: string, value: unknown) => {
    if (!isComponent(value) || !source.startsWith('.')) {
      return null;
    }

    const mock = (props: any) => props.children;

    // Make it possible to do `wrapper.find('ComponentName')` where `wrapper`
    // is an Enzyme wrapper.
    mock.displayName = getDisplayName(value as FunctionComponent);

    return mock;
  };
}
