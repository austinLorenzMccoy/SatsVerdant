"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { request, AddressPurpose } from "sats-connect"

interface WalletInfo {
  address: string
  publicKey: string
  walletType: string
}

interface WalletContextType {
  isConnected: boolean
  address: string | null
  publicKey: string | null
  walletType: string | null
  balance: string
  isLoading: boolean
  error: string | null
  connect: () => Promise<void>
  disconnect: () => void
  clearError: () => void
}

const WalletContext = createContext<WalletContextType | undefined>(undefined)

export function WalletProvider({ children }: { children: ReactNode }) {
  const [isConnected, setIsConnected] = useState(false)
  const [address, setAddress] = useState<string | null>(null)
  const [publicKey, setPublicKey] = useState<string | null>(null)
  const [walletType, setWalletType] = useState<string | null>(null)
  const [balance, setBalance] = useState("0.0000 sBTC")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Check for existing connection on mount
  useEffect(() => {
    const savedAddress = localStorage.getItem('walletAddress')
    const savedWalletType = localStorage.getItem('walletType')
    
    if (savedAddress && savedWalletType) {
      setAddress(savedAddress)
      setWalletType(savedWalletType)
      setIsConnected(true)
      // In a real app, you'd fetch the actual balance here
      setBalance("0.0000 sBTC")
    }
  }, [])

  const connect = async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Request wallet connection
      const response: any = await request('wallet_connect', {
        message: 'Connect to SatsVerdant for waste recycling rewards'
      } as any)

      console.log('Wallet response:', response)

      // Handle error response
      if (response?.status === 'error') {
        const errorMsg = response?.error?.message || 'Unknown error'
        const errorCode = response?.error?.code
        
        const error: any = new Error(errorMsg)
        error.code = errorCode
        throw error
      }

      // Handle success response
      if (response?.status === 'success' && response?.result?.addresses) {
        const addresses = response.result.addresses
        
        // Find Stacks address
        const stacksAddress = addresses.find((addr: any) => 
          addr.purpose === AddressPurpose.Stacks || 
          addr.addressType === 'stacks'
        ) || addresses[0]

        if (stacksAddress?.address) {
          const walletInfo: WalletInfo = {
            address: stacksAddress.address,
            publicKey: stacksAddress.publicKey || '',
            walletType: response.result.walletType || 'unknown'
          }

          // Update state
          setAddress(walletInfo.address)
          setPublicKey(walletInfo.publicKey)
          setWalletType(walletInfo.walletType)
          setIsConnected(true)
          
          // Save to localStorage
          localStorage.setItem('walletAddress', walletInfo.address)
          localStorage.setItem('walletType', walletInfo.walletType)
          
          // In a real app, you'd fetch the actual balance from the blockchain
          setBalance("0.0000 sBTC")
          
          return
        }
      }

      throw new Error('No Stacks addresses found in wallet')
    } catch (err: any) {
      console.error('Connection error:', err)
      
      // Handle specific errors
      if (err.code === -32002) {
        setError('Connection cancelled. Please approve the request in your wallet.')
      } else if (err.message.includes('not installed')) {
        setError('Please install Xverse or Leather wallet extension.')
      } else {
        setError(err.message || 'Failed to connect wallet')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const disconnect = () => {
    setIsConnected(false)
    setAddress(null)
    setPublicKey(null)
    setWalletType(null)
    setBalance("0.0000 sBTC")
    setError(null)
    
    // Clear localStorage
    localStorage.removeItem('walletAddress')
    localStorage.removeItem('walletType')
  }

  const clearError = () => {
    setError(null)
  }

  return (
    <WalletContext.Provider value={{ 
      isConnected, 
      address, 
      publicKey,
      walletType,
      balance, 
      isLoading,
      error,
      connect, 
      disconnect,
      clearError
    }}>
      {children}
    </WalletContext.Provider>
  )
}

export function useWallet() {
  const context = useContext(WalletContext)
  if (!context) {
    throw new Error("useWallet must be used within a WalletProvider")
  }
  return context
}
