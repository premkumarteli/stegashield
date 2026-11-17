import Link from "next/link";
import { ShieldAlert, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center space-y-6">
      <div className="w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center shadow-glass-md">
        <ShieldAlert className="w-8 h-8" />
      </div>
      <div className="space-y-2">
        <span className="text-xs font-mono uppercase tracking-widest text-teal-liquid">
          Error 404
        </span>
        <h1 className="text-3xl font-extrabold text-frost">Page Not Found</h1>
        <p className="text-xs text-frost-muted max-w-sm mx-auto">
          The requested route or steganographic resource does not exist in the StegaShield laboratory.
        </p>
      </div>
      <Link
        href="/"
        className="flex items-center gap-2 px-5 py-2.5 rounded-xl liquid-btn-primary text-xs font-semibold"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Return to Overview</span>
      </Link>
    </div>
  );
}
