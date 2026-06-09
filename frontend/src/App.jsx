import React, { useEffect } from 'react';
import { useStore } from './store.js';
import LoginPage from './components/LoginPage.jsx';
import M2IdeaHub from './components/M2IdeaHub.jsx';
import M3Analysis from './components/M3Analysis.jsx';
import M4Guardrails from './components/M4Guardrails.jsx';
import M5Execution from './components/M5Execution.jsx';
import M6QA from './components/M6QA.jsx';
import M7Release from './components/M7Release.jsx';

const STEPS_CONFIG = [
  { id: 'idea', label: '💡 需求孵化', short: '需求孵化' },
  { id: 'analysis', label: '🔍 智能分析', short: '智能分析' },
  { id: 'guardrails', label: '🛡️ 规则约束', short: '规则约束' },
  { id: 'execution', label: '🤖 Agent执行', short: 'Agent执行' },
  { id: 'qa', label: '🧪 验证QA', short: '验证QA' },
  { id: 'release', label: '📦 发布沉淀', short: '发布沉淀' },
];

function useStoreState() {
  const [, update] = React.useState({});
  useEffect(() => {
    const unsub = useStore.subscribe(() => update({}));
    return unsub;
  }, []);
  return useStore.getState();
}

export function LogPanel({ logs }) {
  const [open, setOpen] = React.useState(false);
  return (
    <div className="absolute bottom-4 right-6 z-30">
      <button onClick={() => setOpen(!open)}
        className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl shadow-md border text-xs font-medium ${open ? 'bg-white border-slate-300' : 'bg-white border-slate-200 text-slate-500'}`}>
        <span className={`w-2 h-2 rounded-full ${logs?.length > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'}`} />
        <span>📋 运行时日志</span>
        {logs?.length > 0 && <span className="bg-slate-100 text-slate-500 text-[10px] px-1.5 py-0.5 rounded-full font-mono">{logs.length}</span>}
        <span className="text-[10px]">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="absolute bottom-full right-0 mb-2 w-[560px] h-72 bg-white rounded-2xl border border-slate-200 shadow-2xl flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-100 bg-slate-50/50">
            <span className="text-xs font-semibold text-slate-500">RUNTIME LOGS</span>
            <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-600">✕</button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 font-mono text-[11px] text-slate-600 space-y-0.5">
            {(logs || []).map((log, i) => <div key={i} className="hover:bg-slate-50 px-2 py-0.5 rounded">{log}</div>)}
          </div>
        </div>
      );
    </div>
  );
}

export default function App() {
  const state = useStoreState();
  const { currentStep, logs, pipeline, navigate, isLoggedIn, currentUser, logout } = state;

  if (!isLoggedIn) return <LoginPage />;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-800 antialiased">
      <aside className="w-60 bg-white border-r border-slate-200 flex flex-col justify-between z-20 shrink-0">
        <div>
          <div className="p-5 border-b border-slate-100 flex items-center space-x-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white font-bold">Ω</div>
            <h1 className="font-bold text-base">AgentDev OS</h1>
          </div>
          <nav className="p-3 space-y-0.5">
            {STEPS_CONFIG.map(step => (
              <button key={step.id} onClick={() => navigate(step.id)}
                className={`w-full flex items-center justify-between px-4 py-2.5 rounded-xl text-left text-sm font-medium transition-all ${
                  currentStep === step.id ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'
                }`}>
                <span className="flex items-center space-x-2.5"><span className="text-base">{step.label.split(' ')[0]}</span><span>{step.label.split(' ').slice(1).join(' ')}</span></span>
              </button>
            ))}
          </nav>
        </div>
        <div className="p-4 border-t border-slate-100 bg-slate-50/40 flex items-center space-x-3 text-xs">
          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-indigo-500 to-violet-500 text-white flex items-center justify-center font-bold text-[11px]">{currentUser?.[0]?.toUpperCase() || 'H'}</div>
          <div className="flex-1"><p className="font-semibold">{currentUser || 'HUSTNLP Lab'}</p><p className="text-[10px] text-slate-400">Gitea: localhost:3000</p></div>
          <button onClick={logout} className="text-[10px] text-slate-400 hover:text-rose-500">退出</button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden relative">
        <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between z-10 shrink-0">
          <div className="flex items-center space-x-2">
            {STEPS_CONFIG.map((step, idx) => (
              <div key={step.id} className="flex items-center space-x-2 text-xs shrink-0">
                <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full border transition-all ${
                  currentStep === step.id ? 'bg-slate-900 text-white' : idx < STEPS_CONFIG.findIndex(s => s.id === currentStep) ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-50 text-slate-400'
                }`}>
                  <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${currentStep === step.id ? 'bg-white text-slate-900' : 'bg-slate-200/60 text-slate-500'}`}>{idx + 1}</span>
                  <span className="font-medium whitespace-nowrap">{step.short}</span>
                </div>
                {idx < STEPS_CONFIG.length - 1 && <span className="text-slate-300">/</span>}
              </div>
            ))}
          </div>
          <div className="flex items-center space-x-2 text-[11px] text-slate-400 font-mono bg-slate-50 border border-slate-200/60 rounded-lg px-2.5 py-1">
            <span className={`w-1.5 h-1.5 rounded-full ${pipeline?.status === 'RUNNING' ? 'bg-amber-500 animate-pulse' : 'bg-slate-300'}`} />
            <span>STATUS: {pipeline?.status || 'IDLE'}</span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-6xl mx-auto">
            {currentStep === 'idea' && <M2IdeaHub />}
            {currentStep === 'analysis' && <M3Analysis />}
            {currentStep === 'guardrails' && <M4Guardrails />}
            {currentStep === 'execution' && <M5Execution />}
            {currentStep === 'qa' && <M6QA />}
            {currentStep === 'release' && <M7Release />}
          </div>
        </main>
        <LogPanel logs={logs} />
      </div>
    </div>
  );
}
