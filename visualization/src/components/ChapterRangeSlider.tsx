interface ChapterRangeSliderProps {
  min?: number;
  max: number;
  value: [number, number];
  onChange: (range: [number, number]) => void;
  onCommit: (range: [number, number]) => void;
}

export function ChapterRangeSlider({
  min = 1,
  max,
  value,
  onChange,
  onCommit,
}: ChapterRangeSliderProps) {
  const [start, end] = value;
  const span = Math.max(max - min, 1);
  const startPct = ((start - min) / span) * 100;
  const endPct = ((end - min) / span) * 100;

  const commit = () => onCommit([start, end]);

  return (
    <div className="mt-3 px-1">
      <div className="relative h-8 flex items-center">
        <div className="absolute left-0 right-0 h-1.5 rounded-full bg-[#e8ddd0]" />
        <div
          className="absolute h-1.5 rounded-full bg-[#8b4513]"
          style={{ left: `${startPct}%`, right: `${100 - endPct}%` }}
        />
        <input
          type="range"
          min={min}
          max={max}
          value={start}
          onChange={(e) => {
            const nextStart = Number.parseInt(e.target.value, 10);
            onChange([Math.min(nextStart, end), end]);
          }}
          onMouseUp={commit}
          onTouchEnd={commit}
          className="chapter-range-thumb chapter-range-thumb-start"
          style={{ zIndex: start >= end - 1 ? 3 : 2 }}
          aria-label="起始章"
        />
        <input
          type="range"
          min={min}
          max={max}
          value={end}
          onChange={(e) => {
            const nextEnd = Number.parseInt(e.target.value, 10);
            onChange([start, Math.max(nextEnd, start)]);
          }}
          onMouseUp={commit}
          onTouchEnd={commit}
          className="chapter-range-thumb chapter-range-thumb-end"
          style={{ zIndex: start >= end - 1 ? 2 : 3 }}
          aria-label="结束章"
        />
      </div>
      <div className="flex justify-between text-[10px] text-gray-400 mt-1 px-0.5">
        <span>第 {min} 章</span>
        <span className="text-[#8b4513] font-medium">
          第 {start} — {end} 章
        </span>
        <span>第 {max} 章</span>
      </div>
    </div>
  );
}
