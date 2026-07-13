import { useState } from 'react';
import { FileText, AlertCircle, CheckCircle } from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import FileDropzone from '../../components/ui/FileDropzone';
import api from '../../services/api';

export default function Upload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setError('');
    setSuccess('');
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setError('');
    setSuccess('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      await api.post('/api/uploads', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setSuccess(`"${selectedFile.name}" has been uploaded successfully!`);
      setSelectedFile(null); // Clear selection on success
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to upload document. Please try again.'
      );
    } finally {
      setIsUploading(false);
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

      {/* Supported formats info */}
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

      {/* Drag-and-drop upload area */}
      <div className="space-y-4">
        <FileDropzone onFileSelect={handleFileSelect} />

        {/* Upload status messages */}
        {error && (
          <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 animate-fade-in">
            <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 animate-fade-in">
            <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
            <p className="text-emerald-400 text-sm">{success}</p>
          </div>
        )}

        {selectedFile && (
          <div className="flex justify-end animate-fade-in">
            <Button
              onClick={handleUpload}
              size="lg"
              isLoading={isUploading}
            >
              Upload Document
            </Button>
          </div>
        )}
      </div>

      {/* Uploaded files section */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Your Documents</h2>
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-14 h-14 rounded-2xl bg-dark-800 flex items-center justify-center mb-3">
              <FileText className="w-7 h-7 text-dark-500" />
            </div>
            <p className="text-dark-400 text-sm">
              No documents uploaded yet. Upload your first file to get started!
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
