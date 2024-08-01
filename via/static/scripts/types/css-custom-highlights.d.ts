// Types for the CSS Custom Highlight API.
//
// See https://developer.mozilla.org/en-US/docs/Web/API/CSS_Custom_Highlight_API.
//
// TypeScript's built-in types includes incomplete versions of these types.

declare interface Highlight {
  add(r: Range): void;
  delete(r: Range): void;
}

interface HighlightRegistry {
  delete(name: string): void;
  get(name: string): Highlight | undefined;
  set(name: string, highlight: Highlight): void;
}
