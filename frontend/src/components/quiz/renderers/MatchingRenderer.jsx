import { useState, useEffect, useMemo } from 'react';
import { ArrowRight } from 'lucide-react';

/**
 * MatchingRenderer
 *
 * Click-to-pair: user clicks a left item then a right item to form a pair.
 * Right column is shuffled on mount so answers aren't position-obvious.
 *
 * Props:
 *   question   : { id, payload: { left_items: [str], right_items: [str] } }
 *   userAnswer : [[leftIdx, rightIdx], ...] | null   (indices into ORIGINAL right array)
 *   onAnswer   : (questionId, value: [[int,int]]) => void
 */
export default function MatchingRenderer({ question, userAnswer, onAnswer }) {
  // Backend stores as left_items/right_items; support both spellings for safety
  const leftItems  = question?.payload?.left_items  ?? question?.payload?.left  ?? [];
  const rightItems = question?.payload?.right_items ?? question?.payload?.right ?? [];

  // Shuffle right column once on mount — keeps original indices so answer_key stays valid
  const shuffledRight = useMemo(() => {
    const indices = rightItems.map((_, i) => i);
    for (let i = indices.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [indices[i], indices[j]] = [indices[j], indices[i]];
    }
    return indices; // shuffledRight[displayPos] = originalRightIdx
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question?.id]);

  // pairs: array of [leftIdx, originalRightIdx]
  const [pairs, setPairs]          = useState(userAnswer ?? []);
  const [selectedLeft, setSelLeft] = useState(null); // left index or null

  useEffect(() => { if (userAnswer) setPairs(userAnswer); }, [userAnswer]);

  // Lookup helpers work on original right indices
  const getPairForLeft         = (li) => pairs.find(([l])    => l === li);
  const getPairForOriginalRight = (ri) => pairs.find(([, r]) => r === ri);

  const handleLeft = (li) => {
    const existing = getPairForLeft(li);
    if (existing) {
      // Click paired left item → unpair it
      const next = pairs.filter(([l]) => l !== li);
      setPairs(next);
      onAnswer(question.id, next);
      return;
    }
    setSelLeft(li);
  };

  const handleRight = (originalRi) => {
    if (selectedLeft === null) return;
    // Remove any existing pair for this left or this right
    const next = pairs.filter(([l, r]) => l !== selectedLeft && r !== originalRi);
    next.push([selectedLeft, originalRi]);
    setPairs(next);
    onAnswer(question.id, next);
    setSelLeft(null);
  };

  return (
    <div className="space-y-3">
      <p className="text-dark-400 text-xs">
        Click a <span className="text-primary-400 font-medium">term</span> on the left, then its matching{' '}
        <span className="text-primary-400 font-medium">definition</span> on the right.
        Click a paired item to remove the pair.
      </p>

      <div className="grid grid-cols-[1fr_28px_1fr] gap-x-2 gap-y-0 items-start">

        {/* Left column — Terms */}
        <div className="space-y-2">
          <p className="text-dark-500 text-xs font-semibold uppercase tracking-wide mb-1 px-1">Terms</p>
          {leftItems.map((item, li) => {
            const pair       = getPairForLeft(li);
            const isSelected = selectedLeft === li;
            const isPaired   = !!pair;
            return (
              <button
                key={li}
                onClick={() => handleLeft(li)}
                className={`w-full text-left px-3 py-2.5 rounded-xl border text-sm transition-all leading-snug ${
                  isSelected
                    ? 'border-primary-500 bg-primary-500/15 text-white shadow-md shadow-primary-500/10'
                    : isPaired
                    ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-300'
                    : 'border-dark-700 bg-dark-800/50 text-dark-300 hover:border-dark-600 hover:text-dark-100'
                }`}
              >
                <span className="font-semibold text-xs opacity-50 mr-1">{li + 1}.</span>
                {item}
              </button>
            );
          })}
        </div>

        {/* Connector column — arrows */}
        <div className="flex flex-col pt-8 gap-2">
          {leftItems.map((_, li) => {
            const pair = getPairForLeft(li);
            return (
              <div key={li} className="h-10 flex items-center justify-center">
                <ArrowRight className={`w-4 h-4 transition-colors ${pair ? 'text-emerald-400' : 'text-dark-700'}`} />
              </div>
            );
          })}
        </div>

        {/* Right column — Definitions (shuffled display order) */}
        <div className="space-y-2">
          <p className="text-dark-500 text-xs font-semibold uppercase tracking-wide mb-1 px-1">Definitions</p>
          {shuffledRight.map((originalRi) => {
            const pair     = getPairForOriginalRight(originalRi);
            const isPaired = !!pair;
            return (
              <button
                key={originalRi}
                onClick={() => handleRight(originalRi)}
                className={`w-full text-left px-3 py-2.5 rounded-xl border text-sm transition-all leading-snug ${
                  isPaired
                    ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-300'
                    : selectedLeft !== null
                    ? 'border-dark-600 bg-dark-800/80 text-dark-200 hover:border-primary-500/50 hover:bg-primary-500/10 cursor-pointer'
                    : 'border-dark-700 bg-dark-800/50 text-dark-300'
                }`}
              >
                {rightItems[originalRi]}
              </button>
            );
          })}
        </div>

      </div>
    </div>
  );
}
