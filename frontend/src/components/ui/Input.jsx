import { forwardRef } from 'react';

const Input = forwardRef(function Input(
  {
    label,
    error,
    icon: Icon,
    className = '',
    ...props
  },
  ref
) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label className="block text-sm font-medium text-dark-300">
          {label}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
            <Icon className="w-4.5 h-4.5 text-dark-400" />
          </div>
        )}
        <input
          ref={ref}
          className={`
            w-full rounded-xl border bg-dark-800/50 backdrop-blur-sm
            text-dark-100 placeholder-dark-500
            transition-all duration-300 ease-out
            focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500
            ${
              error
                ? 'border-red-500/50 focus:ring-red-500/50 focus:border-red-500'
                : 'border-dark-600/50 hover:border-dark-500'
            }
            ${Icon ? 'pl-10.5 pr-4 py-3' : 'px-4 py-3'}
            ${className}
          `}
          {...props}
        />
      </div>
      {error && (
        <p className="text-sm text-red-400 flex items-center gap-1.5">
          <span className="inline-block w-1 h-1 rounded-full bg-red-400" />
          {error}
        </p>
      )}
    </div>
  );
});

export default Input;
