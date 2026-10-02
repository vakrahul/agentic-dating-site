"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Trophy, ArrowRight, Sparkles, User, ExternalLink } from "lucide-react";
import { api } from "../../lib/api";
import type { PersonOut, RankingsOverview } from "../../lib/types";
import { GlassCard, MagneticButton, CardSkeleton } from "../../components/ui";

export default function RankingsOverviewPage() {
  const [data, setData] = useState<RankingsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .rankingsOverview()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 max-w-5xl mx-auto py-8">
        <CardSkeleton />
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (!data || data.people.length === 0) {
    return (
      <div className="max-w-md mx-auto py-24 text-center space-y-4">
        <Trophy className="w-12 h-12 text-muted mx-auto" />
        <h2 className="text-xl font-bold text-ink tracking-tight">No Rankings Computed Yet</h2>
        <p className="text-xs text-muted">
          Add candidates on the home page and run the dating arena, or load the instant demo.
        </p>
        <div className="pt-2 flex justify-center gap-3">
          <Link href="/">
            <MagneticButton variant="primary">Add Candidates</MagneticButton>
          </Link>
          <Link href="/dating">
            <MagneticButton variant="secondary">Go to Dating Arena</MagneticButton>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto py-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-display font-bold text-ink tracking-tightest">
              Compatibility Rankings
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono uppercase bg-spark/15 border border-spark/30 text-spark">
              Leaderboard
            </span>
          </div>
          <p className="text-xs sm:text-sm text-muted">
            Select any candidate agent to review their top ranked matches, score breakdown, and slope changes.
          </p>
        </div>

        <Link href="/dating">
          <MagneticButton variant="secondary" size="md">
            <span>Dating Arena Web</span>
            <ArrowRight className="w-4 h-4" />
          </MagneticButton>
        </Link>
      </div>

      {/* Grid of People Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {data.people.map((person, idx) => (
          <motion.div
            key={person.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: idx * 0.03 }}
          >
            <GlassCard
              className="p-5 space-y-3 hover:border-hairline-bright hover:bg-surface-highlight transition-all group"
              dataCursor="View Rankings"
            >
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-surface-elevated border border-hairline flex items-center justify-center font-display font-bold text-ink text-base">
                  {person.name.charAt(0)}
                </div>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-surface-elevated border border-hairline text-muted">
                  Agent #{person.id}
                </span>
              </div>

              <div>
                <h3 className="font-display font-bold text-base text-ink group-hover:text-accent transition-colors truncate">
                  {person.name}
                </h3>
                <p className="text-xs font-mono text-muted truncate">
                  {person.linkedin_url.replace("https://www.linkedin.com/in/", "")}
                </p>
              </div>

              <div className="pt-2 border-t border-hairline flex items-center justify-between text-xs font-mono">
                <Link
                  href={`/rankings/${person.id}`}
                  className="text-spark font-medium hover:underline flex items-center gap-1"
                >
                  <span>Ranked Matches</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
                <Link
                  href={`/people/${person.id}`}
                  className="text-muted hover:text-ink"
                  title="Profile Details"
                >
                  <User className="w-3.5 h-3.5" />
                </Link>
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
