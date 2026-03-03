# SatsVerdant Backend - Supabase Architecture

## 🏗️ Architecture Overview

This backend is built entirely on **Supabase** - a modern serverless platform that combines PostgreSQL, real-time subscriptions, authentication, storage, and edge functions in a single managed service.

## 📁 Directory Structure

```
backend/
├── supabase/
│   ├── migrations/          # Database schema migrations
│   ├── functions/          # Supabase Edge Functions (serverless API)
│   └── seed-data/          # Initial data for development
├── docs/                   # Backend documentation
├── scripts/                # Utility scripts
└── README.md              # This file
```

## 🚀 Key Components

### 1. **Supabase Database (PostgreSQL + PostGIS)**
- **Managed PostgreSQL** with automatic scaling
- **PostGIS extension** for spatial queries (location verification)
- **Row Level Security (RLS)** for data access control
- **Real-time subscriptions** for live updates

### 2. **Supabase Edge Functions**
- **Serverless functions** for business logic
- **ML inference pipeline** with Groq API integration
- **Fraud detection** and quality grading
- **Location verification** with Radar.io

### 3. **Supabase Auth**
- **Built-in authentication** with multiple providers
- **Stacks Connect OAuth** integration
- **JWT tokens** with automatic refresh
- **User management** and permissions

### 4. **Supabase Storage**
- **File uploads** with automatic CDN
- **IPFS pinning** for permanent records
- **Image optimization** and resizing
- **Access control** via RLS policies

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | PostgreSQL + PostGIS | Primary data + spatial queries |
| **Functions** | Deno (Edge Functions) | Serverless API endpoints |
| **Auth** | Supabase Auth | User authentication |
| **Storage** | Supabase Storage | File uploads & IPFS |
| **Real-time** | Supabase Realtime | Live subscriptions |
| **ML Inference** | Groq API | Ultra-fast classification |
| **Location** | Radar.io | Geofencing verification |
| **MLOps** | MLflow + DVC + DagsHub | Experiment tracking |

## 📊 Database Schema

### Core Tables
- **users** - User profiles and wallet addresses
- **submissions** - Waste submissions with AI results
- **recycling_locations** - Verified recycling points
- **reward_queue** - Pending sBTC rewards
- **fraud_flags** - Fraud detection records

### Spatial Features
- **PostGIS** for location-based queries
- **Geofencing** for recycling point verification
- **Distance calculations** for nearest location finding

## 🔐 Security Features

### Row Level Security (RLS)
- **User data isolation** - users only see their own data
- **Role-based access** - different permissions for different roles
- **JWT-based authentication** - secure token validation
- **API rate limiting** - prevent abuse

### Fraud Prevention
- **Perceptual hashing** - duplicate image detection
- **Rate limiting** - prevent rapid submissions
- **Location verification** - ensure physical presence
- **AI confidence scoring** - quality-based rewards

## 🚀 Deployment

### Supabase Cloud (Recommended)
- **Zero infrastructure management**
- **Automatic scaling** and backups
- **Built-in monitoring** and logging
- **Global CDN** for fast responses

### Self-hosted Option
- **Docker Compose** setup available
- **Manual scaling** required
- **Custom domains** supported
- **Advanced configuration** options

## 📝 Development Workflow

### 1. **Local Development**
```bash
# Start Supabase locally
supabase start

# Run migrations
supabase db reset

# Test edge functions
supabase functions serve
```

### 2. **Database Changes**
```bash
# Create new migration
supabase db diff --use-migra

# Apply migration
supabase db push

# Seed data
supabase db seed
```

### 3. **Edge Functions**
```bash
# Deploy function
supabase functions deploy classify

# Test locally
supabase functions serve --env-file .env.local
```

## 🔗 API Endpoints

### ML Classification
- **POST /functions/v1/classify** - Waste classification with AI
- **GET /functions/v1/health** - Health check endpoint

### User Management
- **POST /auth/v1/signup** - User registration
- **POST /auth/v1/token** - Authentication
- **GET /auth/v1/user** - User profile

### Data Operations
- **REST API** - Automatic CRUD endpoints
- **Real-time** - Live subscription updates
- **Storage** - File upload/download

## 📈 Monitoring & Analytics

### Built-in Monitoring
- **Supabase Dashboard** - Usage metrics
- **Function logs** - Error tracking
- **Database performance** - Query optimization
- **Storage analytics** - File usage

### Custom Analytics
- **MLflow tracking** - Model performance
- **User behavior** - Submission patterns
- **Environmental impact** - Waste metrics
- **Reward distribution** - sBTC statistics

## 🎯 Next Steps

1. **Set up Supabase project** - Create new project
2. **Run database migrations** - Set up schema
3. **Deploy edge functions** - ML inference pipeline
4. **Configure authentication** - Stacks Connect integration
5. **Test end-to-end** - Full workflow validation

---

**This Supabase-based backend provides a modern, serverless foundation for SatsVerdant with zero infrastructure management and built-in scalability.**
