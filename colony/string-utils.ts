/** Escape regex metacharacters in a string for use in RegExp constructors. */
export function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
