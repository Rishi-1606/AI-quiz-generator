import { useState } from 'react';
import { X, Layers, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Button from './Button';
import api from '../../services/api';

export default function GenerateFlashcardsModal({ upload, onClose }) {
  const navigate = useNavigate();
  const [numCards, setNumCards]     = useState(10);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError]           = useState('');

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError('');
    try {
      const res = await api.post('/api/flashcards/generate', {
        upload_id: upload.id,
        num_cards: numCards,
      });
      navigate('/flashcards', {
        state: { cards: res.data.cards, filename: res.data.filename },
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate flashcards. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-sm bg-dark-900 border border-dark-700 rounded-2xl shadow-2xl">

        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-dark-700">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-500/15 flex items-center justify-center">
              <Layers className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h2 className="text-white font-semibold text-sm">Generate Flashcards</h2>
              <p className="text-dark-400 text-xs truncate max-w-[180px]">{upload.filename}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-dark-400 hover:text-white hover:bg-dark-700 transition-all">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-5 space-y-5">
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-dark-300 text-sm font-medium">Number of Cards</label>
              <span className="text-white font-bold text-lg w-8 text-center">{numCards}</span>
            </div>
            <input
              type="range" min={5} max={20} value={numCards}
              onChange={(e) => setNumCards(Number(e.target.value))}
              className="w-full accent-purple-500 cursor-pointer"
            />
            <div className="flex justify-between text-dark-500 text-xs mt-1"><span>5</span><span>20</span></div>
          </div>

          <div className="px-4 py-3 rounded-xl bg-dark-800/60 border border-dark-700">
            <p className="text-dark-400 text-xs">
              📚 {numCards} key concepts will be extracted &nbsp;·&nbsp;
              Powered by <span className="text-purple-400 font-medium">Gemini AI</span>
            </p>
          </div>

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
            disabled={isGenerating}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium transition-all disabled:opacity-50"
          >
            {isGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Layers className="w-4 h-4" />}
            {isGenerating ? 'Generating…' : 'Generate'}
          </button>
        </div>
      </div>
    </div>
  );
}
