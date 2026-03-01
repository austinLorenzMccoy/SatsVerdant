import { Recycle, TreePine, Leaf, Trophy, TrendingUp, Award } from "lucide-react"
import { StatCard } from "@/components/dashboard/stat-card"

const wasteBreakdown = [
  { type: "Plastic", amount: "5.2 kg", percentage: 42, color: "bg-info" },
  { type: "Paper", amount: "3.8 kg", percentage: 30, color: "bg-verdant-gold" },
  { type: "Metal", amount: "2.1 kg", percentage: 17, color: "bg-verdant-sage" },
  { type: "Organic", amount: "1.4 kg", percentage: 11, color: "bg-success" },
]

const achievements = [
  {
    icon: Recycle,
    title: "First Recycle",
    description: "Submitted your first recyclable",
    unlocked: true,
  },
  {
    icon: TreePine,
    title: "Tree Hugger",
    description: "Offset 1kg of CO₂",
    unlocked: true,
  },
  {
    icon: Trophy,
    title: "Eco Warrior",
    description: "Recycle 10kg total",
    unlocked: true,
  },
  {
    icon: Award,
    title: "Green Champion",
    description: "Recycle 50kg total",
    unlocked: false,
  },
]

const timeline = [
  { date: "Jan 24", amount: "0.5 kg", type: "Plastic" },
  { date: "Jan 23", amount: "1.2 kg", type: "Paper" },
  { date: "Jan 21", amount: "0.8 kg", type: "Metal" },
  { date: "Jan 20", amount: "0.3 kg", type: "Organic" },
  { date: "Jan 18", amount: "0.7 kg", type: "Plastic" },
]

export default function ImpactPage() {
  return (
    <div className="space-y-8">
      {/* Personal Impact Stats */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Total Recycled"
          value="12.5 kg"
          change="Waste diverted from landfill"
          icon={Recycle}
        />
        <StatCard
          label="CO₂ Offset"
          value="3.2 kg"
          change="Equivalent to 0.15 trees planted"
          icon={Leaf}
        />
        <StatCard
          label="Submissions"
          value="8"
          change="Verified contributions"
          icon={TrendingUp}
        />
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Waste Breakdown */}
        <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6">
          <div className="mb-6 border-b border-verdant-sage/10 pb-4">
            <h2 className="font-display text-xl font-bold text-verdant-paper">
              Waste Breakdown
            </h2>
            <p className="text-sm text-verdant-sage">By category</p>
          </div>

          <div className="space-y-4">
            {wasteBreakdown.map((item) => (
              <div key={item.type}>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-verdant-paper">{item.type}</span>
                  <span className="font-mono text-verdant-sage">
                    {item.amount} ({item.percentage}%)
                  </span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-verdant-carbon">
                  <div
                    className={`h-full rounded-full ${item.color} transition-all`}
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Visual Impact */}
          <div className="mt-8 rounded-xl border border-verdant-sage/10 bg-verdant-carbon/50 p-6 text-center">
            <div className="mb-4 flex justify-center gap-2">
              {[...Array(Math.round(3.2))].map((_, i) => (
                <TreePine key={i} className="h-8 w-8 text-success" />
              ))}
              <TreePine className="h-8 w-8 text-verdant-sage/30" />
            </div>
            <p className="text-sm text-verdant-sage">
              Your impact equals <span className="font-bold text-success">0.15 trees</span>{" "}
              planted
            </p>
          </div>
        </div>

        {/* Achievements */}
        <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6">
          <div className="mb-6 border-b border-verdant-sage/10 pb-4">
            <h2 className="font-display text-xl font-bold text-verdant-paper">
              Achievements
            </h2>
            <p className="text-sm text-verdant-sage">Your environmental badges</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {achievements.map((achievement) => (
              <div
                key={achievement.title}
                className={`rounded-xl border p-4 text-center transition-all ${
                  achievement.unlocked
                    ? "border-verdant-sats/30 bg-verdant-sats/10"
                    : "border-verdant-sage/10 bg-verdant-carbon/30 opacity-50"
                }`}
              >
                <div
                  className={`mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full ${
                    achievement.unlocked ? "bg-verdant-sats/20" : "bg-verdant-sage/10"
                  }`}
                >
                  <achievement.icon
                    className={`h-6 w-6 ${
                      achievement.unlocked ? "text-verdant-sats" : "text-verdant-sage/50"
                    }`}
                  />
                </div>
                <h4 className="font-semibold text-verdant-paper">{achievement.title}</h4>
                <p className="mt-1 text-xs text-verdant-sage">{achievement.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6">
        <div className="mb-6 border-b border-verdant-sage/10 pb-4">
          <h2 className="font-display text-xl font-bold text-verdant-paper">
            Impact Timeline
          </h2>
          <p className="text-sm text-verdant-sage">
            Your environmental contribution over time
          </p>
        </div>

        <div className="relative">
          {/* Timeline Line */}
          <div className="absolute bottom-0 left-6 top-0 w-px bg-verdant-sage/20" />

          <div className="space-y-6">
            {timeline.map((item, index) => (
              <div key={index} className="relative flex items-center gap-4 pl-12">
                {/* Dot */}
                <div className="absolute left-4 h-4 w-4 rounded-full border-2 border-verdant-sats bg-verdant-carbon" />
                
                <div className="flex flex-1 items-center justify-between rounded-xl border border-verdant-sage/10 bg-verdant-carbon/50 p-4">
                  <div>
                    <p className="font-medium text-verdant-paper">{item.amount}</p>
                    <p className="text-sm text-verdant-sage">{item.type}</p>
                  </div>
                  <span className="font-mono text-sm text-verdant-sage">{item.date}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
