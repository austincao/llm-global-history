import { useCallback, useRef, useState } from 'react';
import { MarkdownContent } from './MarkdownContent';

export interface ChatCitation {
  id: string;
  chapter_index: number;
  paragraph_index: number;
  part_title_cn: string;
  title_cn: string;
  era: string;
  segment_start_time_raw?: string | null;
  text: string;
  score: number;
}

export interface ChatEntity {
  name: string;
  entity_id: string;
  entity_type: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: ChatCitation[];
  entities?: ChatEntity[];
  mode?: string;
  retrieval?: string;
}

interface ChatViewProps {
  chapterStart: number;
  chapterEnd: number;
  activeCitation?: ChatCitation | null;
  onCitationSelect?: (citation: ChatCitation | null) => void;
  onEntityClick?: (entityId: string, entityType: string) => void;
}

const SUGGESTED_QUESTIONS = [
  '作者如何评价哥伦布发现美洲的意义？',
  '1500年前后西欧扩张的背景是什么？',
  '全球通史如何理解中国文明的早期形成？',
];

async function postChat(payload: {
  question: string;
  chapter_start: number;
  chapter_end: number;
  top_k: number;
}) {
  const res = await fetch('/api/rag/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `请求失败 (${res.status})`);
  }
  return res.json() as Promise<{
    answer: string;
    citations: ChatCitation[];
    entities: ChatEntity[];
    mode: string;
    retrieval: string;
  }>;
}

export function ChatView({
  chapterStart,
  chapterEnd,
  activeCitation,
  onCitationSelect,
  onEntityClick,
}: ChatViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retrievalMode, setRetrievalMode] = useState<string>('hybrid');
  const listRef = useRef<HTMLDivElement>(null);

  const ask = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed || loading) return;

      setError(null);
      setLoading(true);
      const userMsg: ChatMessage = {
        id: `u-${Date.now()}`,
        role: 'user',
        content: trimmed,
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput('');

      try {
        const data = await postChat({
          question: trimmed,
          chapter_start: chapterStart,
          chapter_end: chapterEnd,
          top_k: 5,
        });
        setRetrievalMode(data.retrieval || 'bm25');
        const assistantMsg: ChatMessage = {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: data.answer,
          citations: data.citations,
          entities: data.entities,
          mode: data.mode,
          retrieval: data.retrieval,
        };
        setMessages((prev) => [...prev, assistantMsg]);
        if (data.citations.length > 0) {
          onCitationSelect?.(data.citations[0]);
        }
        requestAnimationFrame(() => {
          listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message);
        setMessages((prev) => [
          ...prev,
          {
            id: `e-${Date.now()}`,
            role: 'assistant',
            content:
              '问答服务暂不可用。请先在项目根目录运行：\n\n' +
              '1. uv run python scripts/build_rag_index.py\n' +
              '2. uv run python scripts/rag_chat_server.py\n' +
              '3. cd visualization && npm run dev',
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [chapterStart, chapterEnd, loading, onCitationSelect]
  );

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden flex flex-col min-h-[560px]">
      <div className="px-4 py-3 border-b border-[#d4c5b5] bg-[#faf8f5]">
        <h2 className="text-lg font-bold text-[#2c1810]">问书</h2>
        <p className="text-sm text-gray-600 mt-1">
          {retrievalMode === 'hybrid' ? '语义 + 关键词混合检索' : '关键词检索（BM25）'} · 第 {chapterStart}
          {chapterEnd !== chapterStart ? `—${chapterEnd}` : ''} 章
        </p>
      </div>

      <div ref={listRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4 max-h-[420px]">
        {messages.length === 0 && (
          <div className="text-sm text-gray-600 space-y-3">
            <p>输入问题，系统会从选中章节范围内检索原文并生成回答（需配置 DEEPSEEK_API_KEY）。</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => ask(q)}
                  className="text-left text-xs px-3 py-2 rounded-full border border-[#d4c5b5] hover:bg-[#faf8f5] text-[#5d2e0c]"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`rounded-lg px-4 py-3 text-sm ${
              msg.role === 'user'
                ? 'bg-[#8b4513] text-white ml-8 whitespace-pre-wrap'
                : 'bg-[#faf8f5] text-[#2c1810] mr-4 border border-[#e8ddd0]'
            }`}
          >
            {msg.role === 'assistant' ? (
              <MarkdownContent content={msg.content} />
            ) : (
              msg.content
            )}

            {msg.role === 'assistant' && msg.entities && msg.entities.length > 0 && (
              <div className="mt-3 pt-3 border-t border-[#e8ddd0]">
                <div className="text-xs text-gray-500 mb-2">相关实体（点击查看关系网）</div>
                <div className="flex flex-wrap gap-2">
                  {msg.entities.map((ent) => (
                    <button
                      key={`${ent.entity_type}-${ent.entity_id}`}
                      type="button"
                      onClick={() => onEntityClick?.(ent.entity_id, ent.entity_type)}
                      className="text-xs px-2 py-1 rounded bg-white border border-[#d4c5b5] hover:border-[#8b4513] text-[#5d2e0c]"
                    >
                      {ent.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
              <div className="mt-3 pt-3 border-t border-[#e8ddd0] space-y-2">
                <div className="text-xs text-gray-500">原文引用（点击查看并高亮）</div>
                {msg.citations.map((c, idx) => {
                  const isActive =
                    activeCitation?.chapter_index === c.chapter_index &&
                    activeCitation?.paragraph_index === c.paragraph_index;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => onCitationSelect?.(c)}
                      className={`w-full text-left text-xs rounded border p-2 transition-colors ${
                        isActive
                          ? 'bg-amber-50 border-[#8b4513] ring-1 ring-[#8b4513]/30'
                          : 'bg-white border-[#eee4d8] hover:border-[#8b4513]'
                      }`}
                    >
                      <div className="font-medium text-[#8b4513]">
                        [{idx + 1}] 第{c.chapter_index}章《{c.title_cn}》· 第 {c.paragraph_index} 段
                      </div>
                      <div className="text-gray-700 mt-1 leading-relaxed line-clamp-3">{c.text}</div>
                    </button>
                  );
                })}
              </div>
            )}

            {msg.role === 'assistant' && msg.mode && (
              <div className="mt-2 text-[10px] text-gray-400">
                {msg.mode === 'llm' ? 'LLM 归纳回答' : '检索模式（未调用 LLM）'}
                {msg.retrieval ? ` · ${msg.retrieval === 'hybrid' ? '混合检索' : 'BM25'}` : ''}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="text-sm text-gray-500 flex items-center gap-2">
            <span className="inline-block w-4 h-4 border-2 border-[#8b4513] border-t-transparent rounded-full animate-spin" />
            正在检索原文…
          </div>
        )}
      </div>

      {error && (
        <div className="px-4 py-2 text-xs text-red-600 bg-red-50 border-t border-red-100">{error}</div>
      )}

      <form
        className="border-t border-[#d4c5b5] p-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="例如：作者如何解释大分流？"
          className="flex-1 rounded-lg border border-[#d4c5b5] px-3 py-2 text-sm focus:outline-none focus:border-[#8b4513]"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2 rounded-lg bg-[#8b4513] text-white text-sm font-medium disabled:opacity-50 hover:bg-[#5d2e0c]"
        >
          提问
        </button>
      </form>
    </div>
  );
}
