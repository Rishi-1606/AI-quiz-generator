/**
 * TrueFalseRenderer
 *
 * Props:
 *   question   : { id, question_text }
 *   userAnswer : true | false | null
 *   onAnswer   : (questionId, value: bool) => void
 */
export default function TrueFalseRenderer({ question, userAnswer, onAnswer }) {
  return (
    <div className="flex gap-4 mt-2">
      {[true, false].map((val) => {
        const isSelected = userAnswer === val;
        const label = val ? 'True' : 'False';
        const color = val
          ? 'border-emerald-500 bg-emerald-500/12 text-emerald-400'
          : 'border-red-500 bg-red-500/12 text-red-400';
        const idle = val
          ? 'border-dark-700 bg-dark-800/50 text-dark-300 hover:border-emerald-500/50 hover:text-emerald-400'
          : 'border-dark-700 bg-dark-800/50 text-dark-300 hover:border-red-500/50 hover:text-red-400';

        return (
          <button
            key={label}
            onClick={() => onAnswer(question.id, val)}
            className={`flex-1 py-4 rounded-xl border text-base font-semibold transition-all duration-150 ${
              isSelected ? color : idle
            }`}
          >
            {val ? '✓ True' : '✗ False'}
          </button>
        );
      })}
    </div>
  );
}
