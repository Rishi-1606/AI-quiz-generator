import { useState, useEffect } from 'react';
import {
  User, Mail, BookOpen, Target, Clock,
  Edit3, Check, X, Loader2, Shield,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/ui/Card';
import api from '../../services/api';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(dt) {
  return new Date(dt).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'long', year: 'numeric',
  });
}

function getInitials(name) {
  return (name || '')
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

// ─── Editable field component ─────────────────────────────────────────────────

function EditableField({ label, value, onSave, multiline = false, placeholder = '' }) {
  const [editing, setEditing] = useState(false);
  const [draft,   setDraft]   = useState(value || '');
  const [saving,  setSaving]  = useState(false);

  const handleSave = async () => {
    setSaving(true);
    await onSave(draft.trim());
    setSaving(false);
    setEditing(false);
  };

  const handleCancel = () => { setDraft(value || ''); setEditing(false); };

  return (
    <div className="group">
      <div className="flex items-center justify-between mb-1">
        <p className="text-dark-400 text-xs font-medium uppercase tracking-wide">{label}</p>
        {!editing && (
          <button
            onClick={() => setEditing(true)}
            className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-lg text-dark-500 hover:text-primary-400"
          >
            <Edit3 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {editing ? (
        <div className="flex items-start gap-2">
          {multiline ? (
            <textarea
              value={draft}
              onChange={e => setDraft(e.target.value)}
              placeholder={placeholder}
              rows={3}
              className="flex-1 px-3 py-2 bg-dark-800 border border-primary-500/50 rounded-xl text-dark-100 text-sm resize-none focus:outline-none"
              autoFocus
            />
          ) : (
            <input
              value={draft}
              onChange={e => setDraft(e.target.value)}
              placeholder={placeholder}
              className="flex-1 px-3 py-2 bg-dark-800 border border-primary-500/50 rounded-xl text-dark-100 text-sm focus:outline-none"
              autoFocus
              onKeyDown={e => { if (e.key === 'Enter') handleSave(); if (e.key === 'Escape') handleCancel(); }}
            />
          )}
          <div className="flex gap-1 pt-1">
            <button onClick={handleSave} disabled={saving} className="p-1.5 rounded-lg bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25 transition-all">
              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
            </button>
            <button onClick={handleCancel} className="p-1.5 rounded-lg bg-dark-700 text-dark-400 hover:text-white transition-all">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      ) : (
        <p className={`text-sm ${value ? 'text-dark-100' : 'text-dark-600 italic'}`}>
          {value || placeholder || '—'}
        </p>
      )}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function Profile() {
  const { user: authUser, fetchUser } = useAuth();

  const [profile, setProfile]   = useState(null);
  const [stats,   setStats]     = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [profileRes, statsRes] = await Promise.all([
          api.get('/api/profile'),
          api.get('/api/analytics/dashboard'),
        ]);
        setProfile(profileRes.data);
        setStats(statsRes.data);
      } catch {
        setProfile(authUser);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  const updateField = async (field, value) => {
    try {
      const res = await api.patch('/api/profile', { [field]: value });
      setProfile(res.data);
    } catch {
      // silently fail — field stays unchanged
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
      </div>
    );
  }

  const todayAttempts  = stats?.recent_attempts?.filter(a => {
    const d = new Date(a.attempted_at);
    const today = new Date();
    return d.toDateString() === today.toDateString();
  }).length ?? 0;

  const goalPct = Math.min(100, Math.round((todayAttempts / (profile?.daily_goal || 1)) * 100));

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">

      {/* ── Header card ── */}
      <Card>
        <div className="flex items-center gap-5">
          {/* Avatar */}
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-2xl font-bold text-white flex-shrink-0 shadow-lg shadow-primary-500/25">
            {getInitials(profile?.name)}
          </div>

          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-white">{profile?.name}</h1>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs px-2 py-0.5 rounded-full bg-primary-500/15 text-primary-400 border border-primary-500/20 font-medium capitalize">
                {profile?.role || 'Student'}
              </span>
              <span className="text-dark-500 text-xs flex items-center gap-1">
                <Clock className="w-3 h-3" /> Joined {formatDate(profile?.created_at)}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* ── Stats row ── */}
      {stats && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Quizzes',   value: stats.total_quizzes,   icon: BookOpen,  color: 'text-primary-400',  bg: 'bg-primary-500/10' },
            { label: 'Avg Score', value: `${stats.avg_score}%`, icon: Target,    color: 'text-emerald-400',  bg: 'bg-emerald-500/10' },
            { label: 'Documents', value: stats.total_documents, icon: Shield,    color: 'text-amber-400',    bg: 'bg-amber-500/10'   },
          ].map(s => (
            <Card key={s.label}>
              <div className="flex items-center gap-3">
                <div className={`w-9 h-9 rounded-xl ${s.bg} flex items-center justify-center flex-shrink-0`}>
                  <s.icon className={`w-4 h-4 ${s.color}`} />
                </div>
                <div>
                  <p className="text-white font-bold text-lg leading-none">{s.value}</p>
                  <p className="text-dark-400 text-xs mt-0.5">{s.label}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* ── Editable profile fields ── */}
      <Card>
        <h2 className="text-white font-semibold text-sm mb-5 flex items-center gap-2">
          <User className="w-4 h-4 text-primary-400" /> Profile Information
          <span className="text-dark-500 text-xs font-normal ml-1">hover a field to edit</span>
        </h2>

        <div className="space-y-5">
          <EditableField
            label="Display Name"
            value={profile?.name}
            placeholder="Your full name"
            onSave={val => updateField('name', val)}
          />

          {/* Email (read-only) */}
          <div>
            <p className="text-dark-400 text-xs font-medium uppercase tracking-wide mb-1">Email</p>
            <div className="flex items-center gap-2">
              <Mail className="w-3.5 h-3.5 text-dark-500" />
              <p className="text-dark-300 text-sm">{profile?.email}</p>
              <span className="text-xs text-dark-600">(cannot be changed)</span>
            </div>
          </div>

          <EditableField
            label="Bio"
            value={profile?.bio}
            placeholder="Tell us a little about yourself…"
            multiline
            onSave={val => updateField('bio', val)}
          />
        </div>
      </Card>

      {/* ── Daily Goal ── */}
      <Card>
        <h2 className="text-white font-semibold text-sm mb-5 flex items-center gap-2">
          <Target className="w-4 h-4 text-emerald-400" /> Daily Learning Goal
        </h2>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-100 text-sm">Today&apos;s Progress</p>
              <p className="text-dark-400 text-xs mt-0.5">
                {todayAttempts} / {profile?.daily_goal} quiz{profile?.daily_goal !== 1 ? 'zes' : ''} completed
              </p>
            </div>
            <span className={`text-lg font-bold ${goalPct >= 100 ? 'text-emerald-400' : 'text-primary-400'}`}>
              {goalPct >= 100 ? '🏆 Done!' : `${goalPct}%`}
            </span>
          </div>

          {/* Progress bar */}
          <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${goalPct >= 100 ? 'bg-gradient-to-r from-emerald-500 to-emerald-400' : 'bg-gradient-to-r from-primary-600 to-primary-400'}`}
              style={{ width: `${goalPct}%` }}
            />
          </div>

          {/* Goal slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-dark-300 text-sm">Daily Target</p>
              <span className="text-white font-bold">{profile?.daily_goal} quiz{profile?.daily_goal !== 1 ? 'zes' : ''}/day</span>
            </div>
            <input
              type="range" min={1} max={10}
              value={profile?.daily_goal || 1}
              onChange={async (e) => {
                const val = Number(e.target.value);
                setProfile(p => ({ ...p, daily_goal: val }));
                await updateField('daily_goal', val);
              }}
              className="w-full accent-primary-500 cursor-pointer"
            />
            <div className="flex justify-between text-dark-500 text-xs mt-1"><span>1</span><span>10</span></div>
          </div>
        </div>
      </Card>
    </div>
  );
}
