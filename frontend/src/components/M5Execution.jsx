import React, { useState, useEffect, useRef } from 'react';
import { useStore } from '../store.js';

export default function M5Execution() {
  const store = useStore.getState();
  const pipeline = store.pipeline || {};
  const navigate = store.navigate;
  const [agentData, setAgentData] = useState([]);
  const [isRunning, setRunning] = useState(false);
  const [activeAgent, setActiveAgent] = useState('idle');
  const timerRef = useRef(null);

  const fetchAgentStatus = () => {
    const pid = pipeline.task_id || window.__pipelineId;
    if (!pid) return;
    fetch(`/api/pipeline/agent-status/${pid}`)
      .then(r => r.json())
      .then(d => {
        setAgentData(d.agents || []);
        const running = (d.agents || []).find(a => a.status === 'running');
        if (running) setActiveAgent(running.id);
      }).catch(() => {});
  };

  useEffect(() => {
    fetchAgentStatus();
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, []);

  const handleStart = () => {
    if (isRunning) return;
    setRunning(true);
    setActiveAgent('pm');
    store.startExecution?.();
    timerRef.current = setInterval(() => {
      fetchAgentStatus();
      const pid = pipeline.task_id || window.__pipelineId;
      if (pid) {
        fetch(`/api/pipeline/status?task_id=${pid}`)
          .then(r => r.json())
          .then(d => {
            if (d.progress > 50) { clearInterval(timerRef.current); setRunning(false); setActiveAgent('done'); }
          }).catch(() => {});
      }
    }, 2000);
  };

  const defaultAgents = [
    { id: 'pm', name: 'PM Agent', icon: '🧭', desc: '需求分析', status: 'pending' },
    { id: 'architect', name: 'Architect', icon: '🎨', desc: '架构设计', status: 'pending' },
    { id: 'developer', name: 'Developer', icon: '💻', desc: '代码生成', status: 'pending' },
    { id: 'tester', name: 'Tester', icon: '🧪', desc: '测试执行', status: 'pending' },
    { id: 'reviewer', name: 'Reviewer', icon: '🧐', desc: '代码审查', status: 'pending' },
    { id: 'devops', name: 'DevOps', icon: '🚀', desc: '构建推送', status: 'pending' },
  ];
  const agents = agentData.length > 0 ? agentData : defaultAgents;

  return (
    <div className="grid grid-cols-3 gap-8">
      <div className="col-span-2 bg-white rounded-2xl border border-slate-200 p-6 h-[480px] flex flex-col">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-bold">🤖 LangGraph 多 Agent 协同拓扑</h3>
          {isRunning && <span className="text-xs px-2.5 py-0.5 bg-amber-50 border border-amber-200 text-amber-600 rounded-md animate-pulse">⚡ Agent 密集通信中</span>}
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="grid grid-cols-6 gap-3 w-full">
            {agents.map((a, idx) => (
              <div key={a.id} className="flex flex-col items-center">
                <div className={`p-3 rounded-xl border-2 text-center w-full transition-all ${
                  activeAgent === a.id ? 'border-indigo-500 bg-indigo-50 shadow-md ring-2 ring-indigo-200' :
                  a.status === 'done' ? 'border-emerald-300 bg-emerald-50' : 'border-slate-100 bg-slate-50'
                }`}>
                  <p className="text-xl">{a.icon}</p>
                  <p className="text-[11px] font-bold">{a.name}</p>
                  <p className="text-[9px] text-slate-400">{a.desc}</p>
                  {a.output && <p className="text-[8px] text-indigo-500 mt-0.5">{a.output.substring(0, 30)}</p>}
                </div>
                {idx < agents.length - 1 && (
                  <div className={`h-6 w-0.5 ${a.status === 'done' ? 'bg-emerald-300' : isRunning ? 'bg-indigo-300 animate-pulse' : 'bg-slate-200'}`} />
                )}
              </div>
            ))}
          </div>
        </div>
        <div className="flex items-center justify-between pt-4 border-t">
          <button onClick={handleStart} disabled={isRunning}
            className={`px-5 py-2.5 rounded-xl text-sm font-medium ${isRunning ? 'bg-slate-200 text-slate-400' : 'bg-slate-900 text-white'}`}>
            {isRunning ? '⏳ 执行中...' : activeAgent === 'done' ? '🔄 重新执行' : '🚀 启动多 Agent 构建'}
          </button>
          {!isRunning && (pipeline.progress || 0) > 30 && (
            <button onClick={() => navigate('qa')} className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium pulse-glow">进入验证 QA ➔</button>
          )}
        </div>
      </div>
      <div className="col-span-1 bg-slate-900 text-slate-200 rounded-2xl p-4 font-mono text-xs h-[480px] flex flex-col">
        <div className="text-[10px] text-slate-500 border-b border-slate-800 pb-1.5 font-bold">⚡ Agent Prompt 实时追踪</div>
        <div className="flex-1 overflow-y-auto pt-3 space-y-2">
          {agents.map((a, i) => (
            <div key={i} className="text-emerald-400 text-[11px] p-1.5 hover:bg-slate-800/50 rounded">
              [{a.status === 'done' ? '✅' : a.status === 'running' ? '🔄' : '⬜'}] {a.name}: {a.output || '等待调度...'}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
