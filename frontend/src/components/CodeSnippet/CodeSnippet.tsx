import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCaretDown } from '@fortawesome/free-solid-svg-icons';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { nightOwl as dark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './code-snippet.css';

export default function CodeSnippet({
  code,
  filePath,
  lineStart = 1,
}: {
  code: string;
  filePath: string;
  lineStart?: number;
}) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className='code-snippet-container'>
      {/* Header */}
      <div
        onClick={() => setExpanded((e) => !e)}
        className='code-snippet-header'
        title={expanded ? 'Collapse' : 'Expand'}
      >
        {/* File name */}
        <span className='code-snippet-filepath'>{filePath}</span>
        {/* Arrow icon */}
        <FontAwesomeIcon
          icon={faCaretDown}
          className={`code-snippet-caret${expanded ? ' expanded' : ''}`}
        />
      </div>
      {/* Code */}
      {expanded && (
        <SyntaxHighlighter
          language={filePath.split('.').pop() || 'text'}
          style={dark}
          customStyle={{}}
          showLineNumbers
          startingLineNumber={lineStart}
          lineNumberStyle={{
            color: '#7D8593',
            minWidth: '42px',
            userSelect: 'none',
            textAlign: 'right',
            paddingRight: '18px',
            fontSize: 13,
            opacity: 0.75,
            flexShrink: 0,
          }}
          className='code-snippet-code'
        >
          {code}
        </SyntaxHighlighter>
      )}
    </div>
  );
}
