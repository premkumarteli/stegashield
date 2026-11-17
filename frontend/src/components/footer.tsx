import Link from "next/link";
import { Shield, BookOpen, Lock, Activity } from "lucide-react";

export function Footer() {
  return (
    <footer className="mt-24 border-t border-white/10 bg-abyss-deep/70 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand Info */}
          <div className="space-y-3 md:col-span-1">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-teal-liquid" />
              <span className="font-semibold text-frost tracking-tight text-base">
                StegaShield
              </span>
            </div>
            <p className="text-xs text-frost-muted leading-relaxed">
              Academic-grade authenticated encrypted LSB steganography and statistical steganalysis experimentation platform.
            </p>
            <div className="flex items-center gap-2 text-[11px] text-teal-liquid/80 pt-1">
              <span className="w-2 h-2 rounded-full bg-teal-liquid animate-pulse" />
              <span>Zero-knowledge server ephemeral storage</span>
            </div>
          </div>

          {/* Core Modules */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-frost uppercase tracking-wider">
              Modules
            </h4>
            <ul className="space-y-1.5 text-xs text-frost-muted">
              <li>
                <Link href="/embed" className="hover:text-teal-liquid transition-colors">
                  Authenticated Embedding
                </Link>
              </li>
              <li>
                <Link href="/extract" className="hover:text-teal-liquid transition-colors">
                  Decryption & Extraction
                </Link>
              </li>
              <li>
                <Link href="/analyze" className="hover:text-teal-liquid transition-colors">
                  Distortion & Bitplane Analysis
                </Link>
              </li>
              <li>
                <Link href="/attack-lab" className="hover:text-teal-liquid transition-colors">
                  Attack Lab Matrix Engine
                </Link>
              </li>
            </ul>
          </div>

          {/* Cryptography & Detectors */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-frost uppercase tracking-wider flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-iris" />
              Standards
            </h4>
            <ul className="space-y-1.5 text-xs text-frost-muted">
              <li className="flex items-center gap-1.5">
                <span className="text-teal-liquid font-mono text-[10px]">KDF:</span> Scrypt (N=131072, r=8, p=1)
              </li>
              <li className="flex items-center gap-1.5">
                <span className="text-teal-liquid font-mono text-[10px]">CIPHER:</span> AES-256-GCM + AAD
              </li>
              <li className="flex items-center gap-1.5">
                <span className="text-teal-liquid font-mono text-[10px]">EMBED:</span> LSB Replacement & Matching (±1)
              </li>
              <li className="flex items-center gap-1.5">
                <span className="text-teal-liquid font-mono text-[10px]">ATTACKS:</span> Chi-Square & RS Analysis
              </li>
            </ul>
          </div>

          {/* Academic Citations */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-frost uppercase tracking-wider flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-mint" />
              Academic References
            </h4>
            <p className="text-[11px] text-frost-muted leading-relaxed">
              Westfeld & Pfitzmann (2000) IH&apos;99 · Fridrich, Goljan, Du (2001) IEEE MM · Mielikainen (2006) IEEE SPL.
            </p>
            <div className="pt-2">
              <Link
                href="/about"
                className="inline-flex items-center gap-1 text-xs text-teal-liquid hover:underline"
              >
                <Activity className="w-3.5 h-3.5" />
                <span>View Threat Model & Architecture</span>
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between text-[11px] text-frost-muted/60 gap-4">
          <p>© {new Date().getFullYear()} StegaShield Security Laboratory. All rights reserved.</p>
          <p className="font-mono text-[10px]">
            WCAG 2.2 AA Compliant · Abyssal Liquid System
          </p>
        </div>
      </div>
    </footer>
  );
}
