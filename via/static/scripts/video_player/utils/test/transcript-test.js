import { sampleTranscript } from '../../sample-transcript';
import { filterTranscript, formatTranscript } from '../transcript';

describe('filterTranscript', () => {
  it('returns matching segments and offsets', () => {
    const query = 'Nintendo 64';

    const segmentMatches = filterTranscript(sampleTranscript, query);

    assert.equal(segmentMatches.size, 5);
    for (const [index, matches] of segmentMatches.entries()) {
      const text = sampleTranscript[index].text;
      assert.include(text.toLowerCase(), query.toLowerCase());
      assert.notEqual(matches.length, 0);
      for (const { start, end } of matches) {
        assert.equal(text.slice(start, end).toLowerCase(), query.toLowerCase());
      }
    }
  });
});

describe('formatTranscript', () => {
  it('concatenates text from segments', () => {
    const shortTranscript = sampleTranscript.slice(0, 3);
    const formatted = formatTranscript(shortTranscript);
    assert.equal(
      formatted,
      `
[Music]
how many of you remember the first time
you saw a playstation 1 game if you were
`.trim()
    );
  });
});
