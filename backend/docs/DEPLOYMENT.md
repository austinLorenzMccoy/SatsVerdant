# SatsVerdant Backend Deployment Guide

## 🚀 Quick Start

### Prerequisites
- **Supabase CLI** - Install from https://supabase.com/docs/reference/cli
- **Node.js 18+** - For local development
- **API Keys** - Groq API, Radar.io API

### 1. Setup Local Environment

```bash
# Clone and navigate to backend
cd backend

# Make setup script executable
chmod +x scripts/setup.sh

# Run setup script
./scripts/setup.sh
```

### 2. Configure Environment Variables

Edit `supabase/functions/.env.local`:

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here
RADAR_API_KEY=your_radar_api_key_here
SUPABASE_URL=your_local_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_local_supabase_key

# Optional
OPENAI_API_KEY=your_openai_key
HUGGINGFACE_API_KEY=your_huggingface_key
```

### 3. Start Local Development

```bash
# Start Supabase services
supabase start

# Start Edge Functions
supabase functions serve --env-file supabase/functions/.env.local
```

## 🌐 API Endpoints

### Waste Classification
```bash
curl -X POST http://localhost:54321/functions/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "imageBase64": "base64_encoded_image",
    "userId": "user_uuid",
    "latitude": 30.2672,
    "longitude": -97.7431,
    "deviceInfo": {"device": "iPhone 14", "os": "iOS 16"}
  }'
```

### Health Check
```bash
curl http://localhost:54321/functions/v1/health
```

## 🗄️ Database Management

### Run Migrations
```bash
supabase db reset  # Reset and run all migrations
supabase db push   # Push new migrations
```

### Seed Data
```bash
supabase db seed
```

### View Database
```bash
supabase studio  # Opens database GUI
```

## 🔧 Edge Functions

### Deploy Function
```bash
# Deploy to local
supabase functions deploy classify --no-verify-jwt

# Deploy to production
supabase functions deploy classify
```

### Test Function
```bash
# Test locally
curl -i -X POST 'http://localhost:54321/functions/v1/classify' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"imageBase64":"data:image/jpeg;base64,...","userId":"test"}'
```

## 🌍 Production Deployment

### 1. Create Supabase Project
```bash
# Link to existing project
supabase link --project-ref your-project-ref

# Or create new project
supabase projects create
```

### 2. Deploy to Production
```bash
# Deploy database schema
supabase db push

# Deploy Edge Functions
supabase functions deploy classify

# Set production secrets
supabase secrets set GROQ_API_KEY=your_prod_key
supabase secrets set RADAR_API_KEY=your_prod_key
```

### 3. Configure Production
- Set up custom domain
- Configure CORS policies
- Set up monitoring and alerts
- Configure backup strategies

## 📊 Monitoring

### Local Logs
```bash
supabase logs --follow
```

### Function Logs
```bash
supabase functions logs classify --follow
```

### Database Metrics
- Visit Supabase Dashboard
- Check function performance
- Monitor database queries

## 🔐 Security

### Row Level Security (RLS)
All tables have RLS policies configured:
- Users can only access their own data
- Public read access for recycling locations
- Service role for admin operations

### API Keys
- **Anon Key** - Public client access
- **Service Role Key** - Server-side operations
- **Secret Keys** - Environment variables for functions

### Authentication
- Supabase Auth handles user management
- Stacks Connect integration for wallet authentication
- JWT tokens with automatic refresh

## 🧪 Testing

### Unit Tests
```bash
# Test Edge Functions
supabase functions test classify

# Test database
supabase db test
```

### Integration Tests
```bash
# Test full workflow
curl -X POST http://localhost:54321/functions/v1/classify \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

## 📈 Performance

### Optimization Tips
1. **Database Indexes** - All frequently queried columns are indexed
2. **Edge Functions** - Keep functions lightweight and fast
3. **Image Storage** - Use Supabase Storage CDN
4. **Caching** - Enable Redis caching for frequent queries

### Monitoring
- Track function execution time
- Monitor database query performance
- Set up alerts for high fraud scores
- Monitor API rate limits

## 🚨 Troubleshooting

### Common Issues

#### Function Not Found
```bash
# Check function status
supabase functions list

# Redeploy function
supabase functions deploy classify
```

#### Database Connection Error
```bash
# Check Supabase status
supabase status

# Restart services
supabase stop && supabase start
```

#### Environment Variables Missing
```bash
# Check secrets
supabase secrets list

# Set missing secrets
supabase secrets set GROQ_API_KEY=your_key
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=debug
supabase functions serve --debug
```

## 📚 Documentation

- [Supabase Docs](https://supabase.com/docs)
- [Edge Functions Guide](https://supabase.com/docs/guides/functions)
- [Database Guide](https://supabase.com/docs/guides/database)
- [Auth Guide](https://supabase.com/docs/guides/auth)

