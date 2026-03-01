import Image from "next/image"
import { cn } from "@/lib/utils"

export type WasteType = "plastic" | "paper" | "metal" | "organic"
export type SubmissionStatus = "pending" | "approved" | "minted" | "rejected"

interface SubmissionCardProps {
  image: string
  title: string
  wasteType: WasteType
  status: SubmissionStatus
  weight: string
  time: string
  reward?: string
  rewardLabel?: string
}

const wasteTypeStyles: Record<WasteType, string> = {
  plastic: "bg-info/20 text-info",
  paper: "bg-verdant-gold/20 text-verdant-gold",
  metal: "bg-verdant-sage/20 text-verdant-sage",
  organic: "bg-success/20 text-success",
}

const statusStyles: Record<SubmissionStatus, string> = {
  pending: "bg-warning/20 text-warning",
  approved: "bg-success/20 text-success",
  minted: "bg-verdant-sats/20 text-verdant-sats",
  rejected: "bg-error/20 text-error",
}

export function SubmissionCard({
  image,
  title,
  wasteType,
  status,
  weight,
  time,
  reward,
  rewardLabel,
}: SubmissionCardProps) {
  return (
    <div className="group grid grid-cols-1 items-center gap-4 rounded-xl border border-verdant-sage/20 bg-verdant-moss/15 p-4 transition-all hover:translate-x-1 hover:border-verdant-sats/30 md:grid-cols-[80px_1fr_auto]">
      {/* Image */}
      <div className="relative mx-auto h-20 w-20 overflow-hidden rounded-lg bg-verdant-sage/10 md:mx-0">
        <Image
          src={image || "/placeholder.svg"}
          alt={title}
          fill
          className="object-cover"
        />
      </div>

      {/* Details */}
      <div className="text-center md:text-left">
        <h4 className="font-semibold text-verdant-paper">{title}</h4>
        <div className="mt-2 flex flex-wrap items-center justify-center gap-2 text-sm md:justify-start">
          <span className={cn("rounded-md px-2 py-1 text-xs font-semibold uppercase", wasteTypeStyles[wasteType])}>
            {wasteType}
          </span>
          <span className={cn("rounded-md px-2 py-1 text-xs font-semibold uppercase", statusStyles[status])}>
            {status}
          </span>
          <span className="text-verdant-sage">
            {weight} • {time}
          </span>
        </div>
      </div>

      {/* Reward */}
      <div className="text-center md:text-right">
        {reward && (
          <p
            className={cn(
              "font-mono text-lg font-bold text-verdant-sats",
              status === "pending" && "animate-pulse-glow"
            )}
          >
            {reward}
          </p>
        )}
        {rewardLabel && <p className="text-xs text-verdant-sage">{rewardLabel}</p>}
      </div>
    </div>
  )
}
