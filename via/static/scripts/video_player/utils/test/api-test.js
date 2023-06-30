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

  context('when request fails', () => {
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
      assert.isUndefined(error.error);
      assert.equal(error.message, 'API call failed');
    });

    [{}, { errors: [] }].forEach(responseBody => {
      it('throws exception without `error` if `errors` field is missing or empty', async () => {
        fakeFetch
          .withArgs(videoPlayerConfig.api.transcript.url)
          .resolves(jsonResponse(404, responseBody));

        let error;
        try {
          await callAPI(videoPlayerConfig.api.transcript);
        } catch (e) {
          error = e;
        }

        assert.instanceOf(error, APIError);
        assert.isUndefined(error.error);
        assert.equal(error.status, 404);
        assert.equal(error.message, 'API call failed');
      });
    });

    it('throws exception with `error` if `errors` field is present', async () => {
      const responseBody = {
        errors: [
          {
            code: 'VideoNotFound',
            title: 'This video does not exist',
            detail: 'Video ID is invalid',
          },
        ],
      };

      fakeFetch
        .withArgs(videoPlayerConfig.api.transcript.url)
        .resolves(jsonResponse(404, responseBody));

      let error;
      try {
        await callAPI(videoPlayerConfig.api.transcript);
      } catch (e) {
        error = e;
      }

      assert.instanceOf(error, APIError);
      assert.deepEqual(error.error, responseBody.errors[0]);
      assert.equal(error.status, 404);
      assert.equal(error.message, 'API call failed');
    });
  });
});
