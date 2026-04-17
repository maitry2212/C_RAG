import { useState, useRef, useEffect } from 'react';
import { Search, Loader2, MessageSquare, BookOpen, Sparkles, History, ChevronDown, ChevronUp } from 'lucide-react';
import { queryPipeline, getQueryHistory } from '../services/api';

export default function QueryPanel({ onQueryResult, isIngested }) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const inputRef = useRef();

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await getQueryHistory();
      setHistory(res.data);
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    onQueryResult?.({ status: 'running' });

    try {
      const res = await queryPipeline(question.trim());
      setResult(res.data);
      onQueryResult?.({ status: 'done', data: res.data });
      fetchHistory(); // Refresh history after new query
    } catch (err) {
      const msg = err.response?.data?.detail || 'Query failed.';
      setError(msg);
      onQueryResult?.({ status: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4 border-b border-subtle flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-txt flex items-center gap-2">
            <MessageSquare size={18} className="text-primary" />
            Query Pipeline
          </h2>
          <p className="text-xs text-txt-muted mt-1">Ask a question about your ingested data</p>
        </div>
        <button
          onClick={() => setShowHistory(!showHistory)}
          className={`p-2 rounded-lg transition-colors ${showHistory ? 'bg-primary/20 text-primary' : 'text-txt-muted hover:bg-surface'}`}
          title="Toggle History"
        >
          <History size={18} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {showHistory ? (
          <div className="space-y-4 animate-in fade-in duration-300">
            <h3 className="text-xs font-bold text-txt-muted uppercase tracking-widest flex items-center gap-2">
              <History size={14} /> Past Questions
            </h3>
            {history.length === 0 ? (
              <p className="text-sm text-txt-muted italic text-center py-10">No history yet</p>
            ) : (
              <div className="space-y-3">
                {history.map((item, idx) => (
                  <HistoryItem key={idx} item={item} />
                ))}
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Input area */}
            <div>
              <label className="block text-xs font-medium text-txt-sec mb-2">Your question</label>
              <textarea
                ref={inputRef}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={4}
                placeholder={isIngested ? "What would you like to know?" : "Ingest data first..."}
                disabled={!isIngested}
                className="w-full bg-surface/50 border border-subtle/60 rounded-xl px-4 py-3 text-sm text-txt placeholder:text-txt-muted/50 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all resize-none disabled:opacity-40 disabled:cursor-not-allowed shadow-inner"
              />
            </div>

            {/* Ask button */}
            <button
              onClick={handleAsk}
              disabled={loading || !isIngested || !question.trim()}
              className="w-full py-3.5 rounded-xl bg-primary hover:bg-primary-hover text-white font-medium text-sm transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-[0_4px_14px_0_rgba(139,92,246,0.39)] hover:shadow-[0_6px_20px_rgba(139,92,246,0.23)] hover:-translate-y-0.5"
            >
              {loading ? (
                <><Loader2 size={16} className="animate-spin" /> Running pipeline...</>
              ) : (
                <><Sparkles size={16} /> Ask Question</>
              )}
            </button>

            {/* Error */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg p-4 text-sm">{error}</div>
            )}

            {/* Result */}
            {result && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {/* Answer card */}
                <div className="bg-gradient-to-br from-indigo-500/10 to-purple-500/5 backdrop-blur-md border border-indigo-500/20 rounded-2xl p-6 space-y-4 shadow-lg shadow-indigo-500/5">
                  <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-widest">
                    <Sparkles size={14} className="text-indigo-400" /> Answer
                  </div>
                  <p className="text-[15px] text-txt leading-relaxed whitespace-pre-wrap">{result.answer}</p>
                </div>

                {/* Metadata card */}
                <div className="bg-surface/40 backdrop-blur-sm border border-subtle/50 rounded-2xl p-5 space-y-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-txt-muted uppercase tracking-widest">
                    <BookOpen size={14} /> Pipeline info
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-xs bg-card/50 rounded-xl p-4 border border-white/5">
                    <MetaItem label="Verdict" value={result.verdict} color={
                      result.verdict === 'CORRECT' ? 'text-emerald-400 font-semibold' :
                        result.verdict === 'INCORRECT' ? 'text-red-400 font-semibold' : 'text-amber-400 font-semibold'
                    } />
                    <MetaItem label="Good docs" value={result.num_good_docs} />
                    <MetaItem label="Kept strips" value={result.num_kept_strips} />
                    {result.web_query && <MetaItem label="Web query" value={result.web_query} span />}
                  </div>
                  <p className="text-[11px] text-txt-muted/70 italic px-2">{result.reason}</p>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function HistoryItem({ item }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-card/30 border border-subtle/40 rounded-xl overflow-hidden transition-all duration-300">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-start justify-between gap-3 text-left hover:bg-surface/50 transition-colors"
      >
        <div className="flex-1 min-w-0">
          <p className="text-xs text-txt font-medium truncate">{item.question}</p>
          <p className="text-[10px] text-txt-muted mt-0.5">{new Date(item.timestamp).toLocaleString()}</p>
        </div>
        {expanded ? <ChevronUp size={14} className="mt-1" /> : <ChevronDown size={14} className="mt-1" />}
      </button>
      {expanded && (
        <div className="px-4 pb-4 animate-in slide-in-from-top-2 duration-300">
          <div className="pt-2 border-t border-subtle/30 space-y-3">
            <div>
              <p className="text-[10px] uppercase tracking-wider font-bold text-indigo-400 mb-1">Answer</p>
              <p className="text-sm text-txt-sec leading-relaxed">{item.answer}</p>
            </div>
            <div className="flex gap-4">
              <div>
                <p className="text-[10px] uppercase tracking-wider font-bold text-txt-muted mb-0.5">Verdict</p>
                <p className={`text-[10px] font-semibold ${item.verdict === 'CORRECT' ? 'text-emerald-400' :
                  item.verdict === 'INCORRECT' ? 'text-red-400' : 'text-amber-400'
                  }`}>{item.verdict}</p>
              </div>
            </div>
            {item.reason && (
              <p className="text-[10px] text-txt-muted italic">"{item.reason}"</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function MetaItem({ label, value, color = 'text-txt', span = false }) {
  return (
    <div className={span ? 'col-span-2' : ''}>
      <p className="text-txt-muted mb-0.5">{label}</p>
      <p className={`font-medium ${color} break-all`}>{String(value)}</p>
    </div>
  );
}
