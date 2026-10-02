"use client";

import Link from "next/link";
import { Compass, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-bg text-ink flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative glass-card max-w-md w-full p-8 text-center space-y-6">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-surface-elevated border border-hairline text-accent shadow-glass">
          <Compass className="w-6 h-6 animate-pulse" />
        </div>

        <div className="space-y-2">
          <div className="font-mono text-xs text-muted uppercase tracking-widest">
            Error 404 // Signal Dissolved
          </div>
          <h1 className="text-3xl font-display font-semibold tracking-tight text-ink">
            Target Not Found
          </h1>
          <p className="text-sm text-muted font-sans leading-relaxed">
            The candidate profile, dating transcript, or node coordinate you requested does not exist or has been cleared from memory.
          </p>
        </div>

        <div className="pt-2 flex justify-center">
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-ink text-bg font-sans text-sm font-medium hover:opacity-90 transition-colors shadow-glass"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Arena Hub</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
