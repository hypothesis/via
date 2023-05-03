/**
 * Load the YouTube IFrame Player API.
 *
 * See https://developers.google.com/youtube/iframe_api_reference.
 */
export async function loadYouTubeIFrameAPI(
  scriptSrc = 'https://www.youtube.com/iframe_api'
): Promise<typeof window.YT> {
  if (typeof window.YT?.Player === 'function') {
    return window.YT;
  }

  const scriptEl = document.createElement('script');
  scriptEl.src = scriptSrc;

  return new Promise<typeof window.YT>(resolve => {
    scriptEl.addEventListener('load', () => {
      // @ts-expect-error - The `ready` callback is missing from YT types.
      window.YT.ready(() => resolve(window.YT));
    });
    document.body.append(scriptEl);
  });
}
