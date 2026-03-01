"use client"

import { useWallet } from "@/hooks/use-wallet"
import { Button } from "@/components/ui/button"
import { Copy, LogOut, Bell, Globe, Palette, Download, Trash2 } from "lucide-react"
import { useState } from "react"

export default function SettingsPage() {
  const { isConnected, address, disconnect, connect } = useWallet()
  const [copied, setCopied] = useState(false)

  const copyAddress = () => {
    if (address) {
      navigator.clipboard.writeText(address)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      {/* Account Section */}
      <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6">
        <div className="mb-6 border-b border-verdant-sage/10 pb-4">
          <h2 className="font-display text-xl font-bold text-verdant-paper">
            Account Settings
          </h2>
          <p className="text-sm text-verdant-sage">
            Manage your wallet and preferences
          </p>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="mb-4 flex items-center gap-2 font-semibold text-verdant-paper">
              Wallet
            </h3>
            {isConnected ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3 rounded-xl border border-verdant-sprout/30 bg-verdant-sprout/20 p-4">
                  <div className="flex-1">
                    <p className="text-xs text-verdant-sage">Connected Address</p>
                    <p className="mt-1 font-mono text-sm text-verdant-paper">
                      {address}
                    </p>
                  </div>
                  <Button
                    onClick={copyAddress}
                    size="sm"
                    variant="outline"
                    className="gap-2 border-verdant-sage/30 text-verdant-paper hover:bg-verdant-sage/10 bg-transparent"
                  >
                    <Copy className="h-4 w-4" />
                    {copied ? "Copied!" : "Copy"}
                  </Button>
                </div>
                <Button
                  onClick={disconnect}
                  variant="outline"
                  className="gap-2 border-error/30 text-error hover:bg-error/10 bg-transparent"
                >
                  <LogOut className="h-4 w-4" />
                  Disconnect Wallet
                </Button>
              </div>
            ) : (
              <Button
                onClick={connect}
                className="gap-2 bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon"
              >
                Connect Wallet
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Preferences Section */}
      <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6">
        <div className="mb-6 border-b border-verdant-sage/10 pb-4">
          <h2 className="font-display text-xl font-bold text-verdant-paper">
            Preferences
          </h2>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between rounded-xl border border-verdant-sage/10 bg-verdant-carbon/50 p-4">
            <div className="flex items-center gap-3">
              <Bell className="h-5 w-5 text-verdant-sage" />
              <div>
                <p className="font-medium text-verdant-paper">Email Notifications</p>
                <p className="text-sm text-verdant-sage">Receive updates about your submissions</p>
              </div>
            </div>
            <label className="relative inline-flex cursor-pointer items-center">
              <input type="checkbox" className="peer sr-only" defaultChecked />
              <div className="peer h-6 w-11 rounded-full bg-verdant-sage/30 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-verdant-paper after:transition-all peer-checked:bg-verdant-sats peer-checked:after:translate-x-full" />
            </label>
          </div>

          <div className="flex items-center justify-between rounded-xl border border-verdant-sage/10 bg-verdant-carbon/50 p-4">
            <div className="flex items-center gap-3">
              <Globe className="h-5 w-5 text-verdant-sage" />
              <div>
                <p className="font-medium text-verdant-paper">Language</p>
                <p className="text-sm text-verdant-sage">Select your preferred language</p>
              </div>
            </div>
            <select className="rounded-lg border border-verdant-sage/20 bg-verdant-carbon px-3 py-2 text-sm text-verdant-paper focus:border-verdant-sats focus:outline-none">
              <option>English</option>
              <option>Spanish</option>
              <option>French</option>
            </select>
          </div>

          <div className="flex items-center justify-between rounded-xl border border-verdant-sage/10 bg-verdant-carbon/50 p-4">
            <div className="flex items-center gap-3">
              <Palette className="h-5 w-5 text-verdant-sage" />
              <div>
                <p className="font-medium text-verdant-paper">Network</p>
                <p className="text-sm text-verdant-sage">Current network connection</p>
              </div>
            </div>
            <span className="rounded-lg bg-info/20 px-3 py-1 text-sm font-semibold text-info">
              Testnet
            </span>
          </div>
        </div>
      </div>

      {/* Data Section */}
      <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6">
        <div className="mb-6 border-b border-verdant-sage/10 pb-4">
          <h2 className="font-display text-xl font-bold text-verdant-paper">
            Data Management
          </h2>
        </div>

        <div className="space-y-4">
          <Button
            variant="outline"
            className="w-full justify-start gap-3 border-verdant-sage/20 text-verdant-paper hover:bg-verdant-sage/10 bg-transparent"
          >
            <Download className="h-5 w-5" />
            Export Submission History (CSV)
          </Button>

          <Button
            variant="outline"
            className="w-full justify-start gap-3 border-error/30 text-error hover:bg-error/10 bg-transparent"
          >
            <Trash2 className="h-5 w-5" />
            Delete Account
          </Button>
        </div>
      </div>
    </div>
  )
}
