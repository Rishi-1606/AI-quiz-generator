import { CheckCircle2 } from 'lucide-react';

const OPTION_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F'];

/**
 * MCQRenderer — Multiple Choice Question
 *
 * Props:
 *   question    : question object ({ id, payload: { options: [...] }, options: [...] })
 *   userAnswer  : currently selected option index (int | null)
 *   onAnswer    : (questionId, value) => void
 */
export default function MCQRenderer({ question, userAnswer, onAnswer }) {
  // Support both new payload.options (Sprint 1+) and legacy question.options
  const options =
    question?.payload?.options ??
    question?.options ??
    [];

  return (
    <div className="space-y-3">
      {options.map((option, idx) => {
        const isSelected = userAnswer === idx;
        return (
          <button
            key={idx}
            onClick={() => onAnswer(question.id, idx)}
            className={`w-full flex items-center gap-4 px-4 py-3.5 rounded-xl border text-left transition-all duration-150 ${
              isSelected
                ? 'border-primary-500 bg-primary-500/12 text-white'
                : 'border-dark-700 bg-dark-800/50 text-dark-300 hover:border-dark-600 hover:text-dark-100'
            }`}
          >
            <span className={`flex-shrink-0 w-7 h-7 rounded-lg text-xs font-bold flex items-center justify-center transition-colors ${
              isSelected ? 'bg-primary-500 text-white' : 'bg-dark-700 text-dark-400'
            }`}>
              {OPTION_LETTERS[idx]}
            </span>
            <span className="text-sm leading-snug">{option}</span>
            {isSelected && <CheckCircle2 className="w-4 h-4 text-primary-400 ml-auto flex-shrink-0" />}
          </button>
        );
      })}
    </div>
  );
}
