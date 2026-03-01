import Link from "next/link"
import { LandingNav } from "@/components/landing/landing-nav"
import { HeroSection } from "@/components/landing/hero-section"
import { HowItWorksSection } from "@/components/landing/how-it-works-section"
import { ProblemSection } from "@/components/landing/problem-section"
import { SocialProofSection } from "@/components/landing/social-proof-section"
import { EnterpriseSection } from "@/components/landing/enterprise-section"
import { Footer } from "@/components/landing/footer"
import { WalletProvider } from "@/hooks/use-wallet"

export default function LandingPage() {
  return (
    <WalletProvider>
      <div className="min-h-screen bg-gradient-to-br from-verdant-carbon via-verdant-soil to-verdant-moss">
        <LandingNav />
        <main>
          <HeroSection />
          <HowItWorksSection />
          <ProblemSection />
          <SocialProofSection />
          <EnterpriseSection />
        </main>
        <Footer />
      </div>
    </WalletProvider>
  )
}
