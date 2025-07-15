import CodeSnippet from '../CodeSnippet/CodeSnippet';
import './code-snippet-list.css';

type Snippet = {
  id: string;
  fileName: string;
  code: string;
  lineStart?: number;
};

export default function CodeSnippetList({ snippets }: { snippets: Snippet[] }) {
  return (
    <div className="code-snippet-list-container">
      {snippets.map((snippet) => (
        <CodeSnippet
          key={snippet.id}
          fileName={snippet.fileName}
          code={snippet.code}
          lineStart={snippet.lineStart}
        />
      ))}
    </div>
  );
}
