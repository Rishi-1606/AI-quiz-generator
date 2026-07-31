import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen, Search, Trash2, RotateCcw, Download,
  Sparkles, Loader2, ChevronDown, Filter,
} from 'lucide-react';
import Card from '../../components/ui/Card';
import api from '../../services/api';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(dt) {
  return new Date(dt).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  });
}

function getDifficultyStyle(d) {
  if (d === 'easy')   return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
  if (d === 'hard')   return 'text-red-400 bg-red-500/10 border-red-500/20';
  return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function Quizzes() {
  const navigate = useNavigate();

  const [quizzes, setQuizzes]       = useState([]);
  const [isLoading, setIsLoading]   = useState(true);
  const [search, setSearch]         = useState('');
  const [filter, setFilter]         = useState('all');   // all | easy | medium | hard
  const [deletingId, setDeletingId] = useState(null);
  const [showExport, setShowExport] = useState(null);    // quiz id with open dropdown

  const fetchQuizzes = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/api/quizzes');
      setQuizzes(res.data);
    } catch {
      setQuizzes([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { fetchQuizzes(); }, [fetchQuizzes]);

  // Close export dropdown when clicking outside
  useEffect(() => {
    const close = () => setShowExport(null);
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, []);

  const handleDelete = async (quizId, title) => {
    if (!window.confirm(`Delete "${title}"?\nThis will also remove all attempts.`)) return;
    setDeletingId(quizId);
    try {
      await api.delete(`/api/quizzes/${quizId}`);
      setQuizzes(prev => prev.filter(q => q.id !== quizId));
    } catch {
      alert('Failed to delete quiz. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleExport = (quizId, format, includeAnswers, e) => {
    e.stopPropagation();
    const token = localStorage.getItem('token');
    const url = `http://localhost:8000/api/quizzes/${quizId}/export?format=${format}&include_answers=${includeAnswers}`;
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.blob())
      .then(blob => {
        const ext = format === 'json' ? 'json' : 'txt';
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `quiz_${quizId}.${ext}`;
        a.click();
        URL.revokeObjectURL(a.href);
      });
    setShowExport(null);
  };

  // ── Filtering ────────────────────────────────────────────────────────────────
  const filtered = quizzes.filter(q => {
    const matchSearch = q.title.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === 'all' || q.difficulty === filter;
    return matchSearch && matchFilter;
  });

  // ─── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-primary-400" /> My Quizzes
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            {quizzes.length} quiz{quizzes.length !== 1 ? 'zes' : ''} generated
          </p>
        </div>
        <button
          onClick={() => navigate('/upload')}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium transition-all"
        >
          <Sparkles className="w-4 h-4" /> Generate New
        </button>
      </div>

      {/* Search + Filter bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
          <input
            type="text"
            placeholder="Search quizzes…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-dark-800 border border-dark-700 rounded-xl text-dark-100 text-sm placeholder-dark-500 focus:outline-none focus:border-primary-500/50 transition-colors"
          />
        </div>

        {/* Difficulty filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-dark-500 flex-shrink-0" />
          {['all', 'easy', 'medium', 'hard'].map(d => (
            <button
              key={d}
              onClick={() => setFilter(d)}
              className={`px-3 py-2 rounded-xl text-xs font-semibold capitalize transition-all border ${
                filter === d
                  ? d === 'all'    ? 'bg-primary-500/15 border-primary-500/40 text-primary-400'
                  : d === 'easy'   ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400'
                  : d === 'medium' ? 'bg-yellow-500/15 border-yellow-500/40 text-yellow-400'
                  :                  'bg-red-500/15 border-red-500/40 text-red-400'
                  : 'bg-dark-800 border-dark-700 text-dark-400 hover:border-dark-600'
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <div className="flex flex-col items-center justify-center py-14 text-center">
            <div className="w-16 h-16 rounded-2xl bg-primary-500/10 flex items-center justify-center mb-4">
              <BookOpen className="w-8 h-8 text-primary-400" />
            </div>
            <h3 className="text-lg font-medium text-dark-200 mb-2">
              {search || filter !== 'all' ? 'No quizzes match your search' : 'No quizzes yet!'}
            </h3>
            <p className="text-dark-400 text-sm max-w-xs mb-5">
              {search || filter !== 'all'
                ? 'Try a different search term or difficulty filter.'
                : 'Upload a document and generate your first quiz!'}
            </p>
            {!search && filter === 'all' && (
              <button
                onClick={() => navigate('/upload')}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium transition-all"
              >
                <Sparkles className="w-4 h-4" /> Upload & Generate
              </button>
            )}
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(quiz => (
            <Card key={quiz.id} hover className="flex flex-col">
              {/* Card header */}
              <div className="flex items-start justify-between gap-2 mb-3">
                <h3 className="text-dark-100 font-semibold text-sm leading-snug line-clamp-2 flex-1">
                  {quiz.title}
                </h3>
                <span className={`flex-shrink-0 text-xs px-2 py-1 rounded-lg border font-medium capitalize ${getDifficultyStyle(quiz.difficulty)}`}>
                  {quiz.difficulty}
                </span>
              </div>

              {/* Stats row */}
              <div className="flex items-center gap-4 text-xs text-dark-500 mb-4">
                <span>📝 {quiz.total_questions} questions</span>
                <span>⏱ {Math.round(quiz.time_limit / 60)} min</span>
                <span className="ml-auto">{formatDate(quiz.created_at)}</span>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 mt-auto pt-3 border-t border-dark-800">
                {/* Take quiz */}
                <button
                  onClick={() => navigate(`/quiz/${quiz.id}`)}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-xs font-medium transition-all"
                >
                  <RotateCcw className="w-3.5 h-3.5" /> Take Quiz
                </button>

                {/* Export dropdown */}
                <div className="relative">
                  <button
                    onClick={(e) => { e.stopPropagation(); setShowExport(showExport === quiz.id ? null : quiz.id); }}
                    className="p-2 rounded-xl border border-dark-700 text-dark-400 hover:text-white hover:border-dark-600 transition-all"
                    title="Export"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                  {showExport === quiz.id && (
                    <div className="absolute bottom-10 right-0 z-50 w-48 bg-dark-800 border border-dark-700 rounded-xl shadow-2xl overflow-hidden">
                      <p className="px-3 py-1.5 text-dark-500 text-xs font-semibold uppercase tracking-wide">With Answers</p>
                      <button onClick={(e) => handleExport(quiz.id, 'txt', true, e)}  className="w-full text-left px-4 py-2 text-xs text-dark-300 hover:bg-dark-700 hover:text-white">.txt (with answers)</button>
                      <button onClick={(e) => handleExport(quiz.id, 'json', true, e)} className="w-full text-left px-4 py-2 text-xs text-dark-300 hover:bg-dark-700 hover:text-white">.json (with answers)</button>
                      <p className="px-3 py-1.5 text-dark-500 text-xs font-semibold uppercase tracking-wide border-t border-dark-700">Practice</p>
                      <button onClick={(e) => handleExport(quiz.id, 'txt', false, e)} className="w-full text-left px-4 py-2 text-xs text-dark-300 hover:bg-dark-700 hover:text-white">.txt (no answers)</button>
                    </div>
                  )}
                </div>

                {/* Delete */}
                <button
                  onClick={() => handleDelete(quiz.id, quiz.title)}
                  disabled={deletingId === quiz.id}
                  className="p-2 rounded-xl border border-dark-700 text-dark-400 hover:text-red-400 hover:border-red-500/40 transition-all disabled:opacity-50"
                  title="Delete quiz"
                >
                  {deletingId === quiz.id
                    ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    : <Trash2 className="w-3.5 h-3.5" />}
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
