"use client"

import { useState } from "react"
import { useWallet } from "@/hooks/use-wallet"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Wallet, Smartphone, Monitor, AlertCircle, CheckCircle, ExternalLink } from "lucide-react"

interface WalletConnectModalProps {
  isOpen: boolean
  onClose: () => void
}

export function WalletConnectModal({ isOpen, onClose }: WalletConnectModalProps) {
  const { connect, isLoading, error } = useWallet()
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null)

  const handleConnect = async (walletType: string) => {
    setSelectedWallet(walletType)
    await connect()
    if (!error) {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="mx-4 max-w-md w-full border-verdant-sage/20 bg-verdant-carbon">
        <CardHeader className="text-center">
          <CardTitle className="font-display text-xl text-verdant-paper">
            Connect Your Wallet
          </CardTitle>
          <CardDescription className="text-verdant-sage">
            Choose a wallet to connect to SatsVerdant and start earning sBTC for recycling
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Wallet Options */}
          <div className="space-y-3">
            <Button
              onClick={() => handleConnect('xverse')}
              disabled={isLoading}
              className="w-full gap-3 justify-start border-verdant-sage/20 bg-verdant-moss/20 hover:bg-verdant-moss/30 text-verdant-paper"
            >
              <Smartphone className="h-5 w-5 text-orange-400" />
              <div className="text-left">
                <div className="font-medium">Xverse Wallet</div>
                <div className="text-xs text-verdant-sage">Popular mobile and desktop wallet</div>
              </div>
              {selectedWallet === 'xverse' && isLoading && (
                <div className="ml-auto">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-verdant-sats border-t-transparent" />
                </div>
              )}
            </Button>

            <Button
              onClick={() => handleConnect('leather')}
              disabled={isLoading}
              className="w-full gap-3 justify-start border-verdant-sage/20 bg-verdant-moss/20 hover:bg-verdant-moss/30 text-verdant-paper"
            >
              <Monitor className="h-5 w-5 text-blue-400" />
              <div className="text-left">
                <div className="font-medium">Leather Wallet</div>
                <div className="text-xs text-verdant-sage">Secure browser extension wallet</div>
              </div>
              {selectedWallet === 'leather' && isLoading && (
                <div className="ml-auto">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-verdant-sats border-t-transparent" />
                </div>
              )}
            </Button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 rounded-md bg-red-900/20 border border-red-800/30 p-3">
              <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          {/* Help Section */}
          <div className="rounded-md bg-verdant-moss/10 border border-verdant-sage/20 p-4">
            <h4 className="font-medium text-verdant-paper mb-2">Don't have a wallet?</h4>
            <div className="space-y-2 text-sm text-verdant-sage">
              <div className="flex items-center justify-between">
                <span>Xverse Wallet:</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-1 text-verdant-sats hover:text-verdant-gold"
                  asChild
                >
                  <a
                    href="https://xverse.app"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Download <ExternalLink className="h-3 w-3" />
                  </a>
                </Button>
              </div>
              <div className="flex items-center justify-between">
                <span>Leather Wallet:</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-1 text-verdant-sats hover:text-verdant-gold"
                  asChild
                >
                  <a
                    href="https://leather.io"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Install <ExternalLink className="h-3 w-3" />
                  </a>
                </Button>
              </div>
            </div>
          </div>

          {/* Close Button */}
          <Button
            onClick={onClose}
            variant="outline"
            className="w-full border-verdant-sage/20 text-verdant-sage hover:bg-verdant-moss/20 hover:text-verdant-paper"
          >
            Cancel
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

export function WalletConnectButton() {
  const { isConnected, address, disconnect } = useWallet()
  const [isModalOpen, setIsModalOpen] = useState(false)

  if (isConnected) {
    return (
      <div className="flex items-center gap-2">
        <div className="text-right">
          <div className="text-sm font-medium text-verdant-paper">
            {address ? `${address.slice(0, 6)}...${address.slice(-4)}` : 'Connected'}
          </div>
          <div className="text-xs text-verdant-sage">Wallet Connected</div>
        </div>
        <Button
          onClick={disconnect}
          variant="outline"
          size="sm"
          className="gap-2 border-verdant-sprout text-verdant-sage hover:bg-verdant-sprout hover:text-verdant-paper"
        >
          Disconnect
        </Button>
      </div>
    )
  }

  return (
    <>
      <Button
        onClick={() => setIsModalOpen(true)}
        className="gap-2 bg-verdant-sats text-verdant-carbon hover:bg-verdant-gold"
      >
        <Wallet className="h-4 w-4" />
        Connect Wallet
      </Button>
      
      <WalletConnectModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  )
}
