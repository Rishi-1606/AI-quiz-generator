export default function Card({
  children,
  hover = false,
  padding = 'md',
  className = '',
  ...props
}) {
  const paddings = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={`
        glass rounded-2xl
        ${paddings[padding]}
        ${
          hover
            ? 'transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-xl hover:shadow-primary-500/5 hover:border-primary-500/20 cursor-pointer'
            : ''
        }
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  );
}
