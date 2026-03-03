-- Seed data for SatsVerdant development
-- This file populates the database with initial data for testing

-- Insert sample recycling locations
INSERT INTO public.recycling_locations (name, address, coordinates, waste_types, radar_fence_id, is_active, verified) VALUES
('EcoCenter Downtown', '123 Main St, Austin, TX 78701', ST_MakePoint(-97.7431, 30.2672)::geography, ARRAY['plastic', 'paper', 'metal', 'glass'], 'fence_001', true, true),
('Green Recycling Hub', '456 Oak Ave, Austin, TX 78704', ST_MakePoint(-97.7514, 30.2480)::geography, ARRAY['plastic', 'paper', 'metal', 'organic', 'glass'], 'fence_002', true, true),
('City Waste Management', '789 Pine Rd, Austin, TX 78705', ST_MakePoint(-97.7311, 30.3076)::geography, ARRAY['plastic', 'paper', 'metal'], 'fence_003', true, true),
('Community Recycling Center', '321 Elm St, Austin, TX 78703', ST_MakePoint(-97.7407, 30.2837)::geography, ARRAY['plastic', 'paper', 'organic'], 'fence_004', true, true),
('Sustainable Solutions', '654 Maple Dr, Austin, TX 78756', ST_MakePoint(-97.7206, 30.3265)::geography, ARRAY['metal', 'glass', 'organic'], 'fence_005', true, true);

-- Insert sample users (these would normally be created through auth)
-- Note: In production, users are created through Supabase Auth
INSERT INTO public.users (auth_id, stacks_address, email, username, profile_image_url, total_submissions, total_rewards) VALUES
('00000000-0000-0000-0000-000000000001', 'ST1PQHQKV0RJXZFYRNKKF7K0DQEW8KPPVSVNSVDV', 'alice@example.com', 'alice_recycler', 'https://api.dicebear.com/7.x/avataaars/svg?seed=alice', 15, 0.015),
('00000000-0000-0000-0000-000000000002', 'ST2JHGZY0RJXZFYRNKKF7K0DQEW8KPPVSVNSVDV', 'bob@example.com', 'bob_green', 'https://api.dicebear.com/7.x/avataaars/svg?seed=bob', 8, 0.008),
('00000000-0000-0000-0000-000000000003', 'ST3XYZ1230RJXZFYRNKKF7K0DQEW8KPPVSVNSVDV', 'charlie@example.com', 'charlie_eco', 'https://api.dicebear.com/7.x/avataaars/svg?seed=charlie', 23, 0.023);

-- Insert sample submissions for testing
INSERT INTO public.submissions (
  user_id, waste_type, ai_confidence, quality_grade, estimated_kg, 
  image_url, image_hash, latitude, longitude, location_id, 
  fraud_score, status, reward_amount, device_info, ai_metadata
) VALUES
-- Alice's submissions
((SELECT id FROM public.users WHERE username = 'alice_recycler'), 'plastic', 0.92, 'A', 0.5, 'https://example.com/image1.jpg', 'hash1', 30.2672, -97.7431, (SELECT id FROM public.recycling_locations WHERE name = 'EcoCenter Downtown'), 0.1, 'approved', 0.001, '{"device": "iPhone 14", "os": "iOS 16"}', '{"model_version": "efficientnetb0-v1.0", "inference_time_ms": 45}'),
((SELECT id FROM public.users WHERE username = 'alice_recycler'), 'paper', 0.88, 'B', 0.9, 'https://example.com/image2.jpg', 'hash2', 30.2672, -97.7431, (SELECT id FROM public.recycling_locations WHERE name = 'EcoCenter Downtown'), 0.2, 'approved', 0.00064, '{"device": "iPhone 14", "os": "iOS 16"}', '{"model_version": "efficientnetb0-v1.0", "inference_time_ms": 42}'),
((SELECT id FROM public.users WHERE username = 'alice_recycler'), 'metal', 0.95, 'A', 0.8, 'https://example.com/image3.jpg', 'hash3', 30.2672, -97.7431, (SELECT id FROM public.recycling_locations WHERE name = 'EcoCenter Downtown'), 0.0, 'approved', 0.0012, '{"device": "iPhone 14", "os": "iOS 16"}', '{"model_version": "efficientnetb0-v1.0", "inference_time_ms": 48}'),

-- Bob's submissions
((SELECT id FROM public.users WHERE username = 'bob_green'), 'organic', 0.85, 'B', 1.2, 'https://example.com/image4.jpg', 'hash4', 30.2480, -97.7514, (SELECT id FROM public.recycling_locations WHERE name = 'Green Recycling Hub'), 0.15, 'approved', 0.00048, '{"device": "Samsung Galaxy S23", "os": "Android 13"}', '{"model_version": "efficientnetb0-v1.0", "inference_time_ms": 50}'),
((SELECT id FROM public.users WHERE username = 'bob_green'), 'glass', 0.91, 'A', 0.7, 'https://example.com/image5.jpg', 'hash5', 30.2480, -97.7514, (SELECT id FROM public.recycling_locations WHERE name = 'Green Recycling Hub'), 0.05, 'approved', 0.001, '{"device": "Samsung Galaxy S23", "os": "Android 13"}', '{"model_version": "efficientnetb0-v1.0", "inference_time_ms": 44}'),

-- Charlie's submissions
((SELECT id FROM public.users WHERE username = 'charlie_eco'), 'plastic', 0.78, 'C', 0.4, 'https://example.com/image6.jpg', 'hash6', 30.2837, -97.7407, (SELECT id FROM public.recycling_locations WHERE name = 'Community Recycling Center'), 0.3, 'flagged', 0.00048, '{"device": "Google Pixel 7", "os": "Android 14"}', '{"model_version": "efficientnetb0-v1.0", "inference_time_ms": 52}'),
((SELECT id FROM public.users WHERE username = 'charlie_eco'), 'paper', 0.93, 'A', 1.1, 'https://example.com/image7.jpg', 'hash7', 30.2837, -97.7407, (SELECT id FROM public.recycling_locations WHERE name = 'Community Recycling Center'), 0.0, 'approved', 0.0008, '{"device": "Google Pixel 7", "os": "Android 14"}', '{"model_version": "efficientnetb0-v1.0", "inference_time_ms": 43}');

-- Insert sample reward queue entries
INSERT INTO public.reward_queue (user_id, submission_id, waste_type, amount, status) VALUES
((SELECT id FROM public.users WHERE username = 'alice_recycler'), (SELECT id FROM public.submissions WHERE image_hash = 'hash1'), 'plastic', 0.001, 'completed'),
((SELECT id FROM public.users WHERE username = 'alice_recycler'), (SELECT id FROM public.submissions WHERE image_hash = 'hash2'), 'paper', 0.00064, 'completed'),
((SELECT id FROM public.users WHERE username = 'alice_recycler'), (SELECT id FROM public.submissions WHERE image_hash = 'hash3'), 'metal', 0.0012, 'completed'),
((SELECT id FROM public.users WHERE username = 'bob_green'), (SELECT id FROM public.submissions WHERE image_hash = 'hash4'), 'organic', 0.00048, 'completed'),
((SELECT id FROM public.users WHERE username = 'bob_green'), (SELECT id FROM public.submissions WHERE image_hash = 'hash5'), 'glass', 0.001, 'completed'),
((SELECT id FROM public.users WHERE username = 'charlie_eco'), (SELECT id FROM public.submissions WHERE image_hash = 'hash7'), 'paper', 0.0008, 'pending');

-- Insert sample fraud flags for testing
INSERT INTO public.fraud_flags (user_id, submission_id, flag_type, severity, details, resolved) VALUES
((SELECT id FROM public.users WHERE username = 'charlie_eco'), (SELECT id FROM public.submissions WHERE image_hash = 'hash6'), 'low_confidence', 'medium', '{"confidence": 0.78, "threshold": 0.8}', false);

-- Insert sample user metrics
INSERT INTO public.user_metrics (user_id, date, submissions_count, waste_kg, rewards_earned, quality_score) VALUES
((SELECT id FROM public.users WHERE username = 'alice_recycler'), CURRENT_DATE - INTERVAL '7 days', 3, 2.2, 0.00284, 0.93),
((SELECT id FROM public.users WHERE username = 'bob_green'), CURRENT_DATE - INTERVAL '5 days', 2, 1.9, 0.00148, 0.88),
((SELECT id FROM public.users WHERE username = 'charlie_eco'), CURRENT_DATE - INTERVAL '3 days', 2, 1.5, 0.00128, 0.85);

-- Update user totals to match seed data
UPDATE public.users SET 
  total_submissions = (SELECT COUNT(*) FROM public.submissions WHERE user_id = users.id),
  total_rewards = (SELECT COALESCE(SUM(reward_amount), 0) FROM public.submissions WHERE user_id = users.id AND status = 'approved'),
  updated_at = now();

-- Create storage bucket for submission images
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types) 
VALUES ('submission-images', 'submission-images', true, 10485760, ARRAY['image/jpeg', 'image/png', 'image/webp'])
ON CONFLICT (id) DO NOTHING;

-- Set up storage policies
CREATE POLICY "Users can upload submission images" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'submission-images' AND 
    auth.role() = 'authenticated' AND
    (storage.foldername(name))[1] = auth.uid()::text
  );

CREATE POLICY "Users can view own submission images" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'submission-images' AND 
    (storage.foldername(name))[1] = auth.uid()::text
  );

CREATE POLICY "Images are publicly readable" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'submission-images'
  );

COMMIT;
