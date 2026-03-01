import { Camera, Cpu, Bitcoin } from "lucide-react"

const steps = [
  {
    icon: Camera,
    title: "Snap Photo",
    description: "Take a photo of your recyclables - plastic, paper, metal, or organic waste.",
    step: "01",
  },
  {
    icon: Cpu,
    title: "AI Verifies",
    description: "Our AI classifies your waste and validators approve the submission.",
    step: "02",
  },
  {
    icon: Bitcoin,
    title: "Earn sBTC",
    description: "Get rewarded with sBTC tokens and carbon credits for your contribution.",
    step: "03",
  },
]

export function HowItWorksSection() {
  return (
    <section className="relative bg-verdant-carbon py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mb-16 text-center">
          <h2 className="mb-4 font-display text-4xl font-bold text-verdant-paper md:text-5xl">
            How It Works
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-verdant-sage">
            Three simple steps to turn your recyclables into Bitcoin rewards
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-3">
          {steps.map((step, index) => (
            <div
              key={step.title}
              className="group relative overflow-hidden rounded-2xl border border-verdant-sage/20 bg-gradient-to-br from-verdant-moss/20 to-transparent p-8 backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:border-verdant-sats/30 hover:shadow-xl hover:shadow-verdant-sats/10"
            >
              {/* Step Number */}
              <span className="absolute right-6 top-6 font-mono text-5xl font-bold text-verdant-moss/30">
                {step.step}
              </span>

              {/* Icon */}
              <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-verdant-sats/20 to-verdant-gold/10 text-verdant-sats transition-transform duration-300 group-hover:scale-110">
                <step.icon className="h-8 w-8" />
              </div>

              <h3 className="mb-3 font-display text-xl font-bold text-verdant-paper">
                {step.title}
              </h3>
              <p className="text-verdant-sage">{step.description}</p>

              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div className="absolute -right-4 top-1/2 hidden h-px w-8 bg-gradient-to-r from-verdant-sage/30 to-transparent md:block" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
