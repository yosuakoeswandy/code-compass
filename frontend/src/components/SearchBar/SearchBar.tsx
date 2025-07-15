import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faXmark, faMagnifyingGlass } from '@fortawesome/free-solid-svg-icons';
import './search-bar.css';

export default function SearchBar({
  placeholder = 'Enter a query',
  loading = false,
  onSearch,
}: {
  placeholder?: string;
  loading?: boolean;
  onSearch: (query: string) => void;
}) {
  const [value, setValue] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (value.trim()) {
      onSearch(value);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="search-bar-form">
      {/* Search Icon */}
      <FontAwesomeIcon
        icon={faMagnifyingGlass}
        color='#8A8F98'
        className="search-bar-icon"
        width={22}
        height={22}
        size='lg'
      />
      {/* Input */}
      <input
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        className="search-bar-input"
      />
      {/* Clear Button */}
      {value.length > 0 && !loading && (
        <button
          type='button'
          onClick={() => setValue('')}
          className="search-bar-clear-button"
          aria-label='Clear search input'
        >
          <FontAwesomeIcon icon={faXmark} color='#8A8F98' />
        </button>
      )}
      {/* Submit Button */}
      <button
        type='submit'
        disabled={loading}
        className={`search-bar-submit-button${loading ? ' loading' : ''}`}
      >
        Search
      </button>
    </form>
  );
}
