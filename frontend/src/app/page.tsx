import Link from "next/link";
import {
  ShieldCheck,
  Lock,
  Layers,
  BarChart3,
  Flame,
  ArrowRight,
  Database,
  Cpu,
  CheckCircle2,
} from "lucide-react";
import { PixelWidget } from "@/components/pixel-widget";

export default function HomePage() {
  return (
    <div className="space-y-16 py-4">
      {/* Hero Section */}
      <section className="relative text-center max-w-4xl mx-auto space-y-6 pt-8 pb-4">
        {/* Top Glass Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-clear border border-teal-liquid/30 text-teal-liquid text-xs font-mono font-medium shadow-glass-sm animate-pulse-subtle">
          <ShieldCheck className="w-4 h-4 text-teal-liquid" />
          <span>StegaShield Security Framework · Milestone 4</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-frost leading-[1.1]">
          Academic-Grade <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-liquid via-mint to-iris">
            Authenticated Steganography
          </span>
          <br />&amp; Steganalysis Laboratory
        </h1>

        {/* Hero Subtitle */}
        <p className="text-base sm:text-lg text-frost-muted max-w-2xl mx-auto leading-relaxed">
          Embed encrypted, authenticated secrets into uncompressed raster images using LSB Matching (±1) and PRNG pseudo-random permutation. Evaluate security against Chi-Square and RS Steganalysis attacks.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Link
            href="/embed"
            className="flex items-center gap-2 px-6 py-3 rounded-xl liquid-btn-primary text-sm font-semibold shadow-teal-glow hover:shadow-teal-glow-lg transition-all"
          >
            <span>Launch Embed Studio</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/analyze"
            className="flex items-center gap-2 px-6 py-3 rounded-xl glass-frosted text-sm font-semibold text-frost hover:border-teal-liquid/40 transition-all"
          >
            <BarChart3 className="w-4 h-4 text-teal-liquid" />
            <span>Analyze Image Distortion</span>
          </Link>
          <Link
            href="/attack-lab"
            className="flex items-center gap-2 px-6 py-3 rounded-xl glass-clear text-sm font-semibold text-frost-muted hover:text-frost transition-all"
          >
            <Flame className="w-4 h-4 text-rose-400" />
            <span>Attack Lab Matrix</span>
          </Link>
        </div>

        {/* Verified Security Properties Badges */}
        <div className="pt-6 flex flex-wrap items-center justify-center gap-6 text-xs text-frost-muted/80">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-teal-liquid" />
            <span>AES-256-GCM + AAD Binding</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-teal-liquid" />
            <span>Scrypt KDF (N=2¹⁷, r=8, p=1)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-teal-liquid" />
            <span>Uniform Error Suppression</span>
          </div>
        </div>
      </section>

      {/* 3-Step Feature Strip: Encrypt -> Hide -> Analyze */}
      <section className="relative">
        <div className="text-center mb-8">
          <h2 className="text-xs uppercase tracking-widest font-mono text-teal-liquid">
            End-to-End Pipeline
          </h2>
          <p className="text-2xl font-bold text-frost mt-1">
            How StegaShield Conceals &amp; Audits Information
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Step 1: Encrypt */}
          <div className="glass-frosted rounded-2xl p-6 border border-white/10 relative overflow-hidden group hover:border-teal-liquid/30 transition-all">
            <div className="w-10 h-10 rounded-xl bg-iris/15 border border-iris/30 text-iris flex items-center justify-center mb-4">
              <Lock className="w-5 h-5" />
            </div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-frost text-base">1. Encrypt</h3>
              <span className="font-mono text-xs text-iris font-semibold">
                HKDF + AES-GCM
              </span>
            </div>
            <p className="text-xs text-frost-muted leading-relaxed">
              Plaintext or files are transformed via Scrypt memory-hard key derivation. AES-256-GCM authenticated encryption binds length into AAD, preventing ciphertext manipulation.
            </p>
          </div>

          {/* Step 2: Hide */}
          <div className="glass-frosted rounded-2xl p-6 border border-white/10 relative overflow-hidden group hover:border-teal-liquid/30 transition-all">
            <div className="w-10 h-10 rounded-xl bg-teal-liquid/15 border border-teal-liquid/30 text-teal-liquid flex items-center justify-center mb-4">
              <Layers className="w-5 h-5" />
            </div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-frost text-base">2. Hide</h3>
              <span className="font-mono text-xs text-teal-liquid font-semibold">
                LSB Matching (±1)
              </span>
            </div>
            <p className="text-xs text-frost-muted leading-relaxed">
              Payload bits are dispersed across pseudo-random PRNG coordinate permutations. LSB Matching modifies pixel values by ±1 rather than overwriting bit 0, suppressing PoV asymmetry.
            </p>
          </div>

          {/* Step 3: Analyze */}
          <div className="glass-frosted rounded-2xl p-6 border border-white/10 relative overflow-hidden group hover:border-teal-liquid/30 transition-all">
            <div className="w-10 h-10 rounded-xl bg-mint/15 border border-mint/30 text-mint flex items-center justify-center mb-4">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-frost text-base">3. Analyze</h3>
              <span className="font-mono text-xs text-mint font-semibold">
                Chi-Square &amp; RS
              </span>
            </div>
            <p className="text-xs text-frost-muted leading-relaxed">
              Inspect images using quantitative distortion metrics (MSE, PSNR, SSIM), amplified residual difference maps, and statistical steganalysis (Westfeld Chi-Square &amp; Fridrich RS).
            </p>
          </div>
        </div>
      </section>

      {/* Interactive 8-bit LSB Pixel Widget Section */}
      <section className="space-y-4">
        <PixelWidget />
      </section>

      {/* Feature Navigation Cards Grid */}
      <section className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2">
          <div>
            <h2 className="text-xs uppercase tracking-widest font-mono text-teal-liquid">
              Modules &amp; Tools
            </h2>
            <p className="text-2xl font-bold text-frost mt-1">
              Explore StegaShield Capabilities
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link
            href="/embed"
            className="glass-frosted rounded-2xl p-6 border border-white/10 hover:border-teal-liquid/40 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-teal-liquid/10 text-teal-liquid flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-frost text-base group-hover:text-teal-liquid transition-colors">
                Embedding Studio
              </h3>
              <p className="text-xs text-frost-muted mt-2 leading-relaxed">
                4-step wizard supporting PNG, BMP, TIFF covers up to 16MP. Live capacity estimation, password strength analyzer, and split-screen comparison slider.
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-teal-liquid font-medium pt-4">
              <span>Open Studio</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link
            href="/extract"
            className="glass-frosted rounded-2xl p-6 border border-white/10 hover:border-teal-liquid/40 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-iris/10 text-iris flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                <Lock className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-frost text-base group-hover:text-iris transition-colors">
                Payload Extraction
              </h3>
              <p className="text-xs text-frost-muted mt-2 leading-relaxed">
                Decrypt and reconstruct concealed payloads with uniform error suppression, preventing side-channel leaks on invalid passwords or clean images.
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-iris font-medium pt-4">
              <span>Extract Payload</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link
            href="/analyze"
            className="glass-frosted rounded-2xl p-6 border border-white/10 hover:border-teal-liquid/40 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-mint/10 text-mint flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                <BarChart3 className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-frost text-base group-hover:text-mint transition-colors">
                Distortion &amp; Steganalysis
              </h3>
              <p className="text-xs text-frost-muted mt-2 leading-relaxed">
                Compare Cover vs Stego side-by-side with heatmaps, bitplane slices, and PoV histograms. Run calibrated Chi-Square and RS detectors.
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-mint font-medium pt-4">
              <span>Analyze Images</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link
            href="/attack-lab"
            className="glass-frosted rounded-2xl p-6 border border-white/10 hover:border-teal-liquid/40 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                <Flame className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-frost text-base group-hover:text-rose-400 transition-colors">
                Attack Lab Matrix Engine
              </h3>
              <p className="text-xs text-frost-muted mt-2 leading-relaxed">
                Run automated empirical benchmark sweeps across LSB Replacement vs Matching, ratios (5%–100%), with real-time SSE progress and RFC 4180 CSV export.
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-rose-400 font-medium pt-4">
              <span>Launch Attack Lab</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link
            href="/history"
            className="glass-frosted rounded-2xl p-6 border border-white/10 hover:border-teal-liquid/40 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-300 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                <Database className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-frost text-base group-hover:text-amber-300 transition-colors">
                Session History
              </h3>
              <p className="text-xs text-frost-muted mt-2 leading-relaxed">
                Review session-scoped steganographic operations, calculated distortion metrics, and timestamps. Zero secrets or keys are ever persisted.
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-amber-300 font-medium pt-4">
              <span>View History</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link
            href="/about"
            className="glass-frosted rounded-2xl p-6 border border-white/10 hover:border-teal-liquid/40 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-300 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-frost text-base group-hover:text-cyan-300 transition-colors">
                Architecture &amp; Threat Model
              </h3>
              <p className="text-xs text-frost-muted mt-2 leading-relaxed">
                Formal cryptographic proofs, theoretical detection bounds, information-theoretic limits, and peer-reviewed academic literature citations.
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-cyan-300 font-medium pt-4">
              <span>Read Documentation</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        </div>
      </section>
    </div>
  );
}
