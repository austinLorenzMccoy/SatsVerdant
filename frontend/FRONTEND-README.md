# SatsVerdant Frontend

A modern, sustainable web application that turns recycling into Bitcoin rewards. Built with Next.js 16, TypeScript, and Tailwind CSS, this frontend demonstrates how blockchain technology can drive environmental positive impact.

## 🌱 Overview

SatsVerdant is a proof-of-concept platform that rewards users with sBTC (synthetic Bitcoin) for verified recycling activities. The application showcases a complete user journey from landing page to dashboard management, with a focus on environmental sustainability and blockchain integration.

## 🚀 Tech Stack

### Core Framework
- **Next.js 16** - React framework with App Router
- **TypeScript** - Type-safe development
- **React 19.2** - Modern React with concurrent features

### Styling & UI
- **Tailwind CSS 4.1.9** - Utility-first CSS framework
- **shadcn/ui** - Modern component library built on Radix UI
- **Lucide React** - Beautiful icon library
- **Framer Motion** - Smooth animations and transitions

### State Management & Data
- **React Hook Form** - Form handling with Zod validation
- **Zod** - TypeScript-first schema validation
- **Recharts** - Data visualization and charts

### Development Tools
- **pnpm** - Fast, disk space efficient package manager
- **ESLint** - Code linting and formatting
- **TypeScript** - Static type checking

### Analytics & Monitoring
- **Vercel Analytics** - Performance and usage analytics

## 📁 Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── dashboard/               # Dashboard application
│   │   ├── impact/             # Environmental impact tracking
│   │   ├── rewards/            # Reward management
│   │   ├── settings/           # User settings
│   │   ├── submit/             # Waste submission
│   │   └── validate/           # Submission validation
│   ├── globals.css             # Global styles and theme
│   ├── layout.tsx              # Root layout component
│   ├── not-found.tsx           # 404 page
│   └── page.tsx                # Landing page
├── components/                  # Reusable React components
│   ├── dashboard/              # Dashboard-specific components
│   ├── landing/                # Landing page components
│   ├── ui/                     # shadcn/ui components
│   ├── logo.tsx                # Application logo
│   └── theme-provider.tsx      # Theme context provider
├── hooks/                       # Custom React hooks
│   ├── use-mobile.ts           # Mobile detection
│   ├── use-sidebar.tsx         # Sidebar state management
│   ├── use-toast.ts            # Toast notifications
│   └── use-wallet.tsx          # Bitcoin wallet integration
├── lib/                         # Utility libraries
├── public/                      # Static assets
├── styles/                      # Additional styles
└── types/                       # TypeScript type definitions
```

## 🎨 Design System

### Color Palette (Verdant Theme)
The application uses a custom "Verdant Stack" color palette inspired by nature:

- **Soil** (`#1a1410`) - Dark backgrounds
- **Moss** (`#2d4a2b`) - Secondary backgrounds
- **Sprout** (`#4a7c59`) - Interactive elements
- **Gold** (`#d4a574`) - Accents and highlights
- **Sats** (`#f7931a`) - Bitcoin orange (primary actions)
- **Sage** (`#8ba888`) - Muted text
- **Paper** (`#f4ede4`) - Light text
- **Carbon** (`#0a0e0d`) - Darkest backgrounds

### Typography
- **Instrument Sans** - Primary body font
- **JetBrains Mono** - Monospace for code and data
- **Syne** - Display font for headings

### Component Library
Built on shadcn/ui with extensive customization:
- 57+ UI components
- Full accessibility support
- Dark/light theme support
- Mobile-responsive design

## 🔧 Key Features

### Landing Page
- Hero section with value proposition
- How-it-works explainer
- Problem/solution narrative
- Social proof and testimonials
- Enterprise solutions section

### Dashboard Application
- **Overview**: Metrics, recent submissions, quick actions
- **Submit**: Waste submission with image upload
- **Validate**: Submission status tracking
- **Rewards**: sBTC earning and claiming
- **Impact**: Environmental impact visualization
- **Settings**: User preferences and wallet management

### Bitcoin Integration
- Mock Bitcoin wallet connection
- sBTC balance tracking
- Transaction history
- Reward claiming system

## 🛠 Development Setup

### Prerequisites
- Node.js 18+ 
- pnpm 9.12.2+

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ascent/mvp_folder/frontend
   ```

2. **Install dependencies**
   ```bash
   pnpm install
   ```

3. **Environment Setup**
   Create a `.env.local` file for environment variables:
   ```env
   NEXT_PUBLIC_APP_URL=http://localhost:3000
   NEXT_PUBLIC_BITCOIN_NETWORK=testnet
   ```

4. **Start development server**
   ```bash
   pnpm dev
   ```

5. **Open browser**
   Navigate to `http://localhost:3000`

### Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint

## 📱 Responsive Design

The application is fully responsive with:
- **Mobile-first approach**
- **Adaptive layouts** for all screen sizes
- **Touch-friendly interactions**
- **Optimized performance** for mobile devices

Breakpoints:
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

## 🔐 Security Considerations

- **TypeScript** for type safety
- **Input validation** with Zod schemas
- **XSS protection** through React's built-in safeguards
- **CSRF protection** via Next.js security headers
- **Environment variables** for sensitive configuration

## 🚀 Deployment

### Vercel (Recommended)
1. Connect repository to Vercel
2. Configure environment variables
3. Deploy automatically on git push

### Other Platforms
```bash
# Build for production
pnpm build

# Export static files (if needed)
pnpm export
```

## 🧪 Testing Strategy

While the current setup doesn't include tests, the recommended approach would be:
- **Jest** for unit testing
- **React Testing Library** for component testing
- **Playwright** for E2E testing
- **Storybook** for component documentation

## 📊 Performance Optimization

- **Next.js Image optimization** (currently disabled)
- **Code splitting** via dynamic imports
- **Tree shaking** for unused code
- **Bundle analysis** with webpack-bundle-analyzer
- **Core Web Vitals** monitoring

## 🔮 Future Enhancements

### Planned Features
- Real Bitcoin wallet integration
- Image recognition for waste verification
- Advanced analytics dashboard
- Mobile app (React Native)
- NFT rewards for milestones
- Community features and leaderboards

### Technical Improvements
- Server-side rendering optimization
- Progressive Web App (PWA) features
- Offline functionality
- Advanced caching strategies
- Microservices architecture

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Style
- Follow TypeScript best practices
- Use ESLint configuration
- Maintain component consistency
- Write meaningful commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **shadcn/ui** for the excellent component library
- **Vercel** for hosting and analytics
- **Radix UI** for accessible primitives
- **Tailwind CSS** for the utility framework

## 📞 Support

For questions or support:
- Create an issue in the repository
- Review the documentation
- Check the FAQ section

---

**Built with ❤️ for a sustainable future powered by Bitcoin**
