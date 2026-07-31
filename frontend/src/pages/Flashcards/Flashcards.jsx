import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layers, Loader2, Sparkles, Brain } from 'lucide-react';
import Card from '../../components/ui/Card';
import GenerateFlashcardsModal from '../../components/ui/GenerateFlashcardsModal';
import api from '../../services/api';

function formatDate(dt) {
  return new Date(dt).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  });
}

function getFileIcon(filename) {
  if (!filename) return '📄';
  const ext = filename.split('.').pop().toLowerCase();
  if (ext === 'pdf')  return '📕';
  if (ext === 'docx') return '📘';
  return '📄';
}

export default function Flashcards() {
  const navigate  = useNavigate();
  const [uploads, setUploads]       = useState([]);
  const [isLoading, setIsLoading]   = useState(true);
  const [selectedUpload, setSelected] = useState(null);   // triggers modal

  const fetchUploads = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/api/uploads');
      setUploads(res.data);
    } catch {
      setUploads([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { fetchUploads(); }, [fetchUploads]);

  return (
    <div className="space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Layers className="w-6 h-6 text-primary-400" /> Flashcards
          </h1>
          <p className="text-dark-400 text-sm mt-1">
            Pick a document to generate an AI study deck
          </p>
        </div>
      </div>

      {/* Tip banner */}
      <div className="flex items-start gap-3 px-4 py-3 rounded-2xl bg-primary-500/10 border border-primary-500/20">
        <Brain className="w-5 h-5 text-primary-400 flex-shrink-0 mt-0.5" />
        <p className="text-dark-300 text-sm">
          <span className="text-primary-400 font-semibold">How it works: </span>
          Select any document below → AI extracts key concepts → Study with interactive 3D flip cards!
        </p>
      </div>

      {/* Documents grid */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
        </div>
      ) : uploads.length === 0 ? (
        <Card>
          <div className="flex flex-col items-center justify-center py-14 text-center">
            <div className="w-16 h-16 rounded-2xl bg-primary-500/10 flex items-center justify-center mb-4">
              <Layers className="w-8 h-8 text-primary-400" />
            </div>
            <h3 className="text-lg font-medium text-dark-200 mb-2">No documents yet</h3>
            <p className="text-dark-400 text-sm max-w-xs mb-5">
              Upload a document first to generate AI flashcards from it.
            </p>
            <button
              onClick={() => navigate('/upload')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium transition-all"
            >
              <Sparkles className="w-4 h-4" /> Upload a Document
            </button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {uploads.map(upload => (
            <Card key={upload.id} hover className="flex flex-col">

              {/* File icon + name */}
              <div className="flex items-start gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-primary-500/10 flex items-center justify-center flex-shrink-0 text-xl">
                  {getFileIcon(upload.filename)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-dark-100 font-medium text-sm leading-snug line-clamp-2">
                    {upload.filename}
                  </p>
                  <p className="text-dark-500 text-xs mt-1">{formatDate(upload.created_at)}</p>
                </div>
              </div>

              {/* Generate button */}
              <button
                onClick={() => setSelected(upload)}
                className="mt-auto w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium transition-all"
              >
                <Layers className="w-4 h-4" /> Generate Flashcards
              </button>
            </Card>
          ))}
        </div>
      )}

      {/* Generation modal */}
      {selectedUpload && (
        <GenerateFlashcardsModal
          upload={selectedUpload}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
