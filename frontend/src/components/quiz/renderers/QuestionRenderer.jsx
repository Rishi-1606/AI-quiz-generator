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

// ── Registry — add new renderers here as sprints progress ────────────────────
// Sprint 3 Step 2 will fill in the remaining entries.
const RENDERERS = {
  mcq:          MCQRenderer,
  // true_false   : TrueFalseRenderer,   — added in Sprint 3 Step 2
  // fill_blank   : FillBlankRenderer,   — added in Sprint 3 Step 2
  // short_answer : ShortAnswerRenderer, — added in Sprint 3 Step 2
  // matching     : MatchingRenderer,    — added in Sprint 3 Step 2
  // ordering     : OrderingRenderer,    — added in Sprint 3 Step 2
  // numeric      : NumericRenderer,     — added in Sprint 3 Step 2
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
