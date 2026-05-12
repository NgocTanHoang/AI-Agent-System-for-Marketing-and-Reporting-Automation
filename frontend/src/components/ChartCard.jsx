function ChartCard({ title, subtitle, children, className = '' }) {
  return (
    <div className={`glass-card rounded-2xl p-5 ${className}`}>
      {(title || subtitle) && (
        <div className="flex justify-between items-center mb-4">
          {title && <h3 className="font-headline font-bold text-lg">{title}</h3>}
          {subtitle && <span className="text-xs font-label text-on-surface-variant">{subtitle}</span>}
        </div>
      )}
      <div className="h-64">
        {children}
      </div>
    </div>
  )
}

export default ChartCard
