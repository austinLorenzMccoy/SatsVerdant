-- SatsVerdant Database Schema
-- PostgreSQL + PostGIS with Supabase RLS policies

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  stacks_address TEXT UNIQUE,
  email TEXT UNIQUE,
  username TEXT UNIQUE,
  profile_image_url TEXT,
  total_submissions INTEGER DEFAULT 0,
  total_rewards DECIMAL(20, 8) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Recycling locations table
CREATE TABLE IF NOT EXISTS public.recycling_locations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  address TEXT,
  coordinates GEOGRAPHY(POINT, 4326) NOT NULL,
  waste_types TEXT[] DEFAULT '{}',
  radar_fence_id TEXT,
  is_active BOOLEAN DEFAULT true,
  verified BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Submissions table
CREATE TABLE IF NOT EXISTS public.submissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  waste_type TEXT NOT NULL CHECK (waste_type IN ('plastic','paper','metal','organic','glass')),
  ai_confidence DECIMAL(3,2) NOT NULL CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
  quality_grade CHAR(1) NOT NULL CHECK (quality_grade IN ('A','B','C','D')),
  estimated_kg DECIMAL(8,2),
  image_url TEXT NOT NULL,
  image_hash TEXT NOT NULL,
  image_hashes JSONB, -- perceptual hashes (phash, dhash, whash)
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  location_id UUID REFERENCES public.recycling_locations(id),
  fraud_score DECIMAL(3,2) DEFAULT 0 CHECK (fraud_score >= 0 AND fraud_score <= 1),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending','approved','flagged','rejected')),
  reward_amount DECIMAL(20, 8),
  reward_tx_id TEXT,
  device_info JSONB,
  ai_metadata JSONB, -- model version, inference time, etc.
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Reward queue table
CREATE TABLE IF NOT EXISTS public.reward_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  submission_id UUID REFERENCES public.submissions(id) ON DELETE CASCADE,
  waste_type TEXT NOT NULL,
  amount DECIMAL(20, 8) NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending','processing','completed','failed')),
  stacks_tx_id TEXT,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  processed_at TIMESTAMPTZ
);

-- Fraud flags table
CREATE TABLE IF NOT EXISTS public.fraud_flags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  submission_id UUID REFERENCES public.submissions(id) ON DELETE CASCADE,
  flag_type TEXT NOT NULL CHECK (flag_type IN ('duplicate_image','rapid_submission','low_confidence','location_spoofing')),
  severity TEXT NOT NULL CHECK (severity IN ('low','medium','high','critical')),
  details JSONB,
  resolved BOOLEAN DEFAULT false,
  resolved_by UUID REFERENCES public.users(id),
  resolved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- User metrics table
CREATE TABLE IF NOT EXISTS public.user_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  submissions_count INTEGER DEFAULT 0,
  waste_kg DECIMAL(8,2) DEFAULT 0,
  rewards_earned DECIMAL(20, 8) DEFAULT 0,
  quality_score DECIMAL(3,2) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_auth_id ON public.users(auth_id);
CREATE INDEX IF NOT EXISTS idx_users_stacks_address ON public.users(stacks_address);
CREATE INDEX IF NOT EXISTS idx_recycling_locations_geo ON public.recycling_locations USING GIST(coordinates);
CREATE INDEX IF NOT EXISTS idx_recycling_locations_active ON public.recycling_locations(is_active);
CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON public.submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON public.submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_waste_type ON public.submissions(waste_type);
CREATE INDEX IF NOT EXISTS idx_submissions_created_at ON public.submissions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_image_hash ON public.submissions(image_hash);
CREATE INDEX IF NOT EXISTS idx_submissions_coordinates ON public.submissions USING GIST(ST_MakePoint(longitude, latitude));
CREATE INDEX IF NOT EXISTS idx_reward_queue_status ON public.reward_queue(status);
CREATE INDEX IF NOT EXISTS idx_reward_queue_user_id ON public.reward_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_fraud_flags_user_id ON public.fraud_flags(user_id);
CREATE INDEX IF NOT EXISTS idx_fraud_flags_resolved ON public.fraud_flags(resolved);
CREATE INDEX IF NOT EXISTS idx_user_metrics_user_date ON public.user_metrics(user_id, date);

-- Functions for spatial queries
CREATE OR REPLACE FUNCTION public.nearby_recycling_points(
  user_lat DECIMAL, 
  user_lng DECIMAL, 
  radius_meters INTEGER DEFAULT 100
)
RETURNS TABLE(
  id UUID,
  name TEXT,
  address TEXT,
  distance_meters DECIMAL,
  waste_types TEXT[]
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    rl.id,
    rl.name,
    rl.address,
    ST_Distance(rl.coordinates, ST_MakePoint(user_lng, user_lat)::GEOGRAPHY) AS distance_meters,
    rl.waste_types
  FROM public.recycling_locations rl
  WHERE ST_DWithin(
    rl.coordinates, 
    ST_MakePoint(user_lng, user_lat)::GEOGRAPHY, 
    radius_meters
  )
    AND rl.is_active = true
  ORDER BY distance_meters;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update user metrics
CREATE OR REPLACE FUNCTION public.update_user_metrics()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_metrics (user_id, date, submissions_count, waste_kg, rewards_earned, quality_score)
  VALUES (
    NEW.user_id,
    CURRENT_DATE,
    1,
    COALESCE(NEW.estimated_kg, 0),
    COALESCE(NEW.reward_amount, 0),
    CASE NEW.quality_grade
      WHEN 'A' THEN 1.0
      WHEN 'B' THEN 0.8
      WHEN 'C' THEN 0.6
      ELSE 0.4
    END
  )
  ON CONFLICT (user_id, date)
  DO UPDATE SET
    submissions_count = user_metrics.submissions_count + 1,
    waste_kg = user_metrics.waste_kg + COALESCE(NEW.estimated_kg, 0),
    rewards_earned = user_metrics.rewards_earned + COALESCE(NEW.reward_amount, 0),
    quality_score = (
      user_metrics.quality_score * user_metrics.submissions_count +
      CASE NEW.quality_grade
        WHEN 'A' THEN 1.0
        WHEN 'B' THEN 0.8
        WHEN 'C' THEN 0.6
        ELSE 0.4
      END
    ) / (user_metrics.submissions_count + 1),
    updated_at = now();
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update user metrics
CREATE TRIGGER trigger_update_user_metrics
  AFTER INSERT ON public.submissions
  FOR EACH ROW
  EXECUTE FUNCTION public.update_user_metrics();

-- Function to update user totals
CREATE OR REPLACE FUNCTION public.update_user_totals()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE public.users SET
      total_submissions = total_submissions + 1,
      total_rewards = total_rewards + COALESCE(NEW.reward_amount, 0),
      updated_at = now()
    WHERE id = NEW.user_id;
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    IF OLD.reward_amount IS DISTINCT FROM NEW.reward_amount THEN
      UPDATE public.users SET
        total_rewards = total_rewards + (COALESCE(NEW.reward_amount, 0) - COALESCE(OLD.reward_amount, 0)),
        updated_at = now()
      WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update user totals
CREATE TRIGGER trigger_update_user_totals
  AFTER INSERT OR UPDATE ON public.submissions
  FOR EACH ROW
  EXECUTE FUNCTION public.update_user_totals();

-- Row Level Security (RLS) Policies
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reward_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fraud_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_metrics ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON public.users
  FOR SELECT USING (auth.uid() = auth_id);

CREATE POLICY "Users can update own profile" ON public.users
  FOR UPDATE USING (auth.uid() = auth_id);

-- Submissions policies
CREATE POLICY "Users can view own submissions" ON public.submissions
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert own submissions" ON public.submissions
  FOR INSERT WITH CHECK (user_id = auth.uid());

-- Reward queue policies
CREATE POLICY "Users can view own rewards" ON public.reward_queue
  FOR SELECT USING (user_id = auth.uid());

-- Fraud flags policies
CREATE POLICY "Users can view own fraud flags" ON public.fraud_flags
  FOR SELECT USING (user_id = auth.uid());

-- User metrics policies
CREATE POLICY "Users can view own metrics" ON public.user_metrics
  FOR SELECT USING (user_id = auth.uid());

-- Public read access for recycling locations
CREATE POLICY "Recycling locations are publicly readable" ON public.recycling_locations
  FOR SELECT USING (is_active = true);

-- Grant permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON public.recycling_locations TO anon, authenticated;
GRANT ALL ON public.users TO authenticated;
GRANT ALL ON public.submissions TO authenticated;
GRANT ALL ON public.reward_queue TO authenticated;
GRANT ALL ON public.fraud_flags TO authenticated;
GRANT ALL ON public.user_metrics TO authenticated;
GRANT EXECUTE ON FUNCTION public.nearby_recycling_points TO anon, authenticated;
