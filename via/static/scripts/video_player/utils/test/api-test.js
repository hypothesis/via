import {
  videoPlayerConfig,
  transcriptsAPIResponse,
} from '../../../test-util/video-player-fixtures';
import { APIError, callAPI } from '../api';

/**
 * Create a fake HTTP response with a given status code and JSON body.
 */
function jsonResponse(status, body = null) {
  return new Response(JSON.stringify(body), {
    status,
  });
}

describe('callAPI', () => {
  let fakeFetch;
  beforeEach(() => {
    fakeFetch = sinon.stub(window, 'fetch').resolves(jsonResponse(404));
  });

  afterEach(() => {
    window.fetch.restore();
  });

  it('calls JSON:API method and returns result', async () => {
    fakeFetch
      .withArgs(videoPlayerConfig.api.transcript.url)
      .resolves(jsonResponse(200, transcriptsAPIResponse));

    const result = await callAPI(videoPlayerConfig.api.transcript);

    assert.deepEqual(result, transcriptsAPIResponse);
  });

  it('throws exception if result is not JSON', async () => {
    fakeFetch
      .withArgs(videoPlayerConfig.api.transcript.url)
      .resolves(new Response('<b>Oh no</b>', { status: 500 }));

    let error;
    try {
      await callAPI(videoPlayerConfig.api.transcript);
    } catch (e) {
      error = e;
    }

    assert.instanceOf(error, APIError);
    assert.equal(error.status, 500);
    assert.equal(error.data, null);
    assert.equal(error.message, 'API call failed');
  });

  it('throws exception if API request fails', async () => {
    fakeFetch
      .withArgs(videoPlayerConfig.api.transcript.url)
      .resolves(jsonResponse(404));

    let error;
    try {
      await callAPI(videoPlayerConfig.api.transcript);
    } catch (e) {
      error = e;
    }

    assert.instanceOf(error, APIError);
    assert.equal(error.status, 404);
    assert.equal(error.message, 'API call failed');
  });
});
