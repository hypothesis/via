import { mount } from 'enzyme';

import { APIError } from '../../utils/api';
import TranscriptError from '../TranscriptError';

describe('TranscriptError', () => {
  it('displays just `Error.message` if there are no error details', () => {
    const wrapper = mount(
      <TranscriptError error={new Error('Something went wrong')} />
    );
    assert.equal(
      wrapper.text(),
      ['Unable to load transcript', 'Something went wrong'].join('')
    );
  });

  it('displays `APIError.error.title` field if present', () => {
    const error = new APIError(404, {
      code: 'VideoNotFound',
      title: 'The video was not found',
      detail: 'Some long details here',
    });
    const wrapper = mount(<TranscriptError error={error} />);
    assert.equal(
      wrapper.text(),
      [
        'Unable to load transcript',
        'The video was not found',
        'Error details:Some long details here',
      ].join('')
    );
  });
});
