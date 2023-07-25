// Shared fixtures for video player app tests.

/**
 * Configuration for video player app.
 */
export const videoPlayerConfig = {
  api: {
    transcript: {
      doc: 'Get the transcript of the current video',
      url: 'https://dummy-via.hypothes.is/api/youtube/test_video_id',
      method: 'GET',
      headers: {
        Authorization: 'Bearer FAKE_JWT_TOKEN',
      },
    },
  },
};

/**
 * Dummy response from transcript API endpoint.
 */
export const transcriptsAPIResponse = {
  data: {
    type: 'transcripts',
    id: 'test_video_id',
    attributes: {
      segments: [
        {
          text: '[Music]',
          start: 0.0,
          duration: 7.52,
        },
        {
          text: 'how many of you remember the first time',
          start: 5.6,
          duration: 4.72,
        },
      ],
    },
  },
};
