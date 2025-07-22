import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faXmark, faMagnifyingGlass } from '@fortawesome/free-solid-svg-icons';
import './search-bar.css';

export default function SearchBar({
  inputValue = '',
  placeholder = 'Enter a query',
  loading = false,
  handleChange,
  handleSubmit,
}: {
  inputValue: string;
  placeholder?: string;
  loading?: boolean;
  handleChange: (newValue: string) => void;
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form onSubmit={handleSubmit} className='search-bar-form'>
      {/* Search Icon */}
      <FontAwesomeIcon
        icon={faMagnifyingGlass}
        color='#8A8F98'
        className='search-bar-icon'
        width={22}
        height={22}
        size='lg'
      />
      {/* Input */}
      <input
        value={inputValue}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={placeholder}
        className='search-bar-input'
      />
      {/* Clear Button */}
      {inputValue.length > 0 && !loading && (
        <button
          type='button'
          onClick={() => handleChange('')}
          className='search-bar-clear-button'
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
