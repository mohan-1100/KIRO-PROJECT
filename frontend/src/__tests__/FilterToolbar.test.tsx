import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

function FilterToolbar({ types, onFilter }: { types: string[]; onFilter: (t: string) => void }) {
  return (
    <select aria-label="Filter by type" onChange={e => onFilter(e.target.value)} defaultValue="">
      <option value="">All</option>
      {types.map(t => <option key={t} value={t}>{t}</option>)}
    </select>
  );
}

describe('FilterToolbar', () => {
  it('fires onFilter when a type is selected', () => {
    const onFilter = vi.fn();
    render(<FilterToolbar types={['database','api_service']} onFilter={onFilter} />);
    const select = screen.getByLabelText('Filter by type');
    fireEvent.change(select, { target: { value: 'database' } });
    expect(onFilter).toHaveBeenCalledWith('database');
  });
});
