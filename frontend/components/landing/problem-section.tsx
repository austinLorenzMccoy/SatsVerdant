import { X, Check } from "lucide-react"

const traditional = [
  "Weak financial incentives",
  "No verification of claims",
  "Opaque processes",
  "Easy to greenwash",
]

const satsverdant = [
  "Bitcoin-powered rewards",
  "AI + validator verification",
  "Immutable proof on-chain",
  "Transparent impact metrics",
]

export function ProblemSection() {
  return (
    <section className="relative bg-gradient-to-br from-verdant-soil via-verdant-carbon to-verdant-soil py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mb-16 text-center">
          <h2 className="mb-4 font-display text-4xl font-bold text-verdant-paper md:text-5xl">
            The Problem We Solve
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-verdant-sage">
            Traditional recycling lacks accountability. We bring Bitcoin&apos;s
            transparency to environmental action.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2">
          {/* Traditional */}
          <div className="rounded-2xl border border-error/20 bg-error/5 p-8">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-error/20">
                <X className="h-6 w-6 text-error" />
              </div>
              <h3 className="font-display text-2xl font-bold text-verdant-paper">
                Traditional Recycling
              </h3>
            </div>
            <ul className="space-y-4">
              {traditional.map((item) => (
                <li key={item} className="flex items-center gap-3 text-verdant-sage">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-error/20 text-error">
                    <X className="h-4 w-4" />
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* SatsVerdant */}
          <div className="rounded-2xl border border-success/20 bg-success/5 p-8">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-success/20">
                <Check className="h-6 w-6 text-success" />
              </div>
              <h3 className="font-display text-2xl font-bold text-verdant-paper">
                SatsVerdant
              </h3>
            </div>
            <ul className="space-y-4">
              {satsverdant.map((item) => (
                <li key={item} className="flex items-center gap-3 text-verdant-sage">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-success/20 text-success">
                    <Check className="h-4 w-4" />
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  )
}
