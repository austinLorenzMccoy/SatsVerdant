import Link from "next/link"
import { Bitcoin, Recycle, Leaf, Plus, Gift } from "lucide-react"
import { Button } from "@/components/ui/button"
import { StatCard } from "@/components/dashboard/stat-card"
import { SubmissionCard } from "@/components/dashboard/submission-card"

const submissions = [
  {
    image: "https://images.unsplash.com/photo-1604187351574-c75ca79f5807?w=400",
    title: "Plastic Bottles",
    wasteType: "plastic" as const,
    status: "minted" as const,
    weight: "0.5 kg",
    time: "2 days ago",
    reward: "50 tokens",
    rewardLabel: "0.0005 sBTC",
  },
  {
    image: "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=400",
    title: "Cardboard Boxes",
    wasteType: "paper" as const,
    status: "approved" as const,
    weight: "1.2 kg",
    time: "3 days ago",
    reward: "120 tokens",
    rewardLabel: "Pending mint",
  },
  {
    image: "https://images.unsplash.com/photo-1611284446314-60a58ac0deb9?w=400",
    title: "Aluminum Cans",
    wasteType: "metal" as const,
    status: "pending" as const,
    weight: "0.8 kg",
    time: "5 days ago",
    reward: "Validating...",
    rewardLabel: "Est. 80 tokens",
  },
]

export default function DashboardOverviewPage() {
  return (
    <div className="space-y-8">
      {/* Metrics Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Total Earnings"
          value="0.0042 sBTC"
          change="+12.5% this week"
          icon={Bitcoin}
        />
        <StatCard
          label="Waste Recycled"
          value="12.5 kg"
          change="+3.2 kg this week"
          icon={Recycle}
        />
        <StatCard
          label="Carbon Offset"
          value="3.2 kg"
          change="CO₂ equivalent"
          icon={Leaf}
        />
      </div>

      {/* Quick Actions */}
      <div className="flex flex-wrap gap-4">
        <Link href="/dashboard/submit">
          <Button className="gap-2 bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon">
            <Plus className="h-4 w-4" />
            Submit New Waste
          </Button>
        </Link>
        <Link href="/dashboard/rewards">
          <Button variant="outline" className="gap-2 border-verdant-sprout text-verdant-paper hover:bg-verdant-sprout bg-transparent">
            <Gift className="h-4 w-4" />
            Claim Rewards
          </Button>
        </Link>
      </div>

      {/* Recent Submissions */}
      <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6">
        <div className="mb-6 border-b border-verdant-sage/10 pb-4">
          <h2 className="font-display text-xl font-bold text-verdant-paper">
            Recent Submissions
          </h2>
          <p className="text-sm text-verdant-sage">Your latest waste submissions</p>
        </div>
        <div className="space-y-4">
          {submissions.map((submission) => (
            <SubmissionCard key={submission.title} {...submission} />
          ))}
        </div>
      </div>
    </div>
  )
}
