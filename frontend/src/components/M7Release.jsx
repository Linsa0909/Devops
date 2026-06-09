import React, { useState, useEffect } from 'react';
import { useStore } from '../store.js';

export default function M7Release() {
  const { pipeline } = useStore.getState();
  const [fileTree, setFileTree] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');

  useEffect(() => {
    const pid = pipeline.task_id || window.__pipelineId;
    if (!pid) return;
    fetch(`/api/pipeline/products/${pid}`).then(r => r.json()).then(d => setFileTree(d.files || [])).catch(() => {});
  }, []);

  const openFile = (path) => {
    const pid = pipeline.task_id || window.__pipelineId;
    if (!pid) return;
    setSelectedFile(path);
    fetch(`/api/pipeline/files/${pid}/${path}`).then(r => r.json()).then(d => setFileContent(d.content || '')).catch(() => setFileContent('加载失败'));
  };

  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl p-6 text-white shadow-md">
        <h3 className="text-lg font-bold mb-2">🎉 交付完成 — {pipeline.name || 'AgentDev OS'}</h3>
        <p className="text-sm text-emerald-100">Agent 已将需求转化为可执行代码并归档。共 {fileTree.length} 个文件。</p>
        <div className="mt-3 flex items-center space-x-3">
          <a href="http://localhost:3000" className="px-4 py-2 bg-white text-emerald-700 text-sm font-semibold rounded-xl inline-block">🌐 Gitea 仓库</a>
          <span className="text-xs text-emerald-100 font-mono">{pipeline.task_id || ''}</span>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">🌐 部署预览</h4>
          <button onClick={() => {
            const pid = pipeline.task_id || window.__pipelineId;
            fetch(`/api/deploy/${pid}`, { method: 'POST' }).then(r => r.json()).then(d => d.url && window.open(d.url, '_blank')).catch(() => {});
          }} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold">🚀 部署并打开</button>
        </div>
        <p className="text-[11px] text-slate-500">将 Agent 生成的代码启动为可访问的 Web 服务</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-1 bg-white rounded-2xl border border-slate-200 p-4 h-[400px] flex flex-col">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">📁 产物文件 ({fileTree.length})</h4>
          <div className="flex-1 overflow-y-auto space-y-0.5">
            {fileTree.length === 0 ? <p className="text-xs text-slate-400 text-center pt-10">暂无产物</p> :
              fileTree.map((f, i) => (
                <div key={i} onClick={() => openFile(f.path)}
                  className={`px-2.5 py-1.5 rounded-lg text-xs cursor-pointer flex items-center space-x-2 ${selectedFile === f.path ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-slate-600 hover:bg-slate-50'}`}>
                  <span>📄</span><span className="truncate flex-1">{f.path}</span><span className="text-[10px] text-slate-400">{Math.round(f.size / 1000)}KB</span>
                </div>
              ))}
          </div>
        </div>
        <div className="col-span-2 bg-slate-900 rounded-2xl p-4 font-mono text-xs text-slate-200 h-[400px] flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
            <span className="text-emerald-400 text-[11px]">{selectedFile || '(点击左侧文件查看)'}</span>
            <span className="text-[10px] text-slate-500">{fileContent.length} 字符</span>
          </div>
          <div className="flex-1 overflow-y-auto">
            {selectedFile ? <pre className="text-[11px] leading-relaxed whitespace-pre-wrap">{fileContent || '加载中...'}</pre>
              : (<div className="text-slate-600 text-center pt-16"><p className="text-lg mb-2">📂</p><p>点击左侧文件查看源代码</p></div>)}
          </div>
        </div>
      </div>
    </div>
  );
}
