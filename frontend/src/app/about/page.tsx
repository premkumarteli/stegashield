import {
  Lock,
  Layers,
  BookOpen,
  Cpu,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

export default function AboutPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-12 py-4">
      {/* Page Header */}
      <div className="border-b border-white/10 pb-6 space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-clear border border-teal-liquid/30 text-teal-liquid text-xs font-mono font-medium">
          <Cpu className="w-3.5 h-3.5" />
          <span>Architecture &amp; Theoretical Foundations</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-frost tracking-tight">
          System Architecture &amp; Threat Model
        </h1>
        <p className="text-sm text-frost-muted max-w-3xl leading-relaxed">
          Comprehensive documentation of StegaShield&apos;s cryptographic primitives, spatial steganography engine, empirical steganalysis detection bounds, and formal security guarantees.
        </p>
      </div>

      {/* 1. Interactive Architecture Flow Diagram */}
      <section className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
          <div>
            <h2 className="text-lg font-bold text-frost flex items-center gap-2">
              <Layers className="w-4 h-4 text-teal-liquid" />
              1. End-to-End Pipeline Architecture
            </h2>
            <p className="text-xs text-frost-muted mt-0.5">
              Data flow from plaintext secret ingestion to steganographic carrier generation and verification.
            </p>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-liquid/10 text-teal-liquid border border-teal-liquid/30">
            Pipeline v1.0
          </span>
        </div>

        {/* Styled Architecture Diagram Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Card 1: Ingestion & KDF */}
          <div className="glass-frosted p-4 rounded-xl border border-white/10 space-y-2 relative">
            <div className="w-8 h-8 rounded-lg bg-teal-liquid/15 text-teal-liquid flex items-center justify-center font-mono text-xs font-bold">
              01
            </div>
            <h3 className="font-bold text-xs text-frost">Key Derivation</h3>
            <p className="text-[11px] text-frost-muted leading-relaxed">
              Random 16-byte salt + Passphrase. Scrypt (N=2¹⁷, r=8, p=1) generates master key with ~128 MiB memory hardness.
            </p>
            <div className="pt-2 text-[10px] font-mono text-teal-liquid border-t border-white/5">
              RFC 7914 scrypt
            </div>
          </div>

          {/* Card 2: Key Separation & AEAD */}
          <div className="glass-frosted p-4 rounded-xl border border-white/10 space-y-2 relative">
            <div className="w-8 h-8 rounded-lg bg-iris/15 text-iris flex items-center justify-center font-mono text-xs font-bold">
              02
            </div>
            <h3 className="font-bold text-xs text-frost">AEAD Encryption</h3>
            <p className="text-[11px] text-frost-muted leading-relaxed">
              HKDF-SHA256 separates <code className="text-frost">enc_key</code> and <code className="text-frost">perm_key</code>. AES-256-GCM binds ciphertext length into AAD.
            </p>
            <div className="pt-2 text-[10px] font-mono text-iris border-t border-white/5">
              AES-256-GCM + AAD
            </div>
          </div>

          {/* Card 3: Spatial Embedding */}
          <div className="glass-frosted p-4 rounded-xl border border-white/10 space-y-2 relative">
            <div className="w-8 h-8 rounded-lg bg-mint/15 text-mint flex items-center justify-center font-mono text-xs font-bold">
              03
            </div>
            <h3 className="font-bold text-xs text-frost">Permuted Embedding</h3>
            <p className="text-[11px] text-frost-muted leading-relaxed">
              Sequential 128-bit salt prefix. Permuted coordinates driven by seeded PRNG. LSB Matching (±1) modulates pixel values.
            </p>
            <div className="pt-2 text-[10px] font-mono text-mint border-t border-white/5">
              LSB Matching (±1)
            </div>
          </div>

          {/* Card 4: Steganalysis Verification */}
          <div className="glass-frosted p-4 rounded-xl border border-white/10 space-y-2 relative">
            <div className="w-8 h-8 rounded-lg bg-rose-500/15 text-rose-400 flex items-center justify-center font-mono text-xs font-bold">
              04
            </div>
            <h3 className="font-bold text-xs text-frost">Steganalysis Audit</h3>
            <p className="text-[11px] text-frost-muted leading-relaxed">
              Distortion metrics (MSE, PSNR, SSIM). Westfeld Chi-Square &amp; Fridrich RS analysis test for statistical trace.
            </p>
            <div className="pt-2 text-[10px] font-mono text-rose-400 border-t border-white/5">
              Chi² &amp; RS Solvers
            </div>
          </div>
        </div>
      </section>

      {/* 2. Formal Threat Model & Security Properties */}
      <section className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-6">
        <div className="border-b border-white/10 pb-4">
          <h2 className="text-lg font-bold text-frost flex items-center gap-2">
            <Lock className="w-4 h-4 text-iris" />
            2. Formal Threat Model &amp; Security Guarantees
          </h2>
          <p className="text-xs text-frost-muted mt-0.5">
            Adversary capabilities and cryptographic hardness bounds under Kerckhoffs&apos;s Principle.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Property 1 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-frost">
              <CheckCircle2 className="w-4 h-4 text-teal-liquid shrink-0" />
              <span>Chosen-Plaintext &amp; Chosen-Ciphertext (IND-CCA2) Hardness</span>
            </div>
            <p className="text-xs text-frost-muted leading-relaxed pl-6">
              Authenticated symmetric encryption via AES-256-GCM ensures that any bit flip in the stego image results in an authentication failure, rejecting tampered payloads without revealing plaintext fragments.
            </p>
          </div>

          {/* Property 2 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-frost">
              <CheckCircle2 className="w-4 h-4 text-teal-liquid shrink-0" />
              <span>Decryption Oracle Defense via Uniform Error Suppression</span>
            </div>
            <p className="text-xs text-frost-muted leading-relaxed pl-6">
              When extraction fails, StegaShield yields an identical error (<code className="text-teal-liquid font-mono">WRONG_PASSWORD_OR_NO_DATA</code>) regardless of whether the password was incorrect, GCM tag failed, or no payload exists, preventing side-channel leakage.
            </p>
          </div>

          {/* Property 3 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-frost">
              <CheckCircle2 className="w-4 h-4 text-teal-liquid shrink-0" />
              <span>Memory-Hard GPU/ASIC Resistance (Scrypt N=131072)</span>
            </div>
            <p className="text-xs text-frost-muted leading-relaxed pl-6">
              By enforcing N=2¹⁷ iterations, r=8 block size, deriving a single key requires ~128 MiB RAM. This defeats massive GPU dictionary attacks, requiring orders of magnitude more silicon area per parallel worker.
            </p>
          </div>

          {/* Property 4 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-frost">
              <CheckCircle2 className="w-4 h-4 text-teal-liquid shrink-0" />
              <span>Zero-Knowledge Server Persistence</span>
            </div>
            <p className="text-xs text-frost-muted leading-relaxed pl-6">
              Database models persist solely anonymous session tokens, operation types, timestamps, and aggregate numeric distortion scores. Passwords, cryptographic keys, plaintexts, and permuted maps are purged immediately upon request fulfillment.
            </p>
          </div>
        </div>
      </section>

      {/* 3. Known Limitations & Detection Boundaries */}
      <section className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-6">
        <div className="border-b border-white/10 pb-4">
          <h2 className="text-lg font-bold text-frost flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            3. Known Limitations &amp; Theoretical Detection Boundaries
          </h2>
          <p className="text-xs text-frost-muted mt-0.5">
            Understanding fundamental boundaries in spatial domain steganography.
          </p>
        </div>

        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200/90 space-y-1">
            <span className="font-bold text-amber-300 block">Lossy Compression Destruction</span>
            <p className="leading-relaxed">
              Spatial LSB steganography requires uncompressed/lossless carrier containers (PNG, BMP, TIFF). Converting a stego image to lossy JPEG or WebP applies Discrete Cosine Transform (DCT) quantization and chroma subsampling, obliterating least significant bits and rendering the payload unrecoverable.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-abyss-deep/70 border border-white/10 text-xs text-frost-muted space-y-1">
            <span className="font-bold text-frost block">High-Capacity Detectability Thresholds (Square-Root Law)</span>
            <p className="leading-relaxed">
              By the Square-Root Law of Steganographic Capacity (Ker 2008), embedding capacity is sub-linear in carrier size: O(√N). When payload ratio approaches 100% (1.0 bpp), even LSB matching creates subtle second-order statistical perturbations in adjacent pixel variance that can be detected by specialized High-Order Rich Models (SRM).
            </p>
          </div>
        </div>
      </section>

      {/* 4. Academic Citations */}
      <section className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-6">
        <div className="border-b border-white/10 pb-4">
          <h2 className="text-lg font-bold text-frost flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-teal-liquid" />
            4. Academic Literature &amp; Formal References
          </h2>
          <p className="text-xs text-frost-muted mt-0.5">
            Key peer-reviewed foundational literature implemented throughout the StegaShield engine.
          </p>
        </div>

        <div className="space-y-4 text-xs">
          <div className="p-4 rounded-xl glass-frosted border border-white/10 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-frost">Westfeld, A., &amp; Pfitzmann, A. (2000)</span>
              <span className="text-[10px] font-mono text-teal-liquid">IH&apos;99 · LNCS 1768</span>
            </div>
            <p className="text-frost-muted italic">
              &ldquo;Attacks on Steganographic Systems: Breaking the Stegovanos, EzStego, Jsteg, Steganos, and S-Tools&rdquo;
            </p>
            <p className="text-[11px] text-frost-muted/70">
              Introduced the Pairs-of-Values (PoV) histogram equalization principle and the Chi-Square goodness-of-fit statistical attack for spatial LSB replacement.
            </p>
          </div>

          <div className="p-4 rounded-xl glass-frosted border border-white/10 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-frost">Fridrich, J., Goljan, M., &amp; Du, R. (2001)</span>
              <span className="text-[10px] font-mono text-teal-liquid">IEEE MultiMedia</span>
            </div>
            <p className="text-frost-muted italic">
              &ldquo;Detecting LSB Steganography in Color, and Gray-Scale Images&rdquo;
            </p>
            <p className="text-[11px] text-frost-muted/70">
              Formulated RS Steganalysis, analyzing regular and singular pixel group counts under invertible dual flipping masks to estimate embedded payload ratio.
            </p>
          </div>

          <div className="p-4 rounded-xl glass-frosted border border-white/10 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-frost">Mielikainen, J. (2006)</span>
              <span className="text-[10px] font-mono text-teal-liquid">IEEE Signal Processing Letters</span>
            </div>
            <p className="text-frost-muted italic">
              &ldquo;LSB Matching Revisited: Optimal Non-Deterministic Bit Substitution&rdquo;
            </p>
            <p className="text-[11px] text-frost-muted/70">
              Invented LSB Matching (±1 embedding), demonstrating that modifying pixel samples by ±1 breaks fixed PoV symmetry, granting immunity to standard Chi-Square steganalysis.
            </p>
          </div>

          <div className="p-4 rounded-xl glass-frosted border border-white/10 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-frost">Percival, C., &amp; Josefsson, S. (2016)</span>
              <span className="text-[10px] font-mono text-teal-liquid">IETF RFC 7914</span>
            </div>
            <p className="text-frost-muted italic">
              &ldquo;The scrypt Password-Based Key Derivation Function&rdquo;
            </p>
            <p className="text-[11px] text-frost-muted/70">
              Defined sequential memory-hard key derivation to neutralize parallel FPGA/ASIC password cracking.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
