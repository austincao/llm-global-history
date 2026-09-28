import { useEffect, useState, type KeyboardEvent } from 'react';
import { MAX_CHAPTER, DEFAULT_CHAPTER_RANGE, DEFAULT_YEAR_RANGE } from '../config';
import { ChapterRangeSlider } from './ChapterRangeSlider';

function parseOptionalInt(raw: string): number | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  const n = Number.parseInt(trimmed, 10);
  return Number.isFinite(n) ? n : null;
}

function normalizeChapterRange(start: number, end: number, maxJuan: number): [number, number] {
  let s = Math.min(maxJuan, Math.max(1, start));
  let e = Math.min(maxJuan, Math.max(1, end));
  if (s > e) [s, e] = [e, s];
  return [s, e];
}

interface FilterControlsProps {
  juanRange: [number, number];
  onJuanRangeChange: (range: [number, number]) => void;
  onJuanRangeCommit: (range: [number, number]) => void;
  maxJuan: number;
  timeRange: [number | null, number | null];
  onTimeRangeChange: (range: [number | null, number | null]) => void;
  onTimeRangeCommit: (range: [number | null, number | null]) => void;

  syncJuanYear: boolean;
  syncAvailable: boolean;
  onSyncJuanYearChange: (enabled: boolean) => void;
}

export function FilterControls({
  juanRange,
  onJuanRangeChange,
  onJuanRangeCommit,
  maxJuan,
  timeRange,
  onTimeRangeChange,
  onTimeRangeCommit,
  syncJuanYear,
  syncAvailable,
  onSyncJuanYearChange,
}: FilterControlsProps) {
  const [startDraft, setStartDraft] = useState(String(juanRange[0]));
  const [endDraft, setEndDraft] = useState(String(juanRange[1]));
  const [yearStartDraft, setYearStartDraft] = useState(timeRange[0] !== null ? String(timeRange[0]) : '');
  const [yearEndDraft, setYearEndDraft] = useState(timeRange[1] !== null ? String(timeRange[1]) : '');

  useEffect(() => {
    setStartDraft(String(juanRange[0]));
    setEndDraft(String(juanRange[1]));
  }, [juanRange[0], juanRange[1]]);

  useEffect(() => {
    setYearStartDraft(timeRange[0] !== null ? String(timeRange[0]) : '');
    setYearEndDraft(timeRange[1] !== null ? String(timeRange[1]) : '');
  }, [timeRange[0], timeRange[1]]);

  const commitChapterDraft = () => {
    const start = parseOptionalInt(startDraft) ?? juanRange[0];
    const end = parseOptionalInt(endDraft) ?? juanRange[1];
    const normalized = normalizeChapterRange(start, end, maxJuan);
    setStartDraft(String(normalized[0]));
    setEndDraft(String(normalized[1]));
    onJuanRangeChange(normalized);
    onJuanRangeCommit(normalized);
  };

  const commitYearDraft = () => {
    const next: [number | null, number | null] = [parseOptionalInt(yearStartDraft), parseOptionalInt(yearEndDraft)];
    onTimeRangeChange(next);
    onTimeRangeCommit(next);
  };

  const commitChapterOnEnter = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') commitChapterDraft();
  };

  const commitYearOnEnter = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') commitYearDraft();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-bold text-[#2c1810] mb-4">筛选控制</h3>

      <div className="mb-6">
        <label className="flex items-center gap-2 text-sm text-[#2c1810]">
          <input
            type="checkbox"
            checked={syncJuanYear}
            disabled={!syncAvailable}
            onChange={(e) => onSyncJuanYearChange(e.target.checked)}
            className="accent-[#8b4513]"
          />
          <span className={!syncAvailable ? 'text-gray-400' : undefined}>章↔年份联动</span>
        </label>
        {!syncAvailable && (
          <p className="text-xs text-gray-400 mt-1">缺少 /data/juan_year_index.json，联动不可用</p>
        )}
      </div>

      <div className="mb-6">
        <label className="block text-sm font-semibold text-[#8b4513] mb-2">
          章范围
        </label>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="text-xs text-gray-500">起始章</label>
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={startDraft}
              onChange={(e) => setStartDraft(e.target.value.replace(/[^\d]/g, ''))}
              onBlur={commitChapterDraft}
              onKeyDown={commitChapterOnEnter}
              className="w-full mt-1 px-3 py-2 border border-[#d4c5b5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#8b4513]"
            />
          </div>
          <span className="text-gray-400 mt-6">—</span>
          <div className="flex-1">
            <label className="text-xs text-gray-500">结束章</label>
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={endDraft}
              onChange={(e) => setEndDraft(e.target.value.replace(/[^\d]/g, ''))}
              onBlur={commitChapterDraft}
              onKeyDown={commitChapterOnEnter}
              className="w-full mt-1 px-3 py-2 border border-[#d4c5b5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#8b4513]"
            />
          </div>
        </div>
        <ChapterRangeSlider
          max={maxJuan}
          value={juanRange}
          onChange={(range) => {
            setStartDraft(String(range[0]));
            setEndDraft(String(range[1]));
            onJuanRangeChange(range);
          }}
          onCommit={(range) => {
            setStartDraft(String(range[0]));
            setEndDraft(String(range[1]));
            onJuanRangeCommit(range);
          }}
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-[#8b4513] mb-2">
          时间范围（年，BCE 为负）
        </label>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="text-xs text-gray-500">起始年</label>
            <input
              type="text"
              inputMode="numeric"
              placeholder="不限"
              value={yearStartDraft}
              onChange={(e) => setYearStartDraft(e.target.value.replace(/[^\d-]/g, ''))}
              onBlur={commitYearDraft}
              onKeyDown={commitYearOnEnter}
              className="w-full mt-1 px-3 py-2 border border-[#d4c5b5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#8b4513]"
            />
          </div>
          <span className="text-gray-400 mt-6">—</span>
          <div className="flex-1">
            <label className="text-xs text-gray-500">结束年</label>
            <input
              type="text"
              inputMode="numeric"
              placeholder="不限"
              value={yearEndDraft}
              onChange={(e) => setYearEndDraft(e.target.value.replace(/[^\d-]/g, ''))}
              onBlur={commitYearDraft}
              onKeyDown={commitYearOnEnter}
              className="w-full mt-1 px-3 py-2 border border-[#d4c5b5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#8b4513]"
            />
          </div>
        </div>
      </div>

      <div className="mt-4">
        <label className="block text-sm font-semibold text-[#8b4513] mb-2">
          快速筛选
        </label>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => {
              onJuanRangeChange(DEFAULT_CHAPTER_RANGE);
              onTimeRangeChange(DEFAULT_YEAR_RANGE);
              onJuanRangeCommit(DEFAULT_CHAPTER_RANGE);
              onTimeRangeCommit(DEFAULT_YEAR_RANGE);
            }}
            className="px-3 py-1 text-sm border border-[#8b4513] text-[#8b4513] rounded-full hover:bg-[#8b4513] hover:text-white transition-colors"
          >
            第22章试点
          </button>
          <button
            onClick={() => {
              const range: [number, number] = [22, MAX_CHAPTER];
              const years: [number | null, number | null] = [1500, null];
              onJuanRangeChange(range);
              onTimeRangeChange(years);
              onJuanRangeCommit(range);
              onTimeRangeCommit(years);
            }}
            className="px-3 py-1 text-sm border border-[#8b4513] text-[#8b4513] rounded-full hover:bg-[#8b4513] hover:text-white transition-colors"
          >
            1500年后
          </button>
          <button
            onClick={() => {
              const range: [number, number] = [1, maxJuan];
              const years: [number | null, number | null] = [null, null];
              onJuanRangeChange(range);
              onTimeRangeChange(years);
              onJuanRangeCommit(range);
              onTimeRangeCommit(years);
            }}
            className="px-3 py-1 text-sm border border-[#8b4513] text-[#8b4513] rounded-full hover:bg-[#8b4513] hover:text-white transition-colors"
          >
            重置
          </button>
        </div>
      </div>
    </div>
  );
}
