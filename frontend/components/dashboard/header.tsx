"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { useSidebar } from "@/hooks/use-sidebar"
import { cn } from "@/lib/utils"

const pageTitles: Record<string, string> = {
  "/dashboard": "Overview",
  "/dashboard/submit": "Submit Waste",
  "/dashboard/rewards": "Rewards",
  "/dashboard/validate": "Validate",
  "/dashboard/impact": "Impact",
  "/dashboard/settings": "Settings",
}

export function DashboardHeader() {
  const pathname = usePathname()
  const { isCollapsed } = useSidebar()
  const title = pageTitles[pathname] || "Dashboard"

  return (
    <header
      className={cn(
        "sticky top-0 z-10 border-b border-verdant-sage/10 bg-verdant-carbon/60 px-6 py-4 backdrop-blur-xl lg:px-8"
      )}
      data-collapsed={isCollapsed}
    >
      <h1 className="font-display text-2xl font-bold text-verdant-paper">{title}</h1>
      <div className="mt-1 flex items-center gap-2 text-sm text-verdant-sage">
        <Link href="/" className="transition-colors hover:text-verdant-sats">
          Home
        </Link>
        <span>{">"}</span>
        <span>Dashboard</span>
        {title !== "Overview" && (
          <>
            <span>{">"}</span>
            <span>{title}</span>
          </>
        )}
      </div>
    </header>
  )
}
