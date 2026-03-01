import Link from "next/link"
import { Logo } from "@/components/logo"
import { Github, Twitter, FileText } from "lucide-react"

const links = {
  product: [
    { label: "Dashboard", href: "/dashboard" },
    { label: "Submit Waste", href: "/dashboard/submit" },
    { label: "Become a Validator", href: "/dashboard/validate" },
  ],
  resources: [
    { label: "Documentation", href: "#" },
    { label: "API Reference", href: "#" },
    { label: "Carbon Calculator", href: "#" },
  ],
  legal: [
    { label: "Terms of Service", href: "#" },
    { label: "Privacy Policy", href: "#" },
    { label: "Cookie Policy", href: "#" },
  ],
}

export function Footer() {
  return (
    <footer className="border-t border-verdant-sage/10 bg-verdant-carbon">
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid gap-12 md:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="lg:col-span-1">
            <Logo className="mb-4" />
            <p className="mb-6 text-verdant-sage">
              Turning waste into wealth while proving Bitcoin can heal the planet.
            </p>
            <div className="flex gap-4">
              <a
                href="#"
                className="flex h-10 w-10 items-center justify-center rounded-lg border border-verdant-sage/20 text-verdant-sage transition-colors hover:border-verdant-sats hover:text-verdant-sats"
              >
                <Twitter className="h-5 w-5" />
              </a>
              <a
                href="#"
                className="flex h-10 w-10 items-center justify-center rounded-lg border border-verdant-sage/20 text-verdant-sage transition-colors hover:border-verdant-sats hover:text-verdant-sats"
              >
                <Github className="h-5 w-5" />
              </a>
              <a
                href="#"
                className="flex h-10 w-10 items-center justify-center rounded-lg border border-verdant-sage/20 text-verdant-sage transition-colors hover:border-verdant-sats hover:text-verdant-sats"
              >
                <FileText className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="mb-4 font-semibold text-verdant-paper">Product</h4>
            <ul className="space-y-3">
              {links.product.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-verdant-sage transition-colors hover:text-verdant-sats"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h4 className="mb-4 font-semibold text-verdant-paper">Resources</h4>
            <ul className="space-y-3">
              {links.resources.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-verdant-sage transition-colors hover:text-verdant-sats"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="mb-4 font-semibold text-verdant-paper">Legal</h4>
            <ul className="space-y-3">
              {links.legal.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-verdant-sage transition-colors hover:text-verdant-sats"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-verdant-sage/10 pt-8 md:flex-row">
          <p className="text-sm text-verdant-sage">
            © {new Date().getFullYear()} SatsVerdant. All rights reserved.
          </p>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-success" />
            <span className="font-mono text-sm text-verdant-sage">Stacks Testnet</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
