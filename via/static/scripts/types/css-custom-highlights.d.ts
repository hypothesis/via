// Types for the CSS Custom Highlight API.
//
// See https://developer.mozilla.org/en-US/docs/Web/API/CSS_Custom_Highlight_API.

declare class Highlight {
  constructor(...ranges: Range[]);
  add(r: Range): void;
  delete(r: Range): void;
}

interface HighlightsRegistry {
  delete(name: string): void;
  get(name: string): Highlight | undefined;
  set(name: string, highlight: Highlight): void;
}

declare namespace CSS {
  let highlights: HighlightsRegistry;
}
