import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  BookOpen, BarChart3, Clock, FileText,
  Upload, Brain, ArrowRight, Sparkles,
  RotateCcw, Loader2, Trophy,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/ui/Card';
import api from '../../services/api';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatStudyTime(secs) {
  if (!secs || secs === 0) return '0 min';
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m} min`;
}

function formatDate(dt) {
  return new Date(dt).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  });
}

function getDifficultyColor(d) {
  if (d === 'easy')   return 'text-emerald-400 bg-emerald-500/10';
  if (d === 'hard')   return 'text-red-400 bg-red-500/10';
  return 'text-yellow-400 bg-yellow-500/10';
}

function getScoreBadge(pct) {
  if (pct >= 80) return 'text-emerald-400';
  if (pct >= 50) return 'text-yellow-400';
  return 'text-red-400';
}

// ─── Stat card config (dynamic values from API) ───────────────────────────────

function buildStatCards(stats) {
  return [
    {
      label: 'Total Quizzes',
      value: stats.total_quizzes,
      icon: BookOpen,
      gradient: 'from-primary-500 to-primary-700',
      bgColor: 'bg-primary-500/10',
      textColor: 'text-primary-400',
      barWidth: Math.min(100, stats.total_quizzes * 10),
    },
    {
      label: 'Avg Score',
      value: `${stats.avg_score}%`,
      icon: BarChart3,
      gradient: 'from-emerald-500 to-emerald-700',
      bgColor: 'bg-emerald-500/10',
      textColor: 'text-emerald-400',
      barWidth: Math.round(stats.avg_score),
    },
    {
      label: 'Study Time',
      value: formatStudyTime(stats.total_study_time),
      icon: Clock,
      gradient: 'from-amber-500 to-amber-700',
      bgColor: 'bg-amber-500/10',
      textColor: 'text-amber-400',
      barWidth: Math.min(100, Math.floor(stats.total_study_time / 36)),
    },
    {
      label: 'Documents',
      value: stats.total_documents,
      icon: FileText,
      gradient: 'from-rose-500 to-rose-700',
      bgColor: 'bg-rose-500/10',
      textColor: 'text-rose-400',
      barWidth: Math.min(100, stats.total_documents * 20),
    },
  ];
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const { user } = useAuth();
  const navigate  = useNavigate();

  const [stats, setStats]       = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get('/api/analytics/dashboard');
        setStats(res.data);
      } catch {
        // Non-critical: show zeros on error
        setStats({
          total_quizzes: 0, total_attempts: 0, avg_score: 0,
          total_study_time: 0, total_documents: 0, recent_attempts: [],
        });
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, []);

  const statCards = stats ? buildStatCards(stats) : [];

  return (
    <div className="space-y-8 animate-fade-in">

      {/* ── Welcome header ── */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">
          Welcome back,{' '}
          <span className="gradient-text">{user?.name?.split(' ')[0] || 'User'}</span>
        </h1>
        <p className="text-dark-400 text-lg">
          Here&apos;s an overview of your learning progress
        </p>
      </div>

      {/* ── Stat cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <Card key={i}>
                <div className="animate-pulse space-y-3">
                  <div className="h-3 w-24 bg-dark-700 rounded" />
                  <div className="h-8 w-16 bg-dark-700 rounded" />
                  <div className="h-1 bg-dark-700 rounded" />
                </div>
              </Card>
            ))
          : statCards.map((stat) => (
              <Card key={stat.label} hover>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-dark-400 mb-1">{stat.label}</p>
                    <p className="text-3xl font-bold text-white">{stat.value}</p>
                  </div>
                  <div className={`w-11 h-11 rounded-xl ${stat.bgColor} flex items-center justify-center`}>
                    <stat.icon className={`w-5 h-5 ${stat.textColor}`} />
                  </div>
                </div>
                {/* Progress bar */}
                <div className="mt-4 h-1 rounded-full bg-dark-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full bg-gradient-to-r ${stat.gradient} transition-all duration-700`}
                    style={{ width: `${stat.barWidth}%` }}
                  />
                </div>
              </Card>
            ))
        }
      </div>

      {/* ── Recent Activity ── */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <Trophy className="w-5 h-5 text-primary-400" />
            Recent Activity
          </h2>
          <Link
            to="/upload"
            className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1 transition-colors"
          >
            Upload more <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {isLoading ? (
          <Card>
            <div className="animate-pulse space-y-4 py-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-12 bg-dark-700 rounded-xl" />
              ))}
            </div>
          </Card>
        ) : stats?.recent_attempts?.length === 0 ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-16 h-16 rounded-2xl bg-primary-500/10 flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-primary-400" />
              </div>
              <h3 className="text-lg font-medium text-dark-200 mb-2">No quizzes yet!</h3>
              <p className="text-dark-400 max-w-sm mb-6">
                Upload a document to get started. Our AI will generate personalized quizzes from your study materials.
              </p>
              <Link
                to="/upload"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 text-white text-sm font-medium hover:from-primary-500 hover:to-primary-400 transition-all duration-300 shadow-lg shadow-primary-500/25"
              >
                <Upload className="w-4 h-4" />
                Upload Document
              </Link>
            </div>
          </Card>
        ) : (
          <Card>
            <div className="divide-y divide-dark-800">
              {stats.recent_attempts.map((attempt) => (
                <div key={attempt.attempt_id} className="flex items-center gap-4 py-3.5 first:pt-0 last:pb-0">
                  {/* Score badge */}
                  <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-dark-800 flex flex-col items-center justify-center">
                    <span className={`text-sm font-bold ${getScoreBadge(attempt.percentage)}`}>
                      {Math.round(attempt.percentage)}%
                    </span>
                  </div>

                  {/* Quiz info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-dark-100 text-sm font-medium truncate">{attempt.quiz_title}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`text-xs px-1.5 py-0.5 rounded-md font-medium capitalize ${getDifficultyColor(attempt.difficulty)}`}>
                        {attempt.difficulty}
                      </span>
                      <span className="text-dark-500 text-xs">
                        {attempt.score}/{attempt.total} correct · {formatDate(attempt.attempted_at)}
                      </span>
                    </div>
                  </div>

                  {/* Retake button */}
                  <button
                    onClick={() => navigate(`/quiz/${attempt.quiz_id}`)}
                    className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dark-700 text-dark-400 hover:text-primary-400 hover:border-primary-500/40 text-xs transition-all"
                  >
                    <RotateCcw className="w-3 h-3" /> Retake
                  </button>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* ── Quick Actions ── */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { title: 'Upload Document', desc: 'Upload study materials to generate a quiz', icon: Upload, path: '/upload', gradient: 'from-primary-500 to-blue-600' },
            { title: 'Generate Quiz with AI', desc: 'Pick any uploaded document and start a quiz', icon: Brain, path: '/upload', gradient: 'from-purple-500 to-primary-600' },
          ].map((action) => (
            <Link key={action.title} to={action.path}>
              <div className="group flex items-center gap-4 p-5 rounded-2xl border border-dark-700 bg-dark-900/50 hover:border-primary-500/40 hover:bg-dark-800/60 transition-all duration-200">
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${action.gradient} flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform duration-200`}>
                  <action.icon className="w-5 h-5 text-white" />
                </div>
                <div className="min-w-0">
                  <p className="text-white text-sm font-semibold">{action.title}</p>
                  <p className="text-dark-400 text-xs mt-0.5">{action.desc}</p>
                </div>
                <ArrowRight className="w-4 h-4 text-dark-600 group-hover:text-primary-400 ml-auto flex-shrink-0 transition-colors" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
