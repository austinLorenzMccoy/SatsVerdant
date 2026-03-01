"use client"

import React from "react"

import { useState, useCallback } from "react"
import Image from "next/image"
import { Camera, Upload, X, Loader2, CheckCircle2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type UploadState = "idle" | "uploading" | "classifying" | "classified" | "submitted" | "error"

interface Classification {
  type: string
  confidence: number
  weight: string
  quality: string
  estimatedReward: string
}

export default function SubmitWastePage() {
  const [uploadState, setUploadState] = useState<UploadState>("idle")
  const [preview, setPreview] = useState<string | null>(null)
  const [classification, setClassification] = useState<Classification | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) return

    const reader = new FileReader()
    reader.onload = () => {
      setPreview(reader.result as string)
      simulateUploadAndClassify()
    }
    reader.readAsDataURL(file)
  }, [])

  const simulateUploadAndClassify = () => {
    setUploadState("uploading")
    
    // Simulate upload
    setTimeout(() => {
      setUploadState("classifying")
      
      // Simulate AI classification
      setTimeout(() => {
        setClassification({
          type: "Plastic",
          confidence: 95,
          weight: "~0.5 kg",
          quality: "Grade A",
          estimatedReward: "50 tokens",
        })
        setUploadState("classified")
      }, 2000)
    }, 1500)
  }

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragActive(false)
      if (e.dataTransfer.files[0]) {
        handleFile(e.dataTransfer.files[0])
      }
    },
    [handleFile]
  )

  const handleSubmit = () => {
    setUploadState("submitted")
  }

  const handleReset = () => {
    setUploadState("idle")
    setPreview(null)
    setClassification(null)
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div className="rounded-2xl border border-verdant-sage/20 bg-verdant-moss/10 p-6 lg:p-8">
        <div className="mb-6 border-b border-verdant-sage/10 pb-4">
          <h2 className="font-display text-xl font-bold text-verdant-paper">
            Submit Waste for Verification
          </h2>
          <p className="text-sm text-verdant-sage">
            Upload a photo of your recyclables to earn sBTC
          </p>
        </div>

        {/* Idle State - Upload Zone */}
        {uploadState === "idle" && (
          <div
            className={cn(
              "relative flex min-h-[300px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed transition-colors",
              dragActive
                ? "border-verdant-sats bg-verdant-sats/5"
                : "border-verdant-sage/30 hover:border-verdant-sprout hover:bg-verdant-sprout/5"
            )}
            onDragOver={(e) => {
              e.preventDefault()
              setDragActive(true)
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById("file-input")?.click()}
          >
            <input
              id="file-input"
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-verdant-sage/10">
                <Camera className="h-10 w-10 text-verdant-sage" />
              </div>
              <div>
                <p className="text-lg font-semibold text-verdant-paper">
                  Upload Your Recyclables
                </p>
                <p className="mt-1 text-sm text-verdant-sage">
                  Drag and drop or click to upload
                </p>
                <p className="mt-2 text-xs text-verdant-sage/70">
                  Supports plastic, paper, metal, or organic waste
                </p>
              </div>
              <Button className="mt-4 gap-2 bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon">
                <Upload className="h-4 w-4" />
                Choose Photo
              </Button>
            </div>
          </div>
        )}

        {/* Uploading/Classifying State */}
        {(uploadState === "uploading" || uploadState === "classifying") && (
          <div className="flex flex-col items-center gap-6 py-8">
            {preview && (
              <div className="relative h-48 w-48 overflow-hidden rounded-xl">
                <Image src={preview || "/placeholder.svg"} alt="Preview" fill className="object-cover" />
              </div>
            )}
            <div className="flex items-center gap-3 text-verdant-sats">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="text-lg font-medium">
                {uploadState === "uploading" ? "Uploading..." : "Analyzing with AI..."}
              </span>
            </div>
          </div>
        )}

        {/* Classified State */}
        {uploadState === "classified" && classification && (
          <div className="space-y-6">
            <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start">
              {preview && (
                <div className="relative h-40 w-40 shrink-0 overflow-hidden rounded-xl">
                  <Image src={preview || "/placeholder.svg"} alt="Preview" fill className="object-cover" />
                  <button
                    onClick={handleReset}
                    className="absolute -right-2 -top-2 flex h-8 w-8 items-center justify-center rounded-full bg-verdant-carbon text-verdant-paper shadow-lg transition-colors hover:bg-error"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}
              <div className="flex-1 space-y-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-success" />
                  <span className="font-semibold text-success">AI Classification Complete</span>
                </div>
                <div className="space-y-2 rounded-xl border border-verdant-sage/20 bg-verdant-carbon/50 p-4 font-mono text-sm">
                  <div className="flex justify-between">
                    <span className="text-verdant-sage">Type:</span>
                    <span className="text-verdant-paper">
                      {classification.type}{" "}
                      <span className="text-verdant-sats">
                        ({classification.confidence}% confidence)
                      </span>
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-verdant-sage">Weight:</span>
                    <span className="text-verdant-paper">{classification.weight}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-verdant-sage">Quality:</span>
                    <span className="text-verdant-paper">{classification.quality}</span>
                  </div>
                  <div className="mt-2 border-t border-verdant-sage/10 pt-2">
                    <div className="flex justify-between text-base">
                      <span className="text-verdant-sage">Est. Reward:</span>
                      <span className="font-bold text-verdant-sats">
                        {classification.estimatedReward}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex gap-4">
              <Button
                onClick={handleSubmit}
                className="flex-1 gap-2 bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon"
              >
                Submit for Validation
              </Button>
              <Button
                onClick={handleReset}
                variant="outline"
                className="border-verdant-sage/30 text-verdant-paper hover:bg-verdant-sage/10 bg-transparent"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Submitted State */}
        {uploadState === "submitted" && (
          <div className="flex flex-col items-center gap-6 py-8 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-success/20">
              <CheckCircle2 className="h-10 w-10 text-success" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-verdant-paper">
                Submission Successful!
              </h3>
              <p className="mt-2 text-verdant-sage">
                Your waste has been submitted for validation. You&apos;ll receive your
                reward once approved.
              </p>
              <p className="mt-4 font-mono text-sm text-verdant-sage/70">
                Tracking ID: SV-2024-00847
              </p>
            </div>
            <Button
              onClick={handleReset}
              className="mt-4 gap-2 bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon"
            >
              Submit Another
            </Button>
          </div>
        )}

        {/* Error State */}
        {uploadState === "error" && (
          <div className="flex flex-col items-center gap-6 py-8 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-error/20">
              <AlertCircle className="h-10 w-10 text-error" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-verdant-paper">Upload Failed</h3>
              <p className="mt-2 text-verdant-sage">
                Something went wrong. Please try again.
              </p>
            </div>
            <Button
              onClick={handleReset}
              className="mt-4 gap-2 bg-gradient-to-r from-verdant-sats to-verdant-gold text-verdant-carbon"
            >
              Try Again
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
