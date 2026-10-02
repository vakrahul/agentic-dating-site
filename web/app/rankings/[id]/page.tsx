"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Trophy,
  ArrowLeft,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  User,
  ExternalLink,
  MessageSquare,
} from "lucide-react";
import { api } from "../../../lib/api";
import type { MatchOut, RankingOut, PersonOut } from "../../../lib/types";
import {
  GlassCard,
  MagneticButton,
  RollingNumber,
  HoloBadge,
  CardSkeleton,
} from "../../../components/ui";
import { EASE_OUT_EXPO } from "../../../lib/motion";

const BREAKDOWN_KEYS: { key: keyof MatchOut["breakdown"]; label: string; color: string }[] = [
  { key: "values", label: "Values", color: "#8B8BFF" },
  { key: "interests", label: "Interests", color: "#7CFFB2" },
  { key: "lifestyle", label: "Lifestyle", color: "#FFB020" },
  { key: "ambition", label: "Ambition", color: "#60A5FA" },
  { key: "chemistry", label: "Chemistry", color: "#FF5C7A" },
];

// Slope Graph Component: Before (Similarity Rank) -> After (Final Dating Rank)
function SlopeIndicator({ simRank, finalRank, delta }: { simRank: number; finalRank: number; delta: number }) {
  const isUp = delta > 0;
  const isDown = delta < 0;

  return (
    <div className="flex items-center gap-3 font-mono text-xs">
      <div className="flex flex-col items-center">
        <span className="text-[10px] text-muted uppercase">Sim</span>
        <span className="text-muted font-bold">#{simRank}</span>
      </div>

      {/* Slope Arrow & Delta */}
      <div className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-white/[0.04] border border-hairline">
        {isUp ? (
          <TrendingUp className="w-3.5 h-3.5 text-spark" />
        ) : isDown ? (
          <TrendingDown className="w-3.5 h-3.5 text-friction" />
        ) : (
          <span className="text-muted text-xs">—</span>
        )}
        <span
          className={`font-bold ${
            isUp ? "text-spark" : isDown ? "text-friction" : "text-muted"
          }`}
        >
          {delta > 0 ? `+${delta}` : delta}
        </span>
      </div>

      <div className="flex flex-col items-center">
        <span className="text-[10px] text-muted uppercase">Final</span>
        <span className="text-ink font-bold">#{finalRank}</span>
      </div>
    </div>
  );
}

// Word-by-word reveal for "Why" text with inline citation links
function WordByWordWhy({ text, pairHref }: { text: string; pairHref: string }) {
  const words = useMemo(() => text.split(" "), [text]);

  return (
    <p className="text-xs font-sans text-ink/90 leading-relaxed pl-3 border-l-2 border-accent/40 bg-white/[0.02] p-2 rounded-r-lg">
      {words.map((word, i) => {
        // Detect turn citation like "[turn 3]" or "turn 2"
        const isCitation = /turn\s*\d+/i.test(word);

        return (
          <motion.span
            key={i}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: i * 0.025, ease: EASE_OUT_EXPO }}
            className={`inline-block mr-1 ${
              isCitation
                ? "font-mono text-spark font-semibold hover:underline cursor-pointer"
                : ""
            }`}
          >
            {isCitation ? (
              <Link href={`${pairHref}?turn=1`}>{word}</Link>
            ) : (
              word
            )}
          </motion.span>
        );
      })}
    </p>
  );
}

export default function PersonRankingPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [ranking, setRanking] = useState<RankingOut | null>(null);
  const [allPeople, setAllPeople] = useState<PersonOut[]>([]);
  const [loading, setLoading] = useState(true);

  // Load ranking & all people list for the carousel switcher
  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api
      .getRanking(id)
      .then((data) => {
        setRanking(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));

    api.listPeople().then(setAllPeople).catch(() => {});
  }, [id]);

  // Keyboard Navigation Carousel (Left/Right arrow keys)
  const currentIdx = useMemo(() => {
    return allPeople.findIndex((p) => p.id === Number(id));
  }, [allPeople, id]);

  const handlePrev = useCallback(() => {
    if (currentIdx > 0) {
      router.push(`/rankings/${allPeople[currentIdx - 1].id}`);
    }
  }, [currentIdx, allPeople, router]);

  const handleNext = useCallback(() => {
    if (currentIdx < allPeople.length - 1) {
      router.push(`/rankings/${allPeople[currentIdx + 1].id}`);
    }
  }, [currentIdx, allPeople, router]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") handlePrev();
      if (e.key === "ArrowRight") handleNext();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handlePrev, handleNext]);

  if (loading) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto py-8">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  if (!ranking) {
    return (
      <div className="max-w-md mx-auto py-20 text-center space-y-4">
        <Trophy className="w-12 h-12 text-muted mx-auto" />
        <h2 className="text-lg font-semibold text-ink">Ranking not found</h2>
        <Link href="/rankings">
          <MagneticButton variant="secondary">Back to all rankings</MagneticButton>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-6">
      {/* Top Carousel Switcher */}
      <div className="flex items-center justify-between gap-4">
        <Link
          href="/rankings"
          className="inline-flex items-center gap-2 text-xs font-mono text-muted hover:text-ink transition-colors"
          data-cursor="Leaderboard"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>All Leaderboards</span>
        </Link>

        {/* Person Switcher Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrev}
            disabled={currentIdx <= 0}
            className="p-1.5 rounded-lg bg-surface-elevated border border-hairline text-muted hover:text-ink disabled:opacity-20 transition-all"
            data-cursor="Prev Person"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-xs font-mono text-muted px-2">
            {currentIdx + 1} / {allPeople.length || 25}
          </span>
          <button
            onClick={handleNext}
            disabled={currentIdx >= allPeople.length - 1}
            className="p-1.5 rounded-lg bg-surface-elevated border border-hairline text-muted hover:text-ink disabled:opacity-20 transition-all"
            data-cursor="Next Person"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Target Person Hero Card */}
      <GlassCard className="p-6 sm:p-7 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 border-accent/20">
        <div className="space-y-1.5">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-display font-bold text-ink tracking-tightest">
              {ranking.person.name}
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono uppercase bg-accent/15 border border-accent/30 text-accent">
              Focal Agent
            </span>
          </div>
          <p className="text-xs sm:text-sm text-muted">
            Ranked matches based on multi-turn autonomous date simulations, referee evaluation, and semantic vector similarity.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link href={`/people/${ranking.person.id}`}>
            <MagneticButton variant="secondary" size="sm" data-cursor="Profile">
              <User className="w-3.5 h-3.5 text-accent" />
              <span>Inspect Profile</span>
            </MagneticButton>
          </Link>
        </div>
      </GlassCard>

      {/* Ranked Matches List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-ink tracking-tight flex items-center gap-2">
            <Trophy className="w-4 h-4 text-spark" />
            <span>Ranked Compatibility Matches ({ranking.matches.length})</span>
          </h2>
          <span className="text-xs font-mono text-muted">
            Formula: 0.45×Mutual + 0.40×Referee + 0.15×Embedding
          </span>
        </div>

        <div className="space-y-3">
          <AnimatePresence>
            {ranking.matches.map((match, idx) => (
              <motion.div
                key={match.person_id}
                layout
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: idx * 0.04, ease: EASE_OUT_EXPO }}
              >
                <GlassCard
                  className={`p-5 space-y-4 transition-all hover:border-hairline-bright ${
                    idx === 0 ? "border-spark/30 shadow-spark-glow" : ""
                  }`}
                >
                  {/* Row Top Header */}
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      {/* Big Mono Final Rank */}
                      <span className="font-mono font-extrabold text-2xl sm:text-3xl text-ink/90 w-10 text-center select-none">
                        #{match.final_rank}
                      </span>

                      <div>
                        <div className="flex items-center gap-2.5">
                          <Link
                            href={`/people/${match.person_id}`}
                            className="font-display font-bold text-base sm:text-lg text-ink hover:text-accent transition-colors"
                          >
                            {match.person_name}
                          </Link>
                          {match.badge && (
                            <HoloBadge
                              type={match.badge}
                              reason={match.badge_turn_link?.reason || ""}
                              onClick={() => {
                                if (match.badge_turn_link) {
                                  router.push(
                                    `${match.pair_href}?turn=${match.badge_turn_link.turn_index + 1}`
                                  );
                                }
                              }}
                            />
                          )}
                        </div>
                        <span className="text-[11px] font-mono text-muted">
                          Advanced to Round {match.round_used} • Date #{match.date_id}
                        </span>
                      </div>
                    </div>

                    {/* Right: Slope indicator & Big Final Score */}
                    <div className="flex items-center gap-5 self-end sm:self-auto">
                      <SlopeIndicator
                        simRank={match.similarity_rank}
                        finalRank={match.final_rank}
                        delta={match.delta}
                      />

                      <div className="text-right">
                        <div className="text-2xl sm:text-3xl font-mono font-extrabold text-spark tracking-tight">
                          <RollingNumber value={match.final} decimals={1} />
                        </div>
                        <span className="text-[10px] font-mono uppercase text-muted tracking-wider">
                          Final Score
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Segmented Dimension Breakdown Bar */}
                  <div className="space-y-1.5 pt-2 border-t border-hairline">
                    <div className="flex justify-between items-center text-[11px] font-mono text-muted">
                      <span>Compatibility Breakdown</span>
                      <div className="flex gap-4">
                        {BREAKDOWN_KEYS.map((k) => (
                          <span key={k.key} style={{ color: k.color }}>
                            {k.label}: {match.breakdown[k.key]?.toFixed(0)}%
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="w-full h-2 rounded-full bg-surface-elevated flex overflow-hidden gap-0.5 p-0.5">
                      {BREAKDOWN_KEYS.map((k) => {
                        const score = match.breakdown[k.key] || 0;
                        return (
                          <div
                            key={k.key}
                            className="h-full rounded-sm transition-all duration-700"
                            style={{
                              width: `${score / 5}%`,
                              backgroundColor: k.color,
                            }}
                            title={`${k.label}: ${score.toFixed(0)}`}
                          />
                        );
                      })}
                    </div>
                  </div>

                  {/* Why Text with word-by-word reveal */}
                  {match.why && (
                    <div className="pt-1">
                      <WordByWordWhy text={match.why} pairHref={match.pair_href} />
                    </div>
                  )}

                  {/* Footer link to Pair Replay */}
                  <div className="flex justify-end pt-1">
                    <Link
                      href={match.pair_href}
                      className="inline-flex items-center gap-1.5 text-xs font-mono text-accent hover:text-ink transition-colors"
                      data-cursor="Play Replay"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Watch Agent Date Replay</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
