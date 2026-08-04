import { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react';

/**
 * OrderingRenderer
 *
 * User reorders items using Up/Down buttons.
 * No external drag-and-drop dependency needed.
 *
 * Props:
 *   question   : { id, payload: { items: [str] } }
 *   userAnswer : int[] | null  (indices representing current order)
 *   onAnswer   : (questionId, value: int[]) => void
 */
export default function OrderingRenderer({ question, userAnswer, onAnswer }) {
  const sourceItems = question?.payload?.items ?? [];

  // order: array of original indices in the user's current arrangement
  const [order, setOrder] = useState(() =>
    userAnswer ?? sourceItems.map((_, i) => i)
  );

  useEffect(() => {
    if (userAnswer) setOrder(userAnswer);
  }, [userAnswer]);

  const move = (pos, direction) => {
    const next = [...order];
    const target = pos + direction;
    if (target < 0 || target >= next.length) return;
    [next[pos], next[target]] = [next[target], next[pos]];
    setOrder(next);
    onAnswer(question.id, next);
  };

  return (
    <div className="space-y-2">
      <p className="text-dark-400 text-xs mb-3">Drag or use arrows to arrange in correct order</p>
      {order.map((originalIdx, pos) => (
        <div
          key={originalIdx}
          className="flex items-center gap-3 px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl group"
        >
          <span className="w-6 h-6 rounded-full bg-primary-500/15 text-primary-400 text-xs font-bold flex items-center justify-center flex-shrink-0">
            {pos + 1}
          </span>
          <span className="flex-1 text-dark-100 text-sm">{sourceItems[originalIdx]}</span>
          <div className="flex flex-col gap-0.5 opacity-40 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => move(pos, -1)}
              disabled={pos === 0}
              className="p-0.5 rounded hover:bg-dark-700 disabled:opacity-20 disabled:cursor-not-allowed transition-all"
            >
              <ArrowUp className="w-3.5 h-3.5 text-dark-300" />
            </button>
            <button
              onClick={() => move(pos, 1)}
              disabled={pos === order.length - 1}
              className="p-0.5 rounded hover:bg-dark-700 disabled:opacity-20 disabled:cursor-not-allowed transition-all"
            >
              <ArrowDown className="w-3.5 h-3.5 text-dark-300" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
