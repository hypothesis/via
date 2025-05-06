import { readConfig } from '../config';

describe('readConfig', () => {
  let element;

  function createConfigElement(content) {
    element = document.createElement('script');

    element.type = 'application/json';
    element.className = 'js-config';
    element.textContent = content;

    document.body.appendChild(element);
  }

  afterEach(() => {
    element?.remove();
  });

  it('throws when a config element is not found', () => {
    let error;

    try {
      readConfig();
    } catch (e) {
      error = e;
    }

    assert.equal(
      error?.message,
      'No config object found for selector ".js-config"',
    );
  });

  it('throws if the config element does not contain valid JSON', () => {
    createConfigElement('');

    let error;

    try {
      readConfig();
    } catch (e) {
      error = e;
    }

    assert.equal(error?.message, 'Failed to parse frontend configuration');
  });

  it('parses config body as JSON', () => {
    const config = { foo: ['bar'] };

    createConfigElement(JSON.stringify(config));
    assert.deepEqual(readConfig(), config);
  });
});
