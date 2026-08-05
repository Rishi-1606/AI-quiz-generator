import { useState } from 'react';
import { X, Brain, Loader2, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const DIFFICULTY_OPTIONS = [
  { value: 'easy',   label: 'Easy',   color: 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400' },
  { value: 'medium', label: 'Medium', color: 'border-yellow-500/50 bg-yellow-500/10 text-yellow-400' },
  { value: 'hard',   label: 'Hard',   color: 'border-red-500/50 bg-red-500/10 text-red-400' },
];

const QUESTION_TYPES = [
  { value: 'mcq',          label: 'MCQ',           desc: '4-option multiple choice' },
  { value: 'true_false',   label: 'True / False',  desc: 'Binary true or false'     },
  { value: 'fill_blank',   label: 'Fill in Blank', desc: 'Complete the sentence'    },
  { value: 'short_answer', label: 'Short Answer',  desc: 'AI-evaluated open text'   },
];

const TOPIC_SUGGESTIONS = [
  'Python Programming', 'World War II', 'Human Anatomy',
  'Algebra', 'Machine Learning', 'Indian History',
  'Organic Chemistry', 'Economics Basics', 'Solar System',
];

export default function TopicQuizModal({ onClose }) {
  const navigate             = useNavigate();
  const [topic, setTopic]         = useState('');
  const [numQuestions, setNum]    = useState(5);
  const [difficulty, setDiff]     = useState('medium');
  const [questionTypes, setTypes] = useState(['mcq']);
  const [isGenerating, setGen]    = useState(false);
  const [error, setError]         = useState('');

  const toggleType = (val) => {
    setTypes(prev =>
      prev.includes(val)
        ? prev.length > 1 ? prev.filter(t => t !== val) : prev
        : [...prev, val]
    );
  };

  const handleGenerate = async () => {
    if (!topic.trim()) { setError('Please enter a topic.'); return; }
    setGen(true);
    setError('');
    try {
      const res = await api.post('/api/quizzes/generate-from-topic', {
        topic: topic.trim(),
        num_questions: numQuestions,
        difficulty,
        question_types: questionTypes,
      });
      navigate(`/quiz/${res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate quiz. Please try again.');
    } finally {
      setGen(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-md bg-dark-900 border border-dark-700 rounded-2xl shadow-2xl">

        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-dark-700">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary-500/15 flex items-center justify-center">
              <Brain className="w-5 h-5 text-primary-400" />
            </div>
            <div>
              <h2 className="text-white font-semibold text-sm">Generate from Topic</h2>
              <p className="text-dark-400 text-xs">No document needed — AI knows it all</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-dark-400 hover:text-white hover:bg-dark-700 transition-all">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-5 space-y-5">

          {/* Topic input */}
          <div>
            <label className="text-dark-300 text-sm font-medium block mb-2">Topic or Subject</label>
            <input
              type="text"
              placeholder="e.g. Photosynthesis, Python Loops, World War I…"
              value={topic}
              onChange={e => { setTopic(e.target.value); setError(''); }}
              onKeyDown={e => e.key === 'Enter' && !isGenerating && handleGenerate()}
              className="w-full px-4 py-2.5 bg-dark-800 border border-dark-700 rounded-xl text-dark-100 text-sm placeholder-dark-500 focus:outline-none focus:border-primary-500/50 transition-colors"
              autoFocus
            />
            {/* Suggestions */}
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {TOPIC_SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => setTopic(s)}
                  className="px-2 py-1 rounded-lg bg-dark-800 border border-dark-700 text-dark-400 hover:text-primary-400 hover:border-primary-500/40 text-xs transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Questions count */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-dark-300 text-sm font-medium">Questions</label>
              <span className="text-white font-bold">{numQuestions}</span>
            </div>
            <input
              type="range" min={3} max={15} value={numQuestions}
              onChange={e => setNum(Number(e.target.value))}
              className="w-full accent-primary-500 cursor-pointer"
            />
            <div className="flex justify-between text-dark-500 text-xs mt-1"><span>3</span><span>15</span></div>
          </div>

          {/* Difficulty */}
          <div>
            <label className="text-dark-300 text-sm font-medium block mb-2">Difficulty</label>
            <div className="flex gap-2">
              {DIFFICULTY_OPTIONS.map(d => (
                <button
                  key={d.value}
                  onClick={() => setDiff(d.value)}
                  className={`flex-1 py-2 rounded-xl border text-xs font-semibold transition-all ${
                    difficulty === d.value ? d.color : 'border-dark-700 bg-dark-800 text-dark-400 hover:border-dark-600'
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          {/* Question Types */}
          <div>
            <label className="text-dark-300 text-sm font-medium block mb-2">Question Types</label>
            <div className="grid grid-cols-2 gap-2">
              {QUESTION_TYPES.map((qt) => {
                const active = questionTypes.includes(qt.value);
                return (
                  <button
                    key={qt.value}
                    onClick={() => toggleType(qt.value)}
                    className={`p-3 rounded-xl border text-left transition-all duration-200 ${
                      active
                        ? 'border-primary-500/60 bg-primary-500/12 text-white'
                        : 'bg-dark-800/50 border-dark-700 text-dark-400 hover:border-dark-600'
                    }`}
                  >
                    <p className="font-semibold text-xs flex items-center gap-1.5">
                      {active && <span className="w-1.5 h-1.5 rounded-full bg-primary-400 inline-block"/>}
                      {qt.label}
                    </p>
                    <p className="text-xs mt-0.5 opacity-60">{qt.desc}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-5 pb-5">
          <button onClick={onClose} className="px-4 py-2 rounded-xl text-dark-400 hover:text-white text-sm transition-colors">
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            disabled={isGenerating || !topic.trim()}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating…</>
              : <><Sparkles className="w-4 h-4" /> Generate Quiz</>
            }
          </button>
        </div>
      </div>
    </div>
  );
}
