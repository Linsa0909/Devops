import React, { useState } from 'react';
import { useStore } from '../store.js';

export default function M2IdeaHub() {
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const { pipeline, startPipeline } = useStore.getState();
  const isSubmitting = pipeline.status === 'ANALYZING' || pipeline.status === 'ANALYSIS_READY';
  const charCount = desc.length;

  const templates = [
    { name: '请假审批系统', desc: '员工在线提交请假申请 → 主管审批 → HR备案。支持年假/事假/病假类型，含通知推送。' },
    { name: '智能周报生成', desc: '自动抓取本周Git提交和Jira任务完成情况，大模型润色生成Markdown周报。' },
    { name: 'API网关服务', desc: '统一API网关，支持路由、限流、鉴权、日志。后端微服务注册发现。' },
  ];

  const handleFileUpload = (e) => {
    const files = e.target.files;
    if (!files?.length) return;
    for (let k = 0; k < files.length; k++) {
      const fd = new FormData();
      fd.append('file', files[k]);
      fetch('/api/pipeline/upload', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(d => {
          if (d.text?.length > 10) {
            setDesc(prev => prev + '\n\n## 📎 ' + d.filename + '\n' + d.text.substring(0, 2000));
            setUploadedFiles(prev => [...prev, { name: d.filename, type: d.type, size: d.size }]);
          }
        }).catch(() => {});
    }
  };

  return (
    <div className="grid grid-cols-5 gap-6 animate-fadeIn">
      <div className="col-span-3 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center"><span className="text-xl">💡</span></div>
          <div><h3 className="text-base font-bold text-slate-800">需求孵化</h3><p className="text-[11px] text-slate-400">描述你的产品构想, AI 自动拆解为标准软件需求</p></div>
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-600 flex items-center space-x-1.5 mb-2"><span className="w-1 h-1 rounded-full bg-indigo-500"></span><span>项目名称</span></label>
            <input type="text" disabled={isSubmitting} value={name} onChange={e => setName(e.target.value)}
              placeholder="给你的产品起个名字..." className="w-full text-sm border border-slate-200 rounded-xl px-4 py-3 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 focus:outline-none transition-all placeholder:text-slate-300" />
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-600 flex items-center space-x-1.5"><span className="w-1 h-1 rounded-full bg-indigo-500"></span><span>需求描述</span></label>
              <span className={`text-[10px] font-mono ${charCount > 50 ? 'text-emerald-500' : 'text-slate-400'}`}>{charCount} 字</span>
            </div>
            <textarea rows="10" disabled={isSubmitting} value={desc} onChange={e => setDesc(e.target.value)}
              placeholder="尽情描述你的想法：业务流程是什么？用户怎么交互？" className="w-full text-sm border border-slate-200 rounded-xl px-4 py-3 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 focus:outline-none transition-all placeholder:text-slate-300 font-sans leading-relaxed resize-none"></textarea>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-[10px] text-slate-400 shrink-0">快速模板:</span>
            {templates.map((t, i) => (
              <button key={i} onClick={() => { setName(t.name); setDesc(t.desc); }}
                className="px-3 py-1.5 rounded-lg text-[11px] font-medium bg-slate-50 border border-slate-200 text-slate-500 hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-600 transition-all whitespace-nowrap">{t.name}</button>
            ))}
          </div>

          <label className="block w-full border-2 border-dashed border-slate-200 rounded-xl p-4 text-center cursor-pointer hover:border-indigo-300 hover:bg-indigo-50/30 transition-all">
            <input type="file" accept=".md,.txt,.docx,.pdf,.html,.png,.jpg,.jpeg" multiple onChange={handleFileUpload} className="hidden" />
            <span className="text-2xl block mb-1">📤</span>
            <span className="text-xs font-medium text-slate-500">拖拽文件到此处或 <span className="text-indigo-600">点击上传</span></span>
            <span className="block text-[10px] text-slate-400 mt-0.5">支持 .md .docx .pdf .html .png .jpg (图片自动 OCR)</span>
          </label>

          <div className="flex items-center justify-between pt-2">
            <p className="text-[11px] text-slate-400">提交后 AI: 需求分析 → 架构设计 → 代码生成 → 测试 → 发布</p>
            <button onClick={() => {
              if (!name.trim() || !desc.trim()) { alert('请完整填写需求名称与构想描述！'); return; }
              startPipeline(name, desc);
            }} disabled={isSubmitting}
              className={`px-6 py-3 rounded-xl text-sm font-semibold shadow-sm transition-all flex items-center space-x-2 ${isSubmitting ? 'bg-indigo-100 text-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-200'}`}>
              {isSubmitting ? (<span className="flex items-center space-x-2"><span className="w-4 h-4 border-2 border-indigo-300 border-t-transparent rounded-full animate-spin"></span><span>AI 分析中...</span></span>)
                : (<span className="flex items-center space-x-2"><span>🚀 提交构想</span><span className="text-[10px] opacity-70">→ 自动拆解</span></span>)}
            </button>
          </div>
        </div>
      </div>

      <div className="col-span-2 space-y-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Pipeline 状态</h4>
          {pipeline.status === 'IDLE' ? (
            <div className="text-center py-8"><div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3"><span className="text-3xl">💤</span></div><p className="text-xs text-slate-400">等待提交需求</p></div>
          ) : (
            <div className="space-y-3 animate-fadeIn">
              <div className="flex items-center space-x-2">
                <span className={`w-2.5 h-2.5 rounded-full ${pipeline.status === 'ANALYSIS_READY' ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`}></span>
                <span className="text-xs font-semibold text-slate-700">{pipeline.status === 'ANALYZING' ? 'AI 分析中...' : '处理中'}</span>
              </div>
              <div className="bg-slate-50 rounded-lg p-3 space-y-1.5"><div className="h-2.5 shimmer rounded-full w-3/4"></div><div className="h-2.5 shimmer rounded-full w-1/2"></div></div>
            </div>
          )}
        </div>
        <div className="bg-gradient-to-br from-indigo-50 to-violet-50 rounded-2xl border border-indigo-100 p-4">
          <h5 className="text-xs font-bold text-indigo-700 mb-2">💡 小贴士</h5>
          <ul className="space-y-1.5 text-[11px] text-indigo-600 leading-relaxed"><li>• 描述越详细, AI 拆解越精准</li><li>• 提及角色与场景效果更好</li><li>• 可上传 PRD 文档作为参考</li></ul>
        </div>
      </div>
    </div>
  );
}
