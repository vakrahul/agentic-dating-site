"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Sun, Moon, Search } from "lucide-react";
import { openEventStream, api } from "../lib/api";
import type { RunOut, SseEvent } from "../lib/types";

export function TopBar() {
  const pathname = usePathname();
  const [run, setRun] = useState<RunOut | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    // Read active theme
    const saved = (localStorage.getItem("proxy_theme") as "light" | "dark") || "light";
    setTheme(saved);
    document.documentElement.setAttribute("data-theme", saved);
    document.documentElement.className = saved;

    api.getRun().then(setRun).catch(() => {});

    const close = openEventStream((event) => {
      const e = event as SseEvent;
      if (e.type === "snapshot" && e.run) {
        setRun({
          id: e.run.id,
          status: e.run.status,
          error: null,
          stats: e.run.stats,
          started_at: null,
          finished_at: null,
        });
      } else if (e.type === "run.status") {
        setRun((prev) =>
          prev
            ? { ...prev, status: e.status, error: e.error ?? null }
            : {
                id: e.run_id,
                status: e.status,
                error: e.error ?? null,
                stats: e.stats ?? {},
                started_at: null,
                finished_at: null,
              }
        );
      } else if (e.type === "run.progress" && e.stats) {
        setRun((prev) => (prev ? { ...prev, stats: e.stats } : null));
      }
    });

    return () => close();
  }, []);

  const toggleTheme = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    localStorage.setItem("proxy_theme", next);
    document.documentElement.setAttribute("data-theme", next);
    document.documentElement.className = next;
  };

  const navLinks = [
    { href: "/", label: "Add People" },
    { href: "/dating", label: "Dating Arena" },
    { href: "/rankings", label: "Rankings" },
    { href: "/demo", label: "Demo Tour" },
  ];

  const isRunning = run?.status === "running";
  const isDone = run?.status === "done" || run?.status === "completed";

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-xl bg-bg/85 border-b border-hairline transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Left: Brand Monogram & Live Run Status */}
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="group flex items-center gap-2 focus:outline-none"
            data-cursor="Home"
          >
            {/* Geometric Gateway Monogram */}
            <div className="w-5 h-5 rounded-md bg-gradient-to-tr from-blue-600 to-orange-500 flex items-center justify-center p-0.5 shadow-sm">
              <div className="w-full h-full rounded-[3px] bg-bg flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-accent" />
              </div>
            </div>

            <span className="font-display font-bold text-lg tracking-tightest brand-gradient-text transition-all">
              Proxy
            </span>
            <span className="text-[10px] font-mono uppercase tracking-widest px-1.5 py-0.5 rounded-full bg-surface-elevated border border-hairline text-muted">
              Agentic
            </span>
          </Link>

          {/* Run status pill */}
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-surface border border-hairline text-xs font-mono">
            <span
              className={`w-2 h-2 rounded-full transition-all ${
                isRunning
                  ? "bg-spark shadow-spark-glow animate-pulse"
                  : isDone
                  ? "bg-spark"
                  : "bg-muted-dark"
              }`}
            />
            <span className="text-muted uppercase text-[10px] tracking-wider">
              {isRunning
                ? `Running (${run?.stats?.phase || "dating"})`
                : isDone
                ? "Run Finished"
                : "Idle"}
            </span>
          </div>
        </div>

        {/* Center: Nav links */}
        <nav className="flex items-center gap-1">
          {navLinks.map((link) => {
            const isActive =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);

            return (
              <Link
                key={link.href}
                href={link.href}
                className={`relative px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  isActive ? "text-ink font-semibold" : "text-muted hover:text-ink"
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="topbar-active-pill"
                    className="absolute inset-0 rounded-full bg-surface-elevated border border-hairline shadow-sm"
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                )}
                <span className="relative z-10">{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right: Theme Switcher & Cmd+K */}
        <div className="flex items-center gap-2">
          {/* Light / Dark Theme Switcher */}
          <button
            onClick={toggleTheme}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-elevated border border-hairline hover:border-hairline-bright text-xs text-muted hover:text-ink transition-all font-mono"
            title={`Switch to ${theme === "light" ? "Dark" : "Light"} theme`}
            data-cursor="Toggle Theme"
          >
            {theme === "light" ? (
              <>
                <Sun className="w-3.5 h-3.5 text-amber-500" />
                <span className="hidden sm:inline text-[11px] font-medium text-ink">Light</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-accent" />
                <span className="hidden sm:inline text-[11px] font-medium text-ink">Dark</span>
              </>
            )}
          </button>

          {/* Cmd+K shortcut */}
          <button
            onClick={() => {
              window.dispatchEvent(
                new KeyboardEvent("keydown", { key: "k", metaKey: true })
              );
            }}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface border border-hairline hover:border-hairline-bright text-xs text-muted hover:text-ink transition-all font-mono"
            data-cursor="Search"
          >
            <Search className="w-3 h-3 text-muted" />
            <span className="hidden sm:inline">Search</span>
            <kbd className="text-[10px] px-1 py-0.5 rounded bg-surface-elevated border border-hairline text-muted">
              ⌘K
            </kbd>
          </button>
        </div>
      </div>
    </header>
  );
}
