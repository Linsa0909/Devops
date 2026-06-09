// Zustand 兼容 API 状态管理
// 与 index.html 中的 useStore 保持一致

const STEPS_ORDER = ['idea', 'analysis', 'guardrails', 'execution', 'qa', 'release'];

export const createStore = (createState) => {
  let state;
  const listeners = new Set();
  const setState = (partial) => {
    const nextState = typeof partial === 'function' ? partial(state) : partial;
    if (nextState !== state) {
      state = { ...state, ...nextState };
      listeners.forEach((fn) => fn(state));
    }
  };
  const getState = () => state;
  const subscribe = (fn) => { listeners.add(fn); return () => listeners.delete(fn); };
  state = createState(setState, getState);
  return { setState, getState, subscribe };
};

export const useStore = createStore((set, get) => ({
  isLoggedIn: false,
  currentUser: '',
  authToken: '',
  currentStep: 'idea',
  maxUnlockedStep: 'idea',
  pipeline: { task_id: null, status: 'IDLE', progress: 0, tasks: [] },
  logs: ['[系统初始化] AgentDev OS 准备就绪...'],
  m3Data: { requirement: '', design: '', mermaidChart: '' },
  _pollTimer: null,

  login(username, token) {
    set({ isLoggedIn: true, currentUser: username, authToken: token });
  },
  logout() {
    set({ isLoggedIn: false, currentUser: '', authToken: '', currentStep: 'idea' });
  },
  navigate(step) { set({ currentStep: step }); },
  unlockStep(step) {
    const curMax = STEPS_ORDER.indexOf(get().maxUnlockedStep);
    const tgt = STEPS_ORDER.indexOf(step);
    if (tgt > curMax) set({ maxUnlockedStep: step });
  },
  appendLog(msg) {
    set({ logs: [...get().logs, `[${new Date().toLocaleTimeString()}] ${msg}`] });
  },

  startPipeline(name, desc) {
    const taskId = 'task_' + Date.now();
    set({ pipeline: { task_id: taskId, status: 'ANALYZING', progress: 0, tasks: [] } });
    get().appendLog(`[M2] 提交需求: "${name}"...`);

    fetch('/api/pipeline/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description: desc }),
    })
      .then(r => r.json())
      .then(data => {
        const realTaskId = data.id;
        window.__pipelineId = realTaskId;
        get().appendLog(`[M2] ✅ task_id=${realTaskId}`);
        set({
          pipeline: {
            task_id: realTaskId,
            status: data.status || 'ANALYZING',
            progress: data.progress || 5,
            tasks: data.tasks || [],
          },
          m3Data: {
            requirement: (data.artifacts || []).filter(a => a.type === 'requirement').map(a => a.content).join('') || '',
            design: (data.artifacts || []).filter(a => a.type === 'design').map(a => a.content).join('') || '',
            mermaidChart: '',
          },
        });
        if (data.status === 'GATE_WAIT') {
          get().unlockStep('analysis');
          set({ currentStep: 'analysis' });
        }
      })
      .catch(err => {
        get().appendLog(`[ERROR] ${err.message}`);
      });
  },

  confirmAnalysis() {
    const pid = get().pipeline.task_id;
    get().appendLog('[M3 Gate] 人工审计放行...');
    if (pid?.startsWith('pipe_')) {
      fetch('/api/pipeline/gate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pipeline_id: pid, gate_id: 'Gate1', action: 'approve', comment: '通过' }),
      })
        .then(r => r.json())
        .then(data => {
          get().appendLog('[M3 Gate] ✅ Gate1 批准');
          get().unlockStep('guardrails');
          set({ currentStep: 'guardrails' });
        })
        .catch(() => {
          get().unlockStep('guardrails');
          set({ currentStep: 'guardrails' });
        });
    } else {
      get().unlockStep('guardrails');
      set({ currentStep: 'guardrails' });
    }
  },

  confirmGuardrails() {
    get().appendLog('[M4 Gate] 规则锁定...');
    get().unlockStep('execution');
    set({ currentStep: 'execution' });
  },

  startExecution() {
    get().appendLog('[Runtime] 下发多 Agent 任务...');
  },

  releaseProduct() {
    const pid = get().pipeline.task_id;
    get().appendLog('[System] 调用 Gate3 发布...');
    if (pid?.startsWith('pipe_')) {
      fetch('/api/pipeline/gate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pipeline_id: pid, gate_id: 'Gate3', action: 'approve', comment: '发布' }),
      })
        .then(r => r.json())
        .then(() => {
          get().unlockStep('release');
          set({ currentStep: 'release' });
        })
        .catch(() => {
          get().unlockStep('release');
          set({ currentStep: 'release' });
        });
    } else {
      get().unlockStep('release');
      set({ currentStep: 'release' });
    }
  },

  cleanup() {
    if (get()._pollTimer) clearInterval(get()._pollTimer);
  },
}));
