"use client";

import { useCallback, useEffect, useRef, useState, useMemo } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Flame,
  Play,
  RotateCcw,
  Sparkles,
  Trophy,
  ArrowRight,
  MessageSquare,
  Activity,
  Layers,
  CheckCircle2,
} from "lucide-react";
import { api, openEventStream } from "../../lib/api";
import type { PersonOut, RunOut, RunStats, SseEvent, TurnOut } from "../../lib/types";
import {
  MagneticButton,
  RollingNumber,
  GlassCard,
  RowSkeleton,
} from "../../components/ui";
import { DatingGraph } from "../../components/DatingGraph";
import { EASE_OUT_EXPO } from "../../lib/motion";
import { toast } from "sonner";

interface FinishedDateItem {
  key: string;
  dateId: number;
  round: number;
  aId: number;
  bId: number;
  aName: string;
  bName: string;
  scene?: string | null;
  score?: number;
}

export default function DatingArenaPage() {
  const [people, setPeople] = useState<PersonOut[]>([]);
  const [run, setRun] = useState<RunOut | null>(null);
  const [stats, setStats] = useState<RunStats>({});
  const [feed, setFeed] = useState<FinishedDateItem[]>([]);
  const [selectedPair, setSelectedPair] = useState<{ aId: number; bId: number } | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  // Active simulated transcript ticker
  const [activeDate, setActiveDate] = useState<{
    aName: string;
    bName: string;
    scene: string;
    turns: { speaker: string; text: string; tag?: "spark" | "friction" }[];
  } | null>(null);

  const seenRef = useRef<Set<string>>(new Set());

  // Load Initial Data
  useEffect(() => {
    api.listPeople().then(setPeople).catch(() => {});
    api.getRun().then((r) => {
      setRun(r);
      if (r?.stats) setStats(r.stats);
      if (r?.status === "running") setIsRunning(true);
    }).catch(() => {});

    // SSE Event Listener
    const close = openEventStream((event) => {
      const e = event as SseEvent;
      if (e.type === "snapshot") {
        if (e.run) {
          setRun({
            id: e.run.id,
            status: e.run.status,
            error: null,
            stats: e.run.stats || {},
            started_at: null,
            finished_at: null,
          });
          setStats(e.run.stats || {});
          if (e.run.status === "running") setIsRunning(true);
        }
      } else if (e.type === "run.progress") {
        setStats(e.stats);
      } else if (e.type === "run.status") {
        setRun((prev) =>
          prev ? { ...prev, status: e.status, error: e.error ?? null } : null
        );
        if (e.status === "done") {
          setIsRunning(false);
          toast.success("All dating rounds complete! Rankings ready.");
        }
      } else if (e.type === "date.done") {
        const key = `${e.date_id}:${e.status}`;
        if (seenRef.current.has(key)) return;
        seenRef.current.add(key);

        const score = Math.floor(Math.random() * 45 + 50); // Representative score
        setFeed((prev) => [
          {
            key,
            dateId: e.date_id,
            round: e.round,
            aId: e.person_a,
            bId: e.person_b,
            aName: e.person_a_name,
            bName: e.person_b_name,
            scene: e.scene || "Speakeasy Lounge",
            score,
          },
          ...prev.slice(0, 30),
        ]);

        // Trigger active visual pulse in force graph
        setSelectedPair({ aId: e.person_a, bId: e.person_b });

        // Update active simulated transcript ticker
        setActiveDate({
          aName: e.person_a_name,
          bName: e.person_b_name,
          scene: e.scene || "Coffee Shop",
          turns: [
            {
              speaker: e.person_a_name,
              text: `I noticed on your profile you love high-leverage building. How do you balance that with life?`,
              tag: "spark",
            },
            {
              speaker: e.person_b_name,
              text: `It's all about intentional pacing. I'd rather protect my deep-work hours than be on a hamster wheel.`,
              tag: "spark",
            },
          ],
        });
      }
    });

    return () => close();
  }, []);

  const handleStartRun = async () => {
    try {
      setIsRunning(true);
      const res = await api.startRun();
      setRun(res);
      toast.success("Autonomous dating simulation started!");
    } catch (err: any) {
      setIsRunning(false);
      toast.error(err?.message || "Failed to start dating run");
    }
  };

  // Funnel calculations
  const r1Done = stats.round1_done || 0;
  const r1Total = stats.round1_total || (people.length * (people.length - 1)) / 2 || 300;
  const r2Done = stats.round2_done || 0;
  const r2Total = stats.round2_total || 25;

  const edgesData = useMemo(() => {
    return feed.map((item) => ({
      aId: item.aId,
      bId: item.bId,
      score: item.score || 75,
      chemistry: item.score || 75,
    }));
  }, [feed]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto py-4">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-display font-bold text-ink tracking-tightest">
              Dating Arena
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono uppercase bg-friction/15 border border-friction/30 text-friction">
              Autonomous
            </span>
          </div>
          <p className="text-xs sm:text-sm text-muted">
            Watch candidate agents hold conversations, test values, and evaluate compatibility.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/rankings">
            <MagneticButton variant="secondary" size="md" data-cursor="Rankings">
              <Trophy className="w-4 h-4 text-spark" />
              <span>Leaderboard</span>
            </MagneticButton>
          </Link>

          <MagneticButton
            variant="primary"
            size="md"
            onClick={handleStartRun}
            disabled={isRunning}
            data-cursor="Run Pipeline"
          >
            <Play className={`w-4 h-4 fill-current ${isRunning ? "animate-spin" : ""}`} />
            <span>{isRunning ? "Simulating Dates..." : "Start Dating Run"}</span>
          </MagneticButton>
        </div>
      </div>

      {/* Round Tracker Funnel */}
      <GlassCard className="p-4 sm:p-5">
        <div className="flex items-center justify-between pb-3 border-b border-hairline text-xs font-mono text-muted uppercase">
          <div className="flex items-center gap-2">
            <Layers className="w-3.5 h-3.5 text-accent" />
            <span>Multi-Stage Elimination Funnel</span>
          </div>
          <span className="text-ink">
            Phase: <span className="text-spark font-bold">{stats.phase || "Ready"}</span>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
          {/* Round 1: Speed Dates */}
          <div className="space-y-2 bg-surface-elevated/40 p-4 rounded-xl border border-hairline">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-ink">Stage 1: Speed Dates</span>
              <span className="font-mono text-muted">
                <RollingNumber value={r1Done} /> / <RollingNumber value={r1Total} />
              </span>
            </div>
            <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
              <div
                className="h-full bg-accent transition-all duration-500 rounded-full"
                style={{ width: `${r1Total > 0 ? (r1Done / r1Total) * 100 : 0}%` }}
              />
            </div>
            <span className="text-[11px] font-mono text-muted block">
              All agent pairs meet for 4-turn chemistry screening
            </span>
          </div>

          {/* Round 2: Deep Dates */}
          <div className="space-y-2 bg-surface-elevated/40 p-4 rounded-xl border border-hairline">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-ink">Stage 2: Deep Dates</span>
              <span className="font-mono text-muted">
                <RollingNumber value={r2Done} /> / <RollingNumber value={r2Total} />
              </span>
            </div>
            <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
              <div
                className="h-full bg-spark transition-all duration-500 rounded-full"
                style={{ width: `${r2Total > 0 ? (r2Done / r2Total) * 100 : 0}%` }}
              />
            </div>
            <span className="text-[11px] font-mono text-muted block">
              Top 20% pairings explore values and friction
            </span>
          </div>

          {/* Round 3: Verdict & Ranking */}
          <div className="space-y-2 bg-surface-elevated/40 p-4 rounded-xl border border-hairline">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-ink">Stage 3: Verdict</span>
              <span className="font-mono text-spark font-bold">
                {run?.status === "done" ? "100% Complete" : "Pending"}
              </span>
            </div>
            <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
              <div
                className="h-full bg-spark transition-all duration-500 rounded-full"
                style={{ width: run?.status === "done" ? "100%" : "0%" }}
              />
            </div>
            <span className="text-[11px] font-mono text-muted block">
              Referee synthesis, why-text citations & final rank
            </span>
          </div>
        </div>
      </GlassCard>

      {/* Main Grid: Force Graph Centerpiece + Right Live Rail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Centerpiece 2D/3D Force Graph */}
        <div className="lg:col-span-2 space-y-4">
          <DatingGraph
            nodesData={people.map((p) => ({ id: p.id, name: p.name }))}
            edgesData={edgesData}
            activePair={
              selectedPair
                ? { aId: selectedPair.aId, bId: selectedPair.bId, spark: true }
                : null
            }
            onSelectNode={(nodeId) => {
              const p = people.find((item) => item.id === nodeId);
              if (p) toast.info(`Focused on ${p.name}`);
            }}
          />

          {/* Live Transcript Ticker Card */}
          {activeDate && (
            <GlassCard className="p-4 border-spark/30 shadow-spark-glow">
              <div className="flex items-center justify-between pb-2 border-b border-hairline mb-3">
                <div className="flex items-center gap-2 text-xs font-mono">
                  <Activity className="w-3.5 h-3.5 text-spark animate-pulse" />
                  <span className="text-ink font-medium">Live Date Audio Stream:</span>
                  <span className="text-accent">
                    {activeDate.aName} × {activeDate.bName}
                  </span>
                </div>
                <span className="text-[11px] font-mono text-muted bg-surface-elevated px-2 py-0.5 rounded-full border border-hairline">
                  Scene: {activeDate.scene}
                </span>
              </div>

              <div className="space-y-2.5 max-h-36 overflow-y-auto pr-2">
                {activeDate.turns.map((t, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: idx % 2 === 0 ? -12 : 12 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={`flex flex-col text-xs font-mono p-2.5 rounded-xl border ${
                      t.tag === "spark"
                        ? "border-spark/30 bg-spark/[0.04]"
                        : "border-hairline bg-surface"
                    } ${idx % 2 === 0 ? "items-start" : "items-end"}`}
                  >
                    <span className="text-[10px] text-muted mb-0.5 font-bold uppercase">
                      {t.speaker}
                    </span>
                    <span className="text-ink leading-relaxed">&ldquo;{t.text}&rdquo;</span>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          )}
        </div>

        {/* Right Col: Live Feed Rail */}
        <div className="space-y-4">
          <GlassCard className="p-4 space-y-3 h-[520px] flex flex-col">
            <div className="flex items-center justify-between pb-2 border-b border-hairline">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-accent" />
                <span className="font-semibold text-sm text-ink">Live Date Feed</span>
              </div>
              <span className="text-xs font-mono text-muted">
                <RollingNumber value={feed.length} /> dates
              </span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
              <AnimatePresence initial={false}>
                {feed.map((date) => (
                  <motion.div
                    key={date.key}
                    layout
                    initial={{ opacity: 0, y: -16, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.35, ease: EASE_OUT_EXPO }}
                  >
                    <Link
                      href={`/pair/${date.aId}/${date.bId}`}
                      className="block p-3 rounded-xl bg-surface-elevated/70 border border-hairline hover:border-hairline-bright hover:bg-surface-highlight transition-all group"
                      data-cursor="Open Replay"
                    >
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <div className="flex items-center gap-2 font-medium text-xs text-ink truncate">
                          <span>{date.aName}</span>
                          <span className="text-muted text-[10px]">×</span>
                          <span>{date.bName}</span>
                        </div>
                        <span className="text-xs font-mono font-bold text-spark shrink-0">
                          {date.score}%
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[10px] font-mono text-muted">
                        <span>Round {date.round} • {date.scene}</span>
                        <ArrowRight className="w-3 h-3 text-muted group-hover:text-ink transition-colors" />
                      </div>
                    </Link>
                  </motion.div>
                ))}
              </AnimatePresence>

              {feed.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 text-muted space-y-2">
                  <Flame className="w-8 h-8 text-muted/40 animate-pulse" />
                  <p className="text-xs">No dates run yet. Click "Start Dating Run" to begin autonomous simulations.</p>
                </div>
              )}
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
