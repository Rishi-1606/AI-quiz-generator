import { useState, useEffect } from 'react';

/**
 * NumericRenderer
 *
 * Number input with optional unit label.
 *
 * Props:
 *   question   : { id, payload: { unit: str|null, tolerance: float|null } }
 *   userAnswer : number | null
 *   onAnswer   : (questionId, value: number) => void
 */
export default function NumericRenderer({ question, userAnswer, onAnswer }) {
  const unit      = question?.payload?.unit ?? null;
  const tolerance = question?.payload?.tolerance ?? null;
  const [draft, setDraft] = useState(userAnswer != null ? String(userAnswer) : '');

  useEffect(() => {
    setDraft(userAnswer != null ? String(userAnswer) : '');
  }, [userAnswer]);

  const handleChange = (val) => {
    setDraft(val);
    const num = parseFloat(val);
    if (!isNaN(num)) onAnswer(question.id, num);
    else if (val === '' || val === '-') onAnswer(question.id, null);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <input
          type="number"
          value={draft}
          onChange={e => handleChange(e.target.value)}
          placeholder="Enter a number…"
          className="flex-1 px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-dark-100 text-sm focus:outline-none focus:border-primary-500 transition-colors [appearance:textfield]"
        />
        {unit && (
          <span className="px-3 py-3 bg-dark-800 border border-dark-700 rounded-xl text-dark-400 text-sm font-mono">
            {unit}
          </span>
        )}
      </div>
      {tolerance != null && (
        <p className="text-dark-500 text-xs">
          Accepted tolerance: ±{tolerance} {unit ?? ''}
        </p>
      )}
    </div>
  );
}
