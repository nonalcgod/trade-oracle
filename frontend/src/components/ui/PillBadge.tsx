import React from 'react';

export type PillVariant = 'rose' | 'teal' | 'amber' | 'cream' | 'black' | 'emerald';

export interface PillBadgeProps {
  children: React.ReactNode;
  variant?: PillVariant;
  className?: string;
}

const variantStyles: Record<PillVariant, string> = {
  rose: 'bg-rose text-white',
  teal: 'bg-teal text-white',
  amber: 'bg-amber text-white',
  cream: 'bg-cream text-black border-2 border-black',
  black: 'bg-black text-white',
  emerald: 'bg-emerald text-white',
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
