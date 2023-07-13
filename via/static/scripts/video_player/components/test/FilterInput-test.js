import { mount } from 'enzyme';
import { createRef } from 'preact';

import FilterInput from '../FilterInput';

describe('FilterInput', () => {
  let fakeSetFilter;

  beforeEach(() => {
    fakeSetFilter = sinon.stub();
  });

  const createFilterInput = (filter = '') =>
    mount(
      <FilterInput
        filter={filter}
        setFilter={fakeSetFilter}
        elementRef={createRef()}
      />
    );

  it('sets initial filter', () => {
    const initialFilter = 'foobar';
    const wrapper = createFilterInput(initialFilter);

    assert.equal(wrapper.find('Input').prop('value'), initialFilter);
  });

  it('invokes setFilter when input changes', () => {
    const wrapper = createFilterInput();
    const input = wrapper.find('input[data-testid="filter-input"]');

    input.getDOMNode().value = 'new filter';
    input.simulate('input');

    assert.calledWith(fakeSetFilter, 'new filter');
  });

  it('displays clear button when filter is not empty', () => {
    const wrapper = createFilterInput('not empty');
    const clearButtonSelector = 'button[data-testid="clear-filter-button"]';

    assert.isTrue(wrapper.exists(clearButtonSelector));
  });

  it('does not display clear button when filter is empty', () => {
    const wrapper = createFilterInput();
    const clearButtonSelector = 'button[data-testid="clear-filter-button"]';

    assert.isFalse(wrapper.exists(clearButtonSelector));
  });

  it('clears filter when clear button is pressed', () => {
    const wrapper = createFilterInput('foobar');
    const clearButtonSelector = 'button[data-testid="clear-filter-button"]';

    const clearButton = wrapper.find(clearButtonSelector);
    clearButton.simulate('click');

    assert.calledWith(fakeSetFilter, '');
  });
});
