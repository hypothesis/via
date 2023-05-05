import 'focus-visible';
import { render } from 'preact';
// Enable debugging checks and devtools. Removed in prod builds by Rollup config.
import 'preact/debug';

import type { TranscriptData } from './components/Transcript';
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

    // Ignored until backend is able to provide real transcript data.
    // transcript,

    video_id: videoId,
  } = readConfig();

  // Generate fake transcript for testing.
  const transcript: TranscriptData = { segments: [] };
  for (let i = 0; i < 20; i++) {
    transcript.segments.push({
      isCurrent: false,
      time: i * 15,
      text: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
    });
  }

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
