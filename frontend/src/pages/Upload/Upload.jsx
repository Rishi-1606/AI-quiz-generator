import { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  AlertCircle,
  CheckCircle,
  Trash2,
  FileType,
  Loader2,
} from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import FileDropzone from '../../components/ui/FileDropzone';
import api from '../../services/api';

import FileTypeIcon from '../../components/ui/FileTypeIcon';

// File type label color mapping
const FILE_TYPE_CONFIG = {
  pdf:  { color: 'text-red-400'    },
  docx: { color: 'text-blue-400'   },
  pptx: { color: 'text-orange-400' },
  txt:  { color: 'text-dark-300'   },
};

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

export default function Upload() {
  const [selectedFile, setSelectedFile]   = useState(null);
  const [isUploading, setIsUploading]     = useState(false);
  const [uploadError, setUploadError]     = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');

  const [uploads, setUploads]         = useState([]);
  const [isFetching, setIsFetching]   = useState(true);
  const [deletingId, setDeletingId]   = useState(null);

  // Fetch all uploaded documents for this user
  const fetchUploads = useCallback(async () => {
    setIsFetching(true);
    try {
      const res = await api.get('/api/uploads');
      setUploads(res.data);
    } catch {
      // Silently fail — user will see empty state
    } finally {
      setIsFetching(false);
    }
  }, []);

  useEffect(() => {
    fetchUploads();
  }, [fetchUploads]);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setUploadError('');
    setUploadSuccess('');
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setUploadError('');
    setUploadSuccess('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      await api.post('/api/uploads', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadSuccess(`"${selectedFile.name}" uploaded successfully!`);
      setSelectedFile(null);
      fetchUploads(); // Refresh list
    } catch (err) {
      setUploadError(
        err.response?.data?.detail || 'Failed to upload document. Please try again.'
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (uploadId, filename) => {
    if (!window.confirm(`Delete "${filename}"? This cannot be undone.`)) return;
    setDeletingId(uploadId);
    try {
      await api.delete(`/api/uploads/${uploadId}`);
      setUploads((prev) => prev.filter((u) => u.id !== uploadId));
    } catch {
      alert('Failed to delete document. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page header */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">
          Upload <span className="gradient-text">Documents</span>
        </h1>
        <p className="text-dark-400 text-lg">
          Upload your study materials and let AI generate quizzes from them
        </p>
      </div>

      {/* Supported formats */}
      <div className="flex flex-wrap gap-3">
        {['PDF', 'DOCX', 'PPTX', 'TXT'].map((format) => (
          <span
            key={format}
            className="px-3 py-1.5 rounded-lg bg-primary-500/10 text-primary-400 text-xs font-medium border border-primary-500/20"
          >
            .{format.toLowerCase()}
          </span>
        ))}
        <span className="px-3 py-1.5 rounded-lg bg-dark-800/50 text-dark-400 text-xs">
          Max 10 MB per file
        </span>
      </div>

      {/* Drag-and-drop area */}
      <div className="space-y-4">
        <FileDropzone onFileSelect={handleFileSelect} />

        {uploadError && (
          <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 animate-fade-in">
            <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
            <p className="text-red-400 text-sm">{uploadError}</p>
          </div>
        )}

        {uploadSuccess && (
          <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 animate-fade-in">
            <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
            <p className="text-emerald-400 text-sm">{uploadSuccess}</p>
          </div>
        )}

        {selectedFile && (
          <div className="flex justify-end animate-fade-in">
            <Button onClick={handleUpload} size="lg" isLoading={isUploading}>
              Upload Document
            </Button>
          </div>
        )}
      </div>

      {/* Uploaded files list */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">
          Your Documents
          {uploads.length > 0 && (
            <span className="ml-2 text-sm font-normal text-dark-400">
              ({uploads.length})
            </span>
          )}
        </h2>

        {isFetching ? (
          <Card>
            <div className="flex items-center justify-center py-12 gap-3">
              <Loader2 className="w-5 h-5 text-primary-400 animate-spin" />
              <p className="text-dark-400 text-sm">Loading your documents...</p>
            </div>
          </Card>
        ) : uploads.length === 0 ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-14 h-14 rounded-2xl bg-dark-800 flex items-center justify-center mb-3">
                <FileText className="w-7 h-7 text-dark-500" />
              </div>
              <p className="text-dark-400 text-sm">
                No documents uploaded yet. Upload your first file above!
              </p>
            </div>
          </Card>
        ) : (
          <div className="space-y-3">
            {uploads.map((upload) => {
              const config = FILE_TYPE_CONFIG[upload.file_type] || FILE_TYPE_CONFIG.txt;
              return (
                <Card key={upload.id} padding="sm">
                  <div className="flex items-center gap-4">
                    {/* File type icon */}
                    <FileTypeIcon type={upload.file_type} size={44} />

                    {/* File info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-dark-100 font-medium text-sm truncate">
                        {upload.filename}
                      </p>
                      <div className="flex items-center gap-3 mt-0.5">
                        <span className={`text-xs font-medium uppercase ${config.color}`}>
                          {upload.file_type}
                        </span>
                        <span className="text-dark-500 text-xs">
                          {formatFileSize(upload.file_size)}
                        </span>
                        <span className="text-dark-500 text-xs">
                          {formatDate(upload.uploaded_at)}
                        </span>
                      </div>
                    </div>

                    {/* Delete button */}
                    <button
                      onClick={() => handleDelete(upload.id, upload.filename)}
                      disabled={deletingId === upload.id}
                      className="p-2 rounded-lg text-dark-500 hover:text-red-400 hover:bg-red-500/10 transition-all duration-200 disabled:opacity-50 flex-shrink-0"
                      title="Delete document"
                    >
                      {deletingId === upload.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
