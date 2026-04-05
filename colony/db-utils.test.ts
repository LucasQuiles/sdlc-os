import { describe, it, expect } from 'vitest';
import { ColonyDbError } from './events-db.js';
import { parseJsonField, now } from './db-utils.js';

describe('parseJsonField', () => {
  it('parses valid JSON and returns the object', () => {
    const result = parseJsonField('{"key":"value"}', {});
    expect(result).toEqual({ key: 'value' });
  });

  it('parses valid JSON array', () => {
    const result = parseJsonField('["a","b"]', []);
    expect(result).toEqual(['a', 'b']);
  });

  it('returns fallback when raw is null', () => {
    const fallback = { default: true };
    expect(parseJsonField(null, fallback)).toBe(fallback);
  });

  it('returns fallback when raw is undefined', () => {
    const fallback = { default: true };
    expect(parseJsonField(undefined, fallback)).toBe(fallback);
  });

  it('returns fallback when raw is empty string', () => {
    const fallback: string[] = [];
    expect(parseJsonField('', fallback)).toBe(fallback);
  });

  it('throws ColonyDbError on invalid JSON', () => {
    expect(() => parseJsonField('{not json}', {})).toThrow(ColonyDbError);
  });

  it('includes a truncated preview of the bad value in the error message', () => {
    try {
      parseJsonField('{bad', {});
      expect.fail('should have thrown');
    } catch (err) {
      expect(err).toBeInstanceOf(ColonyDbError);
      expect((err as ColonyDbError).message).toContain('{bad');
    }
  });
});

describe('now', () => {
  it('returns a valid ISO 8601 timestamp', () => {
    const ts = now();
    expect(() => new Date(ts)).not.toThrow();
    expect(ts).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
  });
});
