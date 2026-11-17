"use client";

import { useState, useCallback, useMemo } from "react";
import { useDropzone } from "react-dropzone";
import { ReactCompareSlider, ReactCompareSliderImage } from "react-compare-slider";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  BarChart3,
  Search,
  Upload,
  Layers,
  Activity,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Eye,
  RefreshCw,
  Sparkles,
  Sliders,
  ShieldAlert,
} from "lucide-react";
import { toast } from "sonner";
import {
  analyzeComparison,
  detectSteganography,
  type AnalyzeResponse,
  type DetectResponse,
} from "@/lib/api-client";
import { formatNumber } from "@/lib/utils";

export default function AnalyzePage() {
  const [activeTab, setActiveTab] = useState<"compare" | "detect">("compare");

  // ================= TAB 1: COMPARE STATE =================
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [coverPreview, setCoverPreview] = useState<string | null>(null);
  const [stegoFile, setStegoFile] = useState<File | null>(null);
  const [stegoPreview, setStegoPreview] = useState<string | null>(null);

  const [isComparing, setIsComparing] = useState<boolean>(false);
  const [compareResult, setCompareResult] = useState<AnalyzeResponse | null>(null);

  // Filter PoV bins for chart readability (e.g. sample every 4th or 8th bin or top bins)
  const povChartData = useMemo(() => {
    if (!compareResult?.pov_histogram?.bins) return [];
    const rawBins = compareResult.pov_histogram.bins as Array<{
      k: number;
      even_val: number;
      odd_val: number;
      even_count: number;
      odd_count: number;
      diff: number;
    }>;
    // Downsample 128 bins to 32 grouped or sampled bins for responsive rendering
    return rawBins.filter((_, idx) => idx % 4 === 0).map((bin) => ({
      pair: `${bin.even_val}/${bin.odd_val}`,
      even: bin.even_count,
      odd: bin.odd_count,
      diff: bin.diff,
    }));
  }, [compareResult]);

  // Dropzone for Cover in Compare Tab
  const onCoverDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setCoverFile(file);
      setCoverPreview(URL.createObjectURL(file));
      setCompareResult(null);
    }
  }, []);
  const { getRootProps: getCoverProps, getInputProps: getCoverInputProps, isDragActive: isCoverActive } =
    useDropzone({
      onDrop: onCoverDrop,
      accept: { "image/png": [".png"], "image/bmp": [".bmp"], "image/tiff": [".tiff", ".tif"] },
      multiple: false,
    });

  // Dropzone for Stego in Compare Tab
  const onStegoDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setStegoFile(file);
      setStegoPreview(URL.createObjectURL(file));
      setCompareResult(null);
    }
  }, []);
  const { getRootProps: getStegoProps, getInputProps: getStegoInputProps, isDragActive: isStegoActive } =
    useDropzone({
      onDrop: onStegoDrop,
      accept: { "image/png": [".png"], "image/bmp": [".bmp"], "image/tiff": [".tiff", ".tif"] },
      multiple: false,
    });

  const handleRunCompare = async () => {
    if (!coverFile || !stegoFile) {
      toast.error("Please provide both Cover and Stego images.");
      return;
    }

    setIsComparing(true);
    const toastId = toast.loading("Calculating MSE, PSNR, SSIM, Heatmap, Bitplane, and PoV distributions...");

    try {
      const formData = new FormData();
      formData.append("cover_file", coverFile);
      formData.append("stego_file", stegoFile);

      const resp = await analyzeComparison(formData);
      setCompareResult(resp);
      toast.success("Image comparison completed!", { id: toastId });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to analyze images";
      toast.error(msg, { id: toastId });
    } finally {
      setIsComparing(false);
    }
  };

  // ================= TAB 2: DETECT STATE =================
  const [candidateFile, setCandidateFile] = useState<File | null>(null);
  const [candidatePreview, setCandidatePreview] = useState<string | null>(null);
  const [isDetecting, setIsDetecting] = useState<boolean>(false);
  const [detectResult, setDetectResult] = useState<DetectResponse | null>(null);

  const onCandidateDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setCandidateFile(file);
      setCandidatePreview(URL.createObjectURL(file));
      setDetectResult(null);
    }
  }, []);
  const { getRootProps: getCandidateProps, getInputProps: getCandidateInputProps, isDragActive: isCandidateActive } =
    useDropzone({
      onDrop: onCandidateDrop,
      accept: { "image/png": [".png"], "image/bmp": [".bmp"], "image/tiff": [".tiff", ".tif"] },
      multiple: false,
    });

  const handleRunDetect = async () => {
    if (!candidateFile) {
      toast.error("Please provide a candidate image for steganalysis.");
      return;
    }

    setIsDetecting(true);
    const toastId = toast.loading("Executing Chi-Square (128 PoVs) & RS Analysis quadratic solver...");

    try {
      const formData = new FormData();
      formData.append("image_file", candidateFile);

      const resp = await detectSteganography(formData);
      setDetectResult(resp);
      toast.success("Steganalysis detection completed!", { id: toastId });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Steganalysis detection failed";
      toast.error(msg, { id: toastId });
    } finally {
      setIsDetecting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 py-4">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-clear border border-mint/30 text-mint text-xs font-mono font-medium">
            <Activity className="w-3.5 h-3.5" />
            <span>Quantitative Distortion &amp; Steganalysis</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-frost tracking-tight mt-2">
            Image Quality &amp; Steganalysis Auditor
          </h1>
          <p className="text-xs sm:text-sm text-frost-muted mt-1">
            Audit carrier images using pairwise distortion analysis or blind statistical steganalysis.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center p-1 rounded-xl glass-deep border border-white/10 self-start sm:self-center">
          <button
            type="button"
            onClick={() => setActiveTab("compare")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "compare"
                ? "glass-active text-teal-liquid shadow-teal-glow"
                : "text-frost-muted hover:text-frost"
            }`}
          >
            <Sliders className="w-4 h-4" />
            <span>Tab 1: Compare (Cover vs Stego)</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("detect")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "detect"
                ? "glass-active text-mint shadow-glass-sm"
                : "text-frost-muted hover:text-frost"
            }`}
          >
            <Search className="w-4 h-4" />
            <span>Tab 2: Detect (Blind Steganalysis)</span>
          </button>
        </div>
      </div>

      {/* ================= TAB 1: COMPARE ================= */}
      {activeTab === "compare" && (
        <div className="space-y-8">
          {/* Dual Dropzones */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Cover Dropzone */}
            <div className="glass-deep rounded-2xl p-6 border border-white/10 space-y-3">
              <span className="text-xs font-semibold text-frost flex items-center justify-between">
                <span>Cover Image (Reference)</span>
                {coverFile && <span className="text-[10px] font-mono text-teal-liquid">Loaded</span>}
              </span>

              <div
                {...getCoverProps()}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-2 ${
                  isCoverActive
                    ? "border-teal-liquid bg-teal-liquid/10"
                    : "border-white/10 hover:border-teal-liquid/30 bg-abyss-deep/40"
                }`}
              >
                <input {...getCoverInputProps()} />
                <Upload className="w-6 h-6 text-teal-liquid" />
                <p className="text-xs font-medium text-frost">
                  {coverFile ? coverFile.name : "Select or drop original cover image"}
                </p>
                <p className="text-[10px] text-frost-muted">PNG, BMP, TIFF</p>
              </div>

              {coverPreview && (
                <div className="h-32 rounded-lg overflow-hidden border border-white/10 bg-black/40 flex items-center justify-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={coverPreview} alt="Cover preview" className="h-full object-contain" />
                </div>
              )}
            </div>

            {/* Stego Dropzone */}
            <div className="glass-deep rounded-2xl p-6 border border-white/10 space-y-3">
              <span className="text-xs font-semibold text-frost flex items-center justify-between">
                <span>Stego Image (Carrier to Compare)</span>
                {stegoFile && <span className="text-[10px] font-mono text-teal-liquid">Loaded</span>}
              </span>

              <div
                {...getStegoProps()}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-2 ${
                  isStegoActive
                    ? "border-teal-liquid bg-teal-liquid/10"
                    : "border-white/10 hover:border-teal-liquid/30 bg-abyss-deep/40"
                }`}
              >
                <input {...getStegoInputProps()} />
                <Upload className="w-6 h-6 text-mint" />
                <p className="text-xs font-medium text-frost">
                  {stegoFile ? stegoFile.name : "Select or drop stego carrier image"}
                </p>
                <p className="text-[10px] text-frost-muted">PNG, BMP, TIFF</p>
              </div>

              {stegoPreview && (
                <div className="h-32 rounded-lg overflow-hidden border border-white/10 bg-black/40 flex items-center justify-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={stegoPreview} alt="Stego preview" className="h-full object-contain" />
                </div>
              )}
            </div>
          </div>

          {/* Action Trigger */}
          <div className="flex justify-end">
            <button
              type="button"
              disabled={!coverFile || !stegoFile || isComparing}
              onClick={handleRunCompare}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl liquid-btn-primary text-xs font-semibold"
            >
              {isComparing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Computing Metrics...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Run Distortion Comparison</span>
                </>
              )}
            </button>
          </div>

          {/* Comparison Results */}
          {compareResult && coverPreview && stegoPreview && (
            <div className="space-y-8 pt-4">
              {/* Distortion Metrics Table */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="glass-deep p-5 rounded-2xl border border-white/10 text-center">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-frost-muted">
                    MSE (Mean Squared Error)
                  </span>
                  <p className="text-3xl font-mono font-bold text-teal-liquid mt-1">
                    {formatNumber(compareResult.mse, 5)}
                  </p>
                  <span className="text-[10px] text-frost-muted/70">Average squared pixel difference</span>
                </div>

                <div className="glass-deep p-5 rounded-2xl border border-white/10 text-center">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-frost-muted">
                    PSNR (Peak Signal-to-Noise)
                  </span>
                  <p className="text-3xl font-mono font-bold text-mint mt-1">
                    {formatNumber(compareResult.psnr, 2)} dB
                  </p>
                  <span className="text-[10px] text-frost-muted/70">&gt; 50 dB represents near perfection</span>
                </div>

                <div className="glass-deep p-5 rounded-2xl border border-white/10 text-center">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-frost-muted">
                    SSIM (Structural Similarity)
                  </span>
                  <p className="text-3xl font-mono font-bold text-iris mt-1">
                    {formatNumber(compareResult.ssim, 5)}
                  </p>
                  <span className="text-[10px] text-frost-muted/70">Gaussian-filtered perceptual index [0..1]</span>
                </div>
              </div>

              {/* Before / After Slider */}
              <div className="glass-deep rounded-2xl p-6 border border-white/10 space-y-3">
                <div className="flex items-center justify-between text-xs font-semibold text-frost">
                  <span>Interactive Split Slider: Cover (Left) vs Stego (Right)</span>
                  <span className="text-[10px] font-mono text-teal-liquid">Pixel-Aligned Comparison</span>
                </div>
                <div className="rounded-xl overflow-hidden border border-white/10 h-[380px] sm:h-[460px] bg-black/60">
                  <ReactCompareSlider
                    itemOne={<ReactCompareSliderImage src={coverPreview} alt="Cover" />}
                    itemTwo={<ReactCompareSliderImage src={stegoPreview} alt="Stego" />}
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>

              {/* Visual Maps: Difference Heatmap & Bitplane Viewer */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Amplified Heatmap */}
                <div className="glass-deep rounded-2xl p-6 border border-white/10 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-frost flex items-center gap-1.5">
                      <Eye className="w-3.5 h-3.5 text-teal-liquid" />
                      Amplified Difference Heatmap
                    </span>
                    <span className="text-[10px] font-mono text-frost-muted">Scaled Residuals</span>
                  </div>
                  <div className="h-64 rounded-xl overflow-hidden border border-white/10 bg-black/50 flex items-center justify-center">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={compareResult.heatmap_url}
                      alt="Amplified difference heatmap"
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>
                  <p className="text-[11px] text-frost-muted leading-relaxed">
                    Per-pixel differences are scaled by a high factor to visually reveal exact coordinates where LSB bits were modified.
                  </p>
                </div>

                {/* Bitplane Slice (Bit 0) */}
                <div className="glass-deep rounded-2xl p-6 border border-white/10 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-frost flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-iris" />
                      Bit 0 Bitplane Slicer
                    </span>
                    <span className="text-[10px] font-mono text-frost-muted">LSB Slice</span>
                  </div>
                  <div className="h-64 rounded-xl overflow-hidden border border-white/10 bg-black/50 flex items-center justify-center">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={compareResult.bitplane_url}
                      alt="LSB Bitplane slice"
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>
                  <p className="text-[11px] text-frost-muted leading-relaxed">
                    Isolates Bit 0 across all pixels. Random noisy patterns indicate high-density encrypted payload dispersion.
                  </p>
                </div>
              </div>

              {/* Pairs-of-Values (PoV) Histogram */}
              <div className="glass-deep rounded-2xl p-6 border border-white/10 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-frost flex items-center gap-2">
                      <BarChart3 className="w-4 h-4 text-teal-liquid" />
                      Pairs-of-Values (PoV) Histogram Distribution
                    </h3>
                    <p className="text-xs text-frost-muted mt-0.5">
                      Compares even (2k) and odd (2k+1) pixel frequencies across color bins [0..255].
                    </p>
                  </div>
                  <span className="text-xs font-mono text-frost-muted">
                    Channel: <strong className="text-teal-liquid uppercase">{String(compareResult.pov_histogram.channel)}</strong>
                  </span>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={povChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                      <XAxis
                        dataKey="pair"
                        stroke="#91A9B2"
                        tick={{ fontSize: 9 }}
                        angle={-45}
                        textAnchor="end"
                      />
                      <YAxis stroke="#91A9B2" tick={{ fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#07131D",
                          borderColor: "rgba(54, 214, 195, 0.4)",
                          borderRadius: "12px",
                          fontSize: "11px",
                          color: "#E5F1F3",
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }} />
                      <Bar dataKey="even" name="Even (2k)" fill="#36D6C3" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="odd" name="Odd (2k+1)" fill="#9B91F5" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="text-[11px] text-frost-muted p-3 rounded-xl bg-abyss-deep/60 border border-white/5 flex gap-2">
                  <HelpCircle className="w-4 h-4 text-teal-liquid shrink-0 mt-0.5" />
                  <p>
                    In clean natural images, even and odd pixel frequencies vary independently. Standard LSB Replacement equalizes frequencies within pairs (causing counts to flatten toward equality), which the Chi-Square detector exploits. LSB Matching (±1) avoids this signature.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ================= TAB 2: DETECT ================= */}
      {activeTab === "detect" && (
        <div className="space-y-8">
          {/* Single Image Dropzone */}
          <div className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-4">
            <div>
              <h2 className="text-lg font-bold text-frost flex items-center gap-2">
                <Search className="w-5 h-5 text-mint" />
                Blind Statistical Steganalysis
              </h2>
              <p className="text-xs text-frost-muted mt-1">
                Upload any suspicious image. StegaShield executes Westfeld &amp; Pfitzmann (2000) Chi-Square attack and Fridrich, Goljan, Du (2001) RS Analysis to detect hidden payloads without requiring the original cover image.
              </p>
            </div>

            <div
              {...getCandidateProps()}
              className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-3 ${
                isCandidateActive
                  ? "border-mint bg-mint/10 shadow-glass-md"
                  : "border-white/15 hover:border-mint/40 bg-abyss-deep/40 hover:bg-abyss-deep/60"
              }`}
            >
              <input {...getCandidateInputProps()} />
              <div className="w-12 h-12 rounded-xl bg-mint/10 border border-mint/30 text-mint flex items-center justify-center">
                <Search className="w-6 h-6" />
              </div>
              <p className="text-sm font-semibold text-frost">
                {candidateFile ? candidateFile.name : "Drop suspicious candidate image here, or browse"}
              </p>
              <p className="text-xs text-frost-muted">
                Accepts PNG, BMP, TIFF formats up to 16MP
              </p>
            </div>

            {candidatePreview && (
              <div className="glass-frosted p-3 rounded-xl border border-white/10 flex items-center gap-4">
                <div className="w-16 h-16 rounded-lg overflow-hidden border border-white/20 shrink-0 bg-black/40">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={candidatePreview} alt="Candidate preview" className="w-full h-full object-cover" />
                </div>
                <div className="text-xs space-y-0.5">
                  <p className="font-semibold text-frost">{candidateFile?.name}</p>
                  <p className="text-frost-muted">Ready for statistical feature extraction</p>
                </div>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                type="button"
                disabled={!candidateFile || isDetecting}
                onClick={handleRunDetect}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl liquid-btn-primary text-xs font-semibold"
              >
                {isDetecting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Analyzing Frequencies &amp; Dual Masks...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Run Steganalysis Suite</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Steganalysis Verdict & Gauges */}
          {detectResult && (
            <div className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-8 shadow-glass-lg">
              {/* Overall Calibrated Verdict Banner */}
              <div
                className={`p-5 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  detectResult.classification === "clean"
                    ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-200"
                    : detectResult.classification === "suspicious"
                    ? "bg-amber-500/15 border-amber-500/30 text-amber-200"
                    : "bg-rose-500/15 border-rose-500/40 text-rose-200"
                }`}
              >
                <div className="flex items-center gap-3">
                  {detectResult.classification === "clean" ? (
                    <CheckCircle2 className="w-7 h-7 text-emerald-400 shrink-0" />
                  ) : detectResult.classification === "suspicious" ? (
                    <AlertTriangle className="w-7 h-7 text-amber-400 shrink-0" />
                  ) : (
                    <ShieldAlert className="w-7 h-7 text-rose-400 shrink-0" />
                  )}
                  <div>
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider">
                      Composite Steganalysis Verdict
                    </span>
                    <h3 className="text-xl font-bold uppercase tracking-tight">
                      Classification: {detectResult.classification.replace("_", " ")}
                    </h3>
                  </div>
                </div>

                <div className="font-mono text-xs text-right">
                  <span>Operation ID: {detectResult.operation_id}</span>
                </div>
              </div>

              {/* Gauges Grid: Chi-Square vs RS Analysis */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Detector 1: Westfeld Chi-Square */}
                <div className="glass-frosted p-6 rounded-2xl border border-white/10 space-y-4">
                  <div className="flex items-center justify-between border-b border-white/10 pb-3">
                    <div>
                      <h4 className="text-sm font-bold text-frost">Westfeld Chi-Square Attack</h4>
                      <p className="text-[11px] text-frost-muted">PoV Equalization Test (IH&apos;99)</p>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                        String(detectResult.chi_square.classification) === "clean"
                          ? "bg-emerald-500/20 text-emerald-300"
                          : "bg-rose-500/20 text-rose-300"
                      }`}
                    >
                      {String(detectResult.chi_square.classification)}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div className="p-3 rounded-xl bg-abyss-deep/60 border border-white/5">
                      <span className="text-[10px] text-frost-muted">p-value</span>
                      <p className="text-xl font-mono font-bold text-teal-liquid mt-0.5">
                        {Number(detectResult.chi_square.p_value) < 0.0001
                          ? "< 0.0001"
                          : Number(detectResult.chi_square.p_value).toFixed(4)}
                      </p>
                      <span className="text-[9px] text-frost-muted/60">Threshold: p &lt; 0.05</span>
                    </div>

                    <div className="p-3 rounded-xl bg-abyss-deep/60 border border-white/5">
                      <span className="text-[10px] text-frost-muted">Chi² Statistic</span>
                      <p className="text-xl font-mono font-bold text-frost mt-0.5">
                        {formatNumber(Number(detectResult.chi_square.chi2), 2)}
                      </p>
                      <span className="text-[9px] text-frost-muted/60">df = {String(detectResult.chi_square.df)}</span>
                    </div>
                  </div>

                  <p className="text-[11px] text-frost-muted leading-relaxed">
                    Evaluates pairs-of-values frequency deviations against expected chi-square distribution with Cochran test filter.
                  </p>
                </div>

                {/* Detector 2: Fridrich RS Analysis */}
                <div className="glass-frosted p-6 rounded-2xl border border-white/10 space-y-4">
                  <div className="flex items-center justify-between border-b border-white/10 pb-3">
                    <div>
                      <h4 className="text-sm font-bold text-frost">Fridrich RS Steganalysis</h4>
                      <p className="text-[11px] text-frost-muted">Dual-Mask Quadratic Solver (IEEE MM 2001)</p>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                        String(detectResult.rs_analysis.classification) === "clean"
                          ? "bg-emerald-500/20 text-emerald-300"
                          : "bg-rose-500/20 text-rose-300"
                      }`}
                    >
                      {String(detectResult.rs_analysis.classification)}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div className="p-3 rounded-xl bg-abyss-deep/60 border border-white/5">
                      <span className="text-[10px] text-frost-muted">Estimated Payload Ratio</span>
                      <p className="text-xl font-mono font-bold text-mint mt-0.5">
                        {(Number(detectResult.rs_analysis.estimated_payload_ratio) * 100).toFixed(2)}%
                      </p>
                      <span className="text-[9px] text-frost-muted/60">Alpha root</span>
                    </div>

                    <div className="p-3 rounded-xl bg-abyss-deep/60 border border-white/5">
                      <span className="text-[10px] text-frost-muted">Regular / Singular</span>
                      <p className="text-xs font-mono font-bold text-frost mt-1.5">
                        Rm: {Number(detectResult.rs_analysis.regular_m).toFixed(3)}
                      </p>
                      <p className="text-xs font-mono font-bold text-frost-muted">
                        Sm: {Number(detectResult.rs_analysis.singular_m).toFixed(3)}
                      </p>
                    </div>
                  </div>

                  <p className="text-[11px] text-frost-muted leading-relaxed">
                    Analyzes smoothness variation curves under invertible Flipping masks M = [0,1,1,0] and -M.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
