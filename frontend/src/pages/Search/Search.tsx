import { useState } from 'react';
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

export default function Search() {
  const [loading, setLoading] = useState(false);
  const [snippets, setSnippets] = useState<SearchResponse[]>([]);

  const baseUrl = import.meta.env.VITE_API_URL;
  const collection_name = 'full_stack_fastapi_template';

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

  return (
    <div>
      <SearchBar loading={loading} onSearch={onSearch} />
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
