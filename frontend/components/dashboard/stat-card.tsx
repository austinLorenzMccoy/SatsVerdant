import type { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface StatCardProps {
  label: string
  value: string
  change?: string
  icon?: LucideIcon
  className?: string
}

export function StatCard({ label, value, change, icon: Icon, className }: StatCardProps) {
  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-verdant-sage/20 bg-verdant-moss/20 p-6 backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:border-verdant-sats/30 hover:shadow-xl hover:shadow-verdant-sats/10",
        className
      )}
    >
      {/* Accent Bar */}
      <span className="absolute left-0 right-0 top-0 h-[3px] origin-left scale-x-0 bg-gradient-to-r from-verdant-sats to-verdant-gold transition-transform duration-300 group-hover:scale-x-100" />

      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-verdant-sage">
            {label}
          </p>
          <p className="mt-2 font-mono text-3xl font-bold text-verdant-paper">{value}</p>
          {change && <p className="mt-1 text-sm text-success">{change}</p>}
        </div>
        {Icon && (
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-verdant-sats/10 text-verdant-sats transition-transform duration-300 group-hover:scale-110">
            <Icon className="h-6 w-6" />
          </div>
        )}
      </div>
    </div>
  )
}
