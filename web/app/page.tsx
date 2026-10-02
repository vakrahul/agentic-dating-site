"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Check,
  X,
  Plus,
  Trash2,
  Play,
  RotateCcw,
  Sparkles,
  Clipboard,
  ExternalLink,
  Users,
} from "lucide-react";
import { api, openEventStream } from "../lib/api";
import type { PersonOut, SseEvent } from "../lib/types";
import { ParticleHero } from "../components/ParticleHero";
import {
  MagneticButton,
  SegmentedProgressPill,
  GlassCard,
  RollingNumber,
} from "../components/ui";
import {
  containerStagger,
  itemSlideUp,
  transitionExpo,
  EASE_OUT_EXPO,
} from "../lib/motion";
import { toast } from "sonner";

interface InputRow {
  id: number;
  linkedin: string;
  instagram: string;
  personId?: number;
}

const LINKEDIN_RE = /linkedin\.com\/in\//i;
const INSTAGRAM_RE = /instagram\.com\//i;

let rowKeySeq = 1;

export default function AddPeoplePage() {
  const router = useRouter();
  const [rows, setRows] = useState<InputRow[]>([
    { id: rowKeySeq++, linkedin: "", instagram: "" },
  ]);
  const [pasteMode, setPasteMode] = useState(false);
  const [pasteText, setPasteText] = useState("");
  const [people, setPeople] = useState<PersonOut[]>([]);
  const [live, setLive] = useState<Record<number, PersonOut>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  const refreshPeople = useCallback(async () => {
    try {
      const list = await api.listPeople();
      setPeople(list);
      setLive((prev) => {
        const next = { ...prev };
        for (const p of list) next[p.id] = p;
        return next;
      });
    } catch {
      // Backend not yet available
    }
  }, []);

  useEffect(() => {
    void refreshPeople();
    const closeStream = openEventStream((event) => {
      const e = event as SseEvent;
      if (e.type === "snapshot") {
        setLive((prev) => {
          const next = { ...prev };
          for (const p of e.people) next[p.id] = p;
          return next;
        });
        setPeople(e.people);
      } else if (e.type === "person.status") {
        setLive((prev) => ({
          ...prev,
          [e.person_id]: {
            id: e.person_id,
            name: e.name,
            status: e.status,
            error: e.error ?? null,
            linkedin_url: prev[e.person_id]?.linkedin_url ?? "",
            instagram_url: prev[e.person_id]?.instagram_url ?? "",
            has_analysis: e.status === "analyzed",
          },
        }));
      }
    });

    return () => closeStream();
  }, [refreshPeople]);

  // URL Validations
  const validateField = (type: "linkedin" | "instagram", val: string) => {
    const trimmed = val.trim();
    if (!trimmed) return null;
    if (type === "linkedin") return LINKEDIN_RE.test(trimmed);
    return INSTAGRAM_RE.test(trimmed);
  };

  const handleRowChange = (id: number, field: "linkedin" | "instagram", value: string) => {
    setRows((prev) =>
      prev.map((r) => (r.id === id ? { ...r, [field]: value } : r))
    );
  };

  const addRow = () => {
    setRows((prev) => [...prev, { id: rowKeySeq++, linkedin: "", instagram: "" }]);
  };

  const removeRow = (id: number) => {
    setRows((prev) => (prev.length > 1 ? prev.filter((r) => r.id !== id) : prev));
  };

  // Exploding paste-many logic
  const handleParsePaste = () => {
    const lines = pasteText
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

    if (lines.length === 0) return;

    const parsed: InputRow[] = [];
    for (const line of lines) {
      const parts = line.split(/[\s,;\t]+/).map((s) => s.trim()).filter(Boolean);
      let li = "";
      let ig = "";
      for (const part of parts) {
        if (LINKEDIN_RE.test(part) && !li) li = part;
        else if (INSTAGRAM_RE.test(part) && !ig) ig = part;
      }
      if (li || ig) {
        parsed.push({ id: rowKeySeq++, linkedin: li, instagram: ig });
      }
    }

    if (parsed.length > 0) {
      setRows(parsed);
      setPasteMode(false);
      setPasteText("");
      toast.success(`Exploded ${parsed.length} profile rows`);
    } else {
      toast.error("No valid LinkedIn or Instagram URLs found in pasted text");
    }
  };

  // Load Seed 25 People
  const loadSeed25 = async () => {
    try {
      const res = await fetch("/seed.json");
      if (!res.ok) throw new Error("seed.json not found");
      const data = await res.json();
      const seedRows: InputRow[] = data.map((item: any) => ({
        id: rowKeySeq++,
        linkedin: item.linkedin_url,
        instagram: item.instagram_url,
      }));
      setRows(seedRows);
      toast.success("Loaded 25 verified candidates into table");
    } catch {
      toast.error("Could not load candidate seed");
    }
  };

  // Submit and start ingestion pipeline
  const handleSubmitBatch = async () => {
    const validRows = rows.filter(
      (r) => validateField("linkedin", r.linkedin) && validateField("instagram", r.instagram)
    );

    if (validRows.length === 0) {
      toast.error("Enter at least one row with both a valid LinkedIn and Instagram URL");
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = validRows.map((r) => ({
        linkedin_url: r.linkedin.trim(),
        instagram_url: r.instagram.trim(),
      }));
      const res = await api.createPeople(payload);
      toast.success(`Ingested ${res.count} candidates. Agents analyzing...`);
      await refreshPeople();
    } catch (err: any) {
      toast.error(err?.message || "Failed to ingest candidates");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Load Demo Run
  const handleLoadDemo = async () => {
    setDemoLoading(true);
    try {
      const res = await fetch("/demo_run.json");
      if (!res.ok) throw new Error("demo_run.json not found");
      const demoData = await res.json();
      await api.importRun(demoData);
      toast.success("Pre-computed demo loaded! Redirecting to rankings...");
      router.push("/rankings");
    } catch (err: any) {
      toast.error(err?.message || "Failed to load demo");
    } finally {
      setDemoLoading(false);
    }
  };

  const analyzedCount = useMemo(() => {
    return people.filter((p) => (live[p.id]?.status || p.status) === "analyzed").length;
  }, [people, live]);

  const queuedCount = useMemo(() => {
    return people.filter((p) => {
      const s = live[p.id]?.status || p.status;
      return s === "queued" || s === "failed";
    }).length;
  }, [people, live]);

  return (
    <div className="relative min-h-[85vh] flex flex-col justify-between">
      {/* Particle WebGL Canvas */}
      <ParticleHero />

      {/* Hero Section */}
      <section className="relative z-10 pt-8 pb-12 sm:pt-14 sm:pb-16 text-center max-w-4xl mx-auto space-y-6">
        {/* Assembling Wordmark "Proxy" */}
        <div className="overflow-hidden flex items-center justify-center">
          <motion.h1
            className="font-display font-extrabold text-7xl sm:text-9xl md:text-[140px] tracking-tightest leading-none brand-gradient-text select-none"
            initial="hidden"
            animate="visible"
            variants={{
              hidden: { opacity: 0 },
              visible: {
                opacity: 1,
                transition: { staggerChildren: 0.08, delayChildren: 0.1 },
              },
            }}
          >
            {"Proxy".split("").map((char, index) => (
              <motion.span
                key={index}
                className="inline-block"
                variants={{
                  hidden: { y: "100%", opacity: 0 },
                  visible: {
                    y: 0,
                    opacity: 1,
                    transition: { duration: 0.9, ease: EASE_OUT_EXPO },
                  },
                }}
              >
                {char}
              </motion.span>
            ))}
          </motion.h1>
        </div>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.45, ease: EASE_OUT_EXPO }}
          className="text-base sm:text-xl text-muted font-normal max-w-2xl mx-auto px-4"
        >
          Each person is represented by an autonomous agent. The agents date on their behalf and rank who fits best.
        </motion.p>

        {/* Global Quick Action Pills */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.6, ease: EASE_OUT_EXPO }}
          className="flex flex-wrap items-center justify-center gap-3 pt-2"
        >
          <MagneticButton
            variant="secondary"
            size="sm"
            onClick={loadSeed25}
            data-cursor="Auto-Fill"
          >
            <Sparkles className="w-3.5 h-3.5 text-accent" />
            <span>Load 25 Candidates</span>
          </MagneticButton>

          <MagneticButton
            variant="ghost"
            size="sm"
            onClick={() => setPasteMode((v) => !v)}
            data-cursor="Toggle Paste"
          >
            <Clipboard className="w-3.5 h-3.5 text-muted" />
            <span>{pasteMode ? "Close Paste-Many" : "Paste Many Lines"}</span>
          </MagneticButton>

          <MagneticButton
            variant="ghost"
            size="sm"
            onClick={handleLoadDemo}
            disabled={demoLoading}
            data-cursor="Pre-run Demo"
          >
            <RotateCcw className="w-3.5 h-3.5 text-spark" />
            <span>{demoLoading ? "Loading Demo..." : "Instant Demo Run"}</span>
          </MagneticButton>
        </motion.div>
      </section>

      {/* Main Terminal-Spreadsheet Section */}
      <section className="relative z-10 max-w-5xl mx-auto w-full space-y-6">
        {/* Paste-Many Modal Dropdown */}
        <AnimatePresence>
          {pasteMode && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.4, ease: EASE_OUT_EXPO }}
              className="overflow-hidden"
            >
              <GlassCard className="p-6 space-y-4 border-accent/30 shadow-accent-glow">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-ink">Paste Profile Links</h3>
                    <p className="text-xs text-muted">
                      One candidate per line. Space, comma, or tab separated: <code className="font-mono text-accent">https://linkedin.com/in/user https://instagram.com/user</code>
                    </p>
                  </div>
                  <button
                    onClick={() => setPasteMode(false)}
                    className="text-muted hover:text-ink"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <textarea
                  rows={6}
                  value={pasteText}
                  onChange={(e) => setPasteText(e.target.value)}
                  placeholder="https://www.linkedin.com/in/jadebonacolta/ https://www.instagram.com/jadebonacolta/&#10;https://www.linkedin.com/in/levelsio/ https://www.instagram.com/levelsio/"
                  className="w-full bg-surface-elevated/80 border border-hairline rounded-xl p-3 text-xs font-mono text-ink placeholder:text-muted/60 outline-none focus:border-accent"
                />
                <div className="flex justify-end gap-2">
                  <MagneticButton size="sm" variant="ghost" onClick={() => setPasteMode(false)}>
                    Cancel
                  </MagneticButton>
                  <MagneticButton size="sm" variant="primary" onClick={handleParsePaste}>
                    Parse & Explode Rows
                  </MagneticButton>
                </div>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Input Table */}
        <GlassCard className="p-0 overflow-hidden border border-hairline">
          <div className="px-5 py-4 border-b border-hairline flex flex-wrap items-center justify-between gap-4 bg-surface-elevated/40">
            <div className="flex items-center gap-3">
              <span className="font-display font-semibold text-sm tracking-tight text-ink">
                Candidate Profiles
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-surface-elevated border border-hairline text-muted">
                {rows.length} rows
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={addRow}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-elevated hover:bg-surface-highlight text-xs font-mono text-ink border border-hairline"
                data-cursor="Add Row"
              >
                <Plus className="w-3.5 h-3.5 text-accent" />
                <span>Add Row</span>
              </button>
            </div>
          </div>

          <div className="divide-y divide-hairline">
            <AnimatePresence initial={false}>
              {rows.map((row, index) => {
                const isLiValid = validateField("linkedin", row.linkedin);
                const isIgValid = validateField("instagram", row.instagram);

                return (
                  <motion.div
                    key={row.id}
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.35, ease: EASE_OUT_EXPO }}
                    className="p-3 sm:p-4 flex flex-col sm:flex-row items-center gap-3 group hover:bg-surface-elevated/40 transition-colors"
                  >
                    <span className="font-mono text-xs text-muted w-6 text-center select-none">
                      {String(index + 1).padStart(2, "0")}
                    </span>

                    {/* LinkedIn Field */}
                    <div className="relative flex-1 w-full">
                      <input
                        type="url"
                        value={row.linkedin}
                        onChange={(e) => handleRowChange(row.id, "linkedin", e.target.value)}
                        placeholder="https://www.linkedin.com/in/slug"
                        className="w-full bg-surface-elevated/60 border border-hairline focus:border-accent rounded-xl px-3.5 py-2 text-xs font-mono text-ink placeholder:text-muted/50 outline-none pr-8 transition-all"
                      />
                      <div className="absolute right-2.5 top-1/2 -translate-y-1/2">
                        {isLiValid === true && <Check className="w-3.5 h-3.5 text-spark" />}
                        {isLiValid === false && <X className="w-3.5 h-3.5 text-friction" />}
                      </div>
                    </div>

                    {/* Instagram Field */}
                    <div className="relative flex-1 w-full">
                      <input
                        type="url"
                        value={row.instagram}
                        onChange={(e) => handleRowChange(row.id, "instagram", e.target.value)}
                        placeholder="https://www.instagram.com/handle/"
                        className="w-full bg-surface-elevated/60 border border-hairline focus:border-accent rounded-xl px-3.5 py-2 text-xs font-mono text-ink placeholder:text-muted/50 outline-none pr-8 transition-all"
                      />
                      <div className="absolute right-2.5 top-1/2 -translate-y-1/2">
                        {isIgValid === true && <Check className="w-3.5 h-3.5 text-spark" />}
                        {isIgValid === false && <X className="w-3.5 h-3.5 text-friction" />}
                      </div>
                    </div>

                    {/* Delete action */}
                    <button
                      onClick={() => removeRow(row.id)}
                      disabled={rows.length <= 1}
                      className="p-2 rounded-lg text-muted hover:text-friction hover:bg-friction/10 disabled:opacity-20 disabled:hover:bg-transparent transition-all"
                      data-cursor="Remove"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>

          {/* Action Footer */}
          <div className="p-4 sm:p-5 bg-surface-elevated/40 border-t border-hairline flex flex-wrap items-center justify-between gap-4">
            <div className="text-xs text-muted font-mono">
              Scraping strictly reads public URLs via Apify. Zero login or cookies needed.
            </div>

            <MagneticButton
              variant="primary"
              size="lg"
              onClick={handleSubmitBatch}
              disabled={isSubmitting}
              data-cursor="Start Analysis"
              className="w-full sm:w-auto"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{isSubmitting ? "Ingesting..." : "Ingest & Analyze Agents"}</span>
            </MagneticButton>
          </div>
        </GlassCard>

        {/* Existing People Pipeline Status List */}
        {people.length > 0 && (
          <div className="space-y-3 pt-6">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold tracking-tight text-ink flex items-center gap-2">
                <Users className="w-4 h-4 text-accent" />
                <span>Active Candidates ({people.length})</span>
              </h2>
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-muted">
                  Analyzed:{" "}
                  <span className="text-spark font-bold">
                    <RollingNumber value={analyzedCount} />
                  </span>
                  /{people.length}
                </span>

                {queuedCount > 0 && (
                  <MagneticButton
                    variant="secondary"
                    size="sm"
                    onClick={async () => {
                      try {
                        const res = await api.processQueue(true);
                        toast.success(`Resumed processing for ${res.resumed_count} candidates!`);
                        await refreshPeople();
                      } catch {
                        toast.error("Failed to resume queue. Please ensure backend is running.");
                      }
                    }}
                    data-cursor="Resume Queue"
                  >
                    <Play className="w-3 h-3 text-accent fill-current" />
                    <span>Process Queue ({queuedCount})</span>
                  </MagneticButton>
                )}

                {analyzedCount >= 2 && (
                  <Link href="/dating">
                    <MagneticButton variant="spark" size="sm" data-cursor="Enter Arena">
                      <Play className="w-3 h-3 fill-current" />
                      <span>Enter Dating Arena</span>
                    </MagneticButton>
                  </Link>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {people.map((p) => {
                const currentStatus = live[p.id]?.status || p.status;
                const currentError = live[p.id]?.error || p.error;

                return (
                  <GlassCard
                    key={p.id}
                    className="p-4 space-y-3 hover:border-hairline-bright transition-all"
                    dataCursor="View Profile"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <Link
                        href={`/people/${p.id}`}
                        className="font-medium text-sm text-ink hover:text-accent transition-colors truncate"
                      >
                        {p.name}
                      </Link>
                      <Link
                        href={`/people/${p.id}`}
                        className="text-muted hover:text-ink"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </Link>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <SegmentedProgressPill
                        status={currentStatus}
                        error={currentError}
                        onRetry={async () => {
                          try {
                            await api.retryPerson(p.id);
                            toast.success(`Retrying analysis for ${p.name}...`);
                            await refreshPeople();
                          } catch {
                            toast.error("Failed to retry. Please ensure backend is running.");
                          }
                        }}
                      />
                    </div>
                  </GlassCard>
                );
              })}
            </div>
          </div>
        )}
      </section>

      {/* Subtle bottom tag */}
      <footer className="relative z-10 py-6 text-center text-xs font-mono text-muted/60">
        Proxy Agentic Dating System — Built for Autonomous Behavioral Compatibility
      </footer>
    </div>
  );
}
