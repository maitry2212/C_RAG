import { Link } from 'react-router-dom';
import { Cpu, ArrowRight } from 'lucide-react';

export default function Landing() {
  return (
    <div className="flex flex-col min-h-screen relative overflow-hidden bg-base text-txt">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/40 via-base to-base z-0" />
      
      <header className="relative z-10 max-w-7xl mx-auto w-full p-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.3)]">
            <Cpu size={22} className="text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight">CRAG AI</span>
        </div>
        <nav className="flex items-center gap-4">
          <Link to="/signin" className="text-txt-sec hover:text-white transition-colors text-sm font-medium">Log in</Link>
          <Link to="/signup" className="bg-primary hover:bg-primary-hover transition-colors px-5 py-2 rounded-lg text-sm font-semibold shadow-lg shadow-primary/25">Get Started</Link>
        </nav>
      </header>

      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 text-center -mt-20">
        <div className="inline-block mb-4 px-4 py-1.5 rounded-full border border-subtle bg-surface/50 text-xs font-medium text-emerald-400">
          ✨ Introducing Corrective RAG
        </div>
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 max-w-4xl text-transparent bg-clip-text bg-gradient-to-br from-white to-txt-sec">
          Chat with your documents using advanced AI
        </h1>
        <p className="text-lg md:text-xl text-txt-muted max-w-2xl mb-10 leading-relaxed">
          Upload documents into isolated user collections, visualize graph retrieval, and get accurate answers with web search fallbacks.
        </p>
        <div className="flex items-center gap-4">
          <Link to="/signup" className="flex items-center gap-2 bg-white text-base font-bold text-black px-8 py-3.5 rounded-xl hover:bg-gray-100 transition-all hover:scale-105">
            Start Free Trial <ArrowRight size={18} />
          </Link>
        </div>
      </main>
    </div>
  );
}
