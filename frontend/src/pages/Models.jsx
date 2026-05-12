import { useState, useEffect } from 'react'
import { modelAPI } from '../api/api'
import GlassCard from '../components/GlassCard'

function Models() {
  const [modelInfo, setModelInfo] = useState({
    primary_model: { name: 'Loading...', provider: '', model_id: '', parameters: '', temperature: '', context_window: '', api_connected: false },
    backup_provider: { name: '', api_connected: false },
    orchestrator: { name: '', version: '', agents: [] },
    tools: []
  })

  useEffect(() => {
    const loadModelInfo = async () => {
      try {
        const data = await modelAPI.getInfo()
        setModelInfo(data)
      } catch (e) {
        console.error('Model info error:', e)
      }
    }
    loadModelInfo()
  }, [])

  const pm = modelInfo.primary_model

  return (
    <div className="space-y-6">
      {/* Header */}
      <section className="space-y-2 mb-6">
        <div className="inline-flex items-center px-2 py-1 rounded-full bg-primary/10 border border-primary/20">
          <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse mr-2"></div>
          <span className="text-[10px] font-label font-bold uppercase tracking-widest text-primary">Infrastructure</span>
        </div>
        <h1 className="font-headline text-3xl font-extrabold leading-tight tracking-tighter text-on-surface">
          LLM &<br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">Agent Config</span>
        </h1>
      </section>

      {/* Model Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <GlassCard className="p-5">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="font-headline font-bold text-lg">{pm.name}</h3>
              <p className="text-xs text-on-surface-variant">{pm.provider}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${pm.api_connected ? 'bg-[#34d399]/15 text-[#34d399]' : 'bg-[#aaaab3]/10 text-[#aaaab3]'}`}>
              {pm.api_connected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-surface-container-highest/50 p-3 rounded-xl">
              <p className="text-[9px] font-label uppercase text-on-surface-variant">Model ID</p>
              <p className="text-xs font-bold mt-1 font-mono">{pm.model_id}</p>
            </div>
            <div className="bg-surface-container-highest/50 p-3 rounded-xl">
              <p className="text-[9px] font-label uppercase text-on-surface-variant">Temp</p>
              <p className="text-xs font-bold mt-1">{pm.temperature}</p>
            </div>
            <div className="bg-surface-container-highest/50 p-3 rounded-xl">
              <p className="text-[9px] font-label uppercase text-on-surface-variant">Params</p>
              <p className="text-xs font-bold mt-1">{pm.parameters}</p>
            </div>
            <div className="bg-surface-container-highest/50 p-3 rounded-xl">
              <p className="text-[9px] font-label uppercase text-on-surface-variant">Context</p>
              <p className="text-xs font-bold mt-1">{pm.context_window}</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard className="p-5 bg-gradient-to-br from-surface-container to-surface-container-high">
          <h3 className="font-headline font-bold text-lg mb-2">Orchestrator</h3>
          <p className="text-xs text-on-surface-variant mb-4">{modelInfo.orchestrator.name} v{modelInfo.orchestrator.version}</p>
          <div className="flex gap-2 mb-4">
            <span className="px-3 py-1 rounded-full bg-primary/10 text-[10px] font-bold text-primary uppercase tracking-wider">
              {modelInfo.orchestrator.agents?.length || 3} AGENTS
            </span>
            <span className="px-3 py-1 rounded-full bg-secondary/10 text-[10px] font-bold text-secondary uppercase tracking-wider">
              BACKUP: {modelInfo.backup_provider.name} {modelInfo.backup_provider.api_connected ? '✓' : '✗'}
            </span>
          </div>
          <p className="text-[10px] text-on-surface-variant/50 uppercase tracking-wider mb-2">Pipeline Flow</p>
          <p className="text-xs text-on-surface-variant">Nghiên cứu → Phản biện → Báo cáo MD</p>
        </GlassCard>
      </div>

      {/* Agents List */}
      <section>
        <h2 className="font-headline text-xl font-bold mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-primary">smart_toy</span>
          AI Agent Registry
        </h2>
        <div className="space-y-2">
          {modelInfo.orchestrator.agents?.map((agent, i) => (
            <div key={i} className="glass-card p-4 rounded-xl flex gap-4 hover:bg-surface-container transition-all">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-primary to-secondary flex items-center justify-center font-bold text-surface text-sm shrink-0">
                {i + 1}
              </div>
              <div className="flex-1">
                <div className="font-headline font-bold text-sm text-on-surface mb-1">{agent.role}</div>
                <div className="flex flex-wrap gap-1">
                  {agent.tools?.map((tool, idx) => (
                    <code key={idx} className="bg-primary/10 text-primary px-2 py-0.5 rounded text-[10px] font-mono">{tool}</code>
                  ))}
                </div>
              </div>
            </div>
          )) || <p className="text-on-surface-variant">Loading agents...</p>}
        </div>
      </section>

      {/* Tool Inventory */}
      <section>
        <h2 className="font-headline text-xl font-bold mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-secondary">build</span>
          Tool Inventory
        </h2>
        <GlassCard className="overflow-hidden">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/5">
                <th className="p-4 text-[10px] font-label uppercase tracking-widest text-on-surface-variant">Tool Name</th>
                <th className="p-4 text-[10px] font-label uppercase tracking-widest text-on-surface-variant">Type</th>
                <th className="p-4 text-[10px] font-label uppercase tracking-widest text-on-surface-variant">Description</th>
              </tr>
            </thead>
            <tbody>
              {modelInfo.tools?.map((tool, idx) => (
                <tr key={idx} className="border-b border-white/5 hover:bg-surface-container-highest/30 transition-colors">
                  <td className="p-4 text-primary font-mono text-xs">{tool.name}</td>
                  <td className="p-4 text-xs text-on-surface-variant">{tool.type}</td>
                  <td className="p-4 text-xs text-on-surface-variant">{tool.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </GlassCard>
      </section>
    </div>
  )
}

export default Models
