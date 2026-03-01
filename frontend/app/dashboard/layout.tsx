import React from "react"
import { SidebarProvider } from "@/hooks/use-sidebar"
import { WalletProvider } from "@/hooks/use-wallet"
import { DashboardSidebar } from "@/components/dashboard/sidebar"
import { DashboardHeader } from "@/components/dashboard/header"
import { MobileMenuButton } from "@/components/dashboard/mobile-menu-button"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <WalletProvider>
      <SidebarProvider>
        <div className="flex min-h-screen bg-gradient-to-b from-verdant-soil to-verdant-carbon">
          <DashboardSidebar />
          <main className="flex-1 transition-[margin] duration-300 lg:ml-[260px] lg:data-[collapsed=true]:ml-[72px]">
            <DashboardHeader />
            <div className="p-6 lg:p-8">{children}</div>
          </main>
          <MobileMenuButton />
        </div>
      </SidebarProvider>
    </WalletProvider>
  )
}
