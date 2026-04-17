import { useState, useCallback, useRef } from 'react';
import { Cpu, Zap } from 'lucide-react';
import UploadPanel from '../components/UploadPanel';
import GraphViewer from '../components/GraphViewer';
import QueryPanel from '../components/QueryPanel';

// Node execution order for visual simulation
const EXEC_ORDER_CORRECT = ['retrieve', 'eval_each_doc', 'refine', 'generate'];
const EXEC_ORDER_WEB = ['retrieve', 'eval_each_doc', 'rewrite_query', 'web_search', 'refine', 'generate'];

export default function Dashboard() {
  const [isIngested, setIsIngested] = useState(false);
  const [nodeStatuses, setNodeStatuses] = useState({});
  const timeoutsRef = useRef([]);

  const handleIngested = useCallback(() => {
    setIsIngested(true);
    setNodeStatuses({});
  }, []);

  // Simulate node-by-node execution animation
  const simulateExecution = useCallback((execOrder) => {
    timeoutsRef.current.forEach(clearTimeout);
    timeoutsRef.current = [];
    setNodeStatuses({});

    const delay = 600;
    execOrder.forEach((nodeId, i) => {
      const t1 = setTimeout(() => {
        setNodeStatuses((prev) => ({ ...prev, [nodeId]: 'running' }));
      }, i * delay);
      const t2 = setTimeout(() => {
        setNodeStatuses((prev) => ({ ...prev, [nodeId]: 'completed' }));
      }, (i + 1) * delay);
      timeoutsRef.current.push(t1, t2);
    });
  }, []);

  const handleQueryResult = useCallback(({ status, data }) => {
    if (status === 'running') {
      simulateExecution(EXEC_ORDER_CORRECT);
    }
    if (status === 'done' && data) {
      const path = data.verdict === 'CORRECT' ? EXEC_ORDER_CORRECT : EXEC_ORDER_WEB;
      timeoutsRef.current.forEach(clearTimeout);
      timeoutsRef.current = [];
      const final = {};
      path.forEach((id) => { final[id] = 'completed'; });
      setNodeStatuses(final);
    }
    if (status === 'error') {
      setNodeStatuses((prev) => {
        const next = { ...prev };
        Object.keys(next).forEach((k) => {
          if (next[k] === 'running') next[k] = 'error';
        });
        return next;
      });
    }
  }, [simulateExecution]);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden">
      {/* ── Top bar ──────────────────────────────── */}
      <header className="h-14 shrink-0 flex items-center justify-between px-6 border-b border-subtle bg-surface/60 backdrop-blur-md relative z-30 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Cpu size={18} className="text-white" />
          </div>
          <h1 className="text-base font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            CRAG Pipeline
          </h1>
          <span className="text-[10px] font-medium text-txt-muted bg-card px-2 py-0.5 rounded-full border border-subtle">
            v1.0
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs text-txt-muted">
          <Zap size={12} className={isIngested ? 'text-emerald-400' : 'text-txt-muted'} />
          <span>{isIngested ? 'Data ingested — Ready to query' : 'No data ingested'}</span>
        </div>
      </header>

      {/* ── Main 3-column layout ─────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* LEFT — Upload */}
        <aside className="w-80 shrink-0 border-r border-subtle bg-surface/40 backdrop-blur-2xl overflow-hidden relative z-20 shadow-[8px_0_32px_-12px_rgba(0,0,0,0.5)]">
          <UploadPanel onIngested={handleIngested} />
        </aside>

        {/* CENTER — Graph */}
        <main className="flex-1 bg-transparent relative z-10">
          <GraphViewer nodeStatuses={nodeStatuses} />
        </main>

        {/* RIGHT — Query */}
        <aside className="w-96 shrink-0 border-l border-subtle bg-surface/40 backdrop-blur-2xl overflow-hidden relative z-20 shadow-[-8px_0_32px_-12px_rgba(0,0,0,0.5)]">
          <QueryPanel onQueryResult={handleQueryResult} isIngested={isIngested} />
        </aside>
      </div>
    </div>
  );
}
