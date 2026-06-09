import React, { useState } from 'react';
import { useStore } from '../store.js';

export default function LoginPage() {
  const { login } = useStore.getState();
  const [username, setUsername] = useState('devops');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = () => {
    if (!username.trim()) { setError('请输入用户名'); return; }
    if (!password.trim()) { setError('请输入密码'); return; }
    setLoading(true);
    setError('');
    fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
      .then(r => r.json())
      .then(d => {
        if (d.status === 'ok') {
          login(d.username, d.token);
        } else {
          setError(d.message || '登录失败');
        }
        setLoading(false);
      })
      .catch(e => {
        setError('连接失败: ' + e.message);
        setLoading(false);
      });
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-gradient-to-br from-slate-50 via-indigo-50 to-slate-100">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white font-bold text-2xl shadow-lg shadow-indigo-200 mx-auto mb-3">Ω</div>
          <h1 className="text-xl font-bold text-slate-800">AgentDev OS</h1>
          <p className="text-xs text-slate-500 mt-1">端到端软件需求 Agent 平台</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div>
            <label className="text-[11px] font-bold text-slate-400 block mb-1.5 uppercase tracking-wide">用户名</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleLogin(); }}
              className="w-full text-sm border border-slate-200 rounded-xl px-4 py-2.5 bg-slate-50/50 focus:bg-white focus:border-indigo-500 focus:outline-none transition-all" placeholder="Gitea 用户名" />
          </div>
          <div>
            <label className="text-[11px] font-bold text-slate-400 block mb-1.5 uppercase tracking-wide">密码</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleLogin(); }}
              className="w-full text-sm border border-slate-200 rounded-xl px-4 py-2.5 bg-slate-50/50 focus:bg-white focus:border-indigo-500 focus:outline-none transition-all" placeholder="Gitea 密码" />
          </div>
          {error && <div className="bg-rose-50 border border-rose-200 rounded-xl px-4 py-2.5 text-xs text-rose-600">{error}</div>}
          <button onClick={handleLogin} disabled={loading}
            className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-sm font-semibold shadow-xs transition-all disabled:opacity-50">
            {loading ? '验证中...' : '登录 AgentDev OS'}
          </button>
        </div>
        <p className="text-center text-[11px] text-slate-400 mt-4">
          Gitea: <a href="http://localhost:3000" target="_blank" className="text-indigo-600 hover:underline">localhost:3000</a>
        </p>
      </div>
    </div>
  );
}
