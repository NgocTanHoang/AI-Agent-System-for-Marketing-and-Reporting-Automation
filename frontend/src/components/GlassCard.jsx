function GlassCard({ children, className = '', ...props }) {
  return (
    <div className={`glass-card rounded-2xl p-5 ${className}`} {...props}>
      {children}
    </div>
  )
}

export default GlassCard
