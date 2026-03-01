"use client"

import { useSidebar } from "@/hooks/use-sidebar"
import { Menu } from "lucide-react"

export function MobileMenuButton() {
  const { toggleMobile } = useSidebar()

  return (
    <button
      onClick={toggleMobile}
      className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon shadow-xl shadow-verdant-sats/40 transition-transform hover:scale-105 lg:hidden"
    >
      <Menu className="h-6 w-6" />
    </button>
  )
}
