import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ChevronLeft, ChevronRight, Clock, CheckCircle2,
  AlertCircle, Send, Loader2, BookOpen
} from 'lucide-react';
import api from '../../services/api';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatTime(secs) {
  const m = Math.floor(secs / 60).toString().padStart(2, '0');
  const s = (secs % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

const OPTION_LETTERS = ['A', 'B', 'C', 'D'];

// ─── Component ────────────────────────────────────────────────────────────────

export default function TakeQuiz() {
  const { quizId } = useParams();
  const navigate   = useNavigate();

  const [quiz, setQuiz]             = useState(null);
  const [isLoading, setIsLoading]   = useState(true);
  const [error, setError]           = useState('');

  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers]           = useState({});   // { questionId: optionIndex | null }
  const [timeLeft, setTimeLeft]         = useState(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmSubmit, setConfirmSubmit] = useState(false);

  const timerRef = useRef(null);

  // ── Fetch quiz ──────────────────────────────────────────────────────────────
  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        const res = await api.get(`/api/quizzes/${quizId}`);
        setQuiz(res.data);
        setTimeLeft(res.data.time_limit);
      } catch {
        setError('Failed to load quiz. It may not exist or you may not have access.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchQuiz();
  }, [quizId]);

  // ── Countdown timer ─────────────────────────────────────────────────────────
  const handleSubmit = useCallback(async (autoSubmit = false) => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    clearInterval(timerRef.current);
    try {
      const payload = {
        answers,
        time_taken: quiz ? quiz.time_limit - timeLeft : null,
      };
      const res = await api.post(`/api/quizzes/${quizId}/submit`, payload);
      navigate(`/quiz/${quizId}/results`, { state: { attempt: res.data, quiz } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit quiz. Please try again.');
      setIsSubmitting(false);
    }
  }, [isSubmitting, answers, quiz, timeLeft, quizId, navigate]);

  useEffect(() => {
    if (timeLeft === null) return;
    if (timeLeft <= 0) {
      handleSubmit(true);
      return;
    }
    timerRef.current = setInterval(() => {
      setTimeLeft(prev => prev - 1);
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [timeLeft, handleSubmit]);

  // ── Answer selection ────────────────────────────────────────────────────────
  const selectAnswer = (questionId, optionIndex) => {
    setAnswers(prev => ({
      ...prev,
      [String(questionId)]: optionIndex,
    }));
  };

  // ── Derived ─────────────────────────────────────────────────────────────────
  const answeredCount = Object.keys(answers).length;
  const totalQ        = quiz?.questions?.length ?? 0;
  const currentQ      = quiz?.questions?.[currentIndex];
  const userAnswer    = currentQ ? answers[String(currentQ.id)] : undefined;
  const isTimeLow     = timeLeft !== null && timeLeft < 60;

  // ─── Render ──────────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
          <p className="text-dark-400 text-sm">Loading quiz…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
        <div className="text-center max-w-sm">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <p className="text-white font-semibold mb-2">Something went wrong</p>
          <p className="text-dark-400 text-sm mb-6">{error}</p>
          <button onClick={() => navigate('/upload')} className="text-primary-400 text-sm hover:underline">
            ← Back to documents
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 text-white">
      {/* ── Top Bar ── */}
      <header className="sticky top-0 z-30 bg-dark-900/90 backdrop-blur border-b border-dark-800">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
          {/* Quiz title */}
          <div className="flex items-center gap-3 min-w-0">
            <BookOpen className="w-5 h-5 text-primary-400 flex-shrink-0" />
            <h1 className="text-sm font-semibold text-dark-100 truncate">{quiz.title}</h1>
          </div>

          {/* Progress + Timer */}
          <div className="flex items-center gap-4 flex-shrink-0">
            <span className="text-dark-400 text-sm hidden sm:block">
              {answeredCount}/{totalQ} answered
            </span>
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-mono font-semibold ${
              isTimeLow
                ? 'border-red-500/40 bg-red-500/10 text-red-400 animate-pulse'
                : 'border-dark-700 bg-dark-800 text-dark-200'
            }`}>
              <Clock className="w-3.5 h-3.5" />
              {timeLeft !== null ? formatTime(timeLeft) : '--:--'}
            </div>

            {/* Submit button */}
            <button
              onClick={() => setConfirmSubmit(true)}
              disabled={isSubmitting}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium transition-all disabled:opacity-50"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Submit
            </button>
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-0.5 bg-dark-800">
          <div
            className="h-full bg-gradient-to-r from-primary-600 to-primary-400 transition-all duration-300"
            style={{ width: `${totalQ ? (answeredCount / totalQ) * 100 : 0}%` }}
          />
        </div>
      </header>

      {/* ── Body ── */}
      <div className="max-w-6xl mx-auto px-4 py-8 flex gap-6">

        {/* ─ Question card (main) ─ */}
        <main className="flex-1 min-w-0">
          {currentQ && (
            <div className="bg-dark-900 border border-dark-800 rounded-2xl p-6 shadow-lg">
              {/* Question header */}
              <div className="flex items-start gap-4 mb-6">
                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-500/15 text-primary-400 text-sm font-bold flex items-center justify-center">
                  {currentIndex + 1}
                </span>
                <p className="text-dark-100 text-base leading-relaxed font-medium pt-1">
                  {currentQ.question_text}
                </p>
              </div>

              {/* Options */}
              <div className="space-y-3">
                {currentQ.options.map((option, idx) => {
                  const isSelected = userAnswer === idx;
                  return (
                    <button
                      key={idx}
                      onClick={() => selectAnswer(currentQ.id, idx)}
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

              {/* Navigation buttons */}
              <div className="flex items-center justify-between mt-8 pt-6 border-t border-dark-800">
                <button
                  onClick={() => setCurrentIndex(i => Math.max(0, i - 1))}
                  disabled={currentIndex === 0}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl border border-dark-700 text-dark-400 hover:border-dark-600 hover:text-white text-sm transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" /> Previous
                </button>

                <span className="text-dark-500 text-sm">{currentIndex + 1} / {totalQ}</span>

                <button
                  onClick={() => setCurrentIndex(i => Math.min(totalQ - 1, i + 1))}
                  disabled={currentIndex === totalQ - 1}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl border border-dark-700 text-dark-400 hover:border-dark-600 hover:text-white text-sm transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Next <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </main>

        {/* ─ Question navigator sidebar ─ */}
        <aside className="w-52 flex-shrink-0 hidden md:block">
          <div className="bg-dark-900 border border-dark-800 rounded-2xl p-4 sticky top-24">
            <p className="text-dark-400 text-xs font-semibold uppercase tracking-wide mb-3">Questions</p>
            <div className="grid grid-cols-4 gap-1.5">
              {quiz.questions.map((q, idx) => {
                const isAnswered = answers[String(q.id)] !== undefined;
                const isCurrent  = idx === currentIndex;
                return (
                  <button
                    key={q.id}
                    onClick={() => setCurrentIndex(idx)}
                    className={`w-full aspect-square rounded-lg text-xs font-semibold transition-all ${
                      isCurrent
                        ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
                        : isAnswered
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-dark-800 text-dark-500 hover:bg-dark-700 hover:text-dark-300'
                    }`}
                  >
                    {idx + 1}
                  </button>
                );
              })}
            </div>

            {/* Legend */}
            <div className="mt-4 space-y-1.5">
              {[
                { color: 'bg-primary-500', label: 'Current' },
                { color: 'bg-emerald-500/20 border border-emerald-500/30', label: 'Answered' },
                { color: 'bg-dark-800', label: 'Unanswered' },
              ].map(item => (
                <div key={item.label} className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded ${item.color}`} />
                  <span className="text-dark-500 text-xs">{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>

      {/* ── Confirm submit dialog ── */}
      {confirmSubmit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.7)' }}>
          <div className="w-full max-w-sm bg-dark-900 border border-dark-700 rounded-2xl p-6 shadow-2xl">
            <h2 className="text-white font-semibold text-base mb-2">Submit Quiz?</h2>
            <p className="text-dark-400 text-sm mb-1">
              You have answered <span className="text-white font-medium">{answeredCount}</span> out of <span className="text-white font-medium">{totalQ}</span> questions.
            </p>
            {answeredCount < totalQ && (
              <p className="text-yellow-400 text-sm mb-4">
                ⚠ {totalQ - answeredCount} question{totalQ - answeredCount > 1 ? 's' : ''} left unanswered.
              </p>
            )}
            <div className="flex gap-3 mt-5">
              <button
                onClick={() => setConfirmSubmit(false)}
                className="flex-1 px-4 py-2.5 rounded-xl border border-dark-700 text-dark-400 hover:text-white text-sm transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => { setConfirmSubmit(false); handleSubmit(); }}
                className="flex-1 px-4 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium transition-colors"
              >
                Yes, Submit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
