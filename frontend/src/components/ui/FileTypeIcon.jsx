// SVG file type icons that resemble real application logos

export default function FileTypeIcon({ type, size = 44 }) {
  const s = size;

  if (type === 'pdf') {
    return (
      <svg width={s} height={s} viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="44" height="44" rx="10" fill="#FEE2E2" />
        <rect x="8" y="5" width="22" height="28" rx="2" fill="#EF4444" />
        <path d="M30 5l6 6h-6V5z" fill="#B91C1C" />
        <rect x="30" y="11" width="6" height="22" rx="1" fill="#DC2626" />
        <text x="13" y="26" fontSize="8" fontWeight="800" fill="white" fontFamily="Arial, sans-serif">PDF</text>
      </svg>
    );
  }

  if (type === 'docx') {
    return (
      <svg width={s} height={s} viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="44" height="44" rx="10" fill="#DBEAFE" />
        <rect x="8" y="5" width="22" height="28" rx="2" fill="#2563EB" />
        <path d="M30 5l6 6h-6V5z" fill="#1D4ED8" />
        <rect x="30" y="11" width="6" height="22" rx="1" fill="#1E40AF" />
        {/* W letter */}
        <text x="11" y="27" fontSize="13" fontWeight="900" fill="white" fontFamily="Arial, sans-serif">W</text>
      </svg>
    );
  }

  if (type === 'pptx') {
    return (
      <svg width={s} height={s} viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="44" height="44" rx="10" fill="#FFEDD5" />
        <rect x="8" y="5" width="22" height="28" rx="2" fill="#F97316" />
        <path d="M30 5l6 6h-6V5z" fill="#C2410C" />
        <rect x="30" y="11" width="6" height="22" rx="1" fill="#EA580C" />
        {/* P letter */}
        <text x="12" y="27" fontSize="13" fontWeight="900" fill="white" fontFamily="Arial, sans-serif">P</text>
      </svg>
    );
  }

  // TXT (default)
  return (
    <svg width={s} height={s} viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="44" height="44" rx="10" fill="#1E293B" />
      <rect x="8" y="5" width="22" height="28" rx="2" fill="#475569" />
      <path d="M30 5l6 6h-6V5z" fill="#334155" />
      <rect x="30" y="11" width="6" height="22" rx="1" fill="#334155" />
      {/* Lines representing text */}
      <rect x="12" y="15" width="14" height="2" rx="1" fill="#CBD5E1" />
      <rect x="12" y="20" width="14" height="2" rx="1" fill="#CBD5E1" />
      <rect x="12" y="25" width="9" height="2" rx="1" fill="#CBD5E1" />
    </svg>
  );
}
