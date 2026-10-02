"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Briefcase,
  Camera,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  Flame,
  HelpCircle,
  ExternalLink,
  Target,
  Heart,
  Compass,
} from "lucide-react";
import { api } from "../../../lib/api";
import type { Claim, PersonDetailOut, SayDoGap } from "../../../lib/types";
import {
  GlassCard,
  MagneticButton,
  RollingNumber,
  CardSkeleton,
} from "../../../components/ui";
import { EASE_OUT_EXPO } from "../../../lib/motion";

// Trait Radar SVG Polygon Component
function TraitRadar({
  payload,
  claims,
}: {
  payload: any;
  claims: Claim[];
}) {
  const [activeTrait, setActiveTrait] = useState<string | null>(null);

  const traits = useMemo(() => {
    // Score traits from payload presence (0.0 to 1.0)
    const ambition = payload?.ambition_level?.toLowerCase().includes("high") ? 0.9 : 0.7;
    const social = payload?.lived_self?.social_energy?.toLowerCase().includes("high") ? 0.85 : 0.65;
    const valuesCount = Math.min((payload?.values?.length || 3) / 5, 1);
    const needsCount = Math.min((payload?.needs?.length || 3) / 5, 1);
    const interestsCount = Math.min((payload?.interests?.length || 3) / 6, 1);
    const lifestyle = payload?.lifestyle ? 0.8 : 0.5;

    return [
      { key: "Ambition", val: ambition, desc: payload?.ambition_level || "High drive" },
      { key: "Social Energy", val: social, desc: payload?.lived_self?.social_energy || "Balanced" },
      { key: "Core Values", val: valuesCount, desc: payload?.values?.slice(0, 2).join(", ") || "Principled" },
      { key: "Needs Clarity", val: needsCount, desc: payload?.needs?.slice(0, 2).join(", ") || "Self-aware" },
      { key: "Interests Depth", val: interestsCount, desc: payload?.interests?.slice(0, 2).join(", ") || "Curious" },
      { key: "Lifestyle Fit", val: lifestyle, desc: payload?.lifestyle || "Active" },
    ];
  }, [payload]);

  const size = 260;
  const center = size / 2;
  const radius = size * 0.38;

  const points = traits.map((t, i) => {
    const angle = (Math.PI * 2 * i) / traits.length - Math.PI / 2;
    const r = radius * t.val;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
      labelX: center + (radius + 24) * Math.cos(angle),
      labelY: center + (radius + 24) * Math.sin(angle),
      trait: t,
    };
  });

  const polygonPath = points.map((p) => `${p.x},${p.y}`).join(" ");

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative w-[280px] h-[280px]">
        <svg width="280" height="280" viewBox="0 0 280 280" className="overflow-visible">
          {/* Background Concentric Webs */}
          {[0.25, 0.5, 0.75, 1].map((level) => (
            <polygon
              key={level}
              points={traits
                .map((_, i) => {
                  const angle = (Math.PI * 2 * i) / traits.length - Math.PI / 2;
                  const r = radius * level;
                  return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
                })
                .join(" ")}
              fill="none"
              stroke="rgba(255, 255, 255, 0.07)"
              strokeWidth="1"
            />
          ))}

          {/* Web Spoke Lines */}
          {traits.map((_, i) => {
            const angle = (Math.PI * 2 * i) / traits.length - Math.PI / 2;
            return (
              <line
                key={i}
                x1={center}
                y1={center}
                x2={center + radius * Math.cos(angle)}
                y2={center + radius * Math.sin(angle)}
                stroke="rgba(255, 255, 255, 0.08)"
                strokeWidth="1"
              />
            );
          })}

          {/* Animated Trait Polygon */}
          <motion.polygon
            points={polygonPath}
            fill="rgba(139, 139, 255, 0.2)"
            stroke="#8B8BFF"
            strokeWidth="2"
            initial={{ opacity: 0, scale: 0.1 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, ease: EASE_OUT_EXPO }}
            style={{ transformOrigin: `${center}px ${center}px` }}
          />

          {/* Points & Labels */}
          {points.map((p, i) => (
            <g
              key={i}
              className="cursor-pointer"
              onMouseEnter={() => setActiveTrait(p.trait.key)}
              onMouseLeave={() => setActiveTrait(null)}
            >
              <circle
                cx={p.x}
                cy={p.y}
                r={activeTrait === p.trait.key ? 5 : 3.5}
                className="fill-accent transition-all shadow-accent-glow"
              />
              <text
                x={p.labelX}
                y={p.labelY}
                textAnchor="middle"
                dominantBaseline="middle"
                className={`text-[10px] font-mono tracking-tight transition-colors ${
                  activeTrait === p.trait.key ? "fill-spark font-bold" : "fill-muted"
                }`}
              >
                {p.trait.key}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {/* Trait Hover Insight Pill */}
      <div className="h-6 mt-2 text-center text-xs font-mono text-muted">
        {activeTrait ? (
          <span className="text-spark animate-fadeIn">
            {activeTrait}: {traits.find((t) => t.key === activeTrait)?.desc}
          </span>
        ) : (
          <span>Hover vertices to inspect personality dimensions</span>
        )}
      </div>
    </div>
  );
}

// Signature Say/Do Gap Split View with Connected Animated Curves
function SayDoGapView({ gaps }: { gaps: SayDoGap[] }) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (!gaps || gaps.length === 0) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-ink tracking-tight flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-spark" />
            <span>The Say / Do Gap</span>
          </h3>
          <p className="text-xs text-muted">
            Comparing stated presentation (LinkedIn) with lived behavior (Instagram). Solid green = agree, red = diverge.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative">
        {gaps.map((gap, idx) => {
          const isAgree = gap.type === "agree";
          const isHovered = hoveredIndex === idx;
          const isDimmed = hoveredIndex !== null && !isHovered;

          return (
            <div
              key={idx}
              onMouseEnter={() => setHoveredIndex(idx)}
              onMouseLeave={() => setHoveredIndex(null)}
              className={`glass-card p-5 transition-all duration-300 ${
                isDimmed ? "opacity-30 blur-[0.5px]" : "opacity-100"
              } ${
                isHovered
                  ? isAgree
                    ? "border-spark/40 shadow-spark-glow"
                    : "border-friction/40 shadow-friction-glow"
                  : ""
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-3">
                <span className="text-xs font-mono uppercase tracking-wider text-muted">
                  Vector #{idx + 1}
                </span>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-mono uppercase tracking-wider font-semibold border ${
                    isAgree
                      ? "bg-spark/15 text-spark border-spark/30"
                      : "bg-friction/15 text-friction border-friction/30"
                  }`}
                >
                  {isAgree ? "Agree" : "Diverge"}
                </span>
              </div>

              {/* Split Content */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="space-y-1 bg-surface-elevated/40 p-3 rounded-xl border border-hairline">
                  <div className="text-[10px] font-mono uppercase text-accent flex items-center gap-1.5">
                    <Briefcase className="w-3 h-3" />
                    <span>LinkedIn Stated</span>
                  </div>
                  <p className="text-ink text-xs font-medium leading-relaxed">
                    {gap.stated}
                  </p>
                </div>

                <div className="space-y-1 bg-surface-elevated/40 p-3 rounded-xl border border-hairline">
                  <div className="text-[10px] font-mono uppercase text-friction flex items-center gap-1.5">
                    <Camera className="w-3 h-3" />
                    <span>Instagram Lived</span>
                  </div>
                  <p className="text-ink text-xs font-medium leading-relaxed">
                    {gap.lived}
                  </p>
                </div>
              </div>

              {/* Verbatim Evidence Quotes */}
              {gap.evidence && gap.evidence.length > 0 && (
                <div className="mt-3 pt-3 border-t border-hairline space-y-1.5">
                  <div className="text-[10px] font-mono text-muted uppercase">Verbatim Source Evidence:</div>
                  {gap.evidence.map((ev, eIdx) => (
                    <div
                      key={eIdx}
                      className="text-xs font-mono text-muted pl-2 border-l-2 border-hairline-bright"
                    >
                      <span className="text-accent uppercase text-[10px] mr-1.5">[{ev.source}]</span>
                      &ldquo;{ev.quote}&rdquo;
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Claims List with animated filtering chips
function ClaimsSection({ claims }: { claims: Claim[] }) {
  const [filter, setFilter] = useState<"all" | "linkedin" | "instagram" | "stated" | "inferred">("all");

  const filteredClaims = useMemo(() => {
    if (!claims) return [];
    if (filter === "all") return claims;
    if (filter === "linkedin") return claims.filter((c) => c.source === "linkedin" || c.source === "both");
    if (filter === "instagram") return claims.filter((c) => c.source === "instagram" || c.source === "both");
    if (filter === "stated") return claims.filter((c) => c.kind === "stated");
    if (filter === "inferred") return claims.filter((c) => c.kind === "inferred");
    return claims;
  }, [claims, filter]);

  if (!claims || claims.length === 0) return null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-ink tracking-tight">
            Verifiable Agent Claims ({claims.length})
          </h3>
          <p className="text-xs text-muted">
            Ground-truth claims extracted from public profiles with confidence ratings and exact quotes.
          </p>
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-1.5 bg-surface-elevated/60 p-1 rounded-xl border border-hairline text-xs font-mono">
          {(["all", "linkedin", "instagram", "stated", "inferred"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-2.5 py-1 rounded-lg capitalize transition-colors ${
                filter === tab
                  ? "bg-surface-elevated text-ink font-semibold shadow-sm"
                  : "text-muted hover:text-ink"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <AnimatePresence>
          {filteredClaims.map((claim, idx) => (
            <motion.div
              key={idx}
              layout
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3 }}
              className="glass-card p-4 space-y-3"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-xs font-medium text-ink leading-snug">
                  {claim.claim}
                </span>
                <div className="flex items-center gap-1.5 shrink-0">
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase bg-white/[0.06] border border-hairline text-muted">
                    {claim.kind}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase bg-accent/15 border border-accent/30 text-accent">
                    {claim.source}
                  </span>
                </div>
              </div>

              {/* Confidence Bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] font-mono text-muted">
                  <span>Confidence</span>
                  <span>{(claim.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full h-1 bg-surface-elevated rounded-full overflow-hidden">
                  <div
                    className="h-full bg-spark rounded-full transition-all duration-500"
                    style={{ width: `${claim.confidence * 100}%` }}
                  />
                </div>
              </div>

              {/* Verbatim Quote in Mono */}
              {claim.quote && (
                <div className="pt-2 border-t border-hairline text-xs font-mono text-muted/80 bg-black/20 p-2 rounded-lg">
                  &ldquo;{claim.quote}&rdquo;
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default function PersonProfilePage() {
  const { id } = useParams<{ id: string }>();
  const [person, setPerson] = useState<PersonDetailOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    api
      .getPerson(id)
      .then((data) => {
        setPerson(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="space-y-6 max-w-6xl mx-auto py-8">
        <CardSkeleton />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (!person) {
    return (
      <div className="max-w-md mx-auto py-20 text-center space-y-4">
        <HelpCircle className="w-12 h-12 text-muted mx-auto" />
        <h2 className="text-lg font-semibold text-ink">Person not found</h2>
        <Link href="/">
          <MagneticButton variant="secondary">Back to candidates</MagneticButton>
        </Link>
      </div>
    );
  }

  const payload = person.analysis?.payload;
  const li = (person.linkedin_data || {}) as Record<string, any>;
  const ig = (person.instagram_data || {}) as Record<string, any>;

  const followerCount = ig.followers || ig.follower_count || 0;
  const postCount = ig.post_count || (ig.latest_posts?.length || 0);
  const expCount = li.experience?.length || 0;

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-6">
      {/* Top Breadcrumb & Nav */}
      <div className="flex items-center justify-between">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-mono text-muted hover:text-ink transition-colors"
          data-cursor="Back"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>All Candidates</span>
        </Link>

        <div className="flex items-center gap-2">
          <Link href={`/rankings/${person.id}`}>
            <MagneticButton variant="secondary" size="sm" data-cursor="View Rankings">
              <Target className="w-3.5 h-3.5 text-spark" />
              <span>View Best Matches</span>
            </MagneticButton>
          </Link>
        </div>
      </div>

      {/* Profile Header Hero Card */}
      <GlassCard className="p-6 sm:p-8 space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            {/* Avatar / Photo */}
            <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-2xl bg-surface-elevated border border-hairline-bright overflow-hidden flex items-center justify-center shrink-0 shadow-glass">
              {li.photo_url || ig.profile_pic_url ? (
                <img
                  src={li.photo_url || ig.profile_pic_url}
                  alt={person.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="font-display font-bold text-3xl text-ink">
                  {person.name.charAt(0)}
                </span>
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center gap-3">
                <h1 className="text-2xl sm:text-3xl font-display font-bold text-ink tracking-tightest">
                  {person.name}
                </h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono uppercase bg-spark/15 border border-spark/30 text-spark">
                  {person.status}
                </span>
              </div>
              <p className="text-sm text-muted max-w-xl line-clamp-2">
                {li.headline || payload?.summary || "Public Profile Analyzed"}
              </p>
              <div className="flex items-center gap-3 pt-1 text-xs font-mono text-muted">
                {person.linkedin_url && (
                  <a
                    href={person.linkedin_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 hover:text-ink"
                  >
                    <Briefcase className="w-3.5 h-3.5 text-accent" />
                    <span>LinkedIn</span>
                  </a>
                )}
                {person.instagram_url && (
                  <a
                    href={person.instagram_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 hover:text-ink"
                  >
                    <Camera className="w-3.5 h-3.5 text-friction" />
                    <span>Instagram</span>
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Rolling Counters */}
          <div className="flex items-center gap-6 sm:gap-8 border-t sm:border-t-0 sm:border-l border-hairline pt-4 sm:pt-0 sm:pl-8">
            <div className="text-center sm:text-left">
              <div className="text-2xl font-mono font-bold text-ink">
                <RollingNumber value={followerCount} />
              </div>
              <div className="text-[11px] font-mono text-muted uppercase tracking-wider">
                Followers
              </div>
            </div>

            <div className="text-center sm:text-left">
              <div className="text-2xl font-mono font-bold text-ink">
                <RollingNumber value={postCount} />
              </div>
              <div className="text-[11px] font-mono text-muted uppercase tracking-wider">
                Posts
              </div>
            </div>

            <div className="text-center sm:text-left">
              <div className="text-2xl font-mono font-bold text-ink">
                <RollingNumber value={expCount} />
              </div>
              <div className="text-[11px] font-mono text-muted uppercase tracking-wider">
                Roles
              </div>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Analysis Grid: Personality Dimensions & Trait Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Structured Needs, Hobbies, Interests, Values */}
        <div className="lg:col-span-2 space-y-6">
          <GlassCard className="p-6 space-y-5">
            <h3 className="text-base font-semibold text-ink tracking-tight flex items-center gap-2">
              <Heart className="w-4 h-4 text-friction" />
              <span>Core Needs & Relationship Intent</span>
            </h3>

            {/* Needs Chips */}
            <div className="space-y-2">
              <span className="text-xs font-mono uppercase text-muted tracking-wider block">
                Needs from a Partner:
              </span>
              <div className="flex flex-wrap gap-2">
                {payload?.needs?.map((need: string, i: number) => (
                  <span
                    key={i}
                    className="px-3 py-1.5 rounded-xl bg-surface-elevated border border-hairline text-xs text-ink font-medium"
                  >
                    {need}
                  </span>
                )) || <span className="text-xs text-muted">No explicit needs extracted</span>}
              </div>
            </div>

            {/* Interests & Hobbies */}
            <div className="space-y-2 pt-2">
              <span className="text-xs font-mono uppercase text-muted tracking-wider block">
                Lived Interests & Passions:
              </span>
              <div className="flex flex-wrap gap-2">
                {(payload?.interests || payload?.lived_self?.hobbies || []).map(
                  (interest: string, i: number) => (
                    <span
                      key={i}
                      className="px-3 py-1.5 rounded-xl bg-accent/10 border border-accent/20 text-xs text-accent font-medium"
                    >
                      {interest}
                    </span>
                  )
                )}
              </div>
            </div>

            {/* Values & Qualities */}
            <div className="space-y-2 pt-2">
              <span className="text-xs font-mono uppercase text-muted tracking-wider block">
                Core Values:
              </span>
              <div className="flex flex-wrap gap-2">
                {payload?.values?.map((val: string, i: number) => (
                  <span
                    key={i}
                    className="px-3 py-1.5 rounded-xl bg-spark/10 border border-spark/20 text-xs text-spark font-medium"
                  >
                    {val}
                  </span>
                ))}
              </div>
            </div>
          </GlassCard>

          {/* Say / Do Gap */}
          {payload?.say_do_gap && <SayDoGapView gaps={payload.say_do_gap} />}
        </div>

        {/* Right Col: Trait Radar & Data Gaps */}
        <div className="space-y-6">
          <GlassCard className="p-5 flex flex-col items-center">
            <h3 className="text-sm font-semibold text-ink tracking-tight self-start mb-2">
              Autonomous Trait Radar
            </h3>
            <TraitRadar payload={payload} claims={payload?.claims || []} />
          </GlassCard>

          {/* Data Gaps (Honest Transparency) */}
          <GlassCard className="p-5 space-y-3 bg-surface/50 border-hairline">
            <div className="flex items-center gap-2 text-xs font-mono text-muted uppercase">
              <AlertTriangle className="w-3.5 h-3.5 text-muted" />
              <span>Data Gaps & Missing Signals</span>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              {payload?.data_gaps?.length
                ? payload.data_gaps.join(" ")
                : "Profile strictly derived from public LinkedIn and Instagram text. No private or protected attributes inferred."}
            </p>
          </GlassCard>
        </div>
      </div>

      {/* Claims Ground-Truth Section */}
      {payload?.claims && <ClaimsSection claims={payload.claims} />}
    </div>
  );
}
