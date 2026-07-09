export default function Loader() {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-dark-950">
      {/* Animated gradient ring */}
      <div className="relative w-20 h-20 mb-6">
        <div className="absolute inset-0 rounded-full border-2 border-dark-800" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary-500 border-r-primary-400 animate-spin" />
        <div className="absolute inset-2 rounded-full border-2 border-transparent border-b-primary-300 border-l-primary-400 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl animate-pulse">🧠</span>
        </div>
      </div>

      {/* Loading text */}
      <p className="text-dark-400 text-sm font-medium tracking-wide animate-pulse">
        Loading...
      </p>

      {/* Decorative background gradient */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-20 w-72 h-72 bg-primary-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 -right-20 w-72 h-72 bg-primary-700/5 rounded-full blur-3xl" />
      </div>
    </div>
  );
}
