"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useSidebar } from "@/hooks/use-sidebar"
import { useWallet } from "@/hooks/use-wallet"
import { Logo } from "@/components/logo"
import { Button } from "@/components/ui/button"
import {
  LayoutDashboard,
  Camera,
  Coins,
  CheckCircle2,
  Globe,
  Settings,
  ChevronLeft,
  Wallet,
} from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/submit", label: "Submit Waste", icon: Camera },
  { href: "/dashboard/rewards", label: "Rewards", icon: Coins },
  { href: "/dashboard/validate", label: "Validate", icon: CheckCircle2 },
  { href: "/dashboard/impact", label: "Impact", icon: Globe },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
]

export function DashboardSidebar() {
  const pathname = usePathname()
  const { isCollapsed, isMobileOpen, toggleCollapse, closeMobile } = useSidebar()
  const { isConnected, address, balance, connect } = useWallet()

  return (
    <>
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-verdant-carbon/80 backdrop-blur-sm lg:hidden"
          onClick={closeMobile}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-50 flex h-full flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300",
          isCollapsed ? "w-[72px]" : "w-[260px]",
          isMobileOpen ? "translate-x-0" : "-translate-x-full",
          "lg:translate-x-0"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-sidebar-border p-4">
          <Logo collapsed={isCollapsed} />
          {!isCollapsed && (
            <button
              onClick={toggleCollapse}
              className="hidden rounded-lg border border-verdant-sage/20 p-2 text-verdant-sage transition-colors hover:border-verdant-sprout hover:bg-verdant-sprout/10 lg:flex"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Wallet Status */}
        <div className="border-b border-sidebar-border p-4">
          {isConnected ? (
            <div
              className={cn(
                "rounded-xl border border-verdant-sprout/30 bg-verdant-sprout/20 p-3",
                isCollapsed && "p-2"
              )}
            >
              {!isCollapsed && (
                <p className="truncate font-mono text-xs text-verdant-sage">
                  {address?.slice(0, 8)}...{address?.slice(-4)}
                </p>
              )}
              <p
                className={cn(
                  "mt-1 font-semibold text-verdant-sats",
                  isCollapsed && "text-center text-xs"
                )}
              >
                {isCollapsed ? (
                  <Wallet className="mx-auto h-4 w-4" />
                ) : (
                  balance
                )}
              </p>
            </div>
          ) : (
            <Button
              onClick={connect}
              className={cn(
                "w-full bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon",
                isCollapsed && "p-2"
              )}
            >
              {isCollapsed ? <Wallet className="h-4 w-4" /> : "Connect Wallet"}
            </Button>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-3">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeMobile}
                className={cn(
                  "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 font-medium transition-all",
                  isCollapsed && "justify-center px-2",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-verdant-sage hover:bg-sidebar-accent/50 hover:text-verdant-paper"
                )}
              >
                {/* Active Indicator */}
                <span
                  className={cn(
                    "absolute left-0 top-0 h-full w-[3px] rounded-r-full bg-verdant-sats transition-transform",
                    isActive ? "scale-y-100" : "scale-y-0 group-hover:scale-y-100"
                  )}
                />
                <item.icon className={cn("h-5 w-5 shrink-0", isActive && "text-verdant-sats")} />
                {!isCollapsed && <span>{item.label}</span>}
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="border-t border-sidebar-border p-4">
          <div
            className={cn(
              "rounded-lg border border-info/30 bg-info/20 px-3 py-2 text-center text-xs font-semibold text-info",
              isCollapsed && "px-1 text-[10px]"
            )}
          >
            {isCollapsed ? "Test" : "Stacks Testnet"}
          </div>
        </div>
      </aside>
    </>
  )
}
