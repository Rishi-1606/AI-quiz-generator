import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  ChevronLeft, ChevronRight, RotateCcw, CheckCircle2,
  XCircle, BookOpen, ArrowLeft, Layers,
} from 'lucide-react';

export default function FlashcardsViewer() {
  const location  = useLocation();
  const navigate  = useNavigate();
  const { cards = [], filename = 'Flashcards' } = location.state ?? {};

  const [current, setCurrent]   = useState(0);
  const [flipped, setFlipped]   = useState(false);
  const [known, setKnown]       = useState(new Set());    // card indices the user "Got"
  const [review, setReview]     = useState(new Set());    // card indices needing review
  const [finished, setFinished] = useState(false);

  if (!cards.length) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
        <div className="text-center">
          <Layers className="w-12 h-12 text-primary-400 mx-auto mb-4" />
          <p className="text-white font-semibold mb-2">No flashcards found</p>
          <button onClick={() => navigate('/upload')} className="text-primary-400 text-sm hover:underline">
            ← Back to documents
          </button>
        </div>
      </div>
    );
  }

  const total   = cards.length;
  const card    = cards[current];
  const progress = Math.round(((known.size + review.size) / total) * 100);

  const goNext = () => {
    if (current < total - 1) { setCurrent(c => c + 1); setFlipped(false); }
    else                      { setFinished(true); }
  };
  const goPrev = () => {
    if (current > 0) { setCurrent(c => c - 1); setFlipped(false); }
  };

  const markKnown = () => {
    setKnown(prev => new Set([...prev, current]));
    setReview(prev => { const s = new Set(prev); s.delete(current); return s; });
    goNext();
  };
  const markReview = () => {
    setReview(prev => new Set([...prev, current]));
    setKnown(prev => { const s = new Set(prev); s.delete(current); return s; });
    goNext();
  };
  const restart = () => {
    setCurrent(0); setFlipped(false);
    setKnown(new Set()); setReview(new Set());
    setFinished(false);
  };

  // ── Finished screen ──────────────────────────────────────────────────────
  if (finished) {
    const pct = total > 0 ? Math.round((known.size / total) * 100) : 0;
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
        <div className="w-full max-w-sm bg-dark-900 border border-dark-800 rounded-3xl p-8 text-center shadow-2xl">
          <div className="w-20 h-20 rounded-full bg-primary-500/15 flex items-center justify-center mx-auto mb-5">
            <Layers className="w-10 h-10 text-primary-400" />
          </div>
          <h2 className="text-white text-xl font-bold mb-1">Deck Complete! 🎉</h2>
          <p className="text-dark-400 text-sm mb-6">You reviewed all {total} flashcards</p>

          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="py-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
              <p className="text-2xl font-bold text-emerald-400">{known.size}</p>
              <p className="text-xs text-dark-400 mt-0.5">Got it ✅</p>
            </div>
            <div className="py-4 rounded-2xl bg-red-500/10 border border-red-500/20">
              <p className="text-2xl font-bold text-red-400">{review.size}</p>
              <p className="text-xs text-dark-400 mt-0.5">Need review ❌</p>
            </div>
          </div>

          <p className={`text-lg font-bold mb-6 ${pct >= 70 ? 'text-emerald-400' : 'text-yellow-400'}`}>
            {pct}% mastery
          </p>

          <div className="flex gap-3">
            <button onClick={restart} className="flex-1 py-2.5 rounded-xl border border-dark-700 text-dark-400 hover:text-white text-sm transition-colors flex items-center justify-center gap-1.5">
              <RotateCcw className="w-3.5 h-3.5" /> Restart
            </button>
            <button onClick={() => navigate('/upload')} className="flex-1 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-sm transition-colors flex items-center justify-center gap-1.5">
              <ArrowLeft className="w-3.5 h-3.5" /> Documents
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Viewer ───────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-dark-950 text-white flex flex-col">

      {/* Header */}
      <header className="bg-dark-900/90 backdrop-blur border-b border-dark-800 sticky top-0 z-20">
        <div className="max-w-2xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <BookOpen className="w-5 h-5 text-primary-400 flex-shrink-0" />
            <span className="text-sm font-semibold text-dark-100 truncate">{filename}</span>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <span className="text-dark-400 text-sm">{current + 1} / {total}</span>
            <button onClick={() => navigate('/upload')} className="text-dark-500 hover:text-white text-sm transition-colors">
              ✕
            </button>
          </div>
        </div>
        {/* Progress bar */}
        <div className="h-0.5 bg-dark-800">
          <div className="h-full bg-gradient-to-r from-primary-600 to-primary-400 transition-all duration-500"
               style={{ width: `${progress}%` }} />
        </div>
      </header>

      {/* Card area */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-8">

        {/* Status indicators */}
        <div className="flex items-center gap-4 mb-6 text-sm">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <CheckCircle2 className="w-4 h-4" /> {known.size} got it
          </span>
          <span className="flex items-center gap-1.5 text-red-400">
            <XCircle className="w-4 h-4" /> {review.size} review
          </span>
        </div>

        {/* 3D Flip Card */}
        <div
          className="w-full max-w-md cursor-pointer"
          style={{ perspective: '1000px' }}
          onClick={() => setFlipped(f => !f)}
        >
          <div
            className="relative w-full transition-all duration-500"
            style={{
              transformStyle: 'preserve-3d',
              transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
              height: '260px',
            }}
          >
            {/* Front */}
            <div
              className="absolute inset-0 bg-dark-900 border border-dark-700 rounded-3xl p-8 flex flex-col items-center justify-center shadow-2xl"
              style={{ backfaceVisibility: 'hidden' }}
            >
              <span className="text-xs text-primary-400 font-semibold uppercase tracking-widest mb-4">Term</span>
              <p className="text-white text-xl font-semibold text-center leading-snug">{card.front}</p>
              <p className="text-dark-500 text-xs mt-6">Click to reveal →</p>
            </div>

            {/* Back */}
            <div
              className="absolute inset-0 bg-gradient-to-br from-primary-900/40 to-dark-900 border border-primary-500/30 rounded-3xl p-8 flex flex-col items-center justify-center shadow-2xl"
              style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
            >
              <span className="text-xs text-primary-400 font-semibold uppercase tracking-widest mb-4">Definition</span>
              <p className="text-dark-100 text-base text-center leading-relaxed">{card.back}</p>
            </div>
          </div>
        </div>

        {/* Self-assessment (only show when flipped) */}
        {flipped && (
          <div className="flex gap-4 mt-6 animate-fade-in">
            <button
              onClick={markReview}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 text-sm font-medium transition-all"
            >
              <XCircle className="w-4 h-4" /> Needs Review
            </button>
            <button
              onClick={markKnown}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 text-sm font-medium transition-all"
            >
              <CheckCircle2 className="w-4 h-4" /> Got It!
            </button>
          </div>
        )}

        {/* Navigation */}
        <div className="flex items-center gap-6 mt-8">
          <button
            onClick={goPrev}
            disabled={current === 0}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-dark-700 text-dark-400 hover:text-white hover:border-dark-600 text-sm transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" /> Prev
          </button>

          {/* Dot indicators (max 10 shown) */}
          <div className="flex gap-1.5">
            {cards.slice(0, 10).map((_, i) => (
              <button
                key={i}
                onClick={() => { setCurrent(i); setFlipped(false); }}
                className={`w-2 h-2 rounded-full transition-all ${
                  i === current       ? 'bg-primary-400 w-4' :
                  known.has(i)        ? 'bg-emerald-500' :
                  review.has(i)       ? 'bg-red-500' :
                                        'bg-dark-700'
                }`}
              />
            ))}
            {total > 10 && <span className="text-dark-600 text-xs">+{total - 10}</span>}
          </div>

          <button
            onClick={goNext}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-dark-700 text-dark-400 hover:text-white hover:border-dark-600 text-sm transition-all"
          >
            {current === total - 1 ? 'Finish' : 'Next'} <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
