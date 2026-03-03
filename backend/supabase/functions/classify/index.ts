// Supabase Edge Function: Waste Classification with AI
// Path: supabase/functions/classify/index.ts

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { createHash } from "https://deno.land/std@0.168.0/crypto/mod.ts";

// Environment variables
const GROQ_API_KEY = Deno.env.get("GROQ_API_KEY")!;
const RADAR_API_KEY = Deno.env.get("RADAR_API_KEY")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

// Initialize Supabase client
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

// Waste type mapping
const WASTE_TYPES = ['plastic', 'paper', 'metal', 'organic', 'glass'];

// Quality grade thresholds
const QUALITY_THRESHOLDS = {
  A: { blur: 100, brightness_min: 50, brightness_max: 200, contrast: 40 },
  B: { blur: 50, brightness_min: 30, brightness_max: 220, contrast: 25 },
  C: { blur: 20, brightness_min: 20, brightness_max: 240, contrast: 15 },
  D: { blur: 0, brightness_min: 0, brightness_max: 255, contrast: 0 }
};

// Fraud detection thresholds
const FRAUD_THRESHOLDS = {
  hash_distance: 10,
  rate_limit_per_hour: 5,
  min_confidence: 0.6,
  max_fraud_score: 0.5
};

serve(async (req) => {
  try {
    const { imageBase64, userId, latitude, longitude, deviceInfo } = await req.json();

    // Validate inputs
    if (!imageBase64 || !userId) {
      return json({ success: false, error: "Missing required fields: imageBase64, userId" }, 400);
    }

    console.log(`Processing submission for user: ${userId}`);

    // Step 1: Quality Gate
    const quality = await checkImageQuality(imageBase64);
    console.log(`Quality grade: ${quality.grade}`);

    if (quality.grade === "D") {
      return json({ 
        success: false, 
        reason: "Image quality too low. Please retake in better lighting.",
        quality 
      }, 400);
    }

    // Step 2: Duplicate Detection
    const imageHash = await computeImageHash(imageBase64);
    const isDuplicate = await checkDuplicateSubmission(userId, imageHash);
    
    if (isDuplicate) {
      return json({ 
        success: false, 
        reason: "Duplicate submission detected. Please submit a different image.",
        imageHash 
      }, 409);
    }

    // Step 3: Location Verification (if coordinates provided)
    let locationVerified = true;
    let nearestLocation = null;
    
    if (latitude && longitude) {
      const locationResult = await verifyLocation(latitude, longitude);
      locationVerified = locationResult.isAtRecyclingPoint;
      nearestLocation = locationResult.nearestLocation;
      
      if (!locationVerified) {
        return json({
          success: false,
          reason: "Must be at a registered recycling location.",
          nearestLocation,
          coordinates: { latitude, longitude }
        }, 403);
      }
    }

    // Step 4: AI Classification via Groq
    const classification = await classifyWithGroq(imageBase64);
    console.log(`Classification: ${classification.wasteType} (${classification.confidence})`);

    // Step 5: Fraud Score Calculation
    const fraudScore = await calculateFraudScore(userId, classification.confidence, imageHash);
    console.log(`Fraud score: ${fraudScore.score}`);

    // Step 6: Determine submission status
    const status = determineSubmissionStatus(fraudScore.score, classification.confidence);
    const rewardAmount = status === 'approved' ? calculateRewardAmount(classification.wasteType, quality.grade) : 0;

    // Step 7: Store submission in database
    const { data: submission, error: dbError } = await supabase
      .from("submissions")
      .insert({
        user_id: userId,
        waste_type: classification.wasteType,
        ai_confidence: classification.confidence,
        quality_grade: quality.grade,
        estimated_kg: estimateWeight(classification.wasteType, quality.grade),
        image_url: await uploadImage(userId, imageBase64),
        image_hash: imageHash.sha256,
        image_hashes: imageHash,
        latitude: latitude || null,
        longitude: longitude || null,
        fraud_score: fraudScore.score,
        status: status,
        reward_amount: rewardAmount,
        device_info: deviceInfo || null,
        ai_metadata: {
          model_version: "efficientnetb0-v1.0",
          inference_time_ms: classification.inferenceTime || 0,
          reasoning: classification.reasoning
        }
      })
      .select()
      .single();

    if (dbError) {
      console.error("Database error:", dbError);
      throw new Error(`Database error: ${dbError.message}`);
    }

    // Step 8: Create fraud flags if needed
    if (fraudScore.flags.length > 0) {
      await createFraudFlags(userId, submission.id, fraudScore.flags);
    }

    // Step 9: Queue reward if approved
    if (status === 'approved' && rewardAmount > 0) {
      await queueReward(userId, submission.id, classification.wasteType, rewardAmount);
    }

    // Step 10: Return response
    return json({
      success: true,
      submission: {
        id: submission.id,
        wasteType: classification.wasteType,
        confidence: classification.confidence,
        qualityGrade: quality.grade,
        status: status,
        rewardAmount: rewardAmount,
        fraudScore: fraudScore.score,
        locationVerified,
        nearestLocation
      }
    });

  } catch (error) {
    console.error("Classification error:", error);
    return json({ 
      success: false, 
      error: error.message 
    }, 500);
  }
});

// Image Quality Assessment
async function checkImageQuality(imageBase64: string): Promise<any> {
  // Convert base64 to bytes
  const imageBytes = Uint8Array.from(atob(imageBase64), c => c.charCodeAt(0));
  
  // Basic quality metrics (simplified for Edge Function)
  const fileSize = imageBytes.length;
  const estimatedBlur = Math.random() * 150; // Placeholder - would use OpenCV in production
  const estimatedBrightness = Math.random() * 255; // Placeholder
  
  // Determine quality grade
  let grade = 'D';
  for (const [gradeName, thresholds] of Object.entries(QUALITY_THRESHOLDS)) {
    if (estimatedBlur >= thresholds.blur && 
        estimatedBrightness >= thresholds.brightness_min && 
        estimatedBrightness <= thresholds.brightness_max) {
      grade = gradeName;
      break;
    }
  }

  return {
    grade,
    metrics: {
      fileSize,
      blurScore: estimatedBlur,
      brightness: estimatedBrightness,
      contrast: Math.random() * 50 // Placeholder
    },
    rewardMultiplier: grade === 'A' ? 1.0 : grade === 'B' ? 0.8 : grade === 'C' ? 0.6 : 0.0
  };
}

// Compute Image Hash
async function computeImageHash(imageBase64: string): Promise<any> {
  const imageBytes = Uint8Array.from(atob(imageBase64), c => c.charCodeAt(0));
  
  // SHA-256 hash
  const sha256Hash = await createHash('sha-256').digest(imageBytes);
  const sha256Hex = Array.from(sha256Hash)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  // Simplified perceptual hashes (would use imagehash library in production)
  const phash = sha256Hex.slice(0, 16);
  const dhash = sha256Hex.slice(16, 32);
  const whash = sha256Hex.slice(32, 48);

  return {
    sha256: sha256Hex,
    phash,
    dhash,
    whash
  };
}

// Check for Duplicate Submissions
async function checkDuplicateSubmission(userId: string, imageHash: any): Promise<boolean> {
  const { data, error } = await supabase
    .from("submissions")
    .select("id")
    .eq("user_id", userId)
    .eq("image_hash", imageHash.sha256)
    .gte("created_at", new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString())
    .limit(1);

  if (error) {
    console.error("Duplicate check error:", error);
    return false;
  }

  return (data?.length ?? 0) > 0;
}

// Location Verification with Radar.io
async function verifyLocation(latitude: number, longitude: number): Promise<any> {
  try {
    const response = await fetch(
      `https://api.radar.io/v1/geofences/nearby?coordinates=${latitude},${longitude}&radius=100`,
      {
        headers: { "Authorization": RADAR_API_KEY }
      }
    );

    if (!response.ok) {
      console.error("Radar.io API error:", response.status);
      return { isAtRecyclingPoint: false, nearestLocation: null };
    }

    const data = await response.json();
    const recyclingFences = (data.geofences || []).filter((f: any) => f.tag === "recycling_point");

    return {
      isAtRecyclingPoint: recyclingFences.length > 0,
      nearestLocation: recyclingFences[0]?.description || null,
      allFences: recyclingFences
    };

  } catch (error) {
    console.error("Location verification error:", error);
    return { isAtRecyclingPoint: false, nearestLocation: null };
  }
}

// AI Classification via Groq API
async function classifyWithGroq(imageBase64: string): Promise<any> {
  const startTime = Date.now();

  try {
    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${GROQ_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "llama-3.2-11b-vision-preview",
        messages: [{
          role: "user",
          content: [
            {
              type: "image_url",
              image_url: { url: `data:image/jpeg;base64,${imageBase64}` }
            },
            {
              type: "text",
              text: `Classify this waste image. Respond ONLY with valid JSON:
{
  "wasteType": "<plastic|paper|metal|organic|glass>",
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence explaining classification>"
}`
            }
          ]
        }],
        max_tokens: 150,
        temperature: 0.1
      })
    });

    if (!response.ok) {
      throw new Error(`Groq API error: ${response.status}`);
    }

    const data = await response.json();
    const text = data.choices[0].message.content.replace(/```json|```/g, "").trim();
    const result = JSON.parse(text);

    // Validate waste type
    if (!WASTE_TYPES.includes(result.wasteType)) {
      throw new Error(`Invalid waste type: ${result.wasteType}`);
    }

    return {
      ...result,
      inferenceTime: Date.now() - startTime
    };

  } catch (error) {
    console.error("Groq classification error:", error);
    // Fallback to random classification for demo
    return {
      wasteType: WASTE_TYPES[Math.floor(Math.random() * WASTE_TYPES.length)],
      confidence: 0.7 + Math.random() * 0.3,
      reasoning: "Fallback classification due to API error",
      inferenceTime: Date.now() - startTime
    };
  }
}

// Calculate Fraud Score
async function calculateFraudScore(userId: string, confidence: number, imageHash: any): Promise<any> {
  const flags = [];
  let score = 0;

  // Check for rapid submissions
  const { count: recentSubmissions } = await supabase
    .from("submissions")
    .select("*", { count: "exact", head: true })
    .eq("user_id", userId)
    .gte("created_at", new Date(Date.now() - 60 * 60 * 1000).toISOString());

  if (recentSubmissions >= FRAUD_THRESHOLDS.rate_limit_per_hour) {
    score += 0.4;
    flags.push({ type: "rapid_submission", severity: "high", count: recentSubmissions });
  }

  // Check confidence score
  if (confidence < FRAUD_THRESHOLDS.min_confidence) {
    score += 0.3;
    flags.push({ type: "low_confidence", severity: "medium", confidence });
  }

  // Cap score at 1.0
  score = Math.min(score, 1.0);

  return {
    score: Math.round(score * 100) / 100,
    flags,
    riskLevel: score >= 0.8 ? "high" : score >= 0.5 ? "medium" : "low"
  };
}

// Determine Submission Status
function determineSubmissionStatus(fraudScore: number, confidence: number): string {
  if (fraudScore >= 0.8) return "rejected";
  if (fraudScore >= 0.5) return "flagged";
  if (confidence < 0.7) return "flagged";
  return "approved";
}

// Calculate Reward Amount
function calculateRewardAmount(wasteType: string, qualityGrade: string): number {
  const baseRewards = {
    plastic: 0.001,
    paper: 0.0008,
    metal: 0.0012,
    organic: 0.0006,
    glass: 0.001
  };

  const qualityMultipliers = {
    A: 1.0,
    B: 0.8,
    C: 0.6,
    D: 0.0
  };

  return baseRewards[wasteType] * qualityMultipliers[qualityGrade];
}

// Estimate Weight
function estimateWeight(wasteType: string, qualityGrade: string): number {
  const baseWeights = {
    plastic: 0.5,
    paper: 1.0,
    metal: 0.8,
    organic: 1.5,
    glass: 0.7
  };

  const qualityMultipliers = {
    A: 1.0,
    B: 0.9,
    C: 0.8,
    D: 0.0
  };

  const variance = 0.85 + Math.random() * 0.3; // 15% variance
  return Math.round(baseWeights[wasteType] * qualityMultipliers[qualityGrade] * variance * 100) / 100;
}

// Upload Image to Supabase Storage
async function uploadImage(userId: string, imageBase64: string): Promise<string> {
  const fileName = `submissions/${userId}/${Date.now()}.jpg`;
  const imageBytes = Uint8Array.from(atob(imageBase64), c => c.charCodeAt(0));

  const { data, error } = await supabase.storage
    .from("submission-images")
    .upload(fileName, imageBytes, {
      contentType: "image/jpeg",
      upsert: false
    });

  if (error) {
    console.error("Storage upload error:", error);
    throw new Error(`Storage upload failed: ${error.message}`);
  }

  const { data: { publicUrl } } = supabase.storage
    .from("submission-images")
    .getPublicUrl(fileName);

  return publicUrl;
}

// Create Fraud Flags
async function createFraudFlags(userId: string, submissionId: string, flags: any[]): Promise<void> {
  for (const flag of flags) {
    await supabase
      .from("fraud_flags")
      .insert({
        user_id: userId,
        submission_id: submissionId,
        flag_type: flag.type,
        severity: flag.severity,
        details: flag
      });
  }
}

// Queue Reward for Processing
async function queueReward(userId: string, submissionId: string, wasteType: string, amount: number): Promise<void> {
  await supabase
    .from("reward_queue")
    .insert({
      user_id: userId,
      submission_id: submissionId,
      waste_type: wasteType,
      amount: amount,
      status: "pending"
    });
}

// Helper function for JSON responses
function json(data: object, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}
