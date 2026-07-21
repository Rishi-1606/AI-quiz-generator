import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import {
  CheckCircle2, XCircle, MinusCircle, Clock,
  Trophy, ArrowLeft, RotateCcw, Loader2, BookOpen,
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

const OPTION_LETTERS = ['A', 'B', 'C', 'D'];

// ─── Component ────────────────────────────────────────────────────────────────

export default function QuizResults() {
  const { quizId }  = useParams();
  const location    = useLocation();
  const navigate    = useNavigate();

  // Results can come via navigation state (immediate) or fetched fresh
  const [attempt, setAttempt] = useState(location.state?.attempt ?? null);
  const [quiz,    setQuiz]    = useState(location.state?.quiz    ?? null);
  const [isLoading, setIsLoading] = useState(!attempt || !quiz);
  const [error,     setError]     = useState('');

  useEffect(() => {
    if (attempt && quiz) return; // already have data from navigation state
    const fetchData = async () => {
      try {
        const quizRes = await api.get(`/api/quizzes/${quizId}`);
        setQuiz(quizRes.data);
        // Attempt must have been passed via state; if not, show error
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
          {/* Score ring */}
          <div className="inline-flex items-center justify-center w-28 h-28 rounded-full bg-dark-800 border-4 border-primary-500/40 mb-5">
            <span className="text-4xl font-black text-white">{Math.round(attempt.percentage)}<span className="text-lg text-dark-400">%</span></span>
          </div>

          <p className={`text-xl font-bold mb-1 ${scoreColor}`}>{scoreLabel}</p>
          <p className="text-dark-400 text-sm mb-8">
            You scored <span className="text-white font-semibold">{attempt.correct}</span> out of{' '}
            <span className="text-white font-semibold">{attempt.total}</span> questions
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

        {/* ── Question Breakdown ── */}
        <div>
          <h2 className="text-white font-semibold text-lg mb-4 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-primary-400" />
            Question Breakdown
          </h2>

          <div className="space-y-4">
            {quiz?.questions?.map((q, idx) => {
              const userChoice    = answers[String(q.id)];
              const isCorrect     = userChoice === q.correct_option;
              const isSkipped     = userChoice === undefined || userChoice === null;

              let statusColor  = 'border-yellow-500/30 bg-yellow-500/5';
              let statusIcon   = <MinusCircle className="w-5 h-5 text-yellow-400 flex-shrink-0" />;
              if (!isSkipped && isCorrect)  { statusColor = 'border-emerald-500/30 bg-emerald-500/5'; statusIcon = <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />; }
              if (!isSkipped && !isCorrect) { statusColor = 'border-red-500/30 bg-red-500/5';         statusIcon = <XCircle      className="w-5 h-5 text-red-400 flex-shrink-0"     />; }

              return (
                <div key={q.id} className={`border rounded-2xl p-5 ${statusColor}`}>
                  {/* Question text */}
                  <div className="flex items-start gap-3 mb-4">
                    {statusIcon}
                    <p className="text-dark-100 text-sm font-medium leading-relaxed">
                      <span className="text-dark-400 mr-2">Q{idx + 1}.</span>{q.question_text}
                    </p>
                  </div>

                  {/* Options */}
                  <div className="space-y-2 ml-8">
                    {q.options.map((option, oi) => {
                      const isUserPick    = userChoice === oi;
                      const isCorrectOpt  = q.correct_option === oi;

                      let optClass = 'border-dark-700 bg-dark-800/50 text-dark-400';
                      if (isCorrectOpt)              optClass = 'border-emerald-500/50 bg-emerald-500/10 text-emerald-300';
                      if (isUserPick && !isCorrect)  optClass = 'border-red-500/50 bg-red-500/10 text-red-300';

                      return (
                        <div key={oi} className={`flex items-center gap-3 px-3 py-2 rounded-xl border text-sm ${optClass}`}>
                          <span className="font-bold text-xs w-5 text-center">{OPTION_LETTERS[oi]}</span>
                          <span className="flex-1">{option}</span>
                          {isCorrectOpt && <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />}
                          {isUserPick && !isCorrect && <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />}
                        </div>
                      );
                    })}
                  </div>

                  {/* Explanation */}
                  {q.explanation && (
                    <div className="ml-8 mt-3 px-3 py-2 rounded-xl bg-dark-800/60 border border-dark-700">
                      <p className="text-dark-400 text-xs leading-relaxed">
                        <span className="text-primary-400 font-semibold">Explanation: </span>
                        {q.explanation}
                      </p>
                    </div>
                  )}
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
