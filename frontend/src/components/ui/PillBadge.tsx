import React from 'react';

export type PillVariant = 'rose' | 'teal' | 'amber' | 'cream' | 'black' | 'emerald';

export interface PillBadgeProps {
  children: React.ReactNode;
  variant?: PillVariant;
  className?: string;
}

const variantStyles: Record<PillVariant, string> = {
  rose: 'bg-rose text-white border-2 border-black',
  teal: 'bg-teal text-white border-2 border-black',
  amber: 'bg-amber text-white border-2 border-black',
  cream: 'bg-cream text-black border-2 border-black',
  black: 'bg-black text-white border-2 border-black',
  emerald: 'bg-emerald text-white border-2 border-black',
};

export const PillBadge: React.FC<PillBadgeProps> = ({
  children,
  variant = 'cream',
  className = ''
}) => {
  return (
    <span
      className={`
        inline-flex items-center justify-center
        px-4 py-1.5
        rounded-full
        text-xs font-medium
        uppercase tracking-wide
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {children}
    </span>
  );
};
