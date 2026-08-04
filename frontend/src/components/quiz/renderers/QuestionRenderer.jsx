import MCQRenderer from './MCQRenderer';

/**
 * QuestionRenderer — Dispatcher
 *
 * Reads question.type and renders the correct input component.
 * Adding a new question type only requires:
 *   1. Building a new <TypeRenderer> component in this folder.
 *   2. Adding one line to the RENDERERS map below.
 *
 * Props:
 *   question   : full question object from the API
 *   userAnswer : current answer value for this question (any type)
 *   onAnswer   : (questionId, value) => void — called when user selects/types an answer
 */

// ── Registry — all supported question type renderers ─────────────────────────
const RENDERERS = {
  mcq:          MCQRenderer,
  true_false:   TrueFalseRenderer,
  fill_blank:   FillBlankRenderer,
  short_answer: ShortAnswerRenderer,
  numeric:      NumericRenderer,
  ordering:     OrderingRenderer,
  matching:     MatchingRenderer,
};

export default function QuestionRenderer({ question, userAnswer, onAnswer }) {
  const type = question?.type ?? 'mcq';
  const Renderer = RENDERERS[type] ?? MCQRenderer;  // safe fallback to MCQ

  return (
    <Renderer
      question={question}
      userAnswer={userAnswer}
      onAnswer={onAnswer}
    />
  );
}
