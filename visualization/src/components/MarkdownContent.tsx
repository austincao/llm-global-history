import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

/** Render assistant markdown (bold, lists, headings) safely. */
export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  return (
    <div className={`gh-markdown ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
          strong: ({ children }) => <strong className="font-semibold text-[#2c1810]">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
          ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          h1: ({ children }) => <h4 className="font-bold text-base mt-2 mb-1">{children}</h4>,
          h2: ({ children }) => <h4 className="font-bold text-sm mt-2 mb-1">{children}</h4>,
          h3: ({ children }) => <h4 className="font-semibold text-sm mt-2 mb-1">{children}</h4>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
