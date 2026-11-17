import Link from "next/link";
import { ShieldAlert } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
      <div className="w-16 h-16 rounded-2xl bg-teal-liquid/10 border border-teal-liquid/25 flex items-center justify-center text-teal-liquid mb-4">
        <ShieldAlert className="w-8 h-8" />
      </div>
      <h2 className="text-2xl font-bold text-frost">Page Not Found</h2>
      <p className="text-sm text-frost-muted mt-2 max-w-md">
        The requested StegaShield module or resource does not exist or has expired.
      </p>
      <Link
        href="/"
        className="mt-6 px-4 py-2 rounded-xl bg-teal-liquid text-abyss font-medium text-sm hover:bg-teal-liquid/90 transition-colors"
      >
        Return to Overview
      </Link>
    </div>
  );
}
