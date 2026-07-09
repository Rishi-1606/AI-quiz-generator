import { Link } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';
import Button from '../components/ui/Button';

export default function NotFound() {
  return (
    <div className="min-h-screen gradient-bg flex items-center justify-center p-6">
      <div className="text-center animate-fade-in">
        {/* 404 text */}
        <h1 className="text-[10rem] sm:text-[14rem] font-bold leading-none gradient-text select-none">
          404
        </h1>

        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 -mt-4">
          Page not found
        </h2>
        <p className="text-dark-400 text-lg max-w-md mx-auto mb-8">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>

        <div className="flex items-center justify-center gap-4">
          <Link to="/dashboard">
            <Button size="lg">
              <Home className="w-4 h-4 mr-2" />
              Go to Dashboard
            </Button>
          </Link>
          <Link to={-1}>
            <Button variant="secondary" size="lg">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Button>
          </Link>
        </div>

        {/* Decorative background orbs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-primary-500/5 rounded-full blur-3xl" />
          <div className="absolute bottom-1/3 right-1/4 w-72 h-72 bg-primary-700/5 rounded-full blur-3xl" />
        </div>
      </div>
    </div>
  );
}
