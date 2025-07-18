import CodeSnippet from '../CodeSnippet/CodeSnippet';
import './code-snippet-list.css';

type Snippet = {
  id: string;
  filePath: string;
  code: string;
  lineStart?: number;
};

export default function CodeSnippetList({ snippets }: { snippets: Snippet[] }) {
  return (
    <div className="code-snippet-list-container">
      {snippets.map((snippet) => (
        <CodeSnippet
          key={snippet.id}
          filePath={snippet.filePath}
          code={snippet.code}
          lineStart={snippet.lineStart}
        />
      ))}
    </div>
  );
}
