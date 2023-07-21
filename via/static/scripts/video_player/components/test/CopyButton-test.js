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

  it('copies transcript to clipboard when "Copy" button is pressed', async () => {
    const fakeClipboard = {
      writeText: sinon.stub().resolves(),
    };
    const clipboardStub = sinon
      .stub(navigator, 'clipboard')
      .get(() => fakeClipboard);

    try {
      const wrapper = mount(<CopyButton transcript={transcript} />);

      await wrapper.find('button[data-testid="copy-button"]').prop('onClick')();

      assert.calledWith(fakeClipboard.writeText, 'Hello\nWorld');
    } finally {
      clipboardStub.restore();
    }
  });

  it('logs a warning if accessing clipboard fails', async () => {
    const copyError = new Error('Not allowed');
    const fakeClipboard = {
      writeText: sinon.stub().rejects(copyError),
    };
    const clipboardStub = sinon
      .stub(navigator, 'clipboard')
      .get(() => fakeClipboard);
    const warnStub = sinon.stub(console, 'warn');

    try {
      const wrapper = mount(<CopyButton transcript={transcript} />);

      try {
        await wrapper
          .find('button[data-testid="copy-button"]')
          .prop('onClick')();
      } catch {
        /* ignored */
      }

      assert.calledWith(console.warn, 'Failed to copy transcript', copyError);
    } finally {
      clipboardStub.restore();
      warnStub.restore();
    }
  });
});
