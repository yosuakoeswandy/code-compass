import { useEffect, useState } from 'react';
import SearchBar from '../../components/SearchBar/SearchBar';
import CodeSnippetList from '../../components/CodeSnippetList/CodeSnippetList';
import axios from 'axios';
import './search.css';

interface SearchRequest {
  query: string;
}

interface SearchResponse {
  id: string;
  filePath: string;
  fileName: string;
  content: string;
  lineStart: number;
  lineEnd: number;
  vectorScore: number;
}

const suggestions = [
  'Show me the API endpoint for creating a new user',
  'Is there a confirmation dialog when deleting an item?',
  'What is the default limit when getting users?',
];

export default function Search() {
  const [loading, setLoading] = useState(false);
  const [snippets, setSnippets] = useState<SearchResponse[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [suggestionIndex, setSuggestionIndex] = useState(0);
  const [showSuggestion, setShowSuggestion] = useState(true);

  const baseUrl = import.meta.env.VITE_API_URL;
  const collection_name = 'full_stack_fastapi_template';

  useEffect(() => {
    const interval = setInterval(() => {
      setShowSuggestion(false);
      setTimeout(() => {
        setSuggestionIndex((prev) => (prev + 1) % suggestions.length);
        setShowSuggestion(true);
      }, 500); // 500ms for fade out and fade in
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const onSearch = async (query: string) => {
    try {
      setLoading(true);
      const response = await axios.post<SearchResponse[]>(
        `${baseUrl}/collections/${encodeURIComponent(collection_name)}/search`,
        {
          query: query,
          queryType: 'hybrid',
        } as SearchRequest
      );
      setSnippets(response.data);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSearch(inputValue);
    }
  };

  const handleChange = (newValue: string) => {
    setInputValue(newValue);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion);
    onSearch(suggestion);
  };

  return (
    <div>
      <SearchBar
        loading={loading}
        inputValue={inputValue}
        handleChange={handleChange}
        handleSubmit={handleSubmit}
      />
      {!loading && snippets.length === 0 && (
        <div className='suggestions-row'>
          <span>Try this query:</span>
          <button
            className={`suggestion-btn suggestion-fade${
              showSuggestion ? ' visible' : ''
            }`}
            onClick={() => handleSuggestionClick(suggestions[suggestionIndex])}
          >
            {suggestions[suggestionIndex]}
          </button>
        </div>
      )}
      {loading ? (
        <div className='loading-data'>
          <p>Fetching data...</p>
        </div>
      ) : (
        <CodeSnippetList
          snippets={snippets.map((snippet) => ({
            id: snippet.id,
            code: snippet.content,
            filePath: snippet.filePath,
            lineStart: snippet.lineStart,
          }))}
        />
      )}
    </div>
  );
}
