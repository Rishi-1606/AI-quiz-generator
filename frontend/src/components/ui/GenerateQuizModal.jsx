import { useState } from 'react';
import { X, Sparkles, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Button from './Button';
import api from '../../services/api';

const DIFFICULTIES = [
  { value: 'easy',   label: 'Easy',   desc: 'Factual recall & definitions',      color: 'text-emerald-400', border: 'border-emerald-500/40', bg: 'bg-emerald-500/10' },
  { value: 'medium', label: 'Medium', desc: 'Conceptual understanding',           color: 'text-yellow-400',  border: 'border-yellow-500/40',  bg: 'bg-yellow-500/10'  },
  { value: 'hard',   label: 'Hard',   desc: 'Analysis & edge cases',              color: 'text-red-400',     border: 'border-red-500/40',     bg: 'bg-red-500/10'     },
];

export default function GenerateQuizModal({ upload, onClose, onSuccess }) {
  const navigate = useNavigate();
  const [difficulty, setDifficulty]       = useState('medium');
  const [numQuestions, setNumQuestions]   = useState(5);
  const [isGenerating, setIsGenerating]   = useState(false);
  const [error, setError]                 = useState('');

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError('');
    try {
      const res = await api.post('/api/quizzes/generate', {
        upload_id:     upload.id,
        num_questions: numQuestions,
        difficulty,
      });
      onSuccess?.(res.data);  // notify parent (for toast)
      navigate(`/quiz/${res.data.id}`);  // navigate to quiz page
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate quiz. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      {/* Modal */}
      <div className="w-full max-w-md bg-dark-900 border border-dark-700 rounded-2xl shadow-2xl animate-fade-in">

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
      </div>
    </div>
  );
}
