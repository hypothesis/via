import { mount } from 'enzyme';

import CopyButton from '../CopyButton';

describe('CopyButton', () => {
  const transcript = {
    segments: [
      {
        start: 0,
        text: 'Hello',
      },
      {
        start: 5,
        text: 'World',
      },
    ],
  };
  let fakeAppendToastMessage;

  beforeEach(() => {
    fakeAppendToastMessage = sinon.stub();
  });

  const createWrapper = () =>
    mount(
      <CopyButton
        transcript={transcript}
        appendToastMessage={fakeAppendToastMessage}
      />
    );

  it('copies transcript to clipboard when "Copy" button is pressed', async () => {
    const fakeClipboard = {
      writeText: sinon.stub().resolves(),
    };
    const clipboardStub = sinon
      .stub(navigator, 'clipboard')
      .get(() => fakeClipboard);

    try {
      const wrapper = createWrapper();

      await wrapper.find('button[data-testid="copy-button"]').prop('onClick')();

      assert.calledWith(fakeClipboard.writeText, 'Hello\nWorld');
      assert.calledWith(fakeAppendToastMessage, {
        type: 'success',
        message: 'Transcript copied',
      });
    } finally {
      clipboardStub.restore();
    }
  });

  it('appends toast message if accessing clipboard fails', async () => {
    const copyError = new Error('Not allowed');
    const fakeClipboard = {
      writeText: sinon.stub().rejects(copyError),
    };
    const clipboardStub = sinon
      .stub(navigator, 'clipboard')
      .get(() => fakeClipboard);

    try {
      const wrapper = createWrapper();

      try {
        await wrapper
          .find('button[data-testid="copy-button"]')
          .prop('onClick')();
      } catch {
        /* ignored */
      }

      assert.calledWith(fakeAppendToastMessage, {
        type: 'error',
        message: 'Failed to copy transcript',
      });
    } finally {
      clipboardStub.restore();
    }
  });
});
