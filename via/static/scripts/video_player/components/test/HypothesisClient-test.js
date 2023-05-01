import { mount } from 'enzyme';

import HypothesisClient from '../HypothesisClient';

describe('HypothesisClient', () => {
  it('adds Hypothesis client and configuration to page', () => {
    const config = { openSidebar: true };
    const wrapper = mount(
      <HypothesisClient src="https://hypothes.is/embed.js" config={config} />
    );
    assert.isTrue(wrapper.exists('script[src="https://hypothes.is/embed.js"]'));

    const configScript = wrapper.find('script.js-hypothesis-config');
    assert.isTrue(configScript.exists());
    assert.equal(configScript.text(), JSON.stringify(config));
  });
});
