"use client";

import { useState, useCallback, useMemo } from "react";
import { useDropzone } from "react-dropzone";
import { ReactCompareSlider, ReactCompareSliderImage } from "react-compare-slider";
import {
  Upload,
  Lock,
  Layers,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  Download,
  Eye,
  EyeOff,
  Sparkles,
  FileText,
  FileUp,
  RefreshCw,
  BarChart3,
} from "lucide-react";
import { toast } from "sonner";
import { embedPayload, type EmbedResponse } from "@/lib/api-client";
import { formatBytes, formatNumber } from "@/lib/utils";

// Max 16 Megapixels
const MAX_PIXELS = 16_000_000;
const SALT_BITS = 128; // Sequential salt header prefix

export default function EmbedPage() {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // Step 1: Cover Image
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [coverPreview, setCoverPreview] = useState<string | null>(null);
  const [coverDimensions, setCoverDimensions] = useState<{ width: number; height: number; mp: number } | null>(null);
  const [coverError, setCoverError] = useState<string | null>(null);

  // Step 2: Payload
  const [payloadType, setPayloadType] = useState<"text" | "file">("text");
  const [payloadText, setPayloadText] = useState<string>("");
  const [payloadFile, setPayloadFile] = useState<File | null>(null);

  // Step 3: Security & Method
  const [password, setPassword] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [method, setMethod] = useState<"lsb_matching" | "lsb_replacement">("lsb_matching");

  // Step 4: Loading & Result
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [result, setResult] = useState<EmbedResponse | null>(null);

  // Calculate cover capacity
  const maxCapacityBytes = useMemo(() => {
    if (!coverDimensions) return 0;
    // 3 channels (RGB) x width x height bits, minus 128-bit salt, divided by 8
    const totalSlots = coverDimensions.width * coverDimensions.height * 3;
    const availableSlots = totalSlots - SALT_BITS;
    return availableSlots > 0 ? Math.floor(availableSlots / 8) : 0;
  }, [coverDimensions]);

  // Calculate payload size
  const payloadSizeBytes = useMemo(() => {
    if (payloadType === "text") {
      return new TextEncoder().encode(payloadText).length;
    }
    return payloadFile ? payloadFile.size : 0;
  }, [payloadType, payloadText, payloadFile]);

  const capacityRatio = useMemo(() => {
    if (maxCapacityBytes === 0) return 0;
    return (payloadSizeBytes / maxCapacityBytes) * 100;
  }, [payloadSizeBytes, maxCapacityBytes]);

  const isPayloadTooLarge = payloadSizeBytes > maxCapacityBytes && maxCapacityBytes > 0;

  // Password Strength Meter
  const passwordStrength = useMemo(() => {
    if (!password) return { score: 0, label: "Empty", color: "bg-white/10" };
    let score = 0;
    if (password.length >= 8) score += 1;
    if (password.length >= 14) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;

    if (score <= 2) return { score: 1, label: "Weak", color: "bg-rose-500" };
    if (score <= 3) return { score: 2, label: "Moderate", color: "bg-amber-500" };
    if (score <= 4) return { score: 3, label: "Strong", color: "bg-teal-liquid" };
    return { score: 4, label: "Hardened", color: "bg-mint" };
  }, [password]);

  // Handle Cover Drop
  const onCoverDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setCoverError(null);
    setCoverFile(file);

    const objectUrl = URL.createObjectURL(file);
    setCoverPreview(objectUrl);

    // Measure dimensions
    const img = new Image();
    img.onload = () => {
      const w = img.naturalWidth;
      const h = img.naturalHeight;
      const pixels = w * h;
      const mp = parseFloat((pixels / 1_000_000).toFixed(2));

      if (pixels > MAX_PIXELS) {
        setCoverError(`Image exceeds maximum size of 16MP (${w}x${h} = ${mp}MP). Please select a smaller image.`);
        setCoverDimensions(null);
        return;
      }
      setCoverDimensions({ width: w, height: h, mp });
    };
    img.onerror = () => {
      setCoverError("Unable to decode cover image. Ensure file is an uncorrupted image.");
    };
    img.src = objectUrl;
  }, []);

  const { getRootProps: getCoverRootProps, getInputProps: getCoverInputProps, isDragActive: isCoverDragActive } =
    useDropzone({
      onDrop: onCoverDrop,
      accept: {
        "image/png": [".png"],
        "image/bmp": [".bmp"],
        "image/tiff": [".tiff", ".tif"],
      },
      multiple: false,
    });

  // Handle Payload File Drop
  const onPayloadFileDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) setPayloadFile(file);
  }, []);

  const { getRootProps: getPayloadRootProps, getInputProps: getPayloadInputProps, isDragActive: isPayloadDragActive } =
    useDropzone({
      onDrop: onPayloadFileDrop,
      multiple: false,
    });

  // Handle Embedding Submit
  const handleEmbedSubmit = async () => {
    if (!coverFile) {
      toast.error("Please provide a cover image.");
      return;
    }
    if (payloadSizeBytes === 0) {
      toast.error("Payload cannot be empty.");
      return;
    }
    if (isPayloadTooLarge) {
      toast.error("Payload exceeds maximum cover capacity.");
      return;
    }
    if (!password) {
      toast.error("Please provide an encryption password.");
      return;
    }

    setIsSubmitting(true);
    const toastId = toast.loading("Deriving keys (Scrypt) and embedding secret bits...");

    try {
      const formData = new FormData();
      formData.append("cover_file", coverFile);
      formData.append("password", password);
      formData.append("method", method);
      formData.append("payload_type", payloadType);

      if (payloadType === "text") {
        formData.append("payload_text", payloadText);
      } else if (payloadFile) {
        formData.append("payload_file", payloadFile);
      }

      const resp = await embedPayload(formData);
      setResult(resp);
      setStep(4);
      toast.success("Embedding and authenticated encryption succeeded!", { id: toastId });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to embed payload";
      toast.error(msg, { id: toastId });
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetAll = () => {
    setCoverFile(null);
    setCoverPreview(null);
    setCoverDimensions(null);
    setCoverError(null);
    setPayloadText("");
    setPayloadFile(null);
    setPassword("");
    setResult(null);
    setStep(1);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 py-4">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-clear border border-teal-liquid/30 text-teal-liquid text-xs font-mono font-medium">
            <Layers className="w-3.5 h-3.5" />
            <span>Authenticated LSB Embedding Studio</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-frost tracking-tight mt-2">
            Embed Authenticated Secrets
          </h1>
          <p className="text-xs sm:text-sm text-frost-muted mt-1">
            4-step wizard: Cover verification, payload configuration, Scrypt KDF encryption, and distortion verification.
          </p>
        </div>

        {/* Stepper Progress Indicator */}
        <div className="flex items-center gap-2 self-start sm:self-center">
          {[1, 2, 3, 4].map((s) => {
            const isCompleted = step > s || (step === 4 && s === 4 && result !== null);
            const isCurrent = step === s;
            return (
              <div key={s} className="flex items-center gap-1.5">
                <div
                  className={`w-7 h-7 rounded-xl flex items-center justify-center font-mono text-xs font-bold transition-all ${
                    isCurrent
                      ? "glass-active text-teal-liquid border border-teal-liquid shadow-teal-glow"
                      : isCompleted
                      ? "bg-teal-liquid text-black font-extrabold"
                      : "glass-clear text-frost-muted/50 border border-white/5"
                  }`}
                >
                  {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : s}
                </div>
                {s < 4 && <div className={`w-3 sm:w-6 h-0.5 rounded-full ${step > s ? "bg-teal-liquid" : "bg-white/10"}`} />}
              </div>
            );
          })}
        </div>
      </div>

      {/* STEP 1: Cover Image Selection */}
      {step === 1 && (
        <section className="space-y-6">
          <div className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-6">
            <div>
              <h2 className="text-lg font-bold text-frost flex items-center gap-2">
                <span className="w-6 h-6 rounded-lg bg-teal-liquid/20 text-teal-liquid font-mono text-xs flex items-center justify-center">1</span>
                Select Cover Image
              </h2>
              <p className="text-xs text-frost-muted mt-1">
                Upload an uncompressed raster image (PNG, BMP, TIFF) up to 16 Megapixels. Lossy formats (JPEG) are strictly prohibited.
              </p>
            </div>

            {/* Dropzone */}
            <div
              {...getCoverRootProps()}
              className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-3 relative ${
                isCoverDragActive
                  ? "border-teal-liquid bg-teal-liquid/10 shadow-teal-glow"
                  : "border-white/15 hover:border-teal-liquid/40 bg-abyss-deep/40 hover:bg-abyss-deep/60"
              }`}
            >
              <input {...getCoverInputProps()} />
              <div className="w-14 h-14 rounded-2xl bg-teal-liquid/10 border border-teal-liquid/30 text-teal-liquid flex items-center justify-center">
                <Upload className="w-7 h-7" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-frost">
                  Drag and drop your cover image here, or <span className="text-teal-liquid underline">browse files</span>
                </p>
                <p className="text-xs text-frost-muted">
                  Supports PNG, BMP, TIFF · Maximum 16MP (e.g. 4000×4000)
                </p>
              </div>
            </div>

            {/* Error Message */}
            {coverError && (
              <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{coverError}</span>
              </div>
            )}

            {/* Cover Image Details Card */}
            {coverPreview && coverDimensions && !coverError && (
              <div className="glass-frosted p-4 rounded-xl border border-teal-liquid/30 flex flex-col sm:flex-row items-center gap-4">
                <div className="w-24 h-24 rounded-lg overflow-hidden border border-white/20 shrink-0 relative bg-black/40">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={coverPreview} alt="Cover preview" className="w-full h-full object-cover" />
                </div>
                <div className="flex-1 space-y-1 text-center sm:text-left">
                  <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                    <span className="font-semibold text-frost text-sm">{coverFile?.name}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-teal-liquid/20 text-teal-liquid border border-teal-liquid/30">
                      {coverDimensions.width} × {coverDimensions.height} px ({coverDimensions.mp} MP)
                    </span>
                  </div>
                  <p className="text-xs text-frost-muted">
                    File size: {formatBytes(coverFile?.size || 0)} · Theoretical Capacity:{" "}
                    <span className="text-teal-liquid font-mono font-semibold">{formatBytes(maxCapacityBytes)}</span>
                  </p>
                  <p className="text-[11px] text-frost-muted/70">
                    Max payload: ~{formatNumber(maxCapacityBytes)} characters of encrypted text or binary stream.
                  </p>
                </div>
              </div>
            )}

            {/* Next Step Action */}
            <div className="flex justify-end pt-4 border-t border-white/10">
              <button
                type="button"
                disabled={!coverFile || !coverDimensions || !!coverError}
                onClick={() => setStep(2)}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl liquid-btn-primary text-xs font-semibold"
              >
                <span>Continue to Payload</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </section>
      )}

      {/* STEP 2: Payload Configuration */}
      {step === 2 && (
        <section className="space-y-6">
          <div className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-frost flex items-center gap-2">
                  <span className="w-6 h-6 rounded-lg bg-teal-liquid/20 text-teal-liquid font-mono text-xs flex items-center justify-center">2</span>
                  Configure Payload
                </h2>
                <p className="text-xs text-frost-muted mt-1">
                  Choose between plaintext message or arbitrary binary file (PDF, TXT, ZIP, etc.).
                </p>
              </div>

              {/* Payload Type Toggle */}
              <div className="flex items-center p-1 rounded-xl glass-clear border border-white/10">
                <button
                  type="button"
                  onClick={() => setPayloadType("text")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    payloadType === "text"
                      ? "glass-active text-teal-liquid"
                      : "text-frost-muted hover:text-frost"
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Text</span>
                </button>
                <button
                  type="button"
                  onClick={() => setPayloadType("file")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    payloadType === "file"
                      ? "glass-active text-teal-liquid"
                      : "text-frost-muted hover:text-frost"
                  }`}
                >
                  <FileUp className="w-3.5 h-3.5" />
                  <span>Binary File</span>
                </button>
              </div>
            </div>

            {/* Live Capacity Meter */}
            <div className="glass-frosted p-4 rounded-xl border border-white/10 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-frost-muted flex items-center gap-1">
                  Capacity Utilization
                  {isPayloadTooLarge && (
                    <span className="text-rose-400 font-semibold">(EXCEEDED)</span>
                  )}
                </span>
                <span className="font-mono text-xs text-frost">
                  <span className={isPayloadTooLarge ? "text-rose-400 font-bold" : "text-teal-liquid font-bold"}>
                    {formatBytes(payloadSizeBytes)}
                  </span>
                  {" / "}
                  <span>{formatBytes(maxCapacityBytes)}</span>
                  {" "}({capacityRatio.toFixed(2)}%)
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-abyss-deep overflow-hidden border border-white/5">
                <div
                  className={`h-full transition-all duration-300 ${
                    isPayloadTooLarge
                      ? "bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]"
                      : capacityRatio > 75
                      ? "bg-amber-400"
                      : "bg-teal-liquid shadow-teal-glow"
                  }`}
                  style={{ width: `${Math.min(100, Math.max(0, capacityRatio))}%` }}
                />
              </div>
            </div>

            {/* Input by Payload Type */}
            {payloadType === "text" ? (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-frost">
                  Plaintext Secret Message
                </label>
                <textarea
                  rows={6}
                  value={payloadText}
                  onChange={(e) => setPayloadText(e.target.value)}
                  placeholder="Type or paste confidential payload here..."
                  className="w-full rounded-xl p-3.5 liquid-input font-mono text-xs focus:ring-2 focus:ring-teal-liquid"
                />
                <div className="flex justify-between text-[11px] text-frost-muted">
                  <span>Characters: {payloadText.length}</span>
                  <span>UTF-8 bytes: {payloadSizeBytes} B</span>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <label className="text-xs font-semibold text-frost">
                  Payload File
                </label>
                <div
                  {...getPayloadRootProps()}
                  className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                    isPayloadDragActive
                      ? "border-teal-liquid bg-teal-liquid/10"
                      : "border-white/10 hover:border-teal-liquid/40 bg-abyss-deep/40"
                  }`}
                >
                  <input {...getPayloadInputProps()} />
                  <FileUp className="w-6 h-6 mx-auto mb-2 text-teal-liquid" />
                  <p className="text-xs text-frost font-medium">
                    {payloadFile ? payloadFile.name : "Select or drop payload file"}
                  </p>
                  <p className="text-[11px] text-frost-muted mt-0.5">
                    {payloadFile ? formatBytes(payloadFile.size) : "Any format up to capacity"}
                  </p>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-4 border-t border-white/10">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl glass-clear text-xs font-semibold text-frost-muted hover:text-frost"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <button
                type="button"
                disabled={payloadSizeBytes === 0 || isPayloadTooLarge}
                onClick={() => setStep(3)}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl liquid-btn-primary text-xs font-semibold"
              >
                <span>Continue to Security</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </section>
      )}

      {/* STEP 3: Security & Steganography Method */}
      {step === 3 && (
        <section className="space-y-6">
          <div className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-6">
            <div>
              <h2 className="text-lg font-bold text-frost flex items-center gap-2">
                <span className="w-6 h-6 rounded-lg bg-teal-liquid/20 text-teal-liquid font-mono text-xs flex items-center justify-center">3</span>
                Password &amp; Steganography Configuration
              </h2>
              <p className="text-xs text-frost-muted mt-1">
                Keys are derived via Scrypt with high work factor (N=131072, r=8, p=1). The password is never transmitted in the clear or stored.
              </p>
            </div>

            {/* Password Input & Strength */}
            <div className="space-y-3">
              <label className="text-xs font-semibold text-frost flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-teal-liquid" />
                Encryption Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter strong encryption passphrase..."
                  className="w-full rounded-xl px-4 py-2.5 pr-10 liquid-input font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-frost-muted hover:text-frost"
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Strength Meter Bar */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-frost-muted">Passphrase Strength:</span>
                  <span className="font-mono font-bold text-frost">{passwordStrength.label}</span>
                </div>
                <div className="grid grid-cols-4 gap-1.5">
                  {[1, 2, 3, 4].map((idx) => (
                    <div
                      key={idx}
                      className={`h-1.5 rounded-full transition-all ${
                        passwordStrength.score >= idx ? passwordStrength.color : "bg-white/10"
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Steganography Method Selector */}
            <div className="space-y-3 pt-2">
              <label className="text-xs font-semibold text-frost">
                Steganography Embedding Algorithm
              </label>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* LSB Matching */}
                <div
                  onClick={() => setMethod("lsb_matching")}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    method === "lsb_matching"
                      ? "glass-active border-teal-liquid shadow-teal-glow"
                      : "glass-frosted border-white/10 hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-xs text-frost">LSB Matching (±1)</span>
                    <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-teal-liquid/20 text-teal-liquid border border-teal-liquid/30">
                      Recommended
                    </span>
                  </div>
                  <p className="text-[11px] text-frost-muted leading-relaxed">
                    Mielikainen (2006). Randomly increments or decrements pixel values by 1. Preserves Pairs-of-Values symmetry, evading standard Chi-Square detectors.
                  </p>
                </div>

                {/* LSB Replacement */}
                <div
                  onClick={() => setMethod("lsb_replacement")}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    method === "lsb_replacement"
                      ? "glass-active border-teal-liquid shadow-teal-glow"
                      : "glass-frosted border-white/10 hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-xs text-frost">LSB Replacement</span>
                    <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      Classic
                    </span>
                  </div>
                  <p className="text-[11px] text-frost-muted leading-relaxed">
                    Direct bit-substitution into bit 0. Simpler, but alters PoV histogram distributions, making it vulnerable to statistical Chi-Square steganalysis.
                  </p>
                </div>
              </div>
            </div>

            {/* Navigation and Launch */}
            <div className="flex justify-between pt-4 border-t border-white/10">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl glass-clear text-xs font-semibold text-frost-muted hover:text-frost"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <button
                type="button"
                disabled={!password || isSubmitting}
                onClick={handleEmbedSubmit}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl liquid-btn-primary text-xs font-semibold shadow-teal-glow"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Encrypting &amp; Embedding...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Execute Embedding</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </section>
      )}

      {/* STEP 4: Results & Before/After Slider */}
      {step === 4 && result && coverPreview && (
        <section className="space-y-6">
          <div className="glass-deep rounded-2xl p-6 sm:p-8 border border-teal-liquid/30 space-y-6 shadow-glass-lg">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-5">
              <div>
                <span className="px-2.5 py-0.5 rounded-full bg-teal-liquid/20 text-teal-liquid border border-teal-liquid/40 text-[10px] font-mono font-bold uppercase tracking-wider">
                  Success · Operation Complete
                </span>
                <h2 className="text-xl font-bold text-frost mt-1.5">
                  Stego Image Ready
                </h2>
                <p className="text-xs text-frost-muted">
                  Payload authenticated with AES-256-GCM and concealed via {method === "lsb_matching" ? "LSB Matching" : "LSB Replacement"}.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <a
                  href={result.download_url}
                  download={result.filename}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl liquid-btn-primary text-xs font-semibold"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Stego Image</span>
                </a>
              </div>
            </div>

            {/* Distortion Metrics Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="glass-frosted p-4 rounded-xl border border-white/10 text-center">
                <span className="text-[11px] font-mono uppercase tracking-wider text-frost-muted">
                  MSE (Mean Squared Error)
                </span>
                <p className="text-2xl font-mono font-bold text-teal-liquid mt-1">
                  {formatNumber(result.metrics.mse, 4)}
                </p>
                <span className="text-[10px] text-frost-muted/70">Ideal: &lt; 1.0 (Imperceptible)</span>
              </div>

              <div className="glass-frosted p-4 rounded-xl border border-white/10 text-center">
                <span className="text-[11px] font-mono uppercase tracking-wider text-frost-muted">
                  PSNR (Peak Signal-to-Noise)
                </span>
                <p className="text-2xl font-mono font-bold text-mint mt-1">
                  {formatNumber(result.metrics.psnr, 2)} dB
                </p>
                <span className="text-[10px] text-frost-muted/70">Ideal: &gt; 40 dB (High Fidelity)</span>
              </div>

              <div className="glass-frosted p-4 rounded-xl border border-white/10 text-center">
                <span className="text-[11px] font-mono uppercase tracking-wider text-frost-muted">
                  SSIM (Structural Similarity)
                </span>
                <p className="text-2xl font-mono font-bold text-iris mt-1">
                  {formatNumber(result.metrics.ssim, 4)}
                </p>
                <span className="text-[10px] text-frost-muted/70">Ideal: 1.0000 (Preserved Structure)</span>
              </div>
            </div>

            {/* Before / After Slider */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-medium text-frost-muted">
                <span>Drag slider to inspect Original Cover (Left) vs Stego (Right)</span>
                <span className="font-mono text-teal-liquid">Pixel Difference: Inaudible to Human Vision</span>
              </div>

              <div className="rounded-2xl overflow-hidden border border-white/20 h-[380px] sm:h-[480px] bg-black/60 relative">
                <ReactCompareSlider
                  itemOne={<ReactCompareSliderImage src={coverPreview} alt="Original Cover" />}
                  itemTwo={<ReactCompareSliderImage src={result.download_url} alt="Stego Output" />}
                  className="w-full h-full object-contain"
                />
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-white/10">
              <button
                type="button"
                onClick={resetAll}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl glass-clear text-xs font-semibold text-frost-muted hover:text-frost"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Embed Another Image</span>
              </button>

              <div className="flex items-center gap-2">
                <a
                  href="/analyze"
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl glass-frosted text-xs font-semibold text-frost hover:border-teal-liquid/40"
                >
                  <BarChart3 className="w-3.5 h-3.5 text-teal-liquid" />
                  <span>Send to Steganalysis Lab</span>
                </a>
                <a
                  href={result.download_url}
                  download={result.filename}
                  className="flex items-center gap-1.5 px-5 py-2 rounded-xl liquid-btn-primary text-xs font-semibold"
                >
                  <Download className="w-4 h-4" />
                  <span>Save Image</span>
                </a>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
