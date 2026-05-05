import { useState, useCallback, useRef, useEffect } from 'react';
import { Cpu, Zap, Plus, MessageSquare, Trash2, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getChats, createChat, deleteChat } from '../services/api';
import UploadPanel from '../components/UploadPanel';
import GraphViewer from '../components/GraphViewer';
import QueryPanel from '../components/QueryPanel';

// Node execution order for visual simulation
const EXEC_ORDER_CORRECT = ['retrieve', 'eval_each_doc', 'refine', 'generate'];
const EXEC_ORDER_WEB = ['retrieve', 'eval_each_doc', 'rewrite_query', 'web_search', 'refine', 'generate'];

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [isIngested, setIsIngested] = useState(false);
  const [nodeStatuses, setNodeStatuses] = useState({});
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const timeoutsRef = useRef([]);

  const loadChats = async () => {
    try {
      const res = await getChats();
      setChats(res.data);
      if (res.data.length > 0) {
        if (!activeChatId) setActiveChatId(res.data[0].id);
      } else {
        // Auto-create a chat if none exist
        const newChatRes = await createChat('New Chat ' + new Date().toLocaleTimeString());
        setChats([newChatRes.data]);
        setActiveChatId(newChatRes.data.id);
      }
    } catch(err) {}
  };

  useEffect(() => {
    loadChats();
  }, []);

  const handleNewChat = async () => {
    try {
      const res = await createChat('New Chat ' + new Date().toLocaleTimeString());
      await loadChats();
      setActiveChatId(res.data.id);
    } catch(err) {}
  };

  const handleDeleteChat = async (id, e) => {
    e.stopPropagation();
    try {
      await deleteChat(id);
      if (activeChatId === id) setActiveChatId(null);
      loadChats();
    } catch(err) {}
  };

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

        <div className="flex items-center gap-4 text-xs text-txt-muted">
          <div className="flex items-center gap-2">
            <Zap size={12} className={isIngested ? 'text-emerald-400' : 'text-txt-muted'} />
            <span>{isIngested ? 'Data ingested — Ready to query' : 'No data ingested'}</span>
          </div>
          <div className="h-4 w-px bg-subtle"></div>
          <div className="flex items-center gap-2 pl-2">
             <span className="font-medium text-white">{user?.name}</span>
             <button onClick={logout} className="hover:text-red-400 transition-colors" title="Log out">
               <LogOut size={14} />
             </button>
          </div>
        </div>
      </header>

      {/* ── Main layout ─────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* FAR LEFT — Chats */}
        <aside className="w-64 shrink-0 border-r border-subtle bg-surface/80 backdrop-blur-2xl overflow-hidden flex flex-col relative z-20 shadow-[8px_0_32px_-12px_rgba(0,0,0,0.5)]">
          <div className="p-4 border-b border-subtle/50">
             <button onClick={handleNewChat} className="w-full flex items-center justify-center gap-2 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 rounded-xl py-2.5 text-sm font-medium transition-all">
               <Plus size={16} /> New Chat
             </button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
             {chats.map(c => (
               <div key={c.id} onClick={() => setActiveChatId(c.id)}
                 className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all ${activeChatId === c.id ? 'bg-primary border border-primary' : 'bg-card/50 border border-subtle/40 hover:bg-surface'}`}>
                  <span className="text-sm font-medium truncate flex-1 flex items-center gap-2">
                    <MessageSquare size={14} className="opacity-70" />
                    {c.title}
                  </span>
                  <button onClick={(e) => handleDeleteChat(c.id, e)} className="p-1 hover:bg-white/20 rounded opacity-50 hover:opacity-100 transition-all">
                    <Trash2 size={14} />
                  </button>
               </div>
             ))}
             {chats.length === 0 && <div className="p-4 text-center text-txt-muted text-xs">No chats found. Create one!</div>}
          </div>
        </aside>

        {/* LEFT — Upload */}
        <aside className="w-80 shrink-0 border-r border-subtle bg-surface/40 backdrop-blur-2xl overflow-hidden relative z-10">
          <UploadPanel onIngested={handleIngested} />
        </aside>

        {/* CENTER — Graph */}
        <main className="flex-1 bg-transparent relative z-10">
          <GraphViewer nodeStatuses={nodeStatuses} />
        </main>

        {/* RIGHT — Query */}
        <aside className="w-96 shrink-0 border-l border-subtle bg-surface/40 backdrop-blur-2xl overflow-hidden relative z-20 shadow-[-8px_0_32px_-12px_rgba(0,0,0,0.5)]">
          <QueryPanel onQueryResult={handleQueryResult} isIngested={isIngested} chatId={activeChatId} />
        </aside>
      </div>
    </div>
  );
}
