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
    api,
    client_config: clientConfig,
    client_src: clientSrc,
    video_id: videoId,
  } = readConfig();

  // When content is displayed in an iframe, notify top-level of title and
  // location. This also acts to tell the top-level frame that we finished
  // loading. See proxy.html.jinja2.
  if (window !== window.top) {
    window.parent.postMessage(
      {
        type: 'metadatachange',
        metadata: {
          // TODO: Once https://github.com/hypothesis/via/pull/1015 lands,
          // get the URL from `link[rel=canonical]` or pass the video URL as
          // config.
          location: `https://www.youtube.com/watch?v=${encodeURIComponent(
            videoId
          )}`,
          title: document.title,
        },
      },
      '*'
    );
  }

  render(
    <VideoPlayerApp
      videoId={videoId}
      clientConfig={clientConfig}
      clientSrc={clientSrc}
      transcriptSource={api.transcript}
    />,
    rootEl
  );
}

init();
