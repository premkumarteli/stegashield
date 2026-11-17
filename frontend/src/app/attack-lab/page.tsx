"use client";

import { useState, useEffect, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
} from "recharts";
import {
  Flame,
  Play,
  Download,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Activity,
  Layers,
  Search,
  Sliders,
  Table,
} from "lucide-react";
import { toast } from "sonner";
import { startAttackLab } from "@/lib/api-client";

interface ExperimentItem {
  method: string;
  ratio: number;
  detector: string;
  detected: boolean;
  score?: number;
}

interface ExperimentSummary {
  experiment_id: string;
  total_items: number;
  methods: string[];
  ratios: number[];
  detectors: string[];
  false_positive_rate?: number;
  matrix?: Record<string, Record<string, number>>; // method -> ratio -> detection_rate
  items?: ExperimentItem[];
}

export default function AttackLabPage() {
  // Configuration options
  const [methods, setMethods] = useState<string[]>(["lsb_replacement", "lsb_matching"]);
  const [ratios, setRatios] = useState<number[]>([0.05, 0.1, 0.25, 0.5, 1.0]);
  const [detectors, setDetectors] = useState<string[]>(["chi_square", "rs"]);

  // Execution state
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isMutexLocked, setIsMutexLocked] = useState<boolean>(false);
  const [experimentId, setExperimentId] = useState<string | null>(null);
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [progressStep, setProgressStep] = useState<{ current: number; total: number }>({ current: 0, total: 0 });
  const [currentItemDesc, setCurrentItemDesc] = useState<string | null>(null);
  const [summaryData, setSummaryData] = useState<ExperimentSummary | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);

  // Toggle helpers
  const toggleMethod = (m: string) => {
    setMethods((prev) =>
      prev.includes(m) ? (prev.length > 1 ? prev.filter((x) => x !== m) : prev) : [...prev, m]
    );
  };

  const toggleRatio = (r: number) => {
    setRatios((prev) =>
      prev.includes(r) ? (prev.length > 1 ? prev.filter((x) => x !== r) : prev) : [...prev, r].sort((a, b) => a - b)
    );
  };

  const toggleDetector = (d: string) => {
    setDetectors((prev) =>
      prev.includes(d) ? (prev.length > 1 ? prev.filter((x) => x !== d) : prev) : [...prev, d]
    );
  };

  // Cleanup EventSource on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleStartExperiment = async () => {
    setIsRunning(true);
    setIsMutexLocked(false);
    setProgressPercent(0);
    setProgressStep({ current: 0, total: 0 });
    setSummaryData(null);
    setCurrentItemDesc("Initializing experimental harness...");

    const toastId = toast.loading("Acquiring Attack Lab mutex lock...");

    try {
      const resp = await startAttackLab({ methods, ratios, detectors });
      setExperimentId(resp.experiment_id);
      toast.success("Experiment started. Listening to live telemetry stream...", { id: toastId });

      // Connect to SSE stream
      const sseUrl = `/api/v1/attack-lab/progress/${resp.experiment_id}`;
      const es = new EventSource(sseUrl);
      eventSourceRef.current = es;

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.percent !== undefined) setProgressPercent(data.percent);
          if (data.current_step !== undefined && data.total_steps !== undefined) {
            setProgressStep({ current: data.current_step, total: data.total_steps });
          }

          if (data.current_item) {
            setCurrentItemDesc(
              `Evaluating ${data.current_item.method} @ ${(data.current_item.ratio * 100).toFixed(0)}% payload via ${data.current_item.detector}`
            );
          }

          if (data.status === "completed" || data.percent >= 100) {
            setIsRunning(false);
            setCurrentItemDesc("Experiment matrix complete.");
            if (data.summary) {
              setSummaryData(data.summary);
            }
            es.close();
            toast.success("Attack Lab matrix evaluation finished!");
          }
        } catch {
          // Keep stream open
        }
      };

      es.onerror = () => {
        // SSE disconnected or finished
        es.close();
        setIsRunning(false);
      };
    } catch (err: unknown) {
      setIsRunning(false);
      const msg = err instanceof Error ? err.message : "Failed to start experiment";
      if (msg.includes("ACTIVE_EXPERIMENT_RUNNING") || msg.includes("409")) {
        setIsMutexLocked(true);
        toast.error("Cluster Busy: Another experiment is currently active.", { id: toastId });
      } else {
        toast.error(msg, { id: toastId });
      }
    }
  };

  // Recharts Line Chart Data: Detection Rate vs Payload Ratio
  const chartData = ratios.map((ratio) => {
    const entry: Record<string, number | string> = {
      ratio: `${(ratio * 100).toFixed(0)}%`,
    };

    if (summaryData?.items) {
      // Compute actual measured rates from items
      methods.forEach((m) => {
        detectors.forEach((d) => {
          const matchingItems = summaryData.items?.filter(
            (it) => it.method === m && Math.abs(it.ratio - ratio) < 0.001 && it.detector === d
          );
          if (matchingItems && matchingItems.length > 0) {
            const detectedCount = matchingItems.filter((it) => it.detected).length;
            const rate = (detectedCount / matchingItems.length) * 100;
            const key = `${m === "lsb_matching" ? "Matching" : "Replacement"} (${d === "chi_square" ? "Chi²" : "RS"})`;
            entry[key] = parseFloat(rate.toFixed(1));
          }
        });
      });
    }

    return entry;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-8 py-4">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-clear border border-rose-500/30 text-rose-400 text-xs font-mono font-medium">
            <Flame className="w-3.5 h-3.5" />
            <span>Empirical Attack Matrix Engine</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-frost tracking-tight mt-2">
            Steganalysis Attack Lab
          </h1>
          <p className="text-xs sm:text-sm text-frost-muted mt-1">
            Automated matrix evaluation across embedding methods, payload ratios, and statistical detectors with real-time SSE progress.
          </p>
        </div>

        {experimentId && (
          <a
            href={`/api/v1/attack-lab/export/${experimentId}`}
            download={`attack_lab_${experimentId}.csv`}
            className="flex items-center gap-2 px-4 py-2 rounded-xl glass-frosted text-xs font-semibold text-frost hover:border-teal-liquid/40 self-start sm:self-center"
          >
            <Download className="w-4 h-4 text-teal-liquid" />
            <span>Export RFC 4180 CSV</span>
          </a>
        )}
      </div>

      {/* Mutex Locked Warning */}
      {isMutexLocked && (
        <div className="p-4 rounded-2xl bg-amber-500/15 border border-amber-500/40 text-amber-200 text-xs flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-amber-400 shrink-0" />
          <p className="leading-relaxed">
            <strong>Mutex Lock Active:</strong> Another Attack Lab sweep is currently in progress. StegaShield enforces single-instance CPU concurrency to ensure exact benchmark validity. Please wait ~30 seconds and retry.
          </p>
        </div>
      )}

      {/* Experiment Configuration Panel */}
      <section className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-6">
        <h2 className="text-base font-bold text-frost flex items-center gap-2">
          <Sliders className="w-4 h-4 text-teal-liquid" />
          Matrix Configuration
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Methods Selection */}
          <div className="space-y-3">
            <span className="text-xs font-semibold text-frost flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-teal-liquid" />
              Embedding Algorithms
            </span>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => toggleMethod("lsb_matching")}
                className={`w-full p-3 rounded-xl border text-left text-xs font-medium transition-all flex items-center justify-between ${
                  methods.includes("lsb_matching")
                    ? "glass-active border-teal-liquid text-frost"
                    : "glass-clear border-white/5 text-frost-muted"
                }`}
              >
                <div>
                  <p className="font-bold">LSB Matching (±1)</p>
                  <p className="text-[10px] text-frost-muted">PoV Symmetry Preserved</p>
                </div>
                {methods.includes("lsb_matching") && <CheckCircle2 className="w-4 h-4 text-teal-liquid" />}
              </button>

              <button
                type="button"
                onClick={() => toggleMethod("lsb_replacement")}
                className={`w-full p-3 rounded-xl border text-left text-xs font-medium transition-all flex items-center justify-between ${
                  methods.includes("lsb_replacement")
                    ? "glass-active border-teal-liquid text-frost"
                    : "glass-clear border-white/5 text-frost-muted"
                }`}
              >
                <div>
                  <p className="font-bold">LSB Replacement</p>
                  <p className="text-[10px] text-frost-muted">Classic Bit Substitution</p>
                </div>
                {methods.includes("lsb_replacement") && <CheckCircle2 className="w-4 h-4 text-teal-liquid" />}
              </button>
            </div>
          </div>

          {/* Payload Ratios Selection */}
          <div className="space-y-3">
            <span className="text-xs font-semibold text-frost flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-mint" />
              Payload Capacities (bpp)
            </span>
            <div className="grid grid-cols-3 gap-2">
              {[0.05, 0.1, 0.25, 0.5, 1.0].map((r) => {
                const isSelected = ratios.includes(r);
                return (
                  <button
                    key={r}
                    type="button"
                    onClick={() => toggleRatio(r)}
                    className={`p-2.5 rounded-xl border text-center font-mono text-xs font-bold transition-all ${
                      isSelected
                        ? "glass-active border-mint text-mint shadow-glass-sm"
                        : "glass-clear border-white/5 text-frost-muted hover:text-frost"
                    }`}
                  >
                    {(r * 100).toFixed(0)}%
                  </button>
                );
              })}
            </div>
            <p className="text-[10px] text-frost-muted">
              Select ratio fractions of total maximum carrier bits.
            </p>
          </div>

          {/* Detectors Selection */}
          <div className="space-y-3">
            <span className="text-xs font-semibold text-frost flex items-center gap-1.5">
              <Search className="w-3.5 h-3.5 text-iris" />
              Statistical Detectors
            </span>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => toggleDetector("chi_square")}
                className={`w-full p-3 rounded-xl border text-left text-xs font-medium transition-all flex items-center justify-between ${
                  detectors.includes("chi_square")
                    ? "glass-active border-iris text-frost"
                    : "glass-clear border-white/5 text-frost-muted"
                }`}
              >
                <div>
                  <p className="font-bold">Chi-Square (Westfeld &apos;00)</p>
                  <p className="text-[10px] text-frost-muted">128 PoVs Cochran Filter</p>
                </div>
                {detectors.includes("chi_square") && <CheckCircle2 className="w-4 h-4 text-iris" />}
              </button>

              <button
                type="button"
                onClick={() => toggleDetector("rs")}
                className={`w-full p-3 rounded-xl border text-left text-xs font-medium transition-all flex items-center justify-between ${
                  detectors.includes("rs")
                    ? "glass-active border-iris text-frost"
                    : "glass-clear border-white/5 text-frost-muted"
                }`}
              >
                <div>
                  <p className="font-bold">RS Analysis (Fridrich &apos;01)</p>
                  <p className="text-[10px] text-frost-muted">Dual-Mask Quadratic Root</p>
                </div>
                {detectors.includes("rs") && <CheckCircle2 className="w-4 h-4 text-iris" />}
              </button>
            </div>
          </div>
        </div>

        {/* Matrix Dimensions & Start Button */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-4 border-t border-white/10">
          <div className="text-xs text-frost-muted font-mono">
            <span>Matrix size: </span>
            <strong className="text-teal-liquid">
              {methods.length} methods × {ratios.length} ratios × {detectors.length} detectors ={" "}
              {methods.length * ratios.length * detectors.length} evaluations
            </strong>
          </div>

          <button
            type="button"
            disabled={isRunning}
            onClick={handleStartExperiment}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl liquid-btn-primary text-xs font-semibold shadow-teal-glow"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Running Empirical Sweep...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Execute Matrix Sweep</span>
              </>
            )}
          </button>
        </div>
      </section>

      {/* Live SSE Telemetry Progress */}
      {(isRunning || progressPercent > 0) && (
        <section className="glass-deep rounded-2xl p-6 border border-teal-liquid/30 space-y-4 shadow-glass-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <span className="text-xs font-semibold text-frost flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-teal-liquid animate-pulse" />
              Live Progress Telemetry (SSE)
            </span>
            <span className="font-mono text-xs text-teal-liquid font-bold">
              {progressPercent.toFixed(1)}% {progressStep.total > 0 && `(${progressStep.current}/${progressStep.total} items)`}
            </span>
          </div>

          <div className="w-full h-2.5 rounded-full bg-abyss-deep overflow-hidden border border-white/10">
            <div
              className="h-full bg-gradient-to-r from-teal-liquid to-mint transition-all duration-300 shadow-teal-glow"
              style={{ width: `${Math.min(100, progressPercent)}%` }}
            />
          </div>

          <p className="text-[11px] font-mono text-frost-muted truncate">
            {currentItemDesc || "Synchronizing with engine worker..."}
          </p>
        </section>
      )}

      {/* Results Dashboard: Chart & Summary */}
      {summaryData && (
        <section className="space-y-8">
          {/* Recharts LineChart */}
          <div className="glass-deep rounded-2xl p-6 sm:p-8 border border-white/10 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
              <div>
                <h3 className="text-base font-bold text-frost">
                  Detection Rate vs. Payload Ratio Curve
                </h3>
                <p className="text-xs text-frost-muted mt-0.5">
                  Academic empirical ROC curve illustrating steganographic detectability bounds.
                </p>
              </div>
              <span className="text-xs font-mono text-teal-liquid">
                Total Tested: {summaryData.total_items}
              </span>
            </div>

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 30, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="ratio" stroke="#91A9B2" tick={{ fontSize: 11 }} />
                  <YAxis
                    stroke="#91A9B2"
                    tick={{ fontSize: 11 }}
                    domain={[0, 100]}
                    unit="%"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#07131D",
                      borderColor: "rgba(54, 214, 195, 0.4)",
                      borderRadius: "12px",
                      fontSize: "11px",
                      color: "#E5F1F3",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "12px" }} />
                  {methods.includes("lsb_replacement") && detectors.includes("chi_square") && (
                    <Line
                      type="monotone"
                      dataKey="Replacement (Chi²)"
                      stroke="#F43F5E"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  )}
                  {methods.includes("lsb_matching") && detectors.includes("chi_square") && (
                    <Line
                      type="monotone"
                      dataKey="Matching (Chi²)"
                      stroke="#36D6C3"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  )}
                  {methods.includes("lsb_replacement") && detectors.includes("rs") && (
                    <Line
                      type="monotone"
                      dataKey="Replacement (RS)"
                      stroke="#F59E0B"
                      strokeWidth={2}
                      strokeDasharray="4 4"
                      dot={{ r: 4 }}
                    />
                  )}
                  {methods.includes("lsb_matching") && detectors.includes("rs") && (
                    <Line
                      type="monotone"
                      dataKey="Matching (RS)"
                      stroke="#9B91F5"
                      strokeWidth={2}
                      strokeDasharray="4 4"
                      dot={{ r: 4 }}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Summary Table & False Positive Card */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* False Positive Rate Card */}
            <div className="glass-deep p-6 rounded-2xl border border-white/10 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-frost-muted">
                  Baseline Accuracy
                </span>
                <h4 className="text-base font-bold text-frost mt-1">
                  False Positive Rate (FPR)
                </h4>
                <p className="text-xs text-frost-muted mt-1 leading-relaxed">
                  Percentage of clean un-embedded cover images falsely categorized as stego carriers.
                </p>
              </div>

              <div className="my-6">
                <span className="text-4xl font-mono font-bold text-teal-liquid">
                  {summaryData.false_positive_rate !== undefined
                    ? `${(summaryData.false_positive_rate * 100).toFixed(1)}%`
                    : "0.0%"}
                </span>
                <p className="text-[11px] text-frost-muted mt-1">
                  Target: &lt; 5.0% (Calibrated 95th Percentile)
                </p>
              </div>

              <div className="pt-4 border-t border-white/10">
                <a
                  href={`/api/v1/attack-lab/export/${summaryData.experiment_id}`}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl liquid-btn-primary text-xs font-semibold"
                >
                  <Download className="w-4 h-4" />
                  <span>Download CSV Benchmark</span>
                </a>
              </div>
            </div>

            {/* Matrix Data Table */}
            <div className="lg:col-span-2 glass-deep p-6 rounded-2xl border border-white/10 space-y-3">
              <h4 className="text-sm font-bold text-frost flex items-center gap-2">
                <Table className="w-4 h-4 text-teal-liquid" />
                Empirical Sweep Summary
              </h4>

              <div className="overflow-x-auto max-h-72">
                <table className="w-full text-xs text-left">
                  <thead className="text-[10px] uppercase font-mono text-frost-muted border-b border-white/10">
                    <tr>
                      <th className="py-2 px-3">Method</th>
                      <th className="py-2 px-3">Ratio</th>
                      <th className="py-2 px-3">Detector</th>
                      <th className="py-2 px-3">Detected</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 font-mono">
                    {summaryData.items?.slice(0, 30).map((it, idx) => (
                      <tr key={idx} className="hover:bg-white/5 transition-colors">
                        <td className="py-2 px-3 text-frost">{it.method}</td>
                        <td className="py-2 px-3 text-frost-muted">{(it.ratio * 100).toFixed(0)}%</td>
                        <td className="py-2 px-3 text-teal-liquid">{it.detector}</td>
                        <td className="py-2 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              it.detected
                                ? "bg-rose-500/20 text-rose-300"
                                : "bg-emerald-500/20 text-emerald-300"
                            }`}
                          >
                            {it.detected ? "DETECTED" : "EVADED"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
