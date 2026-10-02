"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Compass,
  Play,
  Pause,
  Video,
  Eye,
  RotateCcw,
  Sparkles,
  ArrowRight,
  Trophy,
  Flame,
  User,
  Heart,
  Briefcase,
} from "lucide-react";
import type { ExportData } from "../../lib/types";
import {
  GlassCard,
  MagneticButton,
  RollingNumber,
  HoloBadge,
  CardSkeleton,
} from "../../components/ui";
import { EASE_OUT_EXPO } from "../../lib/motion";

const TOUR_STEPS = [
  {
    title: "1. 25 Real Candidates Ingested",
    subtitle: "Public LinkedIn & Instagram Only",
    caption:
      "25 real early-career founders, builders, and creators. We scrape only public text: career history, headline, bio, and recent posts via Apify.",
    view: "candidates",
  },
  {
    title: "2. Autonomous Profile Reading",
    subtitle: "Needs, Hobbies & The Say/Do Gap",
    caption:
      "Agents read their candidate and synthesize verified needs, core values, and the Say/Do gap — comparing professional presentation against lived social evidence.",
    view: "profile",
  },
  {
    title: "3. The Agents Date On Their Behalf",
    subtitle: "Multi-Turn Dialogue & Chemistry",
    caption:
      "All 25 agents enter the arena. They meet across cafe and speakeasy scenes, exchanging banter, testing values, and grading mutual chemistry.",
    view: "arena",
  },
  {
    title: "4. Referee Evaluation & Final Rankings",
    subtitle: "Compatibility Leaderboard",
    caption:
      "An independent referee grades 5 compatibility dimensions. Final scores blend mutual warmth, referee critique, and semantic vectors, reordering the leaderboard.",
    view: "rankings",
  },
];

export default function DemoTourPage() {
  const [data, setData] = useState<ExportData | null>(null);
  const [loading, setLoading] = useState(true);

  // Cinematic Tour State
  const [isCinematic, setIsCinematic] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const [recordMode, setRecordMode] = useState(false);

  // Load demo data
  useEffect(() => {
    fetch("/demo_run.json")
      .then((r) => r.json())
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => {
        // Fallback placeholder data if demo_run.json is not yet built
        setLoading(false);
      });
  }, []);

  // Guided Tour Auto-play Timer
  useEffect(() => {
    if (!isCinematic) return;

    const timer = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % TOUR_STEPS.length);
    }, 9000);

    return () => clearInterval(timer);
  }, [isCinematic]);

  const activeTour = TOUR_STEPS[currentStep];

  // User click exits to free mode
  const handleExitCinematic = () => {
    setIsCinematic(false);
  };

  if (loading) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto py-8">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  return (
    <div
      className={`space-y-6 max-w-6xl mx-auto py-4 transition-all ${
        recordMode
          ? "border-2 border-accent/40 rounded-3xl p-6 bg-bg shadow-2xl overflow-hidden aspect-[16/9]"
          : ""
      }`}
      onClick={() => {
        if (isCinematic) handleExitCinematic();
      }}
    >
      {/* Top Banner: Mode Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-accent" />
            <h1 className="text-xl sm:text-2xl font-display font-bold text-ink tracking-tightest">
              Demo Showcase & Tour
            </h1>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-mono uppercase bg-accent/15 border border-accent/30 text-accent">
            {isCinematic ? "Cinematic Auto-Tour" : "Free Explore"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Record Mode Toggle */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setRecordMode((v) => !v);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono border transition-all ${
              recordMode
                ? "bg-friction/20 border-friction text-friction font-bold"
                : "bg-surface-elevated border-hairline text-muted hover:text-ink"
            }`}
            data-cursor="Toggle 16:9 Frame"
          >
            <Video className="w-3.5 h-3.5" />
            <span>{recordMode ? "16:9 Record Locked" : "Record Mode"}</span>
          </button>

          {/* Tour Play / Pause */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsCinematic((v) => !v);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-elevated border border-hairline text-xs font-mono text-muted hover:text-ink transition-all"
          >
            {isCinematic ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isCinematic ? "Pause Tour" : "Resume Tour"}</span>
          </button>
        </div>
      </div>

      {/* Cinematic Step Progress Header */}
      <GlassCard className="p-4 space-y-3 border-accent/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-mono uppercase">
            <span className="text-spark font-bold">{activeTour.title}</span>
            <span className="text-muted">• {activeTour.subtitle}</span>
          </div>

          <div className="flex items-center gap-1">
            {TOUR_STEPS.map((s, idx) => (
              <button
                key={idx}
                onClick={(e) => {
                  e.stopPropagation();
                  setCurrentStep(idx);
                }}
                className={`w-8 h-1.5 rounded-full transition-all ${
                  currentStep === idx ? "bg-spark shadow-spark-glow" : "bg-muted/20"
                }`}
              />
            ))}
          </div>
        </div>

        <motion.p
          key={currentStep}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: EASE_OUT_EXPO }}
          className="text-xs sm:text-sm font-sans text-ink leading-relaxed"
        >
          {activeTour.caption}
        </motion.p>
      </GlassCard>

      {/* Dynamic View Mockup per Tour Step */}
      <div className="space-y-4">
        {activeTour.view === "candidates" && (
          <GlassCard className="p-6 space-y-4">
            <h3 className="text-sm font-mono uppercase tracking-wider text-muted">
              Pre-Seeded 25 Real Candidates
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
              {[
                "Jade Bonacolta",
                "Pieter Levels",
                "Marc Louvion",
                "Grace Beverley",
                "Lara Acosta",
                "Dickie Bush",
                "Harry Stebbings",
                "Sahil Bloom",
                "Dan Koe",
                "Sophie Miller",
              ].map((name, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-surface-elevated/70 border border-hairline flex flex-col items-center text-center space-y-1"
                >
                  <div className="w-10 h-10 rounded-full bg-accent/20 border border-accent/40 flex items-center justify-center font-display font-bold text-accent text-sm">
                    {name.charAt(0)}
                  </div>
                  <span className="text-xs font-medium text-ink truncate max-w-full">
                    {name}
                  </span>
                  <span className="text-[10px] font-mono text-spark">Analyzed</span>
                </div>
              ))}
            </div>
            <div className="flex justify-end pt-2">
              <Link href="/">
                <MagneticButton variant="ghost" size="sm">
                  <span>Open Full Candidate Table</span>
                  <ArrowRight className="w-3 h-3" />
                </MagneticButton>
              </Link>
            </div>
          </GlassCard>
        )}

        {activeTour.view === "profile" && (
          <GlassCard className="p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-hairline">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-surface-elevated border border-hairline flex items-center justify-center font-display font-bold text-lg text-ink">
                  J
                </div>
                <div>
                  <h3 className="font-display font-bold text-base text-ink">
                    Jade Bonacolta (Profile Analysis)
                  </h3>
                  <span className="text-xs font-mono text-muted">
                    Founder The Quiet Rich • 6 Verified Claims
                  </span>
                </div>
              </div>
              <Link href="/people/4">
                <MagneticButton variant="secondary" size="sm">
                  <span>View Live Profile</span>
                </MagneticButton>
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              <div className="bg-surface-elevated/60 p-3 rounded-xl border border-spark/30 space-y-1">
                <span className="text-spark font-bold uppercase text-[10px]">Stated Self (LinkedIn):</span>
                <p className="text-ink font-sans">
                  Focus on mindful entrepreneurship, intentional career growth, and quiet luxury.
                </p>
              </div>
              <div className="bg-surface-elevated/60 p-3 rounded-xl border border-accent/30 space-y-1">
                <span className="text-accent font-bold uppercase text-[10px]">Lived Self (Instagram):</span>
                <p className="text-ink font-sans">
                  Deep passion for motorcycle journeys, cooking experiments, travel, and quiet rituals.
                </p>
              </div>
            </div>
          </GlassCard>
        )}

        {activeTour.view === "arena" && (
          <GlassCard className="p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-hairline">
              <div className="flex items-center gap-2">
                <Flame className="w-4 h-4 text-friction" />
                <h3 className="font-semibold text-sm text-ink">
                  Sample Multi-Turn Autonomous Date
                </h3>
              </div>
              <span className="text-xs font-mono text-spark font-bold">
                Mutual Chemistry: 88%
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs max-h-48 overflow-y-auto">
              <div className="p-3 rounded-xl bg-surface-elevated border border-spark/30 space-y-1">
                <div className="flex justify-between text-[10px] text-spark font-bold uppercase">
                  <span>Agent Jade</span>
                  <span>Spark Tag (+18 Warmth)</span>
                </div>
                <p className="text-ink font-sans">
                  &ldquo;I believe high leverage shouldn't come at the cost of peace. What keeps you grounded?&rdquo;
                </p>
              </div>

              <div className="p-3 rounded-xl bg-surface-highlight border border-hairline space-y-1 text-right">
                <div className="flex justify-between text-[10px] text-accent font-bold uppercase">
                  <span>Neutral Response</span>
                  <span>Agent Pieter</span>
                </div>
                <p className="text-ink font-sans text-left">
                  &ldquo;Building tools that solve real problems in tiny increments while living anywhere on earth.&rdquo;
                </p>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Link href="/dating">
                <MagneticButton variant="spark" size="sm">
                  <span>Launch Dating Arena</span>
                  <ArrowRight className="w-3 h-3" />
                </MagneticButton>
              </Link>
            </div>
          </GlassCard>
        )}

        {activeTour.view === "rankings" && (
          <GlassCard className="p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-hairline">
              <div className="flex items-center gap-2">
                <Trophy className="w-4 h-4 text-spark" />
                <h3 className="font-semibold text-sm text-ink">
                  Final Compatibility Ranking (Example)
                </h3>
              </div>
              <Link href="/rankings">
                <MagneticButton variant="secondary" size="sm">
                  <span>View All Rankings</span>
                </MagneticButton>
              </Link>
            </div>

            <div className="space-y-2">
              {[
                { rank: 1, name: "Marc Louvion", score: 89.4, delta: "+3", badge: "Surprise Match" },
                { rank: 2, name: "Sahil Bloom", score: 86.1, delta: "+1", badge: null },
                { rank: 3, name: "Dan Koe", score: 84.8, delta: "-1", badge: "False Friend" },
              ].map((m) => (
                <div
                  key={m.rank}
                  className="p-3 rounded-xl bg-surface-elevated/70 border border-hairline flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-ink text-base">#{m.rank}</span>
                    <span className="font-semibold text-ink">{m.name}</span>
                    {m.badge && (
                      <HoloBadge type={m.badge === "Surprise Match" ? "surprise_match" : "false_friend"} />
                    )}
                  </div>
                  <div className="flex items-center gap-4 font-mono">
                    <span className="text-muted">Slope: {m.delta}</span>
                    <span className="text-spark font-bold text-sm">{m.score}%</span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        )}
      </div>

      <div className="text-center text-xs font-mono text-muted/60 pt-4">
        Click anywhere to toggle free exploration mode • Use Record Mode for clean screen capture
      </div>
    </div>
  );
}
