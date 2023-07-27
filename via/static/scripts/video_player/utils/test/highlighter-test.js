import { TextHighlighter } from '../highlighter';

describe('TextHighlighter', () => {
  const highlightName = 'test-highlight';

  let highlighters;

  let container;
  beforeEach(() => {
    container = document.createElement('div');
    container.innerHTML = 'Foo <b>bar</b> baz';
    highlighters = [];
  });

  afterEach(() => {
    highlighters.forEach(h => h.dispose());
  });

  function createHighlighter() {
    const highlighter = new TextHighlighter(highlightName);
    highlighters.push(highlighter);
    return highlighter;
  }

  if (CSS.highlights) {
    context('when CSS highlights are supported', () => {
      describe('#highlightSpans', () => {
        it('adds ranges to CSS highlight', () => {
          const highlighter = createHighlighter();
          highlighter.highlightSpans(container, [
            { start: 0, end: 3 },
            { start: 8, end: 11 },
            { start: 20, end: 25 }, // Invalid offset
          ]);
          const highlight = CSS.highlights.get(highlightName);
          const ranges = [...highlight.keys()];
          assert.equal(ranges.length, 2);
          assert.equal(ranges[0].toString(), 'Foo');
          assert.equal(ranges[1].toString(), 'baz');
        });
      });

      describe('#removeHighlights', () => {
        it('removes ranges from CSS highlight', () => {
          const highlighter = createHighlighter();
          highlighter.highlightSpans(container, [
            { start: 0, end: 3 },
            { start: 8, end: 11 },
          ]);
          const highlight = CSS.highlights.get(highlightName);
          assert.equal(highlight.size, 2);

          highlighter.removeHighlights(container);

          assert.equal(highlight.size, 0);
        });

        it('does nothing if there are no highlights for the element', () => {
          const highlighter = createHighlighter();
          highlighter.removeHighlights(container);
        });
      });
    });
  }

  context('when CSS highlights are not supported', () => {
    let highlightsStub;
    beforeEach(() => {
      highlightsStub = sinon.stub(CSS, 'highlights').get(() => null);
    });

    afterEach(() => {
      highlightsStub.restore();
    });

    describe('#highlightSpans', () => {
      it('wraps spans in `<mark>` elements', () => {
        const highlighter = createHighlighter();
        highlighter.highlightSpans(container, [
          { start: 0, end: 3 },
          { start: 8, end: 11 },
        ]);
        assert.equal(
          container.innerHTML,
          `<mark class="${highlightName}">Foo</mark> <b>bar</b> <mark class="${highlightName}">baz</mark>`
        );
      });
    });

    describe('#removeHighlights', () => {
      it('removes `<mark>` elements', () => {
        const originalContent = container.innerHTML;

        const highlighter = createHighlighter();
        highlighter.highlightSpans(container, [
          { start: 0, end: 3 },
          { start: 8, end: 11 },
        ]);
        assert.notEqual(container.innerHTML, originalContent);

        highlighter.removeHighlights(container);
        assert.equal(container.innerHTML, originalContent);
      });
    });
  });
});
