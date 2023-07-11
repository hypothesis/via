import { mount } from 'enzyme';

import HypothesisClient from '../HypothesisClient';

describe('HypothesisClient', () => {
  beforeEach(() => {
    delete window.hypothesisConfig;
  });

  it('adds Hypothesis client and configuration to page', () => {
    const config = { openSidebar: true };
    const wrapper = mount(
      <HypothesisClient src="https://hypothes.is/embed.js" config={config} />
    );
    assert.isTrue(wrapper.exists('script[src="https://hypothes.is/embed.js"]'));

    assert.isFunction(window.hypothesisConfig);
    assert.equal(window.hypothesisConfig(), config);
  });
});
