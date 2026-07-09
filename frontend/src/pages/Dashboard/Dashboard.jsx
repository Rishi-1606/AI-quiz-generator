import { Link } from 'react-router-dom';
import {
  BookOpen,
  BarChart3,
  Clock,
  FileText,
  Upload,
  Brain,
  Layers,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/ui/Card';

const statCards = [
  {
    label: 'Total Quizzes',
    value: '0',
    icon: BookOpen,
    gradient: 'from-primary-500 to-primary-700',
    shadowColor: 'shadow-primary-500/20',
    bgColor: 'bg-primary-500/10',
    textColor: 'text-primary-400',
  },
  {
    label: 'Average Score',
    value: '0%',
    icon: BarChart3,
    gradient: 'from-emerald-500 to-emerald-700',
    shadowColor: 'shadow-emerald-500/20',
    bgColor: 'bg-emerald-500/10',
    textColor: 'text-emerald-400',
  },
  {
    label: 'Study Time',
    value: '0h',
    icon: Clock,
    gradient: 'from-amber-500 to-amber-700',
    shadowColor: 'shadow-amber-500/20',
    bgColor: 'bg-amber-500/10',
    textColor: 'text-amber-400',
  },
  {
    label: 'Documents',
    value: '0',
    icon: FileText,
    gradient: 'from-rose-500 to-rose-700',
    shadowColor: 'shadow-rose-500/20',
    bgColor: 'bg-rose-500/10',
    textColor: 'text-rose-400',
  },
];

const quickActions = [
  {
    title: 'Upload Document',
    description: 'Upload your study materials',
    icon: Upload,
    path: '/upload',
    gradient: 'from-primary-500 to-blue-600',
  },
  {
    title: 'Generate Quiz',
    description: 'Create AI-powered quizzes',
    icon: Brain,
    path: '/quizzes',
    gradient: 'from-purple-500 to-primary-600',
  },
  {
    title: 'Study Flashcards',
    description: 'Review with flashcards',
    icon: Layers,
    path: '/flashcards',
    gradient: 'from-primary-600 to-violet-600',
  },
];

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome header */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">
          Welcome back,{' '}
          <span className="gradient-text">{user?.name?.split(' ')[0] || 'User'}</span>
        </h1>
        <p className="text-dark-400 text-lg">
          Here&apos;s an overview of your learning progress
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 stagger-fade-in">
        {statCards.map((stat) => (
          <Card key={stat.label} hover>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-dark-400 mb-1">{stat.label}</p>
                <p className="text-3xl font-bold text-white">{stat.value}</p>
              </div>
              <div
                className={`w-11 h-11 rounded-xl ${stat.bgColor} flex items-center justify-center`}
              >
                <stat.icon className={`w-5 h-5 ${stat.textColor}`} />
              </div>
            </div>
            {/* Accent gradient bar */}
            <div className="mt-4 h-1 rounded-full bg-dark-800 overflow-hidden">
              <div
                className={`h-full w-0 rounded-full bg-gradient-to-r ${stat.gradient}`}
              />
            </div>
          </Card>
        ))}
      </div>

      {/* Recent Quizzes */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">Recent Quizzes</h2>
          <Link
            to="/quizzes"
            className="text-sm text-primary-400 hover:text-primary-300 flex items-center gap-1 transition-colors"
          >
            View all <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-16 h-16 rounded-2xl bg-primary-500/10 flex items-center justify-center mb-4">
              <Sparkles className="w-8 h-8 text-primary-400" />
            </div>
            <h3 className="text-lg font-medium text-dark-200 mb-2">
              No quizzes yet!
            </h3>
            <p className="text-dark-400 max-w-sm mb-6">
              Upload a document to get started. Our AI will generate personalized
              quizzes from your study materials.
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
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 stagger-fade-in">
          {quickActions.map((action) => (
            <Link key={action.title} to={action.path}>
              <div className="group relative glass rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-primary-500/5 overflow-hidden">
                {/* Gradient border on hover */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-r opacity-0 group-hover:opacity-100 transition-opacity duration-300 p-px"
                  style={{
                    backgroundImage: `linear-gradient(135deg, var(--color-primary-500), var(--color-primary-700))`,
                  }}
                >
                  <div className="w-full h-full rounded-2xl bg-dark-900/95" />
                </div>

                <div className="relative z-10">
                  <div
                    className={`w-12 h-12 rounded-xl bg-gradient-to-br ${action.gradient} flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform duration-300`}
                  >
                    <action.icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-base font-semibold text-white mb-1">
                    {action.title}
                  </h3>
                  <p className="text-sm text-dark-400">{action.description}</p>
                  <div className="mt-4 flex items-center gap-1 text-primary-400 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    Get started <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
