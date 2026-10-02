"use client";

import { useRef, useState, useEffect } from "react";
import { motion, useSpring, useMotionValue, type HTMLMotionProps } from "framer-motion";
import { Sparkles, AlertCircle, CheckCircle2, Clock } from "lucide-react";

// ==========================================
// 1. Magnetic Button (80px pull radius + spring reset)
// ==========================================
interface MagneticButtonProps extends Omit<HTMLMotionProps<"button">, "style"> {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "spark" | "friction" | "brand";
  size?: "sm" | "md" | "lg";
}

export function MagneticButton({
  children,
  variant = "primary",
  size = "md",
  className = "",
  onClick,
  disabled,
  ...props
}: MagneticButtonProps) {
  const btnRef = useRef<HTMLButtonElement | null>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 250, damping: 20 });
  const springY = useSpring(y, { stiffness: 250, damping: 20 });

  const handleMouseMove = (e: React.MouseEvent) => {
    if (disabled || !btnRef.current) return;
    const rect = btnRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const dist = Math.hypot(e.clientX - centerX, e.clientY - centerY);

    if (dist < 80) {
      // Pull toward cursor
      x.set((e.clientX - centerX) * 0.35);
      y.set((e.clientY - centerY) * 0.35);
    }
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  const variantStyles = {
    primary:
      "bg-ink text-bg font-medium hover:opacity-90 shadow-glass border border-hairline",
    secondary:
      "bg-surface-elevated text-ink hover:bg-surface-highlight border border-hairline",
    ghost:
      "bg-transparent text-muted hover:text-ink hover:bg-surface-elevated border border-transparent hover:border-hairline",
    spark:
      "bg-spark/15 text-spark border border-spark/30 hover:bg-spark/25 shadow-spark-glow",
    friction:
      "bg-friction/15 text-friction border border-friction/30 hover:bg-friction/25 shadow-friction-glow",
    brand:
      "bg-gradient-to-r from-blue-600 via-blue-500 to-orange-500 text-white font-medium hover:opacity-95 shadow-md border-0",
  };

  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs rounded-xl",
    md: "px-5 py-2.5 text-sm rounded-2xl",
    lg: "px-7 py-3.5 text-base font-semibold rounded-2xl",
  };

  return (
    <motion.button
      ref={btnRef}
      style={{ x: springX, y: springY }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      whileTap={{ scale: 0.96 }}
      onClick={onClick}
      disabled={disabled}
      className={`relative inline-flex items-center justify-center gap-2 cursor-pointer font-sans transition-colors disabled:opacity-40 disabled:pointer-events-none select-none ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      {...props}
    >
      {children}
    </motion.button>
  );
}

// ==========================================
// 2. Rolling Number (Odometer count-up)
// ==========================================
export function RollingNumber({
  value,
  duration = 1.2,
  decimals = 0,
  prefix = "",
  suffix = "",
}: {
  value: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
}) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    let startTimestamp: number | null = null;
    const startVal = display;
    const endVal = value;

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / (duration * 1000), 1);
      // Ease out expo
      const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      const current = startVal + (endVal - startVal) * easeProgress;
      setDisplay(current);

      if (progress < 1) {
        requestAnimationFrame(step);
      }
    };

    requestAnimationFrame(step);
  }, [value, duration]);

  return (
    <span className="tabular-nums font-mono">
      {prefix}
      {display.toFixed(decimals)}
      {suffix}
    </span>
  );
}

// ==========================================
// 3. Segmented Progress Pill
// ==========================================
export type ProgressStep = "queued" | "scraping" | "analyzing" | "analyzed" | "failed";

export function SegmentedProgressPill({
  status,
  error,
  onRetry,
}: {
  status: ProgressStep | string;
  error?: string | null;
  onRetry?: () => void;
}) {
  const steps: { key: string; label: string }[] = [
    { key: "queued", label: "Queued" },
    { key: "scraping", label: "Scraping" },
    { key: "analyzing", label: "Analyzing" },
    { key: "analyzed", label: "Done" },
  ];

  const stepOrder = ["queued", "scraping", "analyzing", "analyzed"];
  const currentIndex = status === "failed" ? -1 : stepOrder.indexOf(status);

  if (status === "failed") {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-friction/15 border border-friction/30 text-friction text-xs font-mono">
        <AlertCircle className="w-3.5 h-3.5 shrink-0" />
        <span className="truncate max-w-[180px]">{error || "Failed"}</span>
        {onRetry && (
          <button
            onClick={onRetry}
            className="underline hover:opacity-80 ml-1 font-sans"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface border border-hairline text-xs font-mono">
      {steps.map((s, idx) => {
        const isPassed = currentIndex > idx;
        const isCurrent = currentIndex === idx;
        const isActiveShimmer = isCurrent && (status === "scraping" || status === "analyzing");

        let dotColor = "bg-muted-dark";
        if (isPassed || (isCurrent && status === "analyzed")) dotColor = "bg-spark";
        else if (isCurrent) dotColor = "bg-accent";

        return (
          <div key={s.key} className="flex items-center gap-1">
            <span
              className={`w-1.5 h-1.5 rounded-full ${dotColor} ${
                isActiveShimmer ? "animate-pulse" : ""
              }`}
            />
            {isCurrent && (
              <span
                className={`text-[11px] font-medium tracking-tight ${
                  status === "analyzed"
                    ? "text-spark"
                    : isActiveShimmer
                    ? "text-accent shimmer-sweep"
                    : "text-muted"
                }`}
              >
                {s.label}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ==========================================
// 4. Holographic Foil Badge
// ==========================================
export function HoloBadge({
  type,
  reason,
  onClick,
}: {
  type: "surprise_match" | "false_friend" | string;
  reason?: string;
  onClick?: () => void;
}) {
  const isSurprise = type === "surprise_match";
  const label = isSurprise ? "Surprise Match" : "False Friend";

  return (
    <div
      onClick={onClick}
      className={`foil-chip inline-flex items-center gap-1.5 px-3 py-1 text-xs font-mono cursor-pointer transition-transform hover:scale-105 ${
        isSurprise
          ? "text-spark border-spark/30 shadow-spark-glow"
          : "text-friction border-friction/30 shadow-friction-glow"
      }`}
      title={reason}
    >
      <Sparkles className="w-3 h-3 shrink-0" />
      <span className="font-medium tracking-tight">{label}</span>
    </div>
  );
}

// ==========================================
// 5. GlassCard
// ==========================================
export function GlassCard({
  children,
  className = "",
  onClick,
  dataCursor,
}: {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  dataCursor?: string;
}) {
  return (
    <div
      onClick={onClick}
      data-cursor={dataCursor}
      className={`glass-card p-5 ${className}`}
    >
      {children}
    </div>
  );
}

// ==========================================
// 6. Content-Shaped Skeletons (Never generic spinners)
// ==========================================
export function CardSkeleton() {
  return (
    <div className="glass-card p-6 space-y-4 animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-full bg-muted/15" />
        <div className="space-y-2 flex-1">
          <div className="w-32 h-4 rounded bg-muted/20" />
          <div className="w-48 h-3 rounded bg-muted/10" />
        </div>
      </div>
      <div className="space-y-2 pt-2">
        <div className="w-full h-3 rounded bg-muted/15" />
        <div className="w-4/5 h-3 rounded bg-muted/10" />
      </div>
    </div>
  );
}

export function RowSkeleton() {
  return (
    <div className="h-14 w-full rounded-2xl bg-surface border border-hairline p-3 flex items-center justify-between animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-muted/15" />
        <div className="w-40 h-3.5 rounded bg-muted/20" />
      </div>
      <div className="w-20 h-6 rounded-full bg-muted/15" />
    </div>
  );
}
