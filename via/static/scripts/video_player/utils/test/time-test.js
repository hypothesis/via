import { formatTimestamp } from '../time';

describe('formatTimestamp', () => {
  it('formats durations under one hour as m:ss', () => {
    assert.equal(formatTimestamp(30), '0:30');
    assert.equal(formatTimestamp(96), '1:36');
    assert.equal(formatTimestamp(96.35), '1:36');
    assert.equal(formatTimestamp(620), '10:20');
    assert.equal(formatTimestamp(59 * 60 + 59), '59:59');
  });

  it('formats durations over one hour as h:mm:ss', () => {
    assert.equal(formatTimestamp(60 * 60), '1:00:00');
    assert.equal(formatTimestamp(60 * 60 + 123), '1:02:03');
    assert.equal(formatTimestamp(10 * 60 * 60), '10:00:00');
    assert.equal(formatTimestamp(100 * 60 * 60), '100:00:00');
  });

  it('formats invalid timestamps', () => {
    assert.equal(formatTimestamp(NaN), '');
    assert.equal(formatTimestamp(-1), '');
    assert.equal(formatTimestamp(Infinity), '');
  });
});
