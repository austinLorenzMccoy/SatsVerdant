"use client"

import { useState } from "react"
import Image from "next/image"
import { ShieldCheck, CheckCircle2, XCircle, Flag, MapPin, User, Cpu, Coins } from "lucide-react"
import { Button } from "@/components/ui/button"
import { StatCard } from "@/components/dashboard/stat-card"
import { cn } from "@/lib/utils"

interface ValidationItem {
  id: string
  image: string
  aiType: string
  aiConfidence: number
  userReputation: number
  location: string
  submittedAt: string
}

const validationQueue: ValidationItem[] = [
  {
    id: "1",
    image: "https://images.unsplash.com/photo-1604187351574-c75ca79f5807?w=400",
    aiType: "Plastic",
    aiConfidence: 92,
    userReputation: 4.8,
    location: "San Francisco, CA",
    submittedAt: "5 min ago",
  },
  {
    id: "2",
    image: "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=400",
    aiType: "Paper",
    aiConfidence: 88,
    userReputation: 4.2,
    location: "Austin, TX",
    submittedAt: "12 min ago",
  },
  {
    id: "3",
    image: "https://images.unsplash.com/photo-1611284446314-60a58ac0deb9?w=400",
    aiType: "Metal",
    aiConfidence: 95,
    userReputation: 5.0,
    location: "Seattle, WA",
    submittedAt: "18 min ago",
  },
]

export default function ValidatePage() {
  const [isValidator, setIsValidator] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ValidationItem | null>(null)
  const [processedIds, setProcessedIds] = useState<string[]>([])

  const handleAction = (id: string, action: "approve" | "reject" | "flag") => {
    setProcessedIds((prev) => [...prev, id])
    setSelectedItem(null)
  }

  const pendingItems = validationQueue.filter((item) => !processedIds.includes(item.id))

  if (!isValidator) {
    return (
      <div className="mx-auto max-w-2xl">
        <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6 lg:p-8">
          <div className="mb-6 border-b border-verdant-sage/10 pb-4">
            <h2 className="font-display text-xl font-bold text-verdant-paper">
              Validation Queue
            </h2>
            <p className="text-sm text-verdant-sage">
              Review and approve pending submissions
            </p>
          </div>

          <div className="flex flex-col items-center gap-6 py-12 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-verdant-sage/10">
              <ShieldCheck className="h-10 w-10 text-verdant-sage/50" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-verdant-paper">
                Validator Access Required
              </h3>
              <p className="mt-2 max-w-sm text-verdant-sage">
                Stake STX to become a validator and earn fees for verifying
                recycling submissions
              </p>
            </div>
            <Button
              onClick={() => setIsValidator(true)}
              className="mt-4 gap-2 bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon"
            >
              <Coins className="h-4 w-4" />
              Stake STX to Become Validator
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Validator Stats */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Validations" value="156" change="Completed" icon={CheckCircle2} />
        <StatCard label="Accuracy" value="98.2%" change="Rate" icon={Cpu} />
        <StatCard label="STX Staked" value="1,000" change="Locked" icon={Coins} />
        <StatCard label="Reputation" value="4.9/5" change="Score" icon={User} />
      </div>

      {/* Validation Queue */}
      <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6">
        <div className="mb-6 border-b border-verdant-sage/10 pb-4">
          <h2 className="font-display text-xl font-bold text-verdant-paper">
            Pending Validations
          </h2>
          <p className="text-sm text-verdant-sage">
            {pendingItems.length} submissions awaiting review
          </p>
        </div>

        {pendingItems.length === 0 ? (
          <div className="flex flex-col items-center gap-4 py-12 text-center">
            <CheckCircle2 className="h-12 w-12 text-success" />
            <p className="text-verdant-sage">All caught up! No pending validations.</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {pendingItems.map((item) => (
              <div
                key={item.id}
                onClick={() => setSelectedItem(item)}
                className={cn(
                  "cursor-pointer rounded-xl border border-verdant-sage/20 bg-verdant-carbon/50 p-4 transition-all hover:border-verdant-sats/30 hover:shadow-lg",
                  selectedItem?.id === item.id && "border-verdant-sats ring-2 ring-verdant-sats/30"
                )}
              >
                <div className="relative mb-4 aspect-video overflow-hidden rounded-lg">
                  <Image src={item.image || "/placeholder.svg"} alt="Submission" fill className="object-cover" />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="rounded-md bg-info/20 px-2 py-1 text-xs font-semibold text-info">
                      {item.aiType}
                    </span>
                    <span className="font-mono text-sm text-verdant-sats">
                      {item.aiConfidence}% conf.
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-verdant-sage">
                    <MapPin className="h-3 w-3" />
                    {item.location}
                  </div>
                  <div className="flex items-center justify-between text-xs text-verdant-sage">
                    <span>Rep: {item.userReputation}/5</span>
                    <span>{item.submittedAt}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Action Buttons */}
        {selectedItem && (
          <div className="mt-6 flex flex-wrap justify-center gap-4 border-t border-verdant-sage/10 pt-6">
            <Button
              onClick={() => handleAction(selectedItem.id, "approve")}
              className="gap-2 bg-success text-verdant-carbon hover:bg-success/90"
            >
              <CheckCircle2 className="h-4 w-4" />
              Approve
            </Button>
            <Button
              onClick={() => handleAction(selectedItem.id, "reject")}
              className="gap-2 bg-error text-verdant-paper hover:bg-error/90"
            >
              <XCircle className="h-4 w-4" />
              Reject
            </Button>
            <Button
              onClick={() => handleAction(selectedItem.id, "flag")}
              variant="outline"
              className="gap-2 border-warning text-warning hover:bg-warning/10"
            >
              <Flag className="h-4 w-4" />
              Flag for Review
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
