"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Database,
  Trash2,
  RefreshCw,
  Layers,
  Search,
  KeyRound,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { fetchHistory, clearHistory, type OperationItemResponse } from "@/lib/api-client";
import { formatNumber } from "@/lib/utils";

export default function HistoryPage() {
  const queryClient = useQueryClient();

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["history"],
    queryFn: fetchHistory,
  });

  const clearMutation = useMutation({
    mutationFn: clearHistory,
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["history"] });
      toast.success(`Cleared ${res.deleted_count} session record(s).`);
    },
    onError: () => {
      toast.error("Failed to clear session history.");
    },
  });

  const operations: OperationItemResponse[] = data?.operations ?? [];

  const getOpBadge = (type: string) => {
    switch (type.toLowerCase()) {
      case "embed":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase bg-teal-liquid/15 text-teal-liquid border border-teal-liquid/30">
            <Layers className="w-3 h-3" />
            <span>Embed</span>
          </span>
        );
      case "extract":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase bg-iris/15 text-iris border border-iris/30">
            <KeyRound className="w-3 h-3" />
            <span>Extract</span>
          </span>
        );
      case "analyze":
      case "detect":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase bg-mint/15 text-mint border border-mint/30">
            <Search className="w-3 h-3" />
            <span>{type}</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase bg-white/10 text-frost-muted border border-white/10">
            <span>{type}</span>
          </span>
        );
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 py-4">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-clear border border-amber-500/30 text-amber-300 text-xs font-mono font-medium">
            <Database className="w-3.5 h-3.5" />
            <span>Session Audit Trail</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-frost tracking-tight mt-2">
            Session Operations History
          </h1>
          <p className="text-xs sm:text-sm text-frost-muted mt-1">
            Audit logs scoped to your anonymous session cookie. Zero plaintext secrets or cryptographic keys are ever recorded.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-center">
          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl glass-clear text-xs font-semibold text-frost-muted hover:text-frost"
            aria-label="Refresh history"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>

          {operations.length > 0 && (
            <button
              type="button"
              onClick={() => {
                if (window.confirm("Are you sure you want to delete all session operation logs?")) {
                  clearMutation.mutate();
                }
              }}
              disabled={clearMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 hover:bg-rose-500/25 text-xs font-semibold transition-all"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear History</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <div className="glass-deep rounded-2xl p-12 text-center border border-white/10 space-y-3">
          <RefreshCw className="w-8 h-8 mx-auto animate-spin text-teal-liquid" />
          <p className="text-sm font-medium text-frost">Loading session records...</p>
        </div>
      ) : isError ? (
        <div className="glass-deep rounded-2xl p-8 border border-rose-500/30 text-center space-y-3">
          <AlertCircle className="w-8 h-8 mx-auto text-rose-400" />
          <p className="text-sm font-semibold text-rose-200">Failed to load session history</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="px-4 py-2 rounded-xl liquid-btn-primary text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      ) : operations.length === 0 ? (
        /* Meaningful Empty State */
        <div className="glass-deep rounded-2xl p-12 sm:p-16 text-center border border-white/10 space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-teal-liquid/10 border border-teal-liquid/30 text-teal-liquid flex items-center justify-center mx-auto shadow-teal-glow">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-2">
            <h3 className="text-lg font-bold text-frost">No Operations Recorded Yet</h3>
            <p className="text-xs text-frost-muted leading-relaxed">
              You haven&apos;t executed any steganographic embeddings, extractions, or distortion comparisons in this session.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              href="/embed"
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl liquid-btn-primary text-xs font-semibold"
            >
              <span>Embed a Secret</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <Link
              href="/analyze"
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl glass-frosted text-xs font-semibold text-frost hover:border-teal-liquid/30"
            >
              <span>Analyze an Image</span>
            </Link>
          </div>
        </div>
      ) : (
        /* Operations Table */
        <div className="glass-deep rounded-2xl border border-white/10 overflow-hidden shadow-glass-md">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="text-[10px] uppercase font-mono text-frost-muted bg-abyss-deep/70 border-b border-white/10">
                <tr>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Files / Payload</th>
                  <th className="py-3 px-4">Method</th>
                  <th className="py-3 px-4">Distortion Metrics</th>
                  <th className="py-3 px-4 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {operations.map((op) => (
                  <tr key={op.id} className="hover:bg-white/[0.03] transition-colors">
                    {/* Operation Type */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {getOpBadge(op.operation_type)}
                    </td>

                    {/* Files / Payload */}
                    <td className="py-3.5 px-4 font-mono text-xs">
                      <div className="space-y-0.5">
                        {op.cover_filename && (
                          <div className="text-frost">
                            <span className="text-frost-muted text-[10px]">Cover: </span>
                            {op.cover_filename}
                          </div>
                        )}
                        {op.stego_filename && (
                          <div className="text-teal-liquid font-medium">
                            <span className="text-frost-muted text-[10px]">Stego: </span>
                            {op.stego_filename}
                          </div>
                        )}
                        {op.payload_type && (
                          <div className="text-[10px] text-frost-muted">
                            Payload: {op.payload_type}
                          </div>
                        )}
                      </div>
                    </td>

                    {/* Method */}
                    <td className="py-3.5 px-4 font-mono text-xs">
                      {op.method ? (
                        <span className="text-frost-muted">
                          {op.method === "lsb_matching" ? "LSB Matching (±1)" : "LSB Replacement"}
                        </span>
                      ) : (
                        <span className="text-frost-muted/50">—</span>
                      )}
                    </td>

                    {/* Distortion Metrics */}
                    <td className="py-3.5 px-4 font-mono text-xs">
                      {typeof op.mse === "number" && typeof op.psnr === "number" && typeof op.ssim === "number" ? (
                        <div className="space-y-0.5 text-[11px]">
                          <div>
                            <span className="text-frost-muted">MSE: </span>
                            <span className="text-teal-liquid">{formatNumber(op.mse, 4)}</span>
                          </div>
                          <div>
                            <span className="text-frost-muted">PSNR: </span>
                            <span className="text-mint">{formatNumber(op.psnr, 2)} dB</span>
                          </div>
                          <div>
                            <span className="text-frost-muted">SSIM: </span>
                            <span className="text-iris">{formatNumber(op.ssim, 4)}</span>
                          </div>
                        </div>
                      ) : (
                        <span className="text-frost-muted/50">—</span>
                      )}
                    </td>

                    {/* Timestamp */}
                    <td className="py-3.5 px-4 text-right whitespace-nowrap font-mono text-[11px] text-frost-muted">
                      <div className="flex items-center justify-end gap-1">
                        <Clock className="w-3 h-3 text-frost-muted/70" />
                        <span>
                          {new Date(op.created_at).toLocaleString(undefined, {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
