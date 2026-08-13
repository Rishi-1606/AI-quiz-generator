import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useEffect, useState, useRef } from 'react';
import {
  CheckCircle2, XCircle, MinusCircle, Clock,
  Trophy, ArrowLeft, RotateCcw, Loader2, BookOpen, Brain,
  Download, ChevronDown,
} from 'lucide-react';
import api from '../../services/api';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatTime(secs) {
  if (!secs) return '—';
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function getScoreLabel(pct) {
  if (pct >= 90) return { label: 'Outstanding! 🏆', color: 'text-yellow-400' };
  if (pct >= 75) return { label: 'Great Job! 🎉',   color: 'text-emerald-400' };
  if (pct >= 50) return { label: 'Good Effort! 👍', color: 'text-blue-400'    };
  return           { label: 'Keep Practicing 💪',   color: 'text-orange-400'  };
}

function tryParseJson(val) {
  if (!val) return null;
  if (typeof val === 'object') return val;
  try { return JSON.parse(val); } catch { return null; }
}

/**
 * Returns 'correct' | 'wrong' | 'skipped' for each question.
 * matching / ordering / numeric are graded server-side; we get the result
 * from attempt.question_results if available, otherwise mark as 'submitted'.
 */
function getQuestionStatus(q, userAnswer, questionResults) {
  const type = q.type ?? 'mcq';

  // If server returned per-question results (attempt.question_results), use them
  if (questionResults) {
    const res = questionResults[String(q.id)];
    if (res !== undefined) {
      if (userAnswer === undefined || userAnswer === null) return 'skipped';
      return res ? 'correct' : 'wrong';
    }
  }

  if (userAnswer === undefined || userAnswer === null) return 'skipped';

  const ak = tryParseJson(q.answer_key);

  if (type === 'mcq') {
    return userAnswer === (ak?.correct_index ?? 0) ? 'correct' : 'wrong';
  }
  if (type === 'true_false') {
    return userAnswer === ak?.correct ? 'correct' : 'wrong';
  }
  if (type === 'fill_blank') {
    const accepted = ak?.accepted_answers ?? [];
    const norm = s => String(s ?? '').trim().toLowerCase();
    return accepted.some(a => norm(a) === norm(userAnswer)) ? 'correct' : 'wrong';
  }
  if (type === 'short_answer') return 'ai_graded';
  // matching / ordering / numeric — no client-side check; mark as submitted
  return 'submitted';
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function QuizResults() {
  const { quizId }  = useParams();
  const location    = useLocation();
  const navigate    = useNavigate();

  const [attempt, setAttempt] = useState(location.state?.attempt ?? null);
  const [quiz,    setQuiz]    = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error,     setError]     = useState('');
  const [showExport, setShowExport] = useState(false);
  const exportRef = useRef(null);

  useEffect(() => {
    if (attempt && quiz) return;
    const fetchData = async () => {
      try {
        const quizRes = await api.get(`/api/quizzes/${quizId}/with-answers`);
        setQuiz(quizRes.data);
        if (!attempt) {
          setError('No attempt data found. Please take the quiz first.');
        }
      } catch {
        setError('Failed to load results.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [quizId, attempt, quiz]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-white font-semibold mb-2">Something went wrong</p>
          <p className="text-dark-400 text-sm mb-6">{error}</p>
          <button onClick={() => navigate('/upload')} className="text-primary-400 text-sm hover:underline">
            ← Back to documents
          </button>
        </div>
      </div>
    );
  }

  const { label: scoreLabel, color: scoreColor } = getScoreLabel(attempt.percentage);
  const answers = attempt.answers ?? {};
  // Some backends return per-question correctness in attempt.question_results
  const questionResults = attempt.question_results ?? null;

  const handleExport = (format, includeAnswers) => {
    const token = localStorage.getItem('token');
    const url = `http://localhost:8000/api/quizzes/${quizId}/export?format=${format}&include_answers=${includeAnswers}`;
    const a = document.createElement('a');
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.blob())
      .then(blob => {
        const ext = format === 'json' ? 'json' : 'txt';
        const objUrl = URL.createObjectURL(blob);
        a.href = objUrl;
        a.download = `quiz_${quizId}.${ext}`;
        a.click();
        URL.revokeObjectURL(objUrl);
      });
    setShowExport(false);
  };

  return (
    <div className="min-h-screen bg-dark-950 text-white">

      {/* ── Header ── */}
      <header className="bg-dark-900/90 backdrop-blur border-b border-dark-800 sticky top-0 z-20">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BookOpen className="w-5 h-5 text-primary-400" />
            <span className="text-sm font-semibold text-dark-100 truncate max-w-[200px] sm:max-w-none">
              {quiz?.title}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {/* Export dropdown */}
            <div className="relative" ref={exportRef}>
              <button
                onClick={() => setShowExport(s => !s)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-dark-700 text-dark-400 hover:text-white text-sm transition-colors"
              >
                <Download className="w-3.5 h-3.5" /> Export <ChevronDown className="w-3 h-3" />
              </button>
              {showExport && (
                <div className="absolute right-0 top-9 z-50 w-52 bg-dark-800 border border-dark-700 rounded-xl shadow-2xl overflow-hidden">
                  <p className="px-3 py-2 text-dark-500 text-xs font-semibold uppercase tracking-wide">With Answers</p>
                  <button onClick={() => handleExport('txt', true)}  className="w-full text-left px-4 py-2 text-sm text-dark-300 hover:bg-dark-700 hover:text-white transition-colors">.txt (with answers)</button>
                  <button onClick={() => handleExport('json', true)} className="w-full text-left px-4 py-2 text-sm text-dark-300 hover:bg-dark-700 hover:text-white transition-colors">.json (with answers)</button>
                  <p className="px-3 py-2 text-dark-500 text-xs font-semibold uppercase tracking-wide border-t border-dark-700 mt-1">Practice (no answers)</p>
                  <button onClick={() => handleExport('txt', false)}  className="w-full text-left px-4 py-2 text-sm text-dark-300 hover:bg-dark-700 hover:text-white transition-colors">.txt (practice sheet)</button>
                </div>
              )}
            </div>

            <button
              onClick={() => navigate(`/quiz/${quizId}`)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-dark-700 text-dark-400 hover:text-white text-sm transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Retake
            </button>
            <button
              onClick={() => navigate('/upload')}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-sm transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Documents
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-8">

        {/* ── Scorecard Banner ── */}
        <div className="bg-dark-900 border border-dark-800 rounded-3xl p-8 text-center shadow-xl">
          <div className="inline-flex items-center justify-center w-28 h-28 rounded-full bg-dark-800 border-4 border-primary-500/40 mb-5">
            <span className="text-4xl font-black text-white">{Math.round(attempt.percentage)}<span className="text-lg text-dark-400">%</span></span>
          </div>

          <p className={`text-xl font-bold mb-1 ${scoreColor}`}>{scoreLabel}</p>
          <p className="text-dark-400 text-sm mb-6">
            You scored <span className="text-white font-semibold">{attempt.correct}</span> out of{' '}
            <span className="text-white font-semibold">{attempt.total}</span> questions
            {attempt.points_total > 0 && (
              <span className="text-dark-500"> &nbsp;·&nbsp; <span className="text-primary-400 font-semibold">{attempt.points_earned ?? attempt.correct}</span> / {attempt.points_total} pts</span>
            )}
          </p>

          {/* Stats row */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { icon: <CheckCircle2 className="w-5 h-5" />, value: attempt.correct,  label: 'Correct',  color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
              { icon: <XCircle      className="w-5 h-5" />, value: attempt.wrong,    label: 'Wrong',    color: 'text-red-400',     bg: 'bg-red-500/10',     border: 'border-red-500/20'     },
              { icon: <MinusCircle  className="w-5 h-5" />, value: attempt.skipped,  label: 'Skipped',  color: 'text-yellow-400',  bg: 'bg-yellow-500/10',  border: 'border-yellow-500/20'  },
              { icon: <Clock        className="w-5 h-5" />, value: formatTime(attempt.time_taken), label: 'Time', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
            ].map((stat, i) => (
              <div key={i} className={`flex flex-col items-center gap-1.5 py-4 rounded-2xl border ${stat.bg} ${stat.border}`}>
                <span className={stat.color}>{stat.icon}</span>
                <span className={`text-xl font-bold ${stat.color}`}>{stat.value}</span>
                <span className="text-dark-500 text-xs">{stat.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── AI Feedback Card ── */}
        {attempt.ai_feedback && (
          <div className="bg-dark-900 border border-primary-500/25 rounded-2xl p-6 shadow-lg">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 rounded-xl bg-primary-500/15 flex items-center justify-center flex-shrink-0">
                <Brain className="w-4 h-4 text-primary-400" />
              </div>
              <h2 className="text-white font-semibold text-sm">AI Study Recommendations</h2>
              <span className="text-xs text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded-full">Powered by Gemini</span>
            </div>
            <p className="text-dark-300 text-sm leading-relaxed pl-11">{attempt.ai_feedback}</p>
          </div>
        )}

        {/* ── Question Breakdown ── */}
        <div>
          <h2 className="text-white font-semibold text-lg mb-4 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-primary-400" />
            Question Breakdown
          </h2>

          <div className="space-y-3">
            {quiz?.questions?.map((q, idx) => {
              const userAnswer = answers[String(q.id)];
              const status     = getQuestionStatus(q, userAnswer, questionResults);

              // ── Colour / icon per status ──────────────────────────────────
              let borderColor, bgColor, iconEl, labelText, labelColor;

              if (status === 'correct') {
                borderColor = 'border-emerald-500/40';
                bgColor     = 'bg-emerald-500/5';
                iconEl      = <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />;
                labelText   = 'Correct';
                labelColor  = 'text-emerald-400';
              } else if (status === 'wrong') {
                borderColor = 'border-red-500/40';
                bgColor     = 'bg-red-500/5';
                iconEl      = <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />;
                labelText   = 'Wrong';
                labelColor  = 'text-red-400';
              } else if (status === 'ai_graded') {
                // Short-answer: server scores it; we can't know result here, flag as AI graded
                borderColor = 'border-primary-500/30';
                bgColor     = 'bg-primary-500/5';
                iconEl      = <Brain className="w-5 h-5 text-primary-400 flex-shrink-0" />;
                labelText   = 'AI Graded';
                labelColor  = 'text-primary-400';
              } else if (status === 'submitted') {
                // matching / ordering / numeric — server graded, no client result
                borderColor = 'border-dark-600';
                bgColor     = 'bg-dark-800/30';
                iconEl      = <CheckCircle2 className="w-5 h-5 text-dark-500 flex-shrink-0" />;
                labelText   = 'Submitted';
                labelColor  = 'text-dark-500';
              } else {
                // skipped
                borderColor = 'border-yellow-500/30';
                bgColor     = 'bg-yellow-500/5';
                iconEl      = <MinusCircle className="w-5 h-5 text-yellow-400 flex-shrink-0" />;
                labelText   = 'Not answered';
                labelColor  = 'text-yellow-400';
              }

              return (
                <div key={q.id} className={`flex items-center gap-4 px-5 py-4 border rounded-2xl ${borderColor} ${bgColor}`}>
                  {/* Status icon */}
                  {iconEl}

                  {/* Question number + text */}
                  <div className="flex-1 min-w-0">
                    {q.type && q.type !== 'mcq' && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-dark-700 text-dark-400 font-medium mb-1 inline-block capitalize">
                        {q.type.replace(/_/g, ' ')}
                      </span>
                    )}
                    <p className="text-dark-100 text-sm leading-snug">
                      <span className="text-dark-500 mr-2">Q{idx + 1}.</span>
                      {q.question_text}
                    </p>
                  </div>

                  {/* Status label pill */}
                  <span className={`text-xs font-semibold flex-shrink-0 ${labelColor}`}>
                    {labelText}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Bottom Actions ── */}
        <div className="flex flex-col sm:flex-row gap-3 pb-8">
          <button
            onClick={() => navigate(`/quiz/${quizId}`)}
            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl border border-dark-700 text-dark-300 hover:border-dark-600 hover:text-white text-sm font-medium transition-all"
          >
            <RotateCcw className="w-4 h-4" /> Retake Quiz
          </button>
          <button
            onClick={() => handleExport('txt', true)}
            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl border border-dark-700 text-dark-300 hover:border-dark-600 hover:text-white text-sm font-medium transition-all"
          >
            <Download className="w-4 h-4" /> Download Quiz
          </button>
          <button
            onClick={() => navigate('/upload')}
            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium transition-all"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Documents
          </button>
        </div>
      </div>
    </div>
  );
}
