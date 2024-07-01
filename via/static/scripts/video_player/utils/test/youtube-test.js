import { loadYouTubeIFrameAPI } from '../youtube';

describe('loadYouTubeIFrameAPI', () => {
  afterEach(() => {
    delete window.YT;
  });

  function loadPlayerAPI() {
    window.YT = {
      ready: callback => setTimeout(() => callback(), 0),
      Player: sinon.stub(),
    };
    return window.YT;
  }

  it('adds YouTube IFrame API script to page', async () => {
    const scriptURL = URL.createObjectURL(
      new Blob([], { type: 'text/javascript' }),
    );
    const YT = loadYouTubeIFrameAPI(scriptURL.toString());

    // Simulate script setting `window.YT`.
    loadPlayerAPI();

    assert.equal(await YT, window.YT);
  });

  it('returns immediately if IFrame API already loaded', async () => {
    loadPlayerAPI();

    const scriptURL = URL.createObjectURL(
      new Blob([], { type: 'text/javascript' }),
    );
    const YT = await loadYouTubeIFrameAPI(scriptURL.toString());
    assert.equal(await YT, window.YT);
  });
});
