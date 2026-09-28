import { useEffect, useRef, useState } from 'react';
import type { ChatCitation } from './ChatView';

export interface ContextParagraph {
  id: string;
  chapter_index: number;
  paragraph_index: number;
  part_title_cn: string;
  title_cn: string;
  era: string;
  text: string;
  segment_start_time_raw?: string | null;
}

interface CitationReaderProps {
  citation: ChatCitation | null;
  onJumpToChapter?: (chapterIndex: number) => void;
}

async function fetchParagraphContext(citation: ChatCitation): Promise<ContextParagraph[]> {
  const params = new URLSearchParams({
    chapter_index: String(citation.chapter_index),
    paragraph_index: String(citation.paragraph_index),
    before: '2',
    after: '2',
  });
  const res = await fetch(`/api/rag/paragraphs/context?${params.toString()}`);
  if (!res.ok) {
    throw new Error('无法加载段落上下文');
  }
  const data = (await res.json()) as { paragraphs: ContextParagraph[] };
  return data.paragraphs;
}

export function CitationReader({ citation, onJumpToChapter }: CitationReaderProps) {
  const [paragraphs, setParagraphs] = useState<ContextParagraph[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const focusRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!citation) {
      setParagraphs([]);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchParagraphContext(citation)
      .then((items) => {
        if (!cancelled) setParagraphs(items);
      })
      .catch((err) => {
        if (!cancelled) {
          setParagraphs([]);
          setError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [citation]);

  useEffect(() => {
    if (citation && focusRef.current) {
      focusRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [citation, paragraphs]);

  if (!citation) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-[#e8ddd0] p-6 text-sm text-gray-500 min-h-[560px]">
        <h3 className="text-lg font-bold text-[#2c1810] mb-2">原文阅读</h3>
        <p>点击回答中的「原文引用」卡片，将在此高亮显示对应段落及上下文。</p>
      </div>
    );
  }

  const focusMeta = paragraphs.find((p) => p.paragraph_index === citation.paragraph_index);
  const chapterTitle = focusMeta?.title_cn || citation.title_cn;
  const partTitle = focusMeta?.part_title_cn || citation.part_title_cn;

  return (
    <div className="bg-white rounded-lg shadow-md border border-[#e8ddd0] flex flex-col min-h-[560px] overflow-hidden">
      <div className="px-4 py-3 border-b border-[#d4c5b5] bg-[#faf8f5]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-[#2c1810]">原文阅读</h3>
            <p className="text-sm text-[#8b4513] mt-1">
              第 {citation.chapter_index} 章《{chapterTitle}》· 第 {citation.paragraph_index} 段
            </p>
            {partTitle ? <p className="text-xs text-gray-500 mt-1">{partTitle}</p> : null}
          </div>
          {onJumpToChapter && (
            <button
              type="button"
              onClick={() => onJumpToChapter(citation.chapter_index)}
              className="shrink-0 text-xs px-3 py-1.5 rounded-lg border border-[#8b4513] text-[#8b4513] hover:bg-[#faf8f5]"
            >
              定位到第 {citation.chapter_index} 章
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 max-h-[480px]">
        {loading && <div className="text-sm text-gray-500">正在加载上下文…</div>}
        {error && <div className="text-sm text-red-600">{error}</div>}

        {!loading &&
          !error &&
          paragraphs.map((p) => {
            const isFocus = p.paragraph_index === citation.paragraph_index;
            return (
              <div
                key={p.id}
                ref={isFocus ? focusRef : undefined}
                className={`rounded-lg p-3 text-sm leading-relaxed transition-colors ${
                  isFocus
                    ? 'bg-amber-50 border-2 border-[#8b4513] shadow-sm'
                    : 'bg-[#faf8f5] border border-[#eee4d8] text-gray-600'
                }`}
              >
                <div className={`text-xs mb-2 ${isFocus ? 'text-[#8b4513] font-semibold' : 'text-gray-400'}`}>
                  第 {p.paragraph_index} 段
                  {isFocus ? ' · 引用段落' : ''}
                </div>
                <div className={isFocus ? 'text-[#2c1810]' : ''}>{p.text}</div>
              </div>
            );
          })}
      </div>
    </div>
  );
}