import 'focus-visible';
import { render } from 'preact';
// Enable debugging checks and devtools. Removed in prod builds by Rollup config.
import 'preact/debug';

import VideoPlayerApp from './components/VideoPlayerApp';
import { readConfig } from './config';

export function init() {
  const rootEl = document.querySelector('#app');
  if (!rootEl) {
    throw new Error('Container element not found');
  }

  const {
    client_config: clientConfig,
    client_src: clientSrc,
    transcript,
    video_id: videoId,
  } = readConfig();

  render(
    <VideoPlayerApp
      videoId={videoId}
      clientConfig={clientConfig}
      clientSrc={clientSrc}
      transcript={transcript}
    />,
    rootEl
  );
}

init();