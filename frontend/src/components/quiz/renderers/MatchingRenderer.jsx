import { useState, useEffect } from 'react';
import { ArrowRight } from 'lucide-react';

/**
 * MatchingRenderer
 *
 * Click-to-pair: user clicks a left item then a right item to form a pair.
 * Paired items are highlighted. Click a paired item to unpair.
 *
 * Props:
 *   question   : { id, payload: { left: [str], right: [str] } }
 *   userAnswer : [[leftIdx, rightIdx], ...] | null
 *   onAnswer   : (questionId, value: [[int,int]]) => void
 */
export default function MatchingRenderer({ question, userAnswer, onAnswer }) {
  const leftItems  = question?.payload?.left  ?? [];
  const rightItems = question?.payload?.right ?? [];

  // pairs: array of [leftIdx, rightIdx]
  const [pairs, setPairs]           = useState(userAnswer ?? []);
  const [selectedLeft, setSelLeft]  = useState(null); // index or null

  useEffect(() => { if (userAnswer) setPairs(userAnswer); }, [userAnswer]);

  const getPairForLeft  = (li) => pairs.find(([l]) => l === li);
  const getPairForRight = (ri) => pairs.find(([, r]) => r === ri);

  const handleLeft = (li) => {
    // If already paired, unpair
    const existing = getPairForLeft(li);
    if (existing) {
      const next = pairs.filter(([l]) => l !== li);
      setPairs(next); onAnswer(question.id, next);
      return;
    }
    setSelLeft(li);
  };

  const handleRight = (ri) => {
    if (selectedLeft === null) return;
    // Remove any existing pair involving either index
    const next = pairs.filter(([l, r]) => l !== selectedLeft && r !== ri);
    next.push([selectedLeft, ri]);
    setPairs(next);
    onAnswer(question.id, next);
    setSelLeft(null);
  };

  return (
    <div className="space-y-3">
      <p className="text-dark-400 text-xs">Click a left item, then a right item to pair them. Click a paired item to remove the pair.</p>
      <div className="grid grid-cols-[1fr_auto_1fr] gap-3 items-start">
        {/* Left column */}
        <div className="space-y-2">
          {leftItems.map((item, li) => {
            const pair       = getPairForLeft(li);
            const isSelected = selectedLeft === li;
            const isPaired   = !!pair;
            return (
              <button
                key={li}
                onClick={() => handleLeft(li)}
                className={`w-full text-left px-3 py-2.5 rounded-xl border text-sm transition-all ${
                  isSelected
                    ? 'border-primary-500 bg-primary-500/15 text-white'
                    : isPaired
                    ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-300'
                    : 'border-dark-700 bg-dark-800/50 text-dark-300 hover:border-dark-600'
                }`}
              >
                {item}
              </button>
            );
          })}
        </div>

        {/* Connector arrows */}
        <div className="flex flex-col gap-2 pt-1">
          {leftItems.map((_, li) => {
            const pair = getPairForLeft(li);
            return (
              <div key={li} className="h-10 flex items-center justify-center">
                <ArrowRight className={`w-4 h-4 ${pair ? 'text-emerald-400' : 'text-dark-700'}`} />
              </div>
            );
          })}
        </div>

        {/* Right column */}
        <div className="space-y-2">
          {rightItems.map((item, ri) => {
            const pair     = getPairForRight(ri);
            const isPaired = !!pair;
            return (
              <button
                key={ri}
                onClick={() => handleRight(ri)}
                className={`w-full text-left px-3 py-2.5 rounded-xl border text-sm transition-all ${
                  isPaired
                    ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-300'
                    : selectedLeft !== null
                    ? 'border-dark-600 bg-dark-800/80 text-dark-200 hover:border-primary-500/50 hover:bg-primary-500/10'
                    : 'border-dark-700 bg-dark-800/50 text-dark-300'
                }`}
              >
                {item}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
