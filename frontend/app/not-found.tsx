import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Home, LayoutDashboard } from "lucide-react"

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-verdant-carbon via-verdant-soil to-verdant-moss px-6">
      <div className="text-center">
        <h1 className="font-display text-8xl font-bold md:text-9xl">
          <span className="bg-gradient-to-r from-verdant-sats to-verdant-gold bg-clip-text text-transparent">
            404
          </span>
        </h1>
        <h2 className="mt-6 font-display text-2xl font-bold text-verdant-paper md:text-3xl">
          Page Not Found
        </h2>
        <p className="mx-auto mt-4 max-w-md text-verdant-sage">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <div className="mt-8 flex flex-col justify-center gap-4 sm:flex-row">
          <Link href="/">
            <Button className="gap-2 bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon">
              <Home className="h-4 w-4" />
              Go Home
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button
              variant="outline"
              className="gap-2 border-verdant-sprout text-verdant-paper hover:bg-verdant-sprout bg-transparent"
            >
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
