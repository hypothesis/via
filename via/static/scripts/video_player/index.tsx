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
    player,
    video_id: videoId,
    video_src: videoURL,
  } = readConfig();

  // When content is displayed in an iframe, notify top-level of title and
  // location. This also acts to tell the top-level frame that we finished
  // loading. See proxy.html.jinja2.
  if (window !== window.top) {
    const canonicalLink = document.querySelector('link[rel=canonical]') as
      | HTMLLinkElement
      | undefined;
    const documentURL = canonicalLink?.href ?? document.location.href;
    window.parent.postMessage(
      {
        type: 'metadatachange',
        metadata: {
          location: documentURL,
          title: document.title,
        },
      },
      '*'
    );
  }

  render(
    <VideoPlayerApp
      videoId={videoId}
      videoURL={videoURL}
      clientConfig={clientConfig}
      clientSrc={clientSrc}
      player={player}
      transcriptSource={api.transcript}
    />,
    rootEl
  );
}

init();
