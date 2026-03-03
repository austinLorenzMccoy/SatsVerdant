# 🌱 SatsVerdant

<div align="center">

![SatsVerdant Logo](https://raw.githubusercontent.com/austinLorenzMccoy/SatsVerdant/main/frontend/public/satsverdant-logo.svg)

**Turn Trash into Bitcoin - Earn sBTC for verified recycling**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Visit_Success?style=for-the-badge&logo=netlify&logoColor=white)](https://satsverdant.netlify.app)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Backend](https://img.shields.io/badge/Backend-Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![Blockchain](https://img.shields.io/badge/Blockchain-Stacks-F7931A?style=for-the-badge&logo=bitcoin&logoColor=white)](https://www.stacks.co/)
[![ML](https://img.shields.io/badge/ML-EfficientNetB0-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)](https://tensorflow.org/)
[![MLOps](https://img.shields.io/badge/MLOps-MLflow%20%2B%20DVC-007396?style=for-the-badge&logo=dvc&logoColor=white)](https://dvc.org/)

</div>

---

## � Vision

**SatsVerdant** is a revolutionary platform that proves Bitcoin can heal the planet, not hurt it. We create a circular economy where waste becomes valuable through blockchain verification and synthetic Bitcoin rewards.

### 💡 The Problem
- **Environmental Crisis**: 2.12 billion tons of waste generated annually
- **Low Recycling Rates**: Only 32% of waste gets recycled globally
- **Lack of Incentives**: No immediate reward for individual recycling efforts

### 🚀 Our Solution
- **Instant Rewards**: Earn sBTC for every verified recycling submission
- **Blockchain Verification**: Immutable proof of environmental impact
- **Zero Greenwashing**: Transparent, auditable waste tracking

---

## 🏗️ Architecture Overview

```mermaid
graph TB
    A[User Submits Waste] --> B[AI Verification]
    B --> C[Blockchain Record]
    C --> D[sBTC Rewards]
    D --> E[Environmental Impact]
    
    F[Frontend - Next.js] --> G[Backend - FastAPI]
    G --> H[ML Models]
    G --> I[Smart Contracts]
    I --> J[Stacks Blockchain]
```

## 📁 Project Structure

```
mvp_folder/
├── 🎨 frontend/           # Next.js 16 + TypeScript + Tailwind CSS
│   ├── app/              # App Router pages
│   ├── components/       # Reusable UI components
│   ├── hooks/           # Custom React hooks
│   └── public/          # Static assets
├── ⚙️ backend/            # Supabase + FastAPI + Python
│   ├── app/             # API endpoints
│   ├── models/          # Database models
│   ├── services/        # Business logic
│   └── tests/           # Test suite
├── 📜 contracts/         # Clarity Smart Contracts
│   ├── contracts/       # Smart contract code
│   ├── tests/          # Contract tests
│   └── settings/       # Deployment configs
├── 🤖 ml-training/        # Machine Learning Pipeline
│   ├── scripts/        # Training scripts
│   ├── models/         # Trained models
│   ├── data/           # Dataset (DVC-tracked)
│   └── dvc.yaml        # Pipeline definition
└── 📚 docs/              # Documentation & PRDs
```

---

## �️ Technology Stack

### Frontend Technologies
| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.0 | React framework with App Router |
| **TypeScript** | 5.9 | Type-safe development |
| **Tailwind CSS** | 4.1 | Utility-first styling |
| **shadcn/ui** | Latest | Component library |
| **React Hook Form** | 7.71 | Form management |
| **Zod** | 3.25 | Schema validation |

### Backend Technologies
| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | Latest | High-performance API |
| **Python** | 3.12 | Backend language |
| **PostgreSQL** | Latest | Primary database |
| **Redis** | Latest | Caching layer |
| **Pydantic** | Latest | Data validation |

### Blockchain & ML
| Technology | Purpose |
|------------|---------|
| **Stacks** | Bitcoin L1 smart contracts |
| **Clarity** | Smart contract language |
| **TensorFlow** | ML model training |
| **Groq API** | Ultra-fast inference (~50ms/image) |
| **Supabase** | Database + Edge Functions |
| **MLflow** | Experiment tracking |
| **DVC** | Dataset versioning |
| **DagsHub** | Remote storage + collaboration |
| **PostGIS** | Spatial queries for location verification |
| **Radar.io** | Geofencing for fraud prevention |
| **TensorFlow Lite** | On-device inference (React Native) |
| **PyTorch** | Alternative ML framework |

---

## � Quick Start

### Prerequisites
- Node.js 18+ and pnpm
- Python 3.12+ and pip
- Git

### 🎨 Frontend Setup
```bash
cd frontend
pnpm install
pnpm dev
```
🌐 Visit: `http://localhost:3000`

### ⚙️ Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
🌐 Visit: `http://localhost:8000`

### 📜 Smart Contracts
```bash
cd contracts
npm install
npm run test
```

### 🤖 ML Training
```bash
cd ml-training
pip install -r requirements.txt
./run_pipeline.sh
```
🌐 **MLflow Dashboard**: `https://dagshub.com/satsverdant/satsverdant-ml`
📊 **Model Registry**: Tracked experiments with version control
🎯 **Target**: >80% accuracy on waste classification

### 📡 Dataset & Training
- **Dataset Size**: 26,000 labeled images across 5 waste categories
- **Class Distribution**: Plastic (8k), Paper (6.5k), Metal (5k), Organic (4.5k), Glass (2k)
- **Data Sources**: TrashNet, TACO, Kaggle, custom collections
- **MLOps Stack**: MLflow + DVC + DagsHub for full reproducibility
- **Experiment Tracking**: Every run logged with hyperparameters and metrics
- **Model Registry**: Versioned models with staging/production workflow
- **Note**: Electronic waste removed from MVP scope (Phase 4 expansion)

---

## 🌟 Key Features

### 🏠 Landing Page
- **Hero Section**: Compelling value proposition
- **How It Works**: Step-by-step user journey
- **Social Proof**: Trust indicators and testimonials
- **Enterprise Solutions**: B2B offerings

### 📊 Dashboard Application
- **Overview**: Metrics and recent activity
- **Submit**: Waste submission with image upload
- **Validate**: Real-time submission tracking
- **Rewards**: sBTC earning and claiming
- **Impact**: Environmental impact visualization
- **Settings**: Profile and wallet management

### 🔗 Blockchain Integration
- **Smart Contracts**: Waste tokenization on Stacks
- **sBTC Rewards**: Synthetic Bitcoin incentives
- **Immutable Records**: Permanent environmental impact tracking
- **Transparent Auditing**: Public verification system

---

## 🌱 Environmental Impact

### 📈 Metrics Tracked
- **CO₂ Offset**: Carbon footprint reduction
- **Waste Diverted**: Total waste recycled
- **Recycling Rate**: Individual and community metrics
- **Reward Distribution**: sBTC earned and claimed

### 🎯 Sustainability Goals
- **Short Term**: 1,000 active users, 10 tons waste recycled
- **Medium Term**: 10,000 users, 100 tons waste recycled
- **Long Term**: 100,000 users, 1,000 tons waste recycled

---

## 🔧 Development Workflow

### 📋 Git Workflow
```bash
git clone https://github.com/austinLorenzMccoy/SatsVerdant.git
cd SatsVerdant
git checkout -b feature/your-feature
# Make changes
git commit -m "feat: add your feature"
git push origin feature/your-feature
# Create Pull Request
```

### 🧪 Testing
```bash
# Frontend tests
cd frontend && pnpm test

# Backend tests
cd backend && pytest

# Contract tests
cd contracts && npm test
```

### 🚀 Deployment
- **Frontend**: Netlify (automatic on main branch push)
- **Backend**: Render (manual deployment)
- **Contracts**: Stacks testnet/mainnet deployment

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### 🎯 Areas for Contribution
- 🎨 **Frontend**: UI/UX improvements, new components
- ⚙️ **Backend**: API endpoints, database optimization
- 📜 **Smart Contracts**: New contract features, testing
- 🤖 **ML**: Model improvements, new algorithms
- 📚 **Documentation**: Guides, tutorials, API docs

---

## 📊 Project Status

### ✅ Completed Features
- [x] Landing page with hero and sections
- [x] Dashboard with all core pages
- [x] Smart contracts for waste tokenization
- [x] Backend API with FastAPI
- [x] ML pipeline for waste classification
- [x] Netlify deployment configuration
- [x] Real wallet integration (Stacks, sBTC)
- [x] MIT license and comprehensive documentation

### 🚧 In Progress
- [ ] Backend deployment to Render
- [ ] Smart contract deployment to testnet/mainnet
- [ ] ML model training and deployment
- [ ] Image recognition for waste verification
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)

### 🎯 Planned Features
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Community features and leaderboards
- [ ] NFT rewards for milestones
- [ ] Enterprise API access
- [ ] International expansion

---

## 🔗 Important Links

| Link | Description |
|------|-------------|
| [🌐 Live Demo](https://satsverdant.netlify.app) | Deployed frontend application |
| [📚 Documentation](./docs/) | Comprehensive project docs & PRDs |
| [📜 Smart Contracts](./contracts/) | Clarity contract code |
| [🤖 ML Pipeline](./ml-training/) | Machine learning training & models |
| [⚙️ API Docs](https://your-api.onrender.com/docs) | Backend API documentation |
| [🐛 Issues](https://github.com/austinLorenzMccoy/SatsVerdant/issues) | Bug reports and feature requests |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Bitcoin Community** for inspiration and support
- **Stacks Ecosystem** for smart contract platform
- **Next.js Team** for excellent framework
- **FastAPI Community** for amazing backend framework
- **Environmental Organizations** for waste management insights

---

<div align="center">

**🌱 Together, we can turn waste into wealth and heal the planet through Bitcoin**

[![Star History Chart](https://img.shields.io/github/stars/austinLorenzMccoy/SatsVerdant?style=social)](https://github.com/austinLorenzMccoy/SatsVerdant)
[![Forks](https://img.shields.io/github/forks/austinLorenzMccoy/SatsVerdant?style=social)](https://github.com/austinLorenzMccoy/SatsVerdant)
[![Issues](https://img.shields.io/github/issues/austinLorenzMccoy/SatsVerdant)](https://github.com/austinLorenzMccoy/SatsVerdant/issues)

</div>
