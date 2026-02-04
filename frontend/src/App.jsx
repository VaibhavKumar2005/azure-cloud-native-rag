import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleVerify = async () => {
    if (!query) return;
    setLoading(true);
    setResult(null);

    try {
      // Points to your Django backend
      const response = await axios.post('http://127.0.0.1:8000/api/query/', {
        query: query
      });
      setResult(response.data);
    } catch (error) {
      console.error("Link Broken:", error);
      setResult({
        answer: "Connection failed. Is the Django Brain active?",
        faithfulness_score: 0
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 selection:bg-blue-500/30">
      
      {/* Ambient Background Glow */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-500/10 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[10%] right-[-5%] w-[40%] h-[40%] bg-indigo-600/10 blur-[100px] rounded-full"></div>
      </div>

      {/* Tailwind-style Navbar */}
      <nav className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-950/70 backdrop-blur-md px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-tr from-blue-500 to-indigo-600 rounded-lg shadow-lg shadow-blue-500/20 flex items-center justify-center font-black text-white">V</div>
          <span className="text-lg font-bold tracking-tight text-white">VeriRag</span>
        </div>
        <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-400">
          <span className="hover:text-white cursor-pointer transition-colors">Documentation</span>
          <span className="hover:text-white cursor-pointer transition-colors">Project 46</span>
          <div className={`px-3 py-1 rounded-full border border-slate-800 flex items-center gap-2 ${loading ? 'bg-blue-500/10' : 'bg-emerald-500/10'}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${loading ? 'bg-blue-400 animate-pulse' : 'bg-emerald-400'}`}></span>
            <span className="text-[10px] uppercase tracking-widest font-bold text-slate-300">
              {loading ? 'Analyzing' : 'Ready'}
            </span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 max-w-5xl mx-auto px-6 pt-24 pb-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight mb-6">
            RAG that doesn't <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-cyan-400">
              make things up.
            </span>
          </h1>
          <p className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto font-light leading-relaxed">
            Verify the faithfulness of your AI Librarian. Built for high-stakes 
            Computer Science research and verified generation.
          </p>
        </div>

        {/* The Search Engine Input */}
        <div className="max-w-3xl mx-auto relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-2xl blur opacity-20 group-focus-within:opacity-40 transition duration-500"></div>
          <div className="relative bg-slate-900 border border-slate-700 rounded-2xl flex items-center p-2 shadow-2xl">
            <input 
              type="text" 
              className="flex-1 bg-transparent px-5 py-4 text-white outline-none text-lg placeholder-slate-500"
              placeholder="Ask your library a question..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleVerify()}
            />
            <button 
              onClick={handleVerify}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-500 text-white px-10 py-4 rounded-xl font-bold transition-all active:scale-95 shadow-lg shadow-blue-500/20 disabled:bg-slate-800"
            >
              {loading ? 'Thinking...' : 'Verify'}
            </button>
          </div>
        </div>

        {/* Results Card */}
        {result && (
          <div className="mt-12 max-w-3xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-700">
            <div className="bg-slate-900/50 border border-slate-800 rounded-3xl overflow-hidden backdrop-blur-sm">
              <div className="px-8 py-5 border-b border-slate-800/50 flex justify-between items-center bg-slate-800/20">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Verified Response</span>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-slate-400">Faithfulness:</span>
                  <span className={`text-xs font-mono font-bold px-2 py-1 rounded ${result.faithfulness_score > 0.8 ? 'text-emerald-400 bg-emerald-400/10 border border-emerald-500/20' : 'text-amber-400 bg-amber-400/10 border border-amber-500/20'}`}>
                    {(result.faithfulness_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div className="p-10">
                <p className="text-xl text-slate-200 leading-relaxed font-light">
                  {result.answer}
                </p>
                {result.source_citation && (
                  <div className="mt-8 pt-8 border-t border-slate-800/50">
                    <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest block mb-3">Librarian's Proof</span>
                    <div className="p-5 bg-blue-500/5 rounded-2xl border border-blue-500/10 text-sm text-slate-400 font-mono leading-relaxed">
                      "{result.source_citation}"
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;