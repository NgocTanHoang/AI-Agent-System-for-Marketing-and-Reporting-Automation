import { useEffect, useRef, useState } from 'react'
import { pipelineAPI } from '../api/api'
import GlassCard from '../components/GlassCard'

function Pipelines() {
  const [status, setStatus] = useState('IDLE')
  const [pid, setPid] = useState('N/A')
  const [elapsed, setElapsed] = useState(0)
  const [logs, setLogs] = useState('[SYSTEM]: Dashboard ready.')
  const logRef = useRef(null)
  const intervalRef = useRef(null)

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  const pollStatus = async () => {
    try {
      const data = await pipelineAPI.getStatus()
      setStatus(data.status)
      setPid(data.pid ? `#${data.pid}` : 'N/A')

      if (data.start_time) {
        const start = new Date(data.start_time)
        const end = data.status === 'RUNNING' ? new Date() : new Date(data.end_time || new Date())
        setElapsed(Math.floor((end - start) / 1000))
      } else {
        setElapsed(0)
      }

      const logData = await pipelineAPI.getLogs()
      if (logData.logs) {
        setLogs(logData.logs)
      }

      if (data.status !== 'RUNNING') {
        stopPolling()
      }
    } catch (e) {
      console.error('Pipeline polling error:', e)
      stopPolling()
    }
  }

  const startPolling = () => {
    if (intervalRef.current) return
    pollStatus()
    intervalRef.current = setInterval(pollStatus, 3000)
  }

  useEffect(() => {
    startPolling()
    return stopPolling
  }, [])

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [logs])

  const handleRunPipeline = async () => {
    try {
      await pipelineAPI.run()
      setStatus('RUNNING')
      startPolling()
    } catch (e) {
      console.error('Failed to run pipeline:', e)
    }
  }

  return (
    <div className="space-y-6">
      <section className="space-y-2 mb-6">
        <div className="inline-flex items-center px-2 py-1 rounded-full bg-error/10 border border-error/20">
          <div className="w-1.5 h-1.5 rounded-full bg-error animate-pulse mr-2"></div>
          <span className="text-[10px] font-label font-bold uppercase tracking-widest text-error">Processing Layer</span>
        </div>
        <h1 className="font-headline text-3xl font-extrabold leading-tight tracking-tighter text-on-surface">
          Pipeline<br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-error to-tertiary">Monitoring</span>
        </h1>
      </section>

      <div className="grid grid-cols-3 gap-4">
        <GlassCard className="p-4">
          <p className="text-[10px] font-label uppercase tracking-widest text-on-surface-variant mb-2">Status</p>
          <p className="font-headline font-bold">
            <span className={`status-tag status-${status.toLowerCase()}`}>{status}</span>
          </p>
        </GlassCard>
        <GlassCard className="p-4">
          <p className="text-[10px] font-label uppercase tracking-widest text-on-surface-variant mb-2">Process ID</p>
          <p className="font-headline font-bold">{pid}</p>
        </GlassCard>
        <GlassCard className="p-4">
          <p className="text-[10px] font-label uppercase tracking-widest text-on-surface-variant mb-2">Elapsed</p>
          <p className="font-headline font-bold">{elapsed}s</p>
        </GlassCard>
      </div>

      <GlassCard className="p-5">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-headline font-bold text-lg">Live Activity Logs</h3>
          <span className="text-[10px] font-label uppercase tracking-widest text-on-surface-variant">
            ● {status === 'RUNNING' ? 'RUNNING' : 'Standby'}
          </span>
        </div>
        <div
          ref={logRef}
          className="bg-[#000000] border border-surface-container-highest rounded-xl p-4 h-80 overflow-y-auto font-mono text-xs text-[#8899aa] leading-relaxed whitespace-pre-wrap"
        >
          {logs}
        </div>
        <button
          onClick={handleRunPipeline}
          disabled={status === 'RUNNING'}
          className="mt-4 w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {status === 'RUNNING' ? 'RUNNING...' : '▶ Run Pipeline'}
        </button>
      </GlassCard>
    </div>
  )
}

export default Pipelines
