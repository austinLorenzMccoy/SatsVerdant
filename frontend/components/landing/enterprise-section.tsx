import Link from "next/link"
import { Building2, ShieldCheck, BarChart3, FileCheck } from "lucide-react"
import { Button } from "@/components/ui/button"

const features = [
  {
    icon: ShieldCheck,
    title: "Verified Credits",
    description: "Every carbon credit is backed by verified, on-chain proof.",
  },
  {
    icon: BarChart3,
    title: "Real-time Reporting",
    description: "Track your environmental impact with live dashboards.",
  },
  {
    icon: FileCheck,
    title: "Compliance Ready",
    description: "Export-ready reports for ESG and sustainability audits.",
  },
]

export function EnterpriseSection() {
  return (
    <section className="relative bg-gradient-to-br from-verdant-soil via-verdant-moss/20 to-verdant-soil py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          {/* Content */}
          <div>
            <div className="mb-6 flex items-center gap-3">
              <Building2 className="h-8 w-8 text-verdant-gold" />
              <span className="font-mono text-sm font-semibold uppercase tracking-wider text-verdant-gold">
                For Corporations
              </span>
            </div>
            <h2 className="mb-6 font-display text-4xl font-bold text-verdant-paper md:text-5xl text-balance">
              Buy Carbon Credits You Can Actually Prove
            </h2>
            <p className="mb-8 text-lg text-verdant-sage">
              No more greenwashing concerns. Every SatsVerdant carbon credit is
              tied to verified recycling data stored immutably on the blockchain.
            </p>
            <div className="space-y-4">
              {features.map((feature) => (
                <div key={feature.title} className="flex gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-verdant-gold/20">
                    <feature.icon className="h-6 w-6 text-verdant-gold" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-verdant-paper">{feature.title}</h3>
                    <p className="text-verdant-sage">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-10">
              <Link href="/dashboard">
                <Button
                  size="lg"
                  className="bg-verdant-gold px-8 py-6 text-lg font-semibold text-verdant-carbon transition-all hover:bg-verdant-gold/90"
                >
                  Schedule Demo
                </Button>
              </Link>
            </div>
          </div>

          {/* Visual */}
          <div className="relative">
            <div className="aspect-square rounded-3xl border border-verdant-sage/20 bg-gradient-to-br from-verdant-moss/30 to-verdant-carbon p-8">
              <div className="flex h-full flex-col justify-between rounded-2xl border border-verdant-sage/10 bg-verdant-carbon/80 p-6">
                <div>
                  <p className="font-mono text-sm text-verdant-sage">Corporate Dashboard</p>
                  <p className="mt-2 font-display text-2xl font-bold text-verdant-paper">
                    Acme Corp
                  </p>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center justify-between rounded-xl border border-verdant-sage/10 bg-verdant-moss/20 p-4">
                    <span className="text-verdant-sage">Carbon Credits</span>
                    <span className="font-mono text-xl font-bold text-verdant-sats">
                      12,450
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-verdant-sage/10 bg-verdant-moss/20 p-4">
                    <span className="text-verdant-sage">CO₂ Offset</span>
                    <span className="font-mono text-xl font-bold text-success">
                      45.2t
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-verdant-sage/10 bg-verdant-moss/20 p-4">
                    <span className="text-verdant-sage">Verification Rate</span>
                    <span className="font-mono text-xl font-bold text-verdant-gold">
                      99.8%
                    </span>
                  </div>
                </div>
              </div>
            </div>
            {/* Decorative */}
            <div className="absolute -right-4 -top-4 h-24 w-24 rounded-2xl border border-verdant-sats/20 bg-verdant-sats/10" />
            <div className="absolute -bottom-4 -left-4 h-16 w-16 rounded-xl border border-verdant-sprout/20 bg-verdant-sprout/10" />
          </div>
        </div>
      </div>
    </section>
  )
}
