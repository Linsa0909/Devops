import React, { useState, useEffect } from 'react';
import { useStore } from '../store.js';

export default function M6QA() {
  const store = useStore.getState();
  const pipeline = store.pipeline || {};
  const [qaStatus, setQaStatus] = useState('running');
  const [testFiles, setTestFiles] = useState([]);
  const [testOutput, setTestOutput] = useState('');
  const [fixAttempts, setFixAttempts] = useState([]);
  const [selTest, setSelTest] = useState(-1);

  useEffect(() => {
    const pid = pipeline.task_id || window.__pipelineId;
    if (!pid) return;
    fetch(`/api/pipeline/test-results/${pid}`)
      .then(r => r.json())
      .then(d => {
        setTestFiles(d.test_files || []);
        setTestOutput(d.test_output || '');
        setFixAttempts(d.fix_attempts || []);
        setQaStatus(d.total_retries > 0 ? 'healing' : d.test_files?.length > 0 ? 'passed' : 'running');
      }).catch(() => {});
  }, []);

  const banner = {
    running: { bg: 'bg-amber-50 border-amber-200', text: 'text-amber-600', label: '⏳ 测试运行中...' },
    healing: { bg: 'bg-indigo-50 border-indigo-200', text: 'text-indigo-600', label: `🛠️ 自愈修复中 (${fixAttempts.length}次)` },
    passed: { bg: 'bg-emerald-50 border-emerald-200', text: 'text-emerald-600', label: '🟢 全部测试通过' },
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-bold">🧪 自动化沙箱验证与自愈中心</h3>
          <span className={`text-xs px-3 py-1 rounded-full font-medium border ${banner[qaStatus]?.bg || ''} ${banner[qaStatus]?.text || ''}`}>
            {banner[qaStatus]?.label || '⏳'}
          </span>
        </div>
        <div className="grid grid-cols-3 gap-5 mb-5">
          {[{ label: '测试文件', value: String(testFiles.length) }, { label: '重试次数', value: String(fixAttempts.length) }, { label: '状态', value: qaStatus }].map((m, i) => (
            <div key={i} className="bg-slate-50 rounded-xl p-4 border border-slate-100 text-center">
              <span className="text-[10px] text-slate-400 font-bold uppercase block mb-1">{m.label}</span>
              <span className="text-2xl font-black text-slate-700">{m.value}</span>
            </div>
          ))}
        </div>

        {fixAttempts.length > 0 && (
          <div className="mt-4 p-4 bg-slate-900 rounded-xl text-xs font-mono text-slate-300">
            <div className="text-[10px] text-indigo-400 font-bold mb-1">🤖 Self-Healing 日志:</div>
            {fixAttempts.map((f, i) => <div key={i} className="log-line">{f.file}</div>)}
          </div>
        )}

        {testFiles.length > 0 && (
          <div className="mt-4">
            <h5 className="text-xs font-bold text-slate-500 mb-2">📄 测试代码 ({testFiles.length})</h5>
            <div className="flex space-x-2 mb-2">
              {testFiles.map((tf, i) => (
                <button key={i} onClick={() => setSelTest(selTest === i ? -1 : i)}
                  className={`px-3 py-1 rounded-lg text-xs border whitespace-nowrap ${selTest === i ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-slate-50 border-slate-200 text-slate-500'}`}>{tf.path}</button>
              ))}
            </div>
            {selTest >= 0 && testFiles[selTest] && (
              <div className="bg-slate-900 rounded-xl p-3 font-mono text-xs text-emerald-400 max-h-60 overflow-y-auto">
                <pre className="whitespace-pre-wrap">{testFiles[selTest].content}</pre>
              </div>
            )}
          </div>
        )}

        {testOutput && (
          <div className="mt-4">
            <h5 className="text-xs font-bold text-slate-500 mb-1">🧪 Pytest 输出</h5>
            <div className="bg-slate-900 rounded-xl p-3 font-mono text-[10px] text-slate-300 max-h-40 overflow-y-auto">
              <pre className="whitespace-pre-wrap">{testOutput}</pre>
            </div>
          </div>
        )}
      </div>
      {qaStatus === 'passed' && (
        <div className="flex justify-end">
          <button onClick={() => store.releaseProduct()} className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-semibold pulse-glow">一键发布 ➔</button>
        </div>
      )}
    </div>
  );
}
