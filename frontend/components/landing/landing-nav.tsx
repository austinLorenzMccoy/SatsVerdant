"use client"

import Link from "next/link"
import { Logo } from "@/components/logo"
import { Button } from "@/components/ui/button"

export function LandingNav() {
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
          <Link href="/dashboard">
            <Button className="bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon shadow-lg shadow-verdant-sats/30 transition-all hover:scale-[1.02] hover:shadow-verdant-sats/40">
              Connect Wallet
            </Button>
          </Link>
        </div>
      </div>
    </nav>
  )
}
