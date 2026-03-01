"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { useSidebar } from "@/hooks/use-sidebar"
import { useWallet } from "@/hooks/use-wallet"
import { Button } from "@/components/ui/button"
import { Wallet, LogOut, Loader2, AlertCircle } from "lucide-react"
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
  const { isConnected, address, walletType, isLoading, error, connect, disconnect, clearError } = useWallet()
  const title = pageTitles[pathname] || "Dashboard"

  const handleConnect = async () => {
    if (error) clearError()
    await connect()
  }

  return (
    <header
      className={cn(
        "sticky top-0 z-10 border-b border-verdant-sage/10 bg-verdant-carbon/60 px-6 py-4 backdrop-blur-xl lg:px-8"
      )}
      data-collapsed={isCollapsed}
    >
      <div className="flex items-center justify-between">
        <div>
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
        </div>

        {/* Wallet Connection */}
        <div className="flex items-center gap-3">
          {!isConnected ? (
            <Button
              onClick={handleConnect}
              disabled={isLoading}
              className="gap-2 bg-verdant-sats text-verdant-carbon hover:bg-verdant-gold"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Wallet className="h-4 w-4" />
                  Connect Wallet
                </>
              )}
            </Button>
          ) : (
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-sm font-medium text-verdant-paper">
                  {address ? `${address.slice(0, 6)}...${address.slice(-4)}` : 'Connected'}
                </div>
                <div className="text-xs text-verdant-sage capitalize">
                  {walletType || 'Wallet'}
                </div>
              </div>
              <Button
                onClick={disconnect}
                variant="outline"
                size="sm"
                className="gap-2 border-verdant-sprout text-verdant-sage hover:bg-verdant-sprout hover:text-verdant-paper"
              >
                <LogOut className="h-4 w-4" />
                Disconnect
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-3 flex items-center gap-2 rounded-md bg-red-900/20 border border-red-800/30 px-3 py-2">
          <AlertCircle className="h-4 w-4 text-red-400" />
          <p className="text-sm text-red-300">{error}</p>
          <Button
            onClick={clearError}
            variant="ghost"
            size="sm"
            className="ml-auto h-6 w-6 p-0 text-red-400 hover:text-red-300"
          >
            ×
          </Button>
        </div>
      )}
    </header>
  )
}
