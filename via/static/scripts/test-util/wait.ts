/**
 * Wait for a condition to evaluate to a truthy value.
 *
 * @return result of the `condition` function
 */
export async function waitFor<T>(
  condition: () => T,
  timeout = 10,
  what = condition.toString()
): Promise<T> {
  const result = condition();
  if (result) {
    return result;
  }

  const start = Date.now();

  return new Promise((resolve, reject) => {
    const timer = setInterval(() => {
      const result = condition();
      if (result) {
        clearTimeout(timer);
        resolve(result);
      }
      if (Date.now() - start > timeout) {
        clearTimeout(timer);
        reject(new Error(`waitFor(${what}) failed after ${timeout} ms`));
      }
    });
  });
}

export function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
