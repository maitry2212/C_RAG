import { Info } from 'lucide-react';

export default function NodeTooltip({ data, position }) {
  if (!data) return null;

  const { node_id, input_state, output_state } = data;

  return (
    <div
      className="node-tooltip"
      style={{
        left: position.x + 16,
        top: position.y - 8,
      }}
    >
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-subtle">
        <Info size={14} className="text-primary" />
        <span className="font-semibold text-sm text-txt">{node_id}</span>
      </div>

      {/* Input state */}
      <div className="mb-3">
        <p className="text-[10px] font-semibold text-txt-muted uppercase tracking-wider mb-1">Input State</p>
        <StateBlock state={input_state} />
      </div>

      {/* Output state */}
      <div>
        <p className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider mb-1">Output State</p>
        <StateBlock state={output_state} />
      </div>
    </div>
  );
}

function StateBlock({ state }) {
  if (!state || Object.keys(state).length === 0) {
    return <p className="text-xs text-txt-muted italic">No data</p>;
  }

  return (
    <div className="space-y-1">
      {Object.entries(state).map(([key, value]) => {
        let display;
        if (Array.isArray(value)) {
          display = `[${value.length} items]`;
        } else if (typeof value === 'object' && value !== null) {
          display = JSON.stringify(value).slice(0, 80) + '…';
        } else if (typeof value === 'string' && value.length > 80) {
          display = value.slice(0, 80) + '…';
        } else {
          display = String(value || '—');
        }

        return (
          <div key={key} className="flex gap-2">
            <span className="text-primary font-medium shrink-0">{key}:</span>
            <span className="text-txt-sec break-all">{display}</span>
          </div>
        );
      })}
    </div>
  );
}
