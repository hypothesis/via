import { formatTimestamp } from '../time';

describe('formatTimestamp', () => {
  [
    // Times under one hour
    [30, '0:30'],
    [96, '1:36'],
    [96.35, '1:36'],
    [620, '10:20'],
    [59 * 60 + 59, '59:59'],

    // Times >= one hour
    [60 * 60, '1:00:00'],
    [60 * 60 + 123, '1:02:03'],
    [10 * 60 * 60, '10:00:00'],
    [100 * 60 * 60, '100:00:00'],
  ].forEach(([value, expected]) => {
    it('formats durations as digits', () => {
      assert.equal(formatTimestamp(value), expected);
    });
  });

  [
    // Times under one minute.
    [0, '0 seconds'],
    [1, '1 second'],
    [30, '30 seconds'],
    [59, '59 seconds'],
    // Times >= one minute. These only have a seconds component if non-zero.
    [60, '1 minute'],
    [96, '1 minute, 36 seconds'],
    [620, '10 minutes, 20 seconds'],
    [59 * 60 + 59, '59 minutes, 59 seconds'],
    // Times >= one hour. These only have minutes and seconds components if
    // non-zero.
    [60 * 60, '1 hour'],
    [60 * 60 + 123, '1 hour, 2 minutes, 3 seconds'],
    [10 * 60 * 60, '10 hours'],
    [100 * 60 * 60, '100 hours'],
  ].forEach(([value, expected]) => {
    it('formats durations as descriptions', () => {
      assert.equal(formatTimestamp(value, 'description'), expected);
    });
  });

  [NaN, -1, Infinity].forEach(value => {
    it('formats invalid timestamps', () => {
      assert.equal(formatTimestamp(value, 'digits'), '');
      assert.equal(formatTimestamp(value, 'description'), '');
    });
  });
});
