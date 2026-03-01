import Link from "next/link"

interface LogoProps {
  collapsed?: boolean
  className?: string
}

export function Logo({ collapsed = false, className = "" }: LogoProps) {
  return (
    <Link href="/" className={`flex items-center gap-2 ${className}`}>
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-verdant-sprout to-verdant-sats font-display text-sm font-bold text-verdant-carbon">
        SV
      </div>
      {!collapsed && (
        <span className="font-display text-xl font-extrabold text-verdant-sats">
          SatsVerdant
        </span>
      )}
    </Link>
  )
}
