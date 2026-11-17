"use client";

import { useState } from "react";
import { Eye, Info, RotateCcw, Zap } from "lucide-react";

export function PixelWidget() {
  // Initial baseline pixel: RGB(186, 142, 205)
  const [origR] = useState(186);
  const [origG] = useState(142);
  const [origB] = useState(205);

  const [activeChannel, setActiveChannel] = useState<"R" | "G" | "B">("R");
  const [rBits, setRBits] = useState<number[]>([1, 0, 1, 1, 1, 0, 1, 0]); // 186 in binary
  const [gBits, setGBits] = useState<number[]>([1, 0, 0, 0, 1, 1, 1, 0]); // 142 in binary
  const [bBits, setBBits] = useState<number[]>([1, 1, 0, 0, 1, 1, 0, 1]); // 205 in binary

  const currentBits =
    activeChannel === "R" ? rBits : activeChannel === "G" ? gBits : bBits;

  const setCurrentBits = (newBits: number[]) => {
    if (activeChannel === "R") setRBits(newBits);
    else if (activeChannel === "G") setGBits(newBits);
    else setBBits(newBits);
  };

  const bitsToValue = (bits: number[]) =>
    bits.reduce((acc, bit, idx) => acc + (bit ? Math.pow(2, 7 - idx) : 0), 0);

  const currentVal = bitsToValue(currentBits);
  const origVal =
    activeChannel === "R" ? origR : activeChannel === "G" ? origG : origB;
  const delta = Math.abs(currentVal - origVal);

  const curR = bitsToValue(rBits);
  const curG = bitsToValue(gBits);
  const curB = bitsToValue(bBits);

  const toggleBit = (index: number) => {
    const updated = [...currentBits];
    const val = updated[index];
    if (val !== undefined) {
      updated[index] = val === 1 ? 0 : 1;
      setCurrentBits(updated);
    }
  };

  const flipLSBOnly = () => {
    const updated = [...currentBits];
    const lsb = updated[7];
    if (lsb !== undefined) {
      updated[7] = lsb === 1 ? 0 : 1;
      setCurrentBits(updated);
    }
  };

  const flipMSBOnly = () => {
    const updated = [...currentBits];
    const msb = updated[0];
    if (msb !== undefined) {
      updated[0] = msb === 1 ? 0 : 1;
      setCurrentBits(updated);
    }
  };

  const resetAll = () => {
    setRBits([1, 0, 1, 1, 1, 0, 1, 0]);
    setGBits([1, 0, 0, 0, 1, 1, 1, 0]);
    setBBits([1, 1, 0, 0, 1, 1, 0, 1]);
  };

  const diffIntensity = Math.min(255, delta * 32);

  return (
    <div className="glass-deep rounded-2xl p-6 border border-teal-liquid/30 shadow-glass-lg relative overflow-hidden">
      {/* Background Accent glow */}
      <div className="absolute -top-16 -right-16 w-48 h-48 rounded-full bg-teal-liquid/10 blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded-md bg-teal-liquid/15 text-teal-liquid border border-teal-liquid/30">
              Interactive Hardware Visualizer
            </span>
            <span className="text-xs text-frost-muted">8-Bit Bitplane Architecture</span>
          </div>
          <h3 className="text-lg font-bold text-frost mt-1">
            Least Significant Bit (LSB) Pixel Micro-Analyzer
          </h3>
          <p className="text-xs text-frost-muted mt-0.5">
            Click individual bits below to observe why changing Bit 0 is mathematically invisible to human photoreceptors.
          </p>
        </div>

        <button
          type="button"
          onClick={resetAll}
          className="self-start sm:self-center flex items-center gap-1.5 px-3 py-1.5 text-xs text-frost-muted hover:text-frost glass-clear rounded-xl transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Bits</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-6 items-start">
        {/* Left Column: Bit Array Controls */}
        <div className="lg:col-span-7 space-y-5">
          {/* Channel selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-frost-muted uppercase tracking-wider">
              Channel:
            </span>
            {(["R", "G", "B"] as const).map((ch) => (
              <button
                key={ch}
                type="button"
                onClick={() => setActiveChannel(ch)}
                className={`px-3 py-1 text-xs font-mono font-bold rounded-lg transition-all ${
                  activeChannel === ch
                    ? ch === "R"
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/50"
                      : ch === "G"
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/50"
                      : "bg-cyan-500/20 text-cyan-300 border border-cyan-500/50"
                    : "glass-clear text-frost-muted hover:text-frost"
                }`}
              >
                {ch === "R" ? "Red" : ch === "G" ? "Green" : "Blue"}
              </button>
            ))}
          </div>

          {/* 8-Bit Interactive Strip */}
          <div>
            <div className="flex items-center justify-between text-[11px] font-mono text-frost-muted mb-2 px-1">
              <span className="flex items-center gap-1 text-amber-300">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                Bit 7 (MSB, 2⁷ = 128)
              </span>
              <span className="flex items-center gap-1 text-teal-liquid">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-liquid animate-pulse" />
                Bit 0 (LSB, 2⁰ = 1)
              </span>
            </div>

            <div className="grid grid-cols-8 gap-1.5 sm:gap-2">
              {currentBits.map((bit, idx) => {
                const bitPower = Math.pow(2, 7 - idx);
                const isLSB = idx === 7;
                const isMSB = idx === 0;

                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => toggleBit(idx)}
                    className={`flex flex-col items-center justify-center p-2 sm:p-2.5 rounded-xl border transition-all select-none relative group ${
                      bit === 1
                        ? isLSB
                          ? "bg-teal-liquid/25 border-teal-liquid text-teal-liquid shadow-teal-glow"
                          : "bg-white/15 border-white/30 text-frost"
                        : "bg-black/30 border-white/10 text-frost-muted hover:border-white/25"
                    }`}
                  >
                    <span className="text-[10px] font-mono text-frost-muted/70 mb-0.5">
                      b{7 - idx}
                    </span>
                    <span className="text-base sm:text-lg font-mono font-bold">
                      {bit}
                    </span>
                    <span className="text-[9px] font-mono text-frost-muted/50 mt-0.5">
                      {bitPower}
                    </span>

                    {/* Tag label */}
                    {isLSB && (
                      <span className="absolute -bottom-5 px-1 py-0.2 rounded bg-teal-liquid text-black text-[8px] font-bold tracking-tight">
                        LSB
                      </span>
                    )}
                    {isMSB && (
                      <span className="absolute -bottom-5 px-1 py-0.2 rounded bg-amber-400 text-black text-[8px] font-bold tracking-tight">
                        MSB
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Quick experiment buttons */}
          <div className="flex flex-wrap gap-2 pt-4">
            <button
              type="button"
              onClick={flipLSBOnly}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-teal-liquid/15 text-teal-liquid border border-teal-liquid/40 hover:bg-teal-liquid/25 transition-all"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Flip LSB (±1 Secret Embed)</span>
            </button>
            <button
              type="button"
              onClick={flipMSBOnly}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-amber-500/15 text-amber-300 border border-amber-500/40 hover:bg-amber-500/25 transition-all"
            >
              <span>Flip MSB (±128 Distortion)</span>
            </button>
          </div>
        </div>

        {/* Right Column: Visualizer Swatches & Amplification */}
        <div className="lg:col-span-5 space-y-4 glass-frosted p-4 rounded-xl border border-white/10">
          <div className="text-xs font-semibold text-frost flex items-center justify-between">
            <span>Visual Perception Test</span>
            <span className="text-[10px] font-mono text-frost-muted">
              Diff: Δ = {delta} ({(delta / 255 * 100).toFixed(2)}%)
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Original Color */}
            <div className="space-y-1.5 text-center">
              <span className="text-[11px] text-frost-muted">Original Pixel</span>
              <div
                className="h-20 rounded-xl border border-white/20 shadow-inner flex items-center justify-center transition-colors"
                style={{ backgroundColor: `rgb(${origR}, ${origG}, ${origB})` }}
              >
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/60 text-frost backdrop-blur-sm">
                  {origR},{origG},{origB}
                </span>
              </div>
              <span className="text-[10px] font-mono text-frost-muted">
                Val: {origVal}
              </span>
            </div>

            {/* Stego Color */}
            <div className="space-y-1.5 text-center">
              <span className="text-[11px] text-frost-muted">Altered (Stego)</span>
              <div
                className="h-20 rounded-xl border border-white/20 shadow-inner flex items-center justify-center transition-colors relative overflow-hidden"
                style={{ backgroundColor: `rgb(${curR}, ${curG}, ${curB})` }}
              >
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/60 text-frost backdrop-blur-sm">
                  {curR},{curG},{curB}
                </span>
              </div>
              <span className="text-[10px] font-mono text-frost-muted">
                Val: {currentVal}
              </span>
            </div>
          </div>

          {/* Amplified Difference Map */}
          <div className="space-y-1.5 pt-2 border-t border-white/10">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-frost-muted flex items-center gap-1">
                <Eye className="w-3.5 h-3.5 text-teal-liquid" />
                Amplified Residual Heatmap (32x)
              </span>
              <span className="font-mono text-teal-liquid">
                {delta === 0 ? "Identical" : delta === 1 ? "Imperceptible" : "Visible Artefact"}
              </span>
            </div>
            <div
              className="h-6 rounded-lg border border-white/10 transition-colors flex items-center justify-center"
              style={{
                backgroundColor: `rgb(${diffIntensity}, 0, ${diffIntensity > 0 ? 50 : 0})`,
              }}
            >
              <span className="text-[10px] font-mono text-white/80">
                Residual: {delta} unit{delta !== 1 ? "s" : ""}
              </span>
            </div>
          </div>

          {/* Mathematical takeaway */}
          <div className="text-[11px] text-frost-muted bg-abyss-deep/60 p-2.5 rounded-lg border border-white/5 flex gap-2">
            <Info className="w-4 h-4 text-teal-liquid shrink-0 mt-0.5" />
            <p>
              {delta === 1
                ? "Flipping bit 0 changes luminance by only 0.39%. The human eye's Just Noticeable Difference (JND) threshold requires a delta of ≥ 3 to 5 units."
                : delta === 0
                ? "Bits are currently synchronized with the original cover pixel."
                : `Flipping higher bits introduces a massive delta of ${delta} (${(delta / 255 * 100).toFixed(1)}%), immediately exposing steganographic corruption.`}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
