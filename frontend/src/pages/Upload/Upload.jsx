import { Upload as UploadIcon, FileText, Trash2 } from 'lucide-react';
import Card from '../../components/ui/Card';

export default function Upload() {
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

      {/* Upload area placeholder — will be replaced with drag-and-drop in Step 4 */}
      <Card>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-primary-500/10 flex items-center justify-center mb-4">
            <UploadIcon className="w-8 h-8 text-primary-400" />
          </div>
          <h3 className="text-lg font-medium text-dark-200 mb-2">
            Upload area coming soon
          </h3>
          <p className="text-dark-400 max-w-sm">
            Drag-and-drop file upload will be added in the next step.
          </p>
        </div>
      </Card>

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
