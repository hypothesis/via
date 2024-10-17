import type { APIMethod } from './utils/api';

/** Directory of available API methods. */
export type APIIndex = {
  transcript: APIMethod;
};

export type ConfigObject = {
  /** ID of the YouTube video to load. */
  video_id?: string;

  /** Configuration for the Hypothesis client. */
  client_config: object;

  /** URL of the Hypothesis client to load. */
  client_src: string;

  /** Frontend player to use. */
  player: 'youtube' | 'html-video';

  /** URL for use with an HTML `<video>` element. */
  video_src?: string;

  /** API index. */
  api: APIIndex;

  /** Whether to enable download controls for the video. */
  allow_download?: boolean;
};

/**
 * Read frontend app configuration from a JSON `<script>` tag in the page
 * matching the selector ".js-config".
 */
export function readConfig(): ConfigObject {
  const selector = '.js-config';
  const configEl = document.querySelector(selector);

  if (!configEl) {
    throw new Error(`No config object found for selector "${selector}"`);
  }

  try {
    const config = JSON.parse(configEl.textContent!);
    return config;
  } catch {
    throw new Error('Failed to parse frontend configuration');
  }
}
