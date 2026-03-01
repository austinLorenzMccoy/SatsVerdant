"use client"

import Link from "next/link"
import { Logo } from "@/components/logo"
import { Button } from "@/components/ui/button"
import { useWallet } from "@/hooks/use-wallet"
import { Wallet, LogOut, Loader2 } from "lucide-react"

export function LandingNav() {
  const { isConnected, address, walletType, isLoading, connect, disconnect } = useWallet()

  const handleWalletAction = async () => {
    if (isConnected) {
      disconnect()
    } else {
      await connect()
    }
  }

  return (
    <nav className="fixed left-0 right-0 top-0 z-50 border-b border-verdant-sage/10 bg-verdant-carbon/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Logo />
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="hidden text-sm font-medium text-verdant-sage transition-colors hover:text-verdant-paper sm:block"
          >
            Dashboard
          </Link>
          
          {isConnected ? (
            <div className="flex items-center gap-3">
              <div className="hidden text-right sm:block">
                <div className="text-sm font-medium text-verdant-paper">
                  {address ? `${address.slice(0, 6)}...${address.slice(-4)}` : 'Connected'}
                </div>
                <div className="text-xs text-verdant-sage capitalize">
                  {walletType || 'Wallet'}
                </div>
              </div>
              <Button
                onClick={handleWalletAction}
                variant="outline"
                size="sm"
                className="gap-2 border-verdant-sprout text-verdant-sage hover:bg-verdant-sprout hover:text-verdant-paper"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Disconnect</span>
              </Button>
            </div>
          ) : (
            <Button
              onClick={handleWalletAction}
              disabled={isLoading}
              className="gap-2 bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon shadow-lg shadow-verdant-sats/30 transition-all hover:scale-[1.02] hover:shadow-verdant-sats/40"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="hidden sm:inline">Connecting...</span>
                </>
              ) : (
                <>
                  <Wallet className="h-4 w-4" />
                  <span>Connect Wallet</span>
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </nav>
  )
}
