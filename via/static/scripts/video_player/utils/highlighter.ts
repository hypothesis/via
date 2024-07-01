/**
 * Resolve one or more character offsets within an element to (text node,
 * position) pairs.
 *
 * This function was copied from the Hypothesis client.
 *
 * @param element
 * @param offsets - Offsets, which must be sorted in ascending order
 * @throws {RangeError}
 */
export function resolveOffsets(
  element: Element,
  ...offsets: number[]
): Array<{ node: Text; offset: number }> {
  let nextOffset = offsets.shift();
  const nodeIter = element.ownerDocument.createNodeIterator(
    element,
    NodeFilter.SHOW_TEXT,
  );
  const results = [];

  let currentNode = nodeIter.nextNode() as Text | null;
  let textNode;
  let length = 0;

  // Find the text node containing the `nextOffset`th character from the start
  // of `element`.
  while (nextOffset !== undefined && currentNode) {
    textNode = currentNode;
    if (length + textNode.data.length > nextOffset) {
      results.push({ node: textNode, offset: nextOffset - length });
      nextOffset = offsets.shift();
    } else {
      currentNode = nodeIter.nextNode() as Text | null;
      length += textNode.data.length;
    }
  }

  // Boundary case.
  while (nextOffset !== undefined && textNode && length === nextOffset) {
    results.push({ node: textNode, offset: textNode.data.length });
    nextOffset = offsets.shift();
  }

  if (nextOffset !== undefined) {
    throw new RangeError('Offset exceeds text length');
  }

  return results;
}

/**
 * Highlight spans of text content within elements.
 *
 * This uses CSS Custom Highlights if supported or falls back to wrapping text
 * in `<mark>` elements otherwise.
 *
 * NOTE: If using this with an element rendered by Preact, the element's content
 * should either be a single immutable text child, or it should be managed
 * manually, to avoid Preact's re-rendering conflicting with DOM modifications
 * from the highlighter.
 */
export class TextHighlighter {
  public highlight?: Highlight;
  private name: string;
  private _ranges: Map<HTMLElement, Range[]>;

  /**
   * @param name -
   *   Name of the highlight to register in {@link CSS.highlights}. This is
   *   referenced when styling the highlight via `::highlight(<name>)`
   *   selectors. For browsers that don't support CSS Custom Highlights, this
   *   is used as a class name on the `<mark>` elements.
   */
  constructor(name: string) {
    this.name = name;
    this._ranges = new Map();

    if (CSS.highlights) {
      let highlight = CSS.highlights.get(name);
      if (!highlight) {
        highlight = new Highlight();
        CSS.highlights.set(name, highlight);
      }
      this.highlight = highlight;
    }
  }

  /** Remove all highlights created by this highlighter. */
  dispose() {
    for (const element of this._ranges.keys()) {
      this.removeHighlights(element);
    }
  }

  /**
   * Highlight spans of text within `element`.
   */
  highlightSpans(
    element: HTMLElement,
    spans: Array<{ start: number; end: number }>,
  ) {
    let ranges = this._ranges.get(element);
    if (!ranges) {
      ranges = [];
      this._ranges.set(element, ranges);
    }

    for (const { start, end } of spans) {
      try {
        const [startPoint, endPoint] = resolveOffsets(element, start, end);
        const range = new Range();
        range.setStart(startPoint.node, startPoint.offset);
        range.setEnd(endPoint.node, endPoint.offset);
        ranges.push(range);

        if (this.highlight) {
          this.highlight.add(range);
        } else {
          // Fall back to `<mark>` elements. This is probably more expensive
          // since it involves DOM modifications.
          const highlightEl = document.createElement('mark');
          highlightEl.className = this.name;
          range.surroundContents(highlightEl);
        }
      } catch {
        // If we can't find the span to highlight, we just silently skip it.
      }
    }
  }

  /**
   * Remove all highlights that this highlighter has created in `element`.
   */
  removeHighlights(element: HTMLElement) {
    const ranges = this._ranges.get(element);
    if (!ranges) {
      return;
    }
    if (this.highlight) {
      for (const range of ranges) {
        this.highlight.delete(range);
      }
    } else {
      const marks = Array.from(element.querySelectorAll('mark'));
      for (const mark of marks) {
        mark.replaceWith(mark.textContent!);
      }
      // Join adjacent text nodes.
      element.normalize();
    }
    ranges.splice(ranges.length);
  }
}
