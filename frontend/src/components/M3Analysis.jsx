import React, { useState, useEffect } from 'react';
import { useStore } from '../store.js';

export default function M3Analysis() {
  const { m3Data, confirmAnalysis } = useStore.getState();
  const [activeTab, setActiveTab] = useState('req');

  useEffect(() => {
    if (m3Data.mermaidChart && window.mermaid) {
      try {
        window.mermaid.render('mermaid-svg', m3Data.mermaidChart).then(result => {
          const container = document.getElementById('mermaid-diagram');
          if (container) { container.innerHTML = result.svg; container.classList.remove('hidden'); }
        }).catch(() => {});
      } catch (e) { /* mermaid not loaded */ }
    }
  }, [m3Data.mermaidChart]);

  return (
    <div className="grid grid-cols-2 gap-8 animate-fadeIn">
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col h-[500px]">
        <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-2 shrink-0">
          <div className="flex space-x-1 bg-slate-100 p-0.5 rounded-lg">
            {['req', 'design'].map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={`px-3 py-1 text-xs font-medium rounded-md ${activeTab === tab ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500'}`}>
                {tab === 'req' ? '📄 requirement.md' : '🛠️ design.md'}
              </button>
            ))}
          </div>
        </div>
        <textarea className="flex-1 w-full text-xs font-mono p-4 bg-slate-50/50 border border-slate-100 rounded-xl resize-none"
          defaultValue={activeTab === 'req' ? m3Data.requirement : m3Data.design} readOnly />
      </div>
      <div className="flex flex-col h-[500px] space-y-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 flex-1 flex flex-col">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">🧭 架构拓扑图</h4>
          <div className="flex-1 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-center overflow-hidden">
            <div id="mermaid-diagram" className="hidden w-full h-full flex items-center justify-center p-4"></div>
            <div id="mermaid-fallback" className="text-slate-400 text-xs">{m3Data.mermaidChart ? '渲染中...' : '等待架构设计完成'}</div>
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-amber-200 p-4 flex items-center justify-between">
          <div><h5 className="text-xs font-bold">Human-in-the-loop 审计关口</h5><p className="text-[10px] text-slate-500">确认后推进到 M4</p></div>
          <button onClick={confirmAnalysis} className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold pulse-glow">放行并配置规则 ➔</button>
        </div>
      </div>
    </div>
  );
}
