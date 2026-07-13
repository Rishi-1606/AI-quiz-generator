import { useState, useRef, useCallback } from 'react';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';

const ALLOWED_TYPES = {
  'application/pdf': 'pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
  'text/plain': 'txt',
};

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

const FILE_ICONS = {
  pdf: '📄',
  docx: '📝',
  pptx: '📊',
  txt: '📃',
};

export default function FileDropzone({ onFileSelect }) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    // Check file type
    const fileType = ALLOWED_TYPES[file.type];
    if (!fileType) {
      // Also check by extension as a fallback
      const ext = file.name.split('.').pop().toLowerCase();
      if (!['pdf', 'docx', 'pptx', 'txt'].includes(ext)) {
        return 'Unsupported file type. Please upload PDF, DOCX, PPTX, or TXT files.';
      }
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum size is 10 MB.`;
    }

    return null;
  };

  const handleFile = useCallback(
    (file) => {
      setError('');
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      if (onFileSelect) {
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleInputChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFile(file);
    }
    // Reset input so the same file can be selected again
    e.target.value = '';
  };

  const clearFile = () => {
    setSelectedFile(null);
    setError('');
    if (onFileSelect) {
      onFileSelect(null);
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileType = (file) => {
    const mapped = ALLOWED_TYPES[file.type];
    if (mapped) return mapped;
    return file.name.split('.').pop().toLowerCase();
  };

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`
          relative flex flex-col items-center justify-center py-16 px-6
          rounded-2xl border-2 border-dashed cursor-pointer
          transition-all duration-300 ease-out
          ${
            isDragging
              ? 'border-primary-400 bg-primary-500/10 scale-[1.01]'
              : selectedFile
              ? 'border-primary-500/30 bg-primary-500/5'
              : 'border-dark-600/50 bg-dark-800/30 hover:border-dark-500 hover:bg-dark-800/50'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.pptx,.txt"
          onChange={handleInputChange}
          className="hidden"
        />

        {selectedFile ? (
          // File selected preview
          <div className="flex flex-col items-center text-center animate-fade-in">
            <span className="text-4xl mb-3">
              {FILE_ICONS[getFileType(selectedFile)] || '📄'}
            </span>
            <p className="text-white font-medium mb-1">{selectedFile.name}</p>
            <p className="text-dark-400 text-sm">
              {getFileType(selectedFile).toUpperCase()} · {formatSize(selectedFile.size)}
            </p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                clearFile();
              }}
              className="mt-4 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-dark-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              Remove
            </button>
          </div>
        ) : (
          // Empty state
          <div className="flex flex-col items-center text-center">
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-colors duration-300 ${
                isDragging ? 'bg-primary-500/20' : 'bg-dark-700/50'
              }`}
            >
              <Upload
                className={`w-7 h-7 transition-colors duration-300 ${
                  isDragging ? 'text-primary-400' : 'text-dark-400'
                }`}
              />
            </div>
            <p className="text-dark-200 font-medium mb-1">
              {isDragging ? 'Drop your file here' : 'Drag & drop your file here'}
            </p>
            <p className="text-dark-500 text-sm">
              or <span className="text-primary-400 hover:text-primary-300">click to browse</span>
            </p>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 animate-fade-in">
          <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}
