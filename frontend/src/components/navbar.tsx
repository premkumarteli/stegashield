"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { ShieldCheck, Menu, X, Sparkles } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { name: "Overview", href: "/" },
  { name: "Embed", href: "/embed" },
  { name: "Extract", href: "/extract" },
  { name: "Analyze", href: "/analyze" },
  { name: "Attack Lab", href: "/attack-lab" },
  { name: "History", href: "/history" },
  { name: "About", href: "/about" },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-4 z-50 px-4 sm:px-6 max-w-7xl mx-auto w-full">
      <nav
        aria-label="Main Navigation"
        className="glass-frosted rounded-2xl px-4 py-2.5 flex items-center justify-between shadow-glass-md transition-all border border-white/10"
      >
        {/* Brand */}
        <Link
          href="/"
          className="flex items-center gap-2.5 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-liquid rounded-lg px-1.5 py-1"
        >
          <div className="relative flex items-center justify-center w-8 h-8 rounded-xl bg-teal-liquid/15 border border-teal-liquid/30 text-teal-liquid group-hover:scale-105 transition-transform">
            <ShieldCheck className="w-5 h-5 text-teal-liquid" />
            <span className="absolute -inset-0.5 rounded-xl bg-teal-liquid/20 blur-sm -z-10 group-hover:opacity-100 opacity-60 transition-opacity" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-base tracking-tight text-frost flex items-center gap-1.5">
              StegaShield
              <span className="inline-flex items-center px-1.5 py-0.2 text-[10px] font-mono font-medium rounded-full bg-teal-liquid/15 text-teal-liquid border border-teal-liquid/30">
                v1.0
              </span>
            </span>
          </div>
        </Link>

        {/* Desktop Nav Items with Sliding Pill */}
        <div className="hidden md:flex items-center gap-1 relative">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative px-3.5 py-1.5 text-xs font-medium rounded-xl transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-liquid",
                  isActive
                    ? "text-frost font-semibold"
                    : "text-frost-muted hover:text-frost"
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeNavPill"
                    className="absolute inset-0 rounded-xl glass-active"
                    transition={{
                      type: "spring",
                      stiffness: 380,
                      damping: 30,
                    }}
                  />
                )}
                <span className="relative z-10">{item.name}</span>
              </Link>
            );
          })}
        </div>

        {/* Action badge / Mobile Menu Button */}
        <div className="flex items-center gap-2">
          <Link
            href="/embed"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl liquid-btn-primary"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Launch Studio</span>
          </Link>

          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-xl text-frost-muted hover:text-frost hover:bg-white/5 border border-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-liquid"
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
        </div>
      </nav>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          className="md:hidden mt-2 p-3 glass-deep rounded-2xl border border-white/10 flex flex-col gap-1 shadow-glass-lg"
        >
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={cn(
                  "px-3.5 py-2 text-sm font-medium rounded-xl transition-all flex items-center justify-between",
                  isActive
                    ? "glass-active text-frost font-semibold"
                    : "text-frost-muted hover:text-frost hover:bg-white/5"
                )}
              >
                <span>{item.name}</span>
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-liquid shadow-teal-glow" />
                )}
              </Link>
            );
          })}
          <div className="pt-2 border-t border-white/10 mt-1">
            <Link
              href="/embed"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full justify-center flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-xl liquid-btn-primary"
            >
              <Sparkles className="w-4 h-4" />
              <span>Launch Studio</span>
            </Link>
          </div>
        </motion.div>
      )}
    </header>
  );
}
