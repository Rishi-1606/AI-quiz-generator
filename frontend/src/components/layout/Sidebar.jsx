import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  BookOpen,
  Layers,
  BarChart3,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Upload', path: '/upload', icon: Upload },
  { name: 'Quizzes', path: '/quizzes', icon: BookOpen },
  { name: 'Flashcards', path: '/flashcards', icon: Layers },
  { name: 'Analytics', path: '/analytics', icon: BarChart3 },
  { name: 'AI Tutor', path: '/ai-tutor', icon: MessageSquare },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const { user } = useAuth();

  const roleBadgeColors = {
    student: 'bg-primary-500/20 text-primary-400',
    teacher: 'bg-emerald-500/20 text-emerald-400',
    admin: 'bg-amber-500/20 text-amber-400',
  };

  return (
    <aside
      className={`
        hidden lg:flex flex-col h-[calc(100vh-4rem)] glass border-r border-dark-700/50
        transition-all duration-300 ease-out
        ${collapsed ? 'w-20' : 'w-64'}
      `}
    >
      {/* Nav items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;

          return (
            <Link
              key={item.path}
              to={item.path}
              title={collapsed ? item.name : undefined}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium
                transition-all duration-200 group
                ${
                  isActive
                    ? 'bg-primary-500/10 text-primary-400 shadow-sm shadow-primary-500/5'
                    : 'text-dark-400 hover:text-dark-100 hover:bg-dark-800/50'
                }
              `}
            >
              <Icon
                className={`w-5 h-5 flex-shrink-0 transition-colors duration-200 ${
                  isActive
                    ? 'text-primary-400'
                    : 'text-dark-500 group-hover:text-dark-300'
                }`}
              />
              {!collapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* User info at bottom */}
      {!collapsed && user && (
        <div className="px-4 py-4 border-t border-dark-700/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
              {user.name
                ?.split(' ')
                .map((n) => n[0])
                .join('')
                .toUpperCase()
                .slice(0, 2)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-dark-200 truncate">
                {user.name}
              </p>
              <span
                className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium capitalize ${
                  roleBadgeColors[user.role] || roleBadgeColors.student
                }`}
              >
                {user.role || 'Student'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Collapse toggle */}
      <div className="px-3 py-3 border-t border-dark-700/50">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-sm text-dark-400 hover:text-dark-100 hover:bg-dark-800/50 transition-all duration-200"
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
