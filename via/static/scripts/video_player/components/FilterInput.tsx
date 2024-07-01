import { CancelIcon, IconButton, Input } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { Ref } from 'preact';

export type FilterInputProps = {
  elementRef: Ref<HTMLElement | undefined>;
  setFilter: (filter: string) => void;
  filter: string;
};

export default function FilterInput({
  elementRef,
  setFilter,
  filter,
}: FilterInputProps) {
  return (
    <div className="relative">
      <Input
        data-testid="filter-input"
        aria-label="Transcript filter"
        classes={classnames(
          // Match height of search input in sidebar
          'h-[32px]',
          // Extra padding right to prevent text and "clear" button overlapping
          'pr-8',
        )}
        elementRef={elementRef}
        onKeyUp={e => {
          // Allow user to easily remove focus from search input.
          if (e.key === 'Escape') {
            (e.target as HTMLElement).blur();
          }
        }}
        onInput={e => setFilter((e.target as HTMLInputElement).value)}
        placeholder="Search..."
        value={filter}
      />
      {filter && (
        <IconButton
          icon={CancelIcon}
          data-testid="clear-filter-button"
          title="Clear filter"
          onClick={() => setFilter('')}
          // Center button vertically within input. Note the button size will be
          // larger on touch devices.
          classes="absolute right-0 top-[50%] translate-y-[-50%]"
        />
      )}
    </div>
  );
}
