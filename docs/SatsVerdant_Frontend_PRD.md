# SatsVerdant Frontend PRD

## 1. Product Vision

SatsVerdant's frontend must embody the intersection of environmental action and Bitcoin's strength - turning waste into wealth while proving Bitcoin can heal the planet. The design should feel organic yet technological, trustworthy yet innovative.

---

## 2. Design Philosophy & Aesthetic Direction

### **Core Theme: "Verdant Stack"**
A unique aesthetic that merges:
- **Organic textures** (recycled paper, natural fibers, earthy tones)
- **Bitcoin/Tech precision** (monospace fonts, sharp contrasts, hexadecimal greens)
- **Environmental credibility** (earth tones, living greens, natural gradients)

### **Visual Identity**
- **NOT generic crypto** (no purple gradients, no neon, no "tech bro" aesthetic)
- **NOT generic eco** (no cliché leaf icons, no "green washing" pastels)
- **YES unique fusion**: Raw earth meets digital gold

### **Color Palette: "Compost to Bitcoin"**

**Primary Palette:**
```css
--verdant-soil: #1a1410        /* Deep composted earth */
--verdant-moss: #2d4a2b        /* Living moss green */
--verdant-sprout: #4a7c59      /* New growth */
--verdant-gold: #d4a574        /* Bitcoin brass/bronze */
--verdant-sats: #f7931a        /* Bitcoin orange (accent) */
--verdant-sage: #8ba888        /* Muted sage */
--verdant-paper: #f4ede4       /* Recycled paper texture */
--verdant-carbon: #0a0e0d      /* Carbon black */
```

**Functional Colors:**
```css
--success-green: #4caf50
--warning-amber: #ff9800
--error-rust: #d84315
--info-sky: #5fa3d0
```

### **Typography**

**Display/Headers:**
- **"JetBrains Mono"** for technical elements (Bitcoin addresses, transaction IDs, metrics)
- **"Cabinet Grotesk"** or **"Syne"** for headlines (bold, modern, geometric)

**Body Text:**
- **"Instrument Sans"** or **"DM Sans"** (clean, readable, slightly organic curves)

**Accent/Special:**
- **"Berkeley Mono"** for code blocks and validator IDs

### **Visual Language**

**Textures:**
- Subtle noise/grain overlay (recycled paper feel)
- Organic gradient meshes (not linear - complex, earthy)
- Hexagonal pattern overlays (blockchain structure)

**Shapes & Patterns:**
- Rounded corners (8px-16px) - organic but intentional
- Asymmetric layouts - break grid convention
- Hexagonal badges for tokens/achievements
- Diagonal flow elements

**Motion:**
- Smooth, intentional animations (300-500ms)
- Staggered reveals on page load
- Hover states that grow/bloom (organic expansion)
- Scroll-triggered parallax for depth

---

## 3. User Flows & Pages

### **3.1 Landing Page** (`/`)

**Purpose:** Convert visitors → registered users

**Sections:**

1. **Hero Section**
   - Background: Suited environmental image (blurred, darkened overlay)
   - Headline: "Turn Trash into Bitcoin"
   - Subheadline: "Proof that Bitcoin heals the planet, not hurts it"
   - CTA: "Start Earning sBTC" (connects wallet)
   - Floating stats cards: Waste recycled, sBTC distributed, CO₂ offset

2. **How It Works** (3-step visual flow)
   - Step 1: Snap photo of recyclables
   - Step 2: AI verifies, validators approve
   - Step 3: Earn sBTC + carbon credits

3. **The Problem** (side-by-side comparison)
   - Left: Traditional recycling (weak incentives, no verification)
   - Right: SatsVerdant (Bitcoin rewards, immutable proof)

4. **Social Proof**
   - Live feed of recent submissions (anonymized)
   - Real-time counter: "X kg recycled today"
   - Validator testimonials

5. **For Corporations** (enterprise pitch)
   - "Buy carbon credits you can actually prove"
   - CTA: "Schedule Demo"

6. **Footer**
   - Links: Docs, Twitter, GitHub
   - Legal: Terms, Privacy
   - Network status badge

**Key Interactions:**
- Scroll-triggered animations (stats count up)
- Parallax background image
- Hover effects on CTA buttons (glow/expand)

---

### **3.2 Dashboard** (`/dashboard`)

**Purpose:** User command center - view stats, manage submissions, claim rewards

**Layout:** Sidebar + Main Content

#### **Sidebar (Collapsible)**

**Top Section:**
- Logo + "SatsVerdant"
- Wallet connection status
  - Connected: Address (truncated) + balance
  - Disconnected: "Connect Wallet" button

**Navigation:**
- 📊 Overview
- 📸 Submit Waste
- 💰 Rewards
- ✅ Validate (validator role only)
- 🏛️ Governance (future)
- 🌍 Impact
- ⚙️ Settings

**Bottom Section:**
- Network indicator (Testnet/Mainnet)
- Theme toggle (if multiple themes)
- Collapse toggle button

**Responsive Behavior:**
- Desktop (>1024px): Expanded by default, collapsible
- Tablet (768-1024px): Collapsed by default, slides over content
- Mobile (<768px): Bottom navigation bar OR hamburger menu

**State Persistence:**
- Collapsed state: React `useState` in `useSidebar.ts` (NOT localStorage — Supabase Auth manages session, no browser storage used anywhere)
- Active tab: Next.js router (URL is source of truth)

---

#### **Dashboard Pages**

### **3.2.1 Overview** (`/dashboard`)

**Metrics Grid (Top):**
```
┌─────────────────┬─────────────────┬─────────────────┐
│  Total Earnings │  Waste Recycled │  Carbon Offset  │
│   0.0042 sBTC   │     12.5 kg     │    3.2 kg CO₂   │
└─────────────────┴─────────────────┴─────────────────┘
```

**Recent Submissions (Card List):**
- Image thumbnail
- Waste type badge (plastic/paper/metal/organic/glass)
- Status indicator (pending/approved/minted)
- Tokens earned
- Date

**Rewards Summary:**
- Claimable rewards (call-to-action)
- Claimed history

**Quick Actions:**
- "Submit New Waste" button
- "Claim Rewards" button

---

### **3.2.2 Submit Waste** (`/dashboard/submit`)

**Mobile:** Camera capture flow
**Web:** File upload with drag-and-drop

**Steps:**

1. **Photo Upload**
   - Large dropzone: "Drag photo or click to upload"
   - Camera icon
   - Preview thumbnail after upload
   - Geolocation permission request (mobile)

2. **AI Classification** (auto-triggered by  Edge Function)
   - Loading state: "Analyzing..."
   - Radar.io geofence result shown first:
     - ✅ "At GreenDrop Bin — 42m away" (proceeds)
     - ❌ "No recycling point nearby" (blocked with nearest location shown)
   - Groq classification result:
     ```
     Type: Plastic (95% confidence)
     Weight: ~0.5 kg
     Quality: Grade A
     ```
   - Edit option if user disagrees with AI result

3. **Confirmation**
   - Review details
   - Submit to validation queue
   - Expected reward estimate

**UI States:**
- Idle (upload prompt)
- Uploading (progress bar)
- Classifying (spinner + message)
- Classified (results + confirm)
- Submitted (success + tracking ID)
- Error (retry option)

---

### **3.2.3 Rewards** (`/dashboard/rewards`)

**Claimable Rewards Section:**
- Card for each claimable reward
  - Submission thumbnail
  - Token amount
  - sBTC value
  - "Claim" button
- Batch claim option: "Claim All (X rewards)"

**Claimed History:**
- Timeline view
- Transaction links (Stacks Explorer)
- Filter by date range

**Rewards Stats:**
- Total earned (lifetime)
- Average per submission
- Chart: Earnings over time

---

### **3.2.4 Validate** (`/dashboard/validate`) - Validator Only

**Validation Queue:**
- Grid/list of pending submissions
- Each card shows:
  - Image
  - AI classification
  - Confidence score
  - User reputation (if available)
  - GPS location (map pin)

**Review Modal:**
- Large image view
- AI details
- Fraud indicators (duplicate warning, suspicious patterns)
- Actions:
  - ✅ Approve
  - ❌ Reject (with reason)
  - 🚩 Flag for review

**Validator Stats:**
- Validations completed
- Accuracy rate
- STX staked
- Reputation score

---

### **3.2.5 Impact** (`/dashboard/impact`)

**Personal Impact Dashboard:**
- Total waste recycled (by type, pie chart)
- CO₂ offset calculator
  - Visual: "Equivalent to X trees planted"
- Timeline of submissions
- Badges/achievements

**Global Impact:**
- Platform-wide stats
- Leaderboard (optional, gamification)

---

### **3.2.6 Settings** (`/dashboard/settings`)

**Account Section:**
- Wallet address (copy button)
- Disconnect wallet
- Profile (display name, avatar - optional)

**Preferences:**
- Email notifications (optional)
- Language
- Theme (if multiple)

**Security:**
- Two-factor setup (future)
- Session management

**Data:**
- Export submission history (CSV)
- Delete account (GDPR)

---

### **3.3 Mobile App Screens**

**Bottom Navigation:**
- Home (overview)
- Camera (submit)
- Rewards
- Profile (settings)

**Camera Screen:**
- Full-screen camera viewfinder
- Capture button (large, center bottom)
- Flash toggle
- Flip camera toggle
- Recent submissions (swipe up)

**Flow:**
```
Camera → Capture → Preview → AI Classification → Confirm → Success
```

---

## 4. Component Library

### **4.1 Core Components**

#### **Button Variants**
```tsx
<Button variant="primary">   // Bitcoin orange, high contrast
<Button variant="secondary"> // Moss green, outlined
<Button variant="ghost">     // Transparent, hover effect
<Button variant="danger">    // Rust red
```

#### **Card**
```tsx
<Card>
  <CardHeader>
    <CardTitle />
    <CardSubtitle />
  </CardHeader>
  <CardContent />
  <CardFooter />
</Card>
```

**Visual Style:**
- Background: Slight gradient + noise texture
- Border: Subtle, organic color
- Shadow: Soft, layered
- Hover: Lift effect (transform: translateY(-4px))

#### **Badge**
- Hexagonal shape
- Waste type colors:
  - Plastic: Blue-teal
  - Paper: Tan-brown
  - Metal: Steel gray
  - Organic: Green
  - Glass: Blue-green (teal-jade — translucent quality of glass)

#### **Stat Display**
```tsx
<StatCard
  label="Total Earnings"
  value="0.0042 sBTC"
  change="+12%"
  icon={<BitcoinIcon />}
/>
```

#### **Status Indicator**
- Pending: Amber pulse
- Approved: Green checkmark
- Rejected: Red X
- Minted: Gold sparkle

---

### **4.2 Advanced Components**

#### **Image Upload Zone**
- Drag-and-drop
- Click to upload
- Paste support
- Progress indicator
- Preview with crop/rotate (future)

#### **Transaction Toast**
- Bottom-right notifications
- Auto-dismiss (5s)
- Action buttons (view tx, dismiss)

#### **Loading States**
- Skeleton screens (avoid spinners where possible)
- Shimmer effect
- Context-specific messages ("Analyzing waste...", "Minting tokens...")

#### **Empty States**
- Illustration + message
- Call-to-action
- Examples:
  - No submissions: "Ready to earn? Submit your first recyclable!"
  - No rewards: "Your rewards will appear here once approved"

---

## 5. Responsive Design

### **Breakpoints**
```css
--mobile: 0-767px
--tablet: 768px-1023px
--desktop: 1024px+
```

### **Mobile-First Approach**

**Mobile (<768px):**
- Single column layout
- Bottom navigation OR hamburger menu
- Stacked metrics
- Full-width cards
- Touch-optimized buttons (min 44px)

**Tablet (768-1023px):**
- 2-column grid for metrics
- Sidebar slides over (not persistent)
- Optimized for landscape + portrait

**Desktop (1024px+):**
- Sidebar persistent (collapsible)
- Multi-column layouts
- Hover states
- Keyboard shortcuts

---

## 6. Interactions & Animations

### **Page Load**
```css
1. Fade in background (200ms)
2. Slide in sidebar (300ms, delay 100ms)
3. Stagger content cards (each 100ms delay)
```

### **Sidebar Collapse**
```css
- Width transition: 250px → 64px (300ms ease-in-out)
- Icon-only mode (labels hidden)
- Tooltip on hover (collapsed state)
- Smooth animation
```

### **Button Hover**
```css
- Scale: 1 → 1.02
- Shadow: subtle → prominent
- Background: shift +10% brightness
- Transition: 150ms
```

### **Card Hover**
```css
- Transform: translateY(0) → translateY(-4px)
- Shadow: soft → elevated
- Border: subtle → accent glow
```

### **Submission Status**
- Pending: Pulsing amber dot
- Processing: Rotating hexagon
- Approved: Green checkmark with bounce
- Rejected: Red X with shake

---

## 7. Accessibility

**Keyboard Navigation:**
- Tab order follows visual hierarchy
- Focus indicators (thick outline, high contrast)
- Escape closes modals
- Arrow keys navigate lists

**Screen Readers:**
- Semantic HTML (`<nav>`, `<main>`, `<article>`)
- ARIA labels for icons
- Live regions for status updates
- Alt text for all images

**Color Contrast:**
- WCAG AA minimum (4.5:1 text, 3:1 graphics)
- Test all color combinations

**Motion:**
- Respect `prefers-reduced-motion`
- Disable animations for users who prefer

---

## 8. Performance

**Optimization:**
- Lazy load images
- Code splitting (route-based)
- Optimize fonts (subset, preload)
- Compress images (WebP)
- Cache static assets

**Metrics:**
- Lighthouse score: >90
- First Contentful Paint: <1.5s
- Time to Interactive: <3s

---

## 9. Error Handling

### **Error States**

**Network Error:**
- Message: "Connection lost. Retrying..."
- Auto-retry with exponential backoff
- Manual retry button

**Upload Fail:**
- Message: "Upload failed. Check your connection."
- Retry button
- Show partial progress if possible

**Contract Error:**
- Message: "Transaction failed: [reason]"
- Link to explorer
- Contact support option

**404 Page:**
- Friendly message: "This page doesn't exist"
- Links: Home, Dashboard
- Search bar (future)

---

## 10. Technical Implementation

### **Tech Stack**
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS + CSS Modules (for complex animations)
- **Components:** Radix UI (headless) + custom styling
- **State:** React Context + Supabase client (no React Query needed — Supabase JS SDK handles caching and real-time)
- **Icons:** Lucide React (custom SVG for logo/brand)
- **Wallet:** Stacks Connect + Supabase Auth (Google OAuth for validators)
- **Data / API:** Supabase JS SDK (PostgREST auto-generated API + Edge Function invocation)
- **Real-time:** Supabase Realtime (`postgres_changes` subscriptions — MVP, not Phase 2)
- **Mobile storage:** MMKV (encrypted, replaces AsyncStorage — GPS metadata requires encryption)

### **Authentication Architecture**

Two auth paths converge in a single `AuthContext`:

```
Recyclers:   Stacks Connect wallet → sign message → Supabase Auth (custom JWT)
Validators:  Google OAuth via Supabase Auth  OR  Stacks Connect
             └─ Supabase session wraps both, role stored in users.role
```

```tsx
// contexts/AuthContext.tsx
import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { AppConfig, UserSession, showConnect } from '@stacks/connect'

interface AuthState {
  supabaseSession: Session | null
  stacksAddress:   string | null
  role:            'recycler' | 'validator' | 'admin' | null
  isLoading:       boolean
  connectWallet:   () => void
  signOut:         () => Promise<void>
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ ... })

  // On mount: restore Supabase session, derive Stacks address from user metadata
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setState(s => ({ ...s, supabaseSession: session,
        stacksAddress: session?.user.user_metadata?.stacks_address ?? null,
        role: session?.user.user_metadata?.role ?? null,
        isLoading: false }))
    })
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_, session) => {
      setState(s => ({ ...s, supabaseSession: session }))
    })
    return () => subscription.unsubscribe()
  }, [])

  return <AuthContext.Provider value={state}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
```

### **Supabase Client**

```ts
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'   // generated by: supabase gen types

export const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Typed Edge Function invocations (replaces lib/api.ts entirely)
export const edgeFunctions = {
  classify:     (body: { imagePath: string; userId: string; lat: number; lng: number }) =>
    supabase.functions.invoke('classify',      { body }),

  mintTokens:   (body: { submissionId: string }) =>
    supabase.functions.invoke('mint-tokens',   { body }),

  claimReward:  (body: { rewardId: string; userId: string }) =>
    supabase.functions.invoke('claim-reward',  { body }),
}
```

### **Supabase Realtime Patterns**

#### `SubmissionTracker.tsx` — per-submission status channel

```tsx
// components/submissions/SubmissionTracker.tsx
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

// Status labels shown to the user
const STATUS_LABELS: Record<string, string> = {
  pending_classification: 'Uploading...',
  classified:             'AI classified ✓ — awaiting validator',
  pending_validation:     'In validator queue...',
  approved:               'Approved — minting token...',
  minting:                'Minting token...',
  minted:                 'Token minted! Reward ready ✓',
  rejected:               'Submission rejected',
  failed:                 'Minting failed — contact support',
}

export function SubmissionTracker({ submissionId }: { submissionId: string }) {
  const [status, setStatus] = useState<string>('pending_classification')
  const [tokens, setTokens] = useState<number | null>(null)

  useEffect(() => {
    // Subscribe to this specific submission row
    const channel = supabase
      .channel(`submission:${submissionId}`)
      .on('postgres_changes', {
        event:  'UPDATE',
        schema: 'public',
        table:  'submissions',
        filter: `id=eq.${submissionId}`,
      }, (payload) => {
        setStatus(payload.new.status)
        if (payload.new.tokens_minted) setTokens(payload.new.tokens_minted)
      })
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [submissionId])

  return (
    <div className="submission-tracker">
      <StatusIndicator status={status} />
      <p>{STATUS_LABELS[status] ?? status}</p>
      {tokens && <p className="tokens-earned">+{tokens} tokens earned!</p>}
    </div>
  )
}
```

#### `ValidatorQueue.tsx` — live queue for validators

```tsx
// components/validators/ValidatorQueue.tsx
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export function ValidatorQueue() {
  const [queue, setQueue] = useState<Submission[]>([])

  useEffect(() => {
    // Initial load: classified + pending_validation (both need human review)
    supabase.from('submissions')
      .select('*, users(wallet_address)')
      .in('status', ['classified', 'pending_validation'])
      .order('created_at', { ascending: true })
      .then(({ data }) => setQueue(data ?? []))

    // Live updates: new items arrive automatically
    const channel = supabase
      .channel('validator-queue')
      .on('postgres_changes', {
        event:  'INSERT',
        schema: 'public',
        table:  'submissions',
        filter: `status=in.(classified,pending_validation)`,
      }, (payload) => {
        setQueue(q => [...q, payload.new as Submission])
      })
      .on('postgres_changes', {
        event:  'UPDATE',
        schema: 'public',
        table:  'submissions',
      }, (payload) => {
        // Remove from queue once approved/rejected
        if (['approved','rejected'].includes(payload.new.status)) {
          setQueue(q => q.filter(s => s.id !== payload.new.id))
        }
      })
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [])

  return (
    <div className="validator-queue">
      {queue.map(submission => (
        <ValidationCard key={submission.id} submission={submission} />
      ))}
      {queue.length === 0 && <EmptyState message="Queue is clear — great work!" />}
    </div>
  )
}
```

### **Submit Waste Flow**

The submission flow calls `/classify` directly after upload. No polling — `SubmissionTracker` receives all status changes via Realtime:

```tsx
// app/dashboard/submit/page.tsx (simplified)
async function handleSubmit(file: File, coords: { lat: number; lng: number }) {
  // 1. Upload image to Supabase Storage
  const path = `waste-images/${userId}/${Date.now()}.jpg`
  await supabase.storage.from('waste-images').upload(path, file)

  // 2. Call /classify Edge Function
  const { data, error } = await edgeFunctions.classify({
    imagePath: path, userId, lat: coords.lat, lng: coords.lng
  })
  if (error || !data?.submissionId) throw new Error('Classification failed')

  // 3. Mount SubmissionTracker — all further updates are Realtime, no polling
  setSubmissionId(data.submissionId)
}
```

### **Claim Reward Flow**

```tsx
// components/rewards/RewardCard.tsx (simplified)
async function handleClaim(rewardId: string) {
  setClaiming(true)
  const { data, error } = await edgeFunctions.claimReward({ rewardId, userId })
  if (error) { setError('Claim failed. Try again.'); return }
  // Supabase Realtime subscription on rewards table updates card state automatically
}
```

### **File Structure**

```
web/src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                        # Landing
│   ├── dashboard/
│   │   ├── layout.tsx                  # Sidebar layout (AuthContext provider wraps here)
│   │   ├── page.tsx                    # Overview
│   │   ├── submit/page.tsx
│   │   ├── rewards/page.tsx
│   │   ├── validate/page.tsx
│   │   ├── impact/page.tsx
│   │   └── settings/page.tsx
│   └── not-found.tsx                   # 404
│
├── components/
│   ├── ui/                             # Radix primitives + custom styling
│   ├── layout/
│   │   ├── Sidebar.tsx                 # Collapsed state: React useState (NOT localStorage)
│   │   ├── Header.tsx
│   │   └── Footer.tsx
│   ├── auth/
│   │   ├── LoginForm.tsx               # Stacks Connect + Google OAuth buttons
│   │   └── WalletConnect.tsx           # Stacks wallet connection button
│   ├── submissions/
│   │   ├── SubmissionCard.tsx
│   │   └── SubmissionTracker.tsx       # Realtime: pending_classification→classified→minted
│   ├── validators/
│   │   └── ValidatorQueue.tsx          # Realtime: live queue of classified + pending_validation
│   └── rewards/
│       └── RewardCard.tsx
│
├── contexts/
│   └── AuthContext.tsx                 # Supabase Auth + Stacks Connect session
│
├── lib/
│   ├── supabase.ts                     # Supabase client + typed Edge Function wrappers
│   │                                   # (replaces lib/api.ts entirely)
│   ├── contracts.ts                    # Stacks contract address constants + call helpers
│   └── utils.ts
│
├── hooks/
│   ├── useAuth.ts                      # Reads from AuthContext
│   ├── useSubmissions.ts               # Supabase queries (no React Query needed)
│   ├── useWallet.ts                    # Stacks Connect wallet state
│   └── useSidebar.ts                   # React state only — no localStorage
│
└── styles/
    └── globals.css
```

### **Mobile App: Additional Technical Notes**

The mobile app (React Native + Expo) shares the same Supabase project but has two platform-specific additions not present in the web app:

**MMKV for local storage** (replaces AsyncStorage):
```ts
// mobile/src/storage/mmkv.ts
import { MMKV } from 'react-native-mmkv'
export const storage = new MMKV({ id: 'satsverdant', encryptionKey: ENCRYPTION_KEY })

// Offline submission queue — encrypted because submissions contain GPS coordinates
export const offlineQueue = {
  push: (item: PendingSubmission) => {
    const queue = JSON.parse(storage.getString('offline_queue') ?? '[]')
    storage.set('offline_queue', JSON.stringify([...queue, item]))
  },
  drain: (): PendingSubmission[] => {
    const queue = JSON.parse(storage.getString('offline_queue') ?? '[]')
    storage.delete('offline_queue')
    return queue
  },
}
```

**Radar.io geofencing pre-check** (before upload):
```ts
// mobile/src/services/location.ts
import Radar from 'react-native-radar'

export async function checkNearRecyclingPoint(lat: number, lng: number): Promise<{
  inRange: boolean;
  nearestName: string | null;
  distanceM: number | null;
}> {
  // Pre-check on device before uploading (saves bandwidth on rejections)
  // The /classify Edge Function performs the authoritative server-side check
  const result = await Radar.searchGeofences({
    near: { latitude: lat, longitude: lng },
    radius: 150,  // slightly generous client-side; server enforces 100m
    tags: ['recycling'],
    limit: 1,
  })
  const nearest = result.geofences?.[0]
  return {
    inRange: !!nearest,
    nearestName: nearest?.description ?? null,
    distanceM: nearest ? Math.round(nearest.distance) : null,
  }
}
```

---

## 11. MVP Feature Priority

### **Must-Have (Launch)**
- ✅ Landing page
- ✅ Wallet connection (Stacks Connect + Supabase Auth)
- ✅ Submit waste (photo upload → `/classify` Edge Function)
- ✅ Dashboard overview
- ✅ Rewards page (claim via `/claim-reward` Edge Function)
- ✅ Responsive design
- ✅ Collapsible sidebar
- ✅ **Supabase Realtime** — SubmissionTracker + ValidatorQueue (MVP, not Phase 2)

### **Should-Have (Week 2)**
- ✅ Validator queue (ValidatorQueue.tsx with live Realtime subscription)
- ✅ Impact dashboard
- ✅ Settings page
- ✅ Error handling
- ✅ Loading states / skeleton screens

### **Nice-to-Have (Post-MVP)**
- Governance page
- Advanced charts
- Gamification (badges)
- Multi-language support
- Dark/light theme toggle

---

## 12. Testing Requirements

**Unit Tests:**
- Component rendering
- AuthContext state transitions
- Supabase query hooks

**Integration Tests:**
- Wallet connection → Supabase Auth session
- Submit flow: upload → classify → Realtime status update
- Reward claiming: RewardCard → `/claim-reward` → Realtime status update
- ValidatorQueue: Realtime INSERT/UPDATE events

**E2E Tests (Playwright):**
- User journey: Connect → Submit → Realtime classified → Claim
- Validator flow: Queue loads → Approve → queue item removed via Realtime
- Responsive breakpoints

**Manual Testing:**
- Cross-browser (Chrome, Safari, Firefox)
- Mobile devices (iOS Safari, Android Chrome)
- Accessibility audit (aXe)

---

## 13. Success Criteria

**User Experience:**
- 10 users complete submission flow without help
- <3 clicks to submit waste
- <5s page load time
- Zero accessibility errors (aXe audit)

**Design:**
- Unique, memorable aesthetic
- Consistent across all pages
- Professional, trustworthy feel
- Mobile-optimized

**Technical:**
- 100% responsive
- Smooth animations (60fps)
- Works offline (MMKV queue on mobile — NOT localStorage)
- Supabase Realtime delivers status updates in < 200ms
- No localStorage usage anywhere (session managed by Supabase Auth)

---

## 14. Future Enhancements

**Phase 2:**
- Social features (share achievements)
- Referral program
- Advanced analytics dashboard
- Push notifications (Expo + Supabase Edge Function webhook)

**Phase 3:**
- AR features (identify waste via camera)
- Carbon credit marketplace UI
- Corporate ESG dashboard
- Governance page (DAO voting)

*(Note: Real-time updates, mobile app, and Radar.io geofencing are all MVP — not Phase 2 or 3.)*

---

*SatsVerdant Frontend PRD v2.0 — March 2026. Supersedes v1.0. Critical changes: Supabase JS SDK replaces Fetch API + React Query. Supabase Realtime is MVP (not Phase 2). AuthContext added (Stacks Connect + Supabase Auth). SubmissionTracker.tsx and ValidatorQueue.tsx added with live postgres_changes subscriptions. localStorage removed — sidebar state via React useState, session via Supabase Auth. MMKV replaces AsyncStorage on mobile. glass badge color added. Radar.io SDK documented for mobile geofence pre-check.*