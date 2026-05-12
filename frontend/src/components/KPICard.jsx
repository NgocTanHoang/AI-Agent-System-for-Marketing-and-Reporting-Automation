function KPICard({ icon, title, value, subtitle, borderColor = 'border-primary', badge }) {
  return (
    <div className={`glass-card p-4 rounded-xl flex flex-col justify-between h-32 border-l-2 ${borderColor}`}>
      <div className="flex justify-between items-start">
        <span className="material-symbols-outlined text-2xl" style={{ color: 'var(--primary)' }}>{icon}</span>
        {badge && <span className="text-[10px] font-label font-bold uppercase tracking-wider" style={{ color: 'var(--primary)' }}>{badge}</span>}
      </div>
      <div>
        <div className="text-2xl font-headline font-bold">{value}</div>
        <div className="text-[10px] font-label text-on-surface-variant uppercase tracking-wider">{title}</div>
      </div>
    </div>
  )
}

export default KPICard
