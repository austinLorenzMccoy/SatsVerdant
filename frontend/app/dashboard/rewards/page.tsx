"use client"

import { useState } from "react"
import Image from "next/image"
import { Gift, ExternalLink, CheckCircle2, Clock, Bitcoin } from "lucide-react"
import { Button } from "@/components/ui/button"
import { StatCard } from "@/components/dashboard/stat-card"
import { cn } from "@/lib/utils"

interface ClaimableReward {
  id: string
  image: string
  title: string
  tokens: number
  sbtcValue: string
  date: string
}

interface ClaimedReward {
  id: string
  tokens: number
  sbtcValue: string
  date: string
  txHash: string
}

const claimableRewards: ClaimableReward[] = [
  {
    id: "1",
    image: "https://images.unsplash.com/photo-1604187351574-c75ca79f5807?w=400",
    title: "Plastic Bottles",
    tokens: 50,
    sbtcValue: "0.0005",
    date: "Jan 24, 2026",
  },
  {
    id: "2",
    image: "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=400",
    title: "Cardboard Boxes",
    tokens: 120,
    sbtcValue: "0.0012",
    date: "Jan 23, 2026",
  },
]

const claimedHistory: ClaimedReward[] = [
  {
    id: "3",
    tokens: 80,
    sbtcValue: "0.0008",
    date: "Jan 20, 2026",
    txHash: "0x1234...5678",
  },
  {
    id: "4",
    tokens: 65,
    sbtcValue: "0.00065",
    date: "Jan 18, 2026",
    txHash: "0x8765...4321",
  },
  {
    id: "5",
    tokens: 100,
    sbtcValue: "0.001",
    date: "Jan 15, 2026",
    txHash: "0xabcd...efgh",
  },
]

export default function RewardsPage() {
  const [claimingId, setClaimingId] = useState<string | null>(null)
  const [claimedIds, setClaimedIds] = useState<string[]>([])

  const totalClaimable = claimableRewards
    .filter((r) => !claimedIds.includes(r.id))
    .reduce((acc, r) => acc + r.tokens, 0)

  const handleClaim = (id: string) => {
    setClaimingId(id)
    setTimeout(() => {
      setClaimedIds((prev) => [...prev, id])
      setClaimingId(null)
    }, 2000)
  }

  const handleClaimAll = () => {
    const unclaimed = claimableRewards.filter((r) => !claimedIds.includes(r.id))
    if (unclaimed.length === 0) return
    
    setClaimingId("all")
    setTimeout(() => {
      setClaimedIds((prev) => [...prev, ...unclaimed.map((r) => r.id)])
      setClaimingId(null)
    }, 2500)
  }

  const unclaimedRewards = claimableRewards.filter((r) => !claimedIds.includes(r.id))

  return (
    <div className="space-y-8">
      {/* Stats */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Total Earned"
          value="0.0042 sBTC"
          change="Lifetime"
          icon={Bitcoin}
        />
        <StatCard
          label="Claimable"
          value={`${totalClaimable} tokens`}
          change={`${unclaimedRewards.length} rewards`}
          icon={Gift}
        />
        <StatCard
          label="Avg per Submission"
          value="~85 tokens"
          change="Based on history"
          icon={Clock}
        />
      </div>

      {/* Claimable Rewards */}
      <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6">
        <div className="mb-6 flex items-center justify-between border-b border-verdant-sage/10 pb-4">
          <div>
            <h2 className="font-display text-xl font-bold text-verdant-paper">
              Claimable Rewards
            </h2>
            <p className="text-sm text-verdant-sage">
              Claim your earned sBTC rewards
            </p>
          </div>
          {unclaimedRewards.length > 1 && (
            <Button
              onClick={handleClaimAll}
              disabled={claimingId !== null}
              className="gap-2 bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon disabled:opacity-50"
            >
              {claimingId === "all" ? (
                <>Claiming...</>
              ) : (
                <>Claim All ({unclaimedRewards.length})</>
              )}
            </Button>
          )}
        </div>

        {unclaimedRewards.length === 0 ? (
          <div className="flex flex-col items-center gap-4 py-12 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-verdant-sage/10">
              <Gift className="h-10 w-10 text-verdant-sage/50" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-verdant-paper">
                No Rewards Available
              </h3>
              <p className="mt-1 text-verdant-sage">
                Submit and get your waste verified to earn rewards
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {unclaimedRewards.map((reward) => {
              const isClaiming = claimingId === reward.id || claimingId === "all"
              return (
                <div
                  key={reward.id}
                  className="flex flex-col items-center gap-4 rounded-xl border border-verdant-sage/20 bg-verdant-carbon/50 p-4 sm:flex-row"
                >
                  <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-lg">
                    <Image
                      src={reward.image || "/placeholder.svg"}
                      alt={reward.title}
                      fill
                      className="object-cover"
                    />
                  </div>
                  <div className="flex-1 text-center sm:text-left">
                    <p className="font-semibold text-verdant-paper">{reward.title}</p>
                    <p className="text-sm text-verdant-sage">{reward.date}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-center sm:text-right">
                      <p className="font-mono text-lg font-bold text-verdant-sats">
                        {reward.tokens} tokens
                      </p>
                      <p className="text-xs text-verdant-sage">{reward.sbtcValue} sBTC</p>
                    </div>
                    <Button
                      onClick={() => handleClaim(reward.id)}
                      disabled={isClaiming}
                      size="sm"
                      className={cn(
                        "min-w-[80px] bg-verdant-sprout text-verdant-paper disabled:opacity-50",
                        isClaiming && "animate-pulse"
                      )}
                    >
                      {isClaiming ? "..." : "Claim"}
                    </Button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Claimed History */}
      <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6">
        <div className="mb-6 border-b border-verdant-sage/10 pb-4">
          <h2 className="font-display text-xl font-bold text-verdant-paper">
            Claim History
          </h2>
          <p className="text-sm text-verdant-sage">
            Your previously claimed rewards
          </p>
        </div>

        <div className="space-y-3">
          {claimedHistory.map((item) => (
            <div
              key={item.id}
              className="flex items-center justify-between rounded-xl border border-verdant-sage/10 bg-verdant-carbon/30 p-4"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-success/20">
                  <CheckCircle2 className="h-5 w-5 text-success" />
                </div>
                <div>
                  <p className="font-medium text-verdant-paper">
                    +{item.tokens} tokens
                  </p>
                  <p className="text-sm text-verdant-sage">{item.date}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <p className="font-mono text-sm text-verdant-gold">
                  {item.sbtcValue} sBTC
                </p>
                <a
                  href="#"
                  className="flex items-center gap-1 text-sm text-verdant-sats hover:underline"
                >
                  {item.txHash}
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
