"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"

const stats = [
  { value: "1,240", label: "kg Recycled" },
  { value: "0.52", label: "BTC Distributed" },
  { value: "3.2t", label: "CO₂ Offset" },
]

export function HeroSection() {
  return (
    <section className="relative flex min-h-screen items-center justify-center overflow-hidden">
      {/* Background Image */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRagMY-nkc3oSd206H3sDO5rxcT8F4Ztq4ZQg&s')",
        }}
      />

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-verdant-carbon/70 via-verdant-soil/50 to-verdant-moss/40" />

      {/* Content */}
      <div className="relative z-10 mx-auto max-w-4xl px-6 py-32 text-center animate-fade-in-up">
        <h1 className="mb-6 font-display text-5xl font-extrabold leading-tight tracking-tight sm:text-6xl md:text-7xl">
          <span className="bg-gradient-to-r from-verdant-paper via-verdant-gold to-verdant-sats bg-clip-text text-transparent">
            Turn Trash into Bitcoin
          </span>
        </h1>
        <p className="mx-auto mb-10 max-w-2xl text-lg text-verdant-sage sm:text-xl md:text-2xl text-balance">
          Proof that Bitcoin heals the planet, not hurts it. Earn sBTC for
          verified recycling. Zero greenwashing.
        </p>
        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link href="/dashboard">
            <Button
              size="lg"
              className="relative overflow-hidden bg-gradient-to-r from-verdant-sats to-verdant-gold px-8 py-6 text-lg font-semibold text-verdant-carbon shadow-xl shadow-verdant-sats/30 transition-all hover:scale-[1.02] hover:shadow-verdant-sats/40"
            >
              Start Earning sBTC
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button
              variant="outline"
              size="lg"
              className="border-2 border-verdant-sprout px-8 py-6 text-lg font-semibold text-verdant-paper transition-all hover:bg-verdant-sprout hover:text-verdant-paper bg-transparent"
            >
              View Dashboard
            </Button>
          </Link>
        </div>
      </div>

      {/* Floating Stats */}
      <div className="absolute bottom-12 left-1/2 z-10 flex -translate-x-1/2 flex-wrap justify-center gap-4 px-6 md:gap-6">
        {stats.map((stat, index) => (
          <div
            key={stat.label}
            className={`rounded-2xl border border-verdant-sage/20 bg-verdant-moss/40 p-4 text-center backdrop-blur-xl md:min-w-[160px] md:p-6 ${
              index === 0
                ? "animate-float"
                : index === 1
                  ? "animate-float-delay-1"
                  : "animate-float-delay-2"
            }`}
          >
            <span className="block font-mono text-2xl font-bold text-verdant-sats md:text-3xl">
              {stat.value}
            </span>
            <span className="mt-1 text-sm text-verdant-sage">{stat.label}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
