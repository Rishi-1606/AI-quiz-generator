import { useState, useEffect } from 'react';
import { X, Sparkles, Loader2, Shuffle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Button from './Button';
import api from '../../services/api';

const DIFFICULTIES = [
  { value: 'easy',   label: 'Easy',   desc: 'Factual recall & definitions',      color: 'text-emerald-400', border: 'border-emerald-500/40', bg: 'bg-emerald-500/10' },
  { value: 'medium', label: 'Medium', desc: 'Conceptual understanding',           color: 'text-yellow-400',  border: 'border-yellow-500/40',  bg: 'bg-yellow-500/10'  },
  { value: 'hard',   label: 'Hard',   desc: 'Analysis & edge cases',              color: 'text-red-400',     border: 'border-red-500/40',     bg: 'bg-red-500/10'     },
];

const QUESTION_TYPES = [
  { value: 'mcq',          label: 'MCQ',            desc: '4-option multiple choice',   icon: '🔤' },
  { value: 'true_false',   label: 'True / False',   desc: 'Binary true or false',        icon: '✅' },
  { value: 'fill_blank',   label: 'Fill in Blank',  desc: 'Complete the sentence',       icon: '✏️' },
  { value: 'short_answer', label: 'Short Answer',   desc: 'AI-evaluated open text',      icon: '💬' },
  { value: 'matching',     label: 'Matching',       desc: 'Match terms to definitions',  icon: '🔗' },
  { value: 'ordering',     label: 'Ordering',       desc: 'Arrange steps in sequence',   icon: '🔢' },
  { value: 'numeric',      label: 'Numeric',        desc: 'Enter a calculated value',    icon: '🧮' },
];

const ALL_TYPE_VALUES = QUESTION_TYPES.map(t => t.value);

export default function GenerateQuizModal({ upload, onClose, onSuccess }) {
  const navigate = useNavigate();
  const [difficulty, setDifficulty]         = useState('medium');
  const [numQuestions, setNumQuestions]     = useState(5);
  const [randomMix, setRandomMix]           = useState(false);
  const [questionTypes, setQuestionTypes]   = useState(['mcq']);
  const [isGenerating, setIsGenerating]     = useState(false);
  const [error, setError]                   = useState('');

  const toggleType = (val) => {
    if (randomMix) return;
    setQuestionTypes(prev =>
      prev.includes(val)
        ? prev.length > 1 ? prev.filter(t => t !== val) : prev  // keep at least 1
        : [...prev, val]
    );
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError('');
    try {
      const res = await api.post('/api/quizzes/generate', {
        upload_id:      upload.id,
        num_questions:  numQuestions,
        difficulty,
        question_types: randomMix ? ALL_TYPE_VALUES : questionTypes,
      });
      onSuccess?.(res.data);  // notify parent (for toast)
      navigate(`/quiz/${res.data.id}`);  // navigate to quiz page
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate quiz. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const GENERATING_STEPS = [
    { icon: '📄', text: 'Reading your document…' },
    { icon: '🧠', text: 'Crafting questions…' },
    { icon: '🔍', text: 'Validating answers…' },
    { icon: '✨', text: 'Almost ready…' },
  ];
  const [genStep, setGenStep] = useState(0);

  useEffect(() => {
    if (!isGenerating) return;
    setGenStep(0);
    const interval = setInterval(() => {
      setGenStep(prev => (prev < GENERATING_STEPS.length - 1 ? prev + 1 : prev));
    }, 2200);
    return () => clearInterval(interval);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isGenerating]);

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}
      onClick={(e) => !isGenerating && e.target === e.currentTarget && onClose()}
    >
      {/* ── Generating overlay ── */}
      {isGenerating && (
        <div className="w-full max-w-sm text-center">
          <div className="relative w-20 h-20 mx-auto mb-6">
            <div className="absolute inset-0 rounded-full border-4 border-primary-500/20" />
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-primary-500 animate-spin" />
            <span className="absolute inset-0 flex items-center justify-center text-3xl">
              {GENERATING_STEPS[genStep].icon}
            </span>
          </div>
          <h2 className="text-white font-semibold text-lg mb-2">Generating your quiz…</h2>
          <p className="text-primary-300 text-sm font-medium mb-6">{GENERATING_STEPS[genStep].text}</p>
          <div className="flex justify-center gap-2">
            {GENERATING_STEPS.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 rounded-full transition-all duration-500 ${
                  i <= genStep ? 'bg-primary-500 w-6' : 'bg-dark-700 w-3'
                }`}
              />
            ))}
          </div>
          <p className="text-dark-500 text-xs mt-4">This may take 10–20 seconds</p>
        </div>
      )}

      {/* ── Modal ── */}
      {!isGenerating && <div className="w-full max-w-md bg-dark-900 border border-dark-700 rounded-2xl shadow-2xl animate-fade-in">

        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-dark-700">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary-500/15 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary-400" />
            </div>
            <div>
              <h2 className="text-white font-semibold text-base">Generate Quiz</h2>
              <p className="text-dark-400 text-xs truncate max-w-[200px]">{upload.filename}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-dark-400 hover:text-white hover:bg-dark-700 transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-6">

          {/* Difficulty selector */}
          <div>
            <label className="text-dark-300 text-sm font-medium mb-3 block">Difficulty</label>
            <div className="grid grid-cols-3 gap-2">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.value}
                  onClick={() => setDifficulty(d.value)}
                  className={`p-3 rounded-xl border text-left transition-all duration-200 ${
                    difficulty === d.value
                      ? `${d.bg} ${d.border} ${d.color}`
                      : 'bg-dark-800/50 border-dark-700 text-dark-400 hover:border-dark-600'
                  }`}
                >
                  <p className="font-semibold text-sm">{d.label}</p>
                  <p className="text-xs mt-0.5 opacity-70">{d.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Number of questions slider */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-dark-300 text-sm font-medium">Number of Questions</label>
              <span className="text-white font-bold text-lg w-8 text-center">{numQuestions}</span>
            </div>
            <input
              type="range"
              min={3}
              max={15}
              value={numQuestions}
              onChange={(e) => setNumQuestions(Number(e.target.value))}
              className="w-full accent-primary-500 cursor-pointer"
            />
            <div className="flex justify-between text-dark-500 text-xs mt-1">
              <span>3</span>
              <span>15</span>
            </div>
          </div>

          {/* Question Types */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-dark-300 text-sm font-medium">Question Types</label>
              {/* Random Mix toggle */}
              <button
                onClick={() => setRandomMix(prev => !prev)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-lg border text-xs font-semibold transition-all duration-200 ${
                  randomMix
                    ? 'border-violet-500/60 bg-violet-500/15 text-violet-300'
                    : 'border-dark-600 bg-dark-800 text-dark-400 hover:border-dark-500 hover:text-dark-200'
                }`}
              >
                <Shuffle className="w-3 h-3" />
                Random Mix
              </button>
            </div>
            {randomMix ? (
              <div className="px-4 py-3 rounded-xl border border-violet-500/30 bg-violet-500/8 text-center">
                <p className="text-violet-300 text-xs font-medium">🎲 AI will mix all 7 question types automatically</p>
                <p className="text-dark-400 text-xs mt-1">MCQ · True/False · Fill in Blank · Short Answer · Matching · Ordering · Numeric</p>
              </div>
            ) : (
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
                      <p className="font-semibold text-sm flex items-center gap-1.5">
                        <span>{qt.icon}</span>
                        {active && <span className="w-1.5 h-1.5 rounded-full bg-primary-400 inline-block"/>}
                        {qt.label}
                      </p>
                      <p className="text-xs mt-0.5 opacity-60">{qt.desc}</p>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Estimate */}
          <div className="px-4 py-3 rounded-xl bg-dark-800/60 border border-dark-700">
            <p className="text-dark-400 text-xs">
              ⏱ Estimated time limit: <span className="text-white font-medium">{numQuestions} min</span>
              &nbsp;·&nbsp;
              Powered by <span className="text-primary-400 font-medium">Gemini AI</span>
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 pb-6">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-dark-400 hover:text-white text-sm transition-colors"
          >
            Cancel
          </button>
          <Button onClick={handleGenerate} isLoading={isGenerating} disabled={isGenerating}>
            {isGenerating ? 'Generating…' : 'Generate Quiz'}
          </Button>
        </div>
      </div>}
    </div>
  );
}
