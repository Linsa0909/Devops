import React, { useState } from 'react';
import { useStore } from '../store.js';

const DEFAULT_RULES = [
  { id: 'R-1', cat: '安全', title: '禁止明文传输和存储 Token', active: true, desc: '必须通过环境变量或 K8s Secret 挂载。' },
  { id: 'R-2', cat: '安全', title: '数据脱敏审查规则', active: true, desc: '禁止将含商业机密的日志发送给公有大模型。' },
  { id: 'R-3', cat: '规范', title: '前后端分离设计标准', active: true, desc: '禁止在前端嵌入业务逻辑 SQL。' },
  { id: 'R-4', cat: '规范', title: 'TailwindCSS 样式', active: true, desc: '禁止行内 style 样式。' },
  { id: 'R-5', cat: '性能', title: 'LLM 响应超时阻断', active: false, desc: '单次交互超过 15s 转异步。' },
  { id: 'R-6', cat: '安全', title: '容器镜像漏洞扫描', active: true, desc: '禁止高危漏洞镜像。' },
  { id: 'R-7', cat: '规范', title: 'API OpenAPI 3.0 规范', active: true, desc: '自动校验接口文档完整性。' },
  { id: 'R-8', cat: '性能', title: '数据库 LIMIT 分页', active: true, desc: '禁止无限制全表扫描。' },
];

export default function M4Guardrails() {
  const { confirmGuardrails } = useStore.getState();
  const [rules, setRules] = useState(DEFAULT_RULES);
  const [newRule, setNewRule] = useState('');

  const toggleRule = (id) => {
    setRules(rules.map(r => r.id === id ? { ...r, active: !r.active } : r));
  };

  const catColors = { '安全': 'bg-rose-100 text-rose-600 border-rose-200', '性能': 'bg-amber-100 text-amber-600 border-amber-200', '规范': 'bg-indigo-100 text-indigo-600 border-indigo-200', '自定义': 'bg-slate-100 text-slate-600 border-slate-200' };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-bold">🛡️ 规则约束矩阵</h3>
          <span className="text-xs text-slate-400">已激活 {rules.filter(r => r.active).length} / {rules.length}</span>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {rules.map(rule => (
            <div key={rule.id} className={`p-4 rounded-xl border ${rule.active ? 'bg-white border-slate-200' : 'bg-slate-50 border-slate-100 opacity-55'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-[10px] px-2 py-0.5 font-bold rounded-md border ${catColors[rule.cat] || catColors['自定义']}`}>{rule.cat}</span>
                <input type="checkbox" checked={rule.active} onChange={() => toggleRule(rule.id)} />
              </div>
              <h4 className="text-xs font-bold">{rule.id}: {rule.title}</h4>
              <p className="text-[11px] text-slate-500">{rule.desc}</p>
            </div>
          ))}
        </div>
        <div className="mt-4 flex space-x-2">
          <input value={newRule} onChange={e => setNewRule(e.target.value)} placeholder="➕ 追加自定义规则..."
            className="flex-1 text-sm border rounded-xl px-4 py-2.5" />
          <button onClick={() => { if (newRule.trim()) setRules([...rules, { id: `R-${rules.length + 1}`, cat: '自定义', title: newRule, active: true, desc: '' }]); setNewRule(''); }}
            className="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm">添加</button>
        </div>
      </div>
      <div className="flex justify-end">
        <button onClick={confirmGuardrails} className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold pulse-glow">保存约束，交由 Agent 协同执行 ➔</button>
      </div>
    </div>
  );
}
