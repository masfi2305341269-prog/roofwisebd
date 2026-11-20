import React from 'react';

interface DemoBadgeProps {
  label?: string;
  tooltip?: string;
}

export const DemoBadge: React.FC<DemoBadgeProps> = ({
  label = 'DEMO PREVIEW',
  tooltip = 'Demonstration data for layout and architecture preview. Not an active trained inference.',
}) => {
  return (
    <span
      title={tooltip}
      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300 shadow-sm"
    >
      <span className="w-1.5 h-1.5 mr-1.5 bg-amber-500 rounded-full animate-pulse"></span>
      {label}
    </span>
  );
};
