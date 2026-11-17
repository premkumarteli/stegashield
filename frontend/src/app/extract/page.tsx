"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  Lock,
  KeyRound,
  FileText,
  Download,
  Copy,
  Check,
  Eye,
  EyeOff,
  AlertCircle,
  RefreshCw,
  Sparkles,
  ShieldAlert,
} from "lucide-react";
import { toast } from "sonner";
import { extractPayload, type ExtractResponse } from "@/lib/api-client";
import { formatBytes } from "@/lib/utils";

export default function ExtractPage() {
  const [stegoFile, setStegoFile] = useState<File | null>(null);
  const [stegoPreview, setStegoPreview] = useState<string | null>(null);
  const [password, setPassword] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setErrorMessage(null);
    setResult(null);
    setStegoFile(file);
    setStegoPreview(URL.createObjectURL(file));
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/png": [".png"],
      "image/bmp": [".bmp"],
      "image/tiff": [".tiff", ".tif"],
    },
    multiple: false,
  });

  const handleExtract = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stegoFile) {
      toast.error("Please drop or select a stego image.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setResult(null);
    const toastId = toast.loading("Executing Scrypt KDF, locating PRNG permutation, and authenticating AES-GCM ciphertext...");

    try {
      const formData = new FormData();
      formData.append("stego_file", stegoFile);
      formData.append("password", password);

      const resp = await extractPayload(formData);
      setResult(resp);
      toast.success("Payload extracted and verified successfully!", { id: toastId });
    } catch {
      setErrorMessage(
        "Decryption or authentication failed. Either the password is incorrect, or the provided image contains no authenticated StegaShield payload. StegaShield strictly enforces uniform error suppression to prevent decryption oracle attacks."
      );
      toast.error("Extraction failed (Uniform Error Suppression)", { id: toastId });
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async () => {
    if (!result?.payload_text) return;
    try {
      await navigator.clipboard.writeText(result.payload_text);
      setCopied(true);
      toast.success("Plaintext copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Failed to copy to clipboard.");
    }
  };

  const resetAll = () => {
    setStegoFile(null);
    setStegoPreview(null);
    setPassword("");
    setResult(null);
    setErrorMessage(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-4">
      {/* Header */}
      <div className="border-b border-white/10 pb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-clear border border-iris/30 text-iris text-xs font-mono font-medium">
          <KeyRound className="w-3.5 h-3.5" />
          <span>Authenticated Decryption &amp; Extraction</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-frost tracking-tight mt-2">
          Extract Steganographic Payload
        </h1>
        <p className="text-xs sm:text-sm text-frost-muted mt-1">
          Recover AES-256-GCM encrypted secrets from carrier images with zero-knowledge side-channel protection.
        </p>
      </div>

      {/* Main Extraction Form */}
      <form onSubmit={handleExtract} className="space-y-6">
        <div className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-6">
          {/* Stego Image Upload Dropzone */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-frost">
              1. Carrier / Stego Image
            </label>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-2xl p-6 sm:p-10 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-3 ${
                isDragActive
                  ? "border-iris bg-iris/10 shadow-glass-md"
                  : "border-white/15 hover:border-iris/40 bg-abyss-deep/40 hover:bg-abyss-deep/60"
              }`}
            >
              <input {...getInputProps()} />
              <div className="w-12 h-12 rounded-xl bg-iris/10 border border-iris/30 text-iris flex items-center justify-center">
                <Upload className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold text-frost">
                  {stegoFile ? stegoFile.name : "Drop your stego image here, or browse"}
                </p>
                <p className="text-xs text-frost-muted">
                  {stegoFile
                    ? `Size: ${formatBytes(stegoFile.size)}`
                    : "Accepts lossless carrier formats (PNG, BMP, TIFF)"}
                </p>
              </div>
            </div>
          </div>

          {/* Image Thumbnail Preview if chosen */}
          {stegoPreview && (
            <div className="glass-frosted p-3 rounded-xl border border-white/10 flex items-center gap-3">
              <div className="w-16 h-16 rounded-lg overflow-hidden border border-white/20 shrink-0 bg-black/40">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={stegoPreview} alt="Stego preview" className="w-full h-full object-cover" />
              </div>
              <div className="text-xs space-y-0.5">
                <p className="font-semibold text-frost">{stegoFile?.name}</p>
                <p className="text-frost-muted">{formatBytes(stegoFile?.size || 0)}</p>
              </div>
            </div>
          )}

          {/* Password Input */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-frost flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-iris" />
              2. Secret Encryption Passphrase
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter passphrase used during embedding..."
                className="w-full rounded-xl px-4 py-2.5 pr-10 liquid-input font-mono text-xs focus:ring-2 focus:ring-iris"
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
            <p className="text-[11px] text-frost-muted">
              The 128-bit salt stored in the cover header is combined with this passphrase via Scrypt to reproduce the permutation sequence and AES-256-GCM key.
            </p>
          </div>

          {/* Error Message with Uniform Error Suppression explanation */}
          {errorMessage && (
            <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/40 text-rose-200 text-xs space-y-1">
              <div className="flex items-center gap-2 font-bold text-rose-300">
                <ShieldAlert className="w-4 h-4 shrink-0 text-rose-400" />
                <span>Uniform Error Suppression Triggered</span>
              </div>
              <p className="leading-relaxed pl-6">{errorMessage}</p>
            </div>
          )}

          {/* Submit Action */}
          <div className="pt-2 flex items-center justify-between">
            <button
              type="button"
              onClick={resetAll}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl glass-clear text-xs font-semibold text-frost-muted hover:text-frost"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>

            <button
              type="submit"
              disabled={!stegoFile || isLoading}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl liquid-btn-primary text-xs font-semibold"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Decrypting Payload...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Extract &amp; Decrypt</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Extraction Result Card */}
      {result && (
        <section className="glass-deep rounded-2xl p-6 sm:p-8 border border-teal-liquid/40 shadow-glass-lg space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
            <div>
              <span className="px-2.5 py-0.5 rounded-full bg-teal-liquid/20 text-teal-liquid border border-teal-liquid/40 text-[10px] font-mono font-bold uppercase tracking-wider">
                Authentication Verified · AES-256-GCM
              </span>
              <h2 className="text-xl font-bold text-frost mt-1.5">
                Concealed Payload Recovered
              </h2>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-frost-muted">
              <span>Type: <strong className="text-frost uppercase">{result.payload_type}</strong></span>
              <span>·</span>
              <span>Size: <strong className="text-frost">{formatBytes(result.size_bytes)}</strong></span>
            </div>
          </div>

          {/* Text Payload Display */}
          {result.payload_type === "text" && result.payload_text && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-frost flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-teal-liquid" />
                  Decrypted Plaintext
                </span>
                <button
                  type="button"
                  onClick={copyToClipboard}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg glass-clear text-xs text-teal-liquid hover:bg-teal-liquid/10 transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-mint" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? "Copied!" : "Copy Text"}</span>
                </button>
              </div>

              <div className="p-4 rounded-xl bg-abyss-deep/80 border border-white/10 font-mono text-xs text-frost whitespace-pre-wrap break-words max-h-80 overflow-y-auto selection:bg-teal-liquid/30">
                {result.payload_text}
              </div>
            </div>
          )}

          {/* Binary File Payload Display */}
          {result.payload_type === "file" && result.download_url && (
            <div className="space-y-4">
              <div className="glass-frosted p-4 rounded-xl border border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-teal-liquid/15 border border-teal-liquid/30 text-teal-liquid flex items-center justify-center">
                    <Download className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="font-semibold text-frost text-sm">
                      {result.filename || "extracted_payload.bin"}
                    </p>
                    <p className="text-xs text-frost-muted">
                      Original file reconstructed ({formatBytes(result.size_bytes)})
                    </p>
                  </div>
                </div>

                <a
                  href={result.download_url}
                  download={result.filename || "payload.bin"}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl liquid-btn-primary text-xs font-semibold"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Extracted File</span>
                </a>
              </div>
            </div>
          )}

          <div className="text-[11px] text-frost-muted pt-2 border-t border-white/10 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-teal-liquid shrink-0" />
            <span>Ephemeral delivery: Stored file artifacts expire after 30 minutes. Operation ID: {result.operation_id}</span>
          </div>
        </section>
      )}
    </div>
  );
}
