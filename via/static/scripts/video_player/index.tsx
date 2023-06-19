import 'focus-visible';
import { render } from 'preact';
// Enable debugging checks and devtools. Removed in prod builds by Rollup config.
import 'preact/debug';

import VideoPlayerApp from './components/VideoPlayerApp';
import { readConfig } from './config';
import { sampleTranscript } from './sample-transcript';
import type { TranscriptData } from './utils/transcript';
import { mergeSegments } from './utils/transcript';

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

  // Pre-fetched transcript for testing. From the video
  // https://www.youtube.com/watch?v=x8TO-nrUtSI.
  const transcript: TranscriptData = { segments: sampleTranscript };

  // Group segments together for better readability.
  transcript.segments = mergeSegments(transcript.segments, 3);

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
