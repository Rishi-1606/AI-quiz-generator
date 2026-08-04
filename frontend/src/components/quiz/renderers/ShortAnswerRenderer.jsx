import { useState, useEffect } from 'react';

/**
 * ShortAnswerRenderer
 *
 * Free-text textarea. AI-graded in Sprint 5.
 *
 * Props:
 *   question   : { id }
 *   userAnswer : string | null
 *   onAnswer   : (questionId, value: string) => void
 */
export default function ShortAnswerRenderer({ question, userAnswer, onAnswer }) {
  const MAX = 500;
  const [draft, setDraft] = useState(userAnswer ?? '');

  useEffect(() => { setDraft(userAnswer ?? ''); }, [userAnswer]);

  const handleChange = (val) => {
    if (val.length > MAX) return;
    setDraft(val);
    onAnswer(question.id, val);
  };

  return (
    <div className="space-y-2">
      <textarea
        value={draft}
        onChange={e => handleChange(e.target.value)}
        placeholder="Write your answer here…"
        rows={4}
        className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-dark-100 text-sm focus:outline-none focus:border-primary-500 transition-colors resize-none"
      />
      <div className="flex justify-between items-center">
        <p className="text-dark-500 text-xs">AI will evaluate your response</p>
        <p className={`text-xs ${draft.length > MAX * 0.9 ? 'text-yellow-400' : 'text-dark-500'}`}>
          {draft.length}/{MAX}
        </p>
      </div>
    </div>
  );
}
