import { useState, useEffect } from 'react';

/**
 * FillBlankRenderer
 *
 * Displays a sentence with ___ replaced by an underlined text input.
 * If no text_with_blanks payload, shows a plain text input.
 *
 * Props:
 *   question   : { id, payload: { text_with_blanks: str } }
 *   userAnswer : string | null
 *   onAnswer   : (questionId, value: string) => void
 */
export default function FillBlankRenderer({ question, userAnswer, onAnswer }) {
  const [draft, setDraft] = useState(userAnswer ?? '');

  // Keep draft in sync if parent resets answer (e.g. navigation)
  useEffect(() => { setDraft(userAnswer ?? ''); }, [userAnswer]);

  const textWithBlanks = question?.payload?.text_with_blanks ?? null;

  const handleChange = (val) => {
    setDraft(val);
    onAnswer(question.id, val);
  };

  // If we have a templated sentence, render it with the input inline
  if (textWithBlanks) {
    const parts = textWithBlanks.split('___');
    return (
      <div className="text-dark-100 text-base leading-loose">
        {parts.map((part, i) => (
          <span key={i}>
            {part}
            {i < parts.length - 1 && (
              <input
                type="text"
                value={draft}
                onChange={e => handleChange(e.target.value)}
                placeholder="your answer"
                className="inline-block mx-2 px-3 py-1 bg-dark-800 border-b-2 border-primary-500 text-primary-300 text-sm rounded-t-lg focus:outline-none min-w-[120px]"
              />
            )}
          </span>
        ))}
      </div>
    );
  }

  // Fallback: plain text input
  return (
    <input
      type="text"
      value={draft}
      onChange={e => handleChange(e.target.value)}
      placeholder="Type your answer here…"
      className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-dark-100 text-sm focus:outline-none focus:border-primary-500 transition-colors"
    />
  );
}
