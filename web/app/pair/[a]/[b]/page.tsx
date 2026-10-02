"use client";

import { useEffect, useMemo, useRef, useState, useCallback, Suspense } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  Flame,
  User,
  ShieldCheck,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { api } from "../../../../lib/api";
import type { PairOut, RefereeOut, TurnOut } from "../../../../lib/types";
import {
  GlassCard,
  MagneticButton,
  RollingNumber,
  CardSkeleton,
} from "../../../../components/ui";
import { EASE_OUT_EXPO } from "../../../../lib/motion";

// Circular Arc Progress Ring for Referee Dimensions
function ArcScoreRing({ label, value, color }: { label: string; value: number; color: string }) {
  const size = 68;
  const strokeWidth = 5;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-2 text-center">
      <div className="relative w-[68px] h-[68px] flex items-center justify-center">
        <svg width={size} height={size} className="rotate-[-90deg]">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={strokeWidth}
          />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.0, ease: EASE_OUT_EXPO }}
            strokeLinecap="round"
          />
        </svg>
        <span className="absolute font-mono font-bold text-xs text-ink">
          {value.toFixed(0)}
        </span>
      </div>
      <span className="text-[10px] font-mono text-muted uppercase tracking-tight mt-1.5 max-w-[80px] truncate">
        {label}
      </span>
    </div>
  );
}

// Running Chemistry Sparkline
function ChemistryLine({
  turns,
  currentTurn,
  tags,
}: {
  turns: TurnOut[];
  currentTurn: number;
  tags: { turn_index: number; tag: "spark" | "friction" }[];
}) {
  const width = 600;
  const height = 48;
  const pad = 16;

  // Build warmth values across turns
  const points = useMemo(() => {
    let warmth = 50;
    return turns.map((t, i) => {
      const tag = tags.find((item) => item.turn_index === i);
      if (tag?.tag === "spark") warmth = Math.min(100, warmth + 18);
      else if (tag?.tag === "friction") warmth = Math.max(10, warmth - 16);
      else warmth += (Math.random() - 0.45) * 6;

      const x = pad + (i / Math.max(1, turns.length - 1)) * (width - pad * 2);
      const y = height - (warmth / 100) * (height - pad * 2) - pad;
      return { x, y, warmth, turn: i };
    });
  }, [turns, tags]);

  if (points.length < 2) return null;

  const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  return (
    <div className="w-full bg-surface-elevated/40 border border-hairline rounded-xl p-2.5 space-y-1">
      <div className="flex justify-between items-center text-[10px] font-mono text-muted uppercase">
        <span className="flex items-center gap-1.5">
          <Sparkles className="w-3 h-3 text-spark" />
          <span>Running Conversation Chemistry</span>
        </span>
        <span>Turn {currentTurn + 1} / {turns.length}</span>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-10 overflow-visible">
        <path
          d={pathD}
          fill="none"
          stroke="rgba(255, 255, 255, 0.15)"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        {/* Active progress path */}
        {currentTurn > 0 && (
          <path
            d={points
              .slice(0, currentTurn + 1)
              .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
              .join(" ")}
            fill="none"
            stroke="#7CFFB2"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
        )}

        {/* Current turn scrubber head */}
        {points[currentTurn] && (
          <circle
            cx={points[currentTurn].x}
            cy={points[currentTurn].y}
            r="4.5"
            className="fill-spark shadow-spark-glow"
          />
        )}
      </svg>
    </div>
  );
}

function PairReplayContent() {
  const params = useParams<{ a: string; b: string }>();
  const search = useSearchParams();
  const router = useRouter();

  const [dates, setDates] = useState<PairOut[]>([]);
  const [selectedRoundIdx, setSelectedRoundIdx] = useState<number>(0);
  const [currentTurnIdx, setCurrentTurnIdx] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [isRegenerating, setIsRegenerating] = useState<boolean>(false);

  // Load Date Pair Data
  useEffect(() => {
    setLoading(true);
    api
      .getPair(params.a, params.b)
      .then((list) => {
        setDates(list);
        setLoading(false);
        const urlRound = search.get("round");
        if (urlRound) {
          const idx = list.findIndex((d) => String(d.round) === urlRound);
          if (idx >= 0) setSelectedRoundIdx(idx);
        }
        const urlTurn = search.get("turn");
        if (urlTurn) {
          const tIdx = Math.max(0, parseInt(urlTurn, 10) - 1);
          setCurrentTurnIdx(tIdx);
        }
      })
      .catch(() => setLoading(false));
  }, [params.a, params.b, search]);

  const activeDate = dates[selectedRoundIdx];

  const handleRegenerate = async () => {
    if (!activeDate || isRegenerating) return;
    setIsRegenerating(true);
    try {
      const updated = await api.regeneratePair(params.a, params.b, activeDate.round);
      setDates((prev) =>
        prev.map((d, i) => (i === selectedRoundIdx ? updated : d))
      );
      setCurrentTurnIdx(0);
      setIsPlaying(true);
    } catch (err) {
      console.error("Failed to regenerate date:", err);
    } finally {
      setIsRegenerating(false);
    }
  };
  const turns = activeDate?.turns || [];
  const referee = activeDate?.referee;
  const taggedTurns = referee?.tagged_turns || [];

  // Playback timer loop
  useEffect(() => {
    if (!isPlaying) return;
    if (turns.length === 0) return;

    const interval = setInterval(() => {
      setCurrentTurnIdx((prev) => {
        if (prev >= turns.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 2400 / playbackSpeed);

    return () => clearInterval(interval);
  }, [isPlaying, turns.length, playbackSpeed]);

  // Keyboard Shortcuts: Space = Play/Pause, Left/Right = Steps
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.code === "Space") {
        e.preventDefault();
        setIsPlaying((v) => !v);
      } else if (e.code === "ArrowLeft") {
        e.preventDefault();
        setCurrentTurnIdx((prev) => Math.max(0, prev - 1));
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        setCurrentTurnIdx((prev) => Math.min(turns.length - 1, prev + 1));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [turns.length]);

  if (loading) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto py-8">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  if (!activeDate) {
    return (
      <div className="max-w-md mx-auto py-24 text-center space-y-4">
        <Flame className="w-12 h-12 text-muted mx-auto" />
        <h2 className="text-xl font-bold text-ink">No Date Recorded Between These Agents</h2>
        <p className="text-xs text-muted">
          Run the dating arena to simulate the date between these candidates.
        </p>
        <Link href="/dating">
          <MagneticButton variant="primary">Go to Dating Arena</MagneticButton>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto py-4">
      {/* Top Header & Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          href="/dating"
          className="inline-flex items-center gap-2 text-xs font-mono text-muted hover:text-ink transition-colors"
          data-cursor="Back"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Dating Arena</span>
        </Link>

        <div className="flex items-center gap-3">
          {/* Round Switcher Indicator */}
          {dates.length > 1 && (
            <div className="flex items-center gap-1 bg-surface-elevated/70 p-1 rounded-xl border border-hairline">
              {dates.map((d, idx) => (
                <button
                  key={d.date_id}
                  onClick={() => {
                    setSelectedRoundIdx(idx);
                    setCurrentTurnIdx(0);
                  }}
                  className={`relative px-3 py-1 text-xs font-mono rounded-lg transition-colors ${
                    selectedRoundIdx === idx ? "text-ink font-bold" : "text-muted hover:text-ink"
                  }`}
                >
                  {selectedRoundIdx === idx && (
                    <motion.div
                      layoutId="pair-round-pill"
                      className="absolute inset-0 rounded-lg bg-accent/10 border border-accent/20"
                      transition={{ type: "spring", stiffness: 350, damping: 25 }}
                    />
                  )}
                  <span className="relative z-10">Round {d.round}</span>
                </button>
              ))}
            </div>
          )}

          <button
            onClick={handleRegenerate}
            disabled={isRegenerating || !activeDate}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-spark/10 border border-spark/30 text-spark hover:bg-spark/20 transition-all text-xs font-mono disabled:opacity-50 shadow-sm"
            title="Generate a fresh, natural conversation for this pair"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isRegenerating ? "animate-spin text-spark" : "text-spark"}`} />
            <span>{isRegenerating ? "Synthesizing..." : "Re-simulate with AI"}</span>
          </button>
        </div>
      </div>

      {/* Split-Screen Header: Person A vs Person B */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Person A Card */}
        <GlassCard className="p-4 flex items-center justify-between border-accent/20">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-surface-elevated border border-hairline flex items-center justify-center font-display font-bold text-lg text-ink">
              {activeDate.person_a_name.charAt(0)}
            </div>
            <div>
              <Link
                href={`/people/${activeDate.person_a}`}
                className="font-display font-bold text-base text-ink hover:text-accent transition-colors flex items-center gap-1.5"
              >
                <span>{activeDate.person_a_name}</span>
                <ExternalLink className="w-3 h-3 text-muted" />
              </Link>
              <span className="text-[11px] font-mono text-muted block">
                Agent #{activeDate.person_a}
              </span>
            </div>
          </div>
          <Link href={`/rankings/${activeDate.person_a}`}>
            <span className="text-xs font-mono text-spark hover:underline">Rankings</span>
          </Link>
        </GlassCard>

        {/* Person B Card */}
        <GlassCard className="p-4 flex items-center justify-between border-friction/20">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-surface-elevated border border-hairline flex items-center justify-center font-display font-bold text-lg text-ink">
              {activeDate.person_b_name.charAt(0)}
            </div>
            <div>
              <Link
                href={`/people/${activeDate.person_b}`}
                className="font-display font-bold text-base text-ink hover:text-accent transition-colors flex items-center gap-1.5"
              >
                <span>{activeDate.person_b_name}</span>
                <ExternalLink className="w-3 h-3 text-muted" />
              </Link>
              <span className="text-[11px] font-mono text-muted block">
                Agent #{activeDate.person_b}
              </span>
            </div>
          </div>
          <Link href={`/rankings/${activeDate.person_b}`}>
            <span className="text-xs font-mono text-spark hover:underline">Rankings</span>
          </Link>
        </GlassCard>
      </div>

      {/* Running Chemistry Sparkline Chart */}
      <ChemistryLine
        turns={turns}
        currentTurn={currentTurnIdx}
        tags={taggedTurns}
      />

      {/* Central Conversation Chat Area */}
      <GlassCard className="p-6 space-y-4 min-h-[380px] max-h-[500px] overflow-y-auto">
        <div className="flex items-center justify-between pb-3 border-b border-hairline text-xs font-mono text-muted">
          <span>Date Scene: {activeDate.scene || "Acoustic Cafe"}</span>
          <span>Showing turns 1 through {currentTurnIdx + 1}</span>
        </div>

        <div className="space-y-4">
          <AnimatePresence>
            {turns.slice(0, currentTurnIdx + 1).map((turn, idx) => {
              const isSpeakerA = turn.speaker_id === activeDate.person_a;
              const tag = taggedTurns.find((t) => t.turn_index === idx);

              return (
                <motion.div
                  key={idx}
                  id={`turn-${idx + 1}`}
                  initial={{ opacity: 0, y: 12, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ duration: 0.35, ease: EASE_OUT_EXPO }}
                  className={`flex flex-col ${isSpeakerA ? "items-start" : "items-end"}`}
                >
                  <div className="flex items-center gap-2 mb-1 px-1">
                    <span className="text-[11px] font-mono font-bold text-muted uppercase">
                      {turn.speaker_name}
                    </span>
                    <span className="text-[10px] font-mono text-muted/60">
                      turn #{turn.idx + 1}
                    </span>
                    {tag && (
                      <span
                        className={`text-[10px] font-mono uppercase px-2 py-0.2 rounded-full border ${
                          tag.tag === "spark"
                            ? "bg-spark/15 text-spark border-spark/30"
                            : "bg-friction/15 text-friction border-friction/30"
                        }`}
                        title={tag.reason}
                      >
                        {tag.tag}
                      </span>
                    )}
                  </div>

                  <div
                    className={`max-w-[85%] sm:max-w-[75%] p-4 rounded-2xl text-xs sm:text-sm font-sans leading-relaxed border transition-all ${
                      tag?.tag === "spark"
                        ? "border-spark/40 bg-spark/[0.05] shadow-spark-glow"
                        : tag?.tag === "friction"
                        ? "border-friction/40 bg-friction/[0.05] shadow-friction-glow"
                        : isSpeakerA
                        ? "border-hairline bg-surface-elevated text-ink rounded-tl-sm"
                        : "border-hairline bg-surface-highlight text-ink rounded-tr-sm"
                    }`}
                  >
                    {turn.content}
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </GlassCard>

      {/* Timeline Scrubber & Replay Controls */}
      <GlassCard className="p-4 space-y-3">
        <div className="flex items-center justify-between text-xs font-mono text-muted">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsPlaying((v) => !v)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-ink text-bg font-sans font-semibold hover:opacity-90 transition-all shadow-sm"
              data-cursor="Play / Pause"
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              <span>{isPlaying ? "Pause" : "Play Replay"}</span>
            </button>

            <button
              onClick={() => setCurrentTurnIdx(0)}
              className="p-2 rounded-xl text-muted hover:text-ink hover:bg-surface-elevated transition-colors"
              title="Reset"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>

            {/* Speed Control */}
            <div className="flex items-center gap-1 bg-surface-elevated px-2 py-1 rounded-lg border border-hairline text-xs font-mono">
              {[1, 2, 4].map((spd) => (
                <button
                  key={spd}
                  onClick={() => setPlaybackSpeed(spd)}
                  className={`px-1.5 py-0.5 rounded transition-colors ${
                    playbackSpeed === spd ? "bg-accent/15 text-accent font-bold" : "text-muted hover:text-ink"
                  }`}
                >
                  {spd}x
                </button>
              ))}
            </div>
          </div>

          <span className="text-[11px]">
            [Space] to play/pause • [← / →] to step turns
          </span>
        </div>

        {/* Scrubber Range Slider */}
        <div className="space-y-1">
          <input
            type="range"
            min={0}
            max={Math.max(0, turns.length - 1)}
            value={currentTurnIdx}
            onChange={(e) => setCurrentTurnIdx(parseInt(e.target.value, 10))}
            className="w-full accent-spark cursor-pointer"
          />
        </div>
      </GlassCard>

      {/* Referee Panel with Dimension Score Arcs */}
      {referee && (
        <GlassCard className="p-6 space-y-4 border-spark/20">
          <div className="flex items-center justify-between pb-3 border-b border-hairline">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-spark" />
              <h3 className="font-semibold text-sm text-ink">
                Independent Referee Synthesis
              </h3>
            </div>
            <span className="text-xs font-mono text-muted">
              Evaluated across 5 compatibility vectors
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
            <ArcScoreRing label="Chemistry" value={referee.chemistry} color="#7CFFB2" />
            <ArcScoreRing label="Values Fit" value={referee.values_fit} color="#8B8BFF" />
            <ArcScoreRing label="Lifestyle" value={referee.lifestyle_fit} color="#FFB020" />
            <ArcScoreRing label="Ambition" value={referee.ambition_fit} color="#60A5FA" />
            <ArcScoreRing label="Interests" value={referee.interests_fit} color="#FF5C7A" />
          </div>
        </GlassCard>
      )}
    </div>
  );
}

export default function PairReplayPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-5xl mx-auto space-y-6 pt-6">
          <CardSkeleton />
        </div>
      }
    >
      <PairReplayContent />
    </Suspense>
  );
}
