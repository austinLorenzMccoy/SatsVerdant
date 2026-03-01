"use client"

import { useEffect, useState } from "react"
import { Recycle, TrendingUp } from "lucide-react"

const recentSubmissions = [
  { type: "Plastic", amount: "0.5 kg", reward: "50 tokens", time: "2 min ago" },
  { type: "Paper", amount: "1.2 kg", reward: "120 tokens", time: "5 min ago" },
  { type: "Metal", amount: "0.3 kg", reward: "45 tokens", time: "8 min ago" },
  { type: "Organic", amount: "2.1 kg", reward: "84 tokens", time: "12 min ago" },
  { type: "Plastic", amount: "0.8 kg", reward: "80 tokens", time: "15 min ago" },
]

const testimonials = [
  {
    quote: "Finally, recycling that actually pays. The sBTC rewards are a game-changer.",
    author: "Validator #47",
    role: "Community Validator",
  },
  {
    quote: "I've verified over 500 submissions. The AI makes validation fast and accurate.",
    author: "Validator #12",
    role: "Top Validator",
  },
]

export function SocialProofSection() {
  const [recycledToday, setRecycledToday] = useState(847)

  useEffect(() => {
    const interval = setInterval(() => {
      setRecycledToday((prev) => prev + Math.floor(Math.random() * 3))
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <section className="relative bg-verdant-carbon py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-6">
        {/* Real-time Counter */}
        <div className="mb-16 flex flex-col items-center justify-center gap-4 rounded-2xl border border-verdant-sage/20 bg-gradient-to-r from-verdant-moss/20 via-verdant-carbon to-verdant-moss/20 p-8 text-center">
          <div className="flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-verdant-sats" />
            <span className="font-mono text-4xl font-bold text-verdant-sats md:text-5xl">
              {recycledToday.toLocaleString()} kg
            </span>
          </div>
          <p className="text-lg text-verdant-sage">recycled today globally</p>
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* Live Feed */}
          <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6">
            <div className="mb-6 flex items-center gap-3">
              <Recycle className="h-6 w-6 text-verdant-sats" />
              <h3 className="font-display text-xl font-bold text-verdant-paper">
                Live Submissions
              </h3>
              <span className="ml-auto flex items-center gap-2 text-sm text-verdant-sage">
                <span className="h-2 w-2 animate-pulse rounded-full bg-success" />
                Live
              </span>
            </div>
            <div className="space-y-3">
              {recentSubmissions.map((submission, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-xl border border-verdant-sage/10 bg-verdant-carbon/50 p-4 transition-colors hover:border-verdant-sage/20"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`rounded-lg px-2 py-1 text-xs font-semibold ${
                        submission.type === "Plastic"
                          ? "bg-info/20 text-info"
                          : submission.type === "Paper"
                            ? "bg-verdant-gold/20 text-verdant-gold"
                            : submission.type === "Metal"
                              ? "bg-verdant-sage/20 text-verdant-sage"
                              : "bg-success/20 text-success"
                      }`}
                    >
                      {submission.type}
                    </span>
                    <span className="text-verdant-paper">{submission.amount}</span>
                  </div>
                  <div className="text-right">
                    <span className="block font-mono text-sm text-verdant-sats">
                      +{submission.reward}
                    </span>
                    <span className="text-xs text-verdant-sage">{submission.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Testimonials */}
          <div className="space-y-6">
            <h3 className="font-display text-xl font-bold text-verdant-paper">
              From Our Validators
            </h3>
            {testimonials.map((testimonial, index) => (
              <div
                key={index}
                className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6"
              >
                <p className="mb-4 text-lg text-verdant-paper">
                  &ldquo;{testimonial.quote}&rdquo;
                </p>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-verdant-sats/20 font-mono text-sm font-bold text-verdant-sats">
                    V
                  </div>
                  <div>
                    <p className="font-semibold text-verdant-paper">{testimonial.author}</p>
                    <p className="text-sm text-verdant-sage">{testimonial.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
