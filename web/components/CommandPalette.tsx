"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  Search,
  Sparkles,
  Flame,
  Users,
  Compass,
  Trophy,
  Play,
  RotateCcw,
  ExternalLink,
} from "lucide-react";
import { api } from "../lib/api";
import type { PersonOut } from "../lib/types";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [people, setPeople] = useState<PersonOut[]>([]);
  const router = useRouter();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || e.key === "/") {
        if (
          (e.target instanceof HTMLElement && e.target.isContentEditable) ||
          e.target instanceof HTMLInputElement ||
          e.target instanceof HTMLTextAreaElement
        ) {
          return;
        }
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };

    window.addEventListener("keydown", down);
    return () => window.removeEventListener("keydown", down);
  }, []);

  useEffect(() => {
    if (open) {
      api.listPeople().then(setPeople).catch(() => {});
    }
  }, [open]);

  const runCommand = (command: () => void) => {
    setOpen(false);
    command();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100000] flex items-start justify-center pt-20 p-4 bg-black/70 backdrop-blur-md">
      <div
        className="fixed inset-0"
        onClick={() => setOpen(false)}
        aria-hidden="true"
      />
      <Command
        className="relative w-full max-w-xl glass-card border border-hairline shadow-2xl overflow-hidden p-2 z-10"
        loop
      >
        <div className="flex items-center gap-3 px-3 py-2 border-b border-hairline">
          <Search className="w-4 h-4 text-muted shrink-0" />
          <Command.Input
            placeholder="Search people, routes, or run actions..."
            className="w-full bg-transparent text-sm text-ink placeholder:text-muted outline-none border-none py-1"
            autoFocus
          />
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-surface-elevated border border-hairline rounded text-muted">
            ESC
          </kbd>
        </div>

        <Command.List className="max-h-[360px] overflow-y-auto py-2 px-1 text-sm space-y-1">
          <Command.Empty className="py-8 text-center text-xs text-muted">
            No matching results found.
          </Command.Empty>

          <Command.Group heading="Navigation" className="px-2 py-1 text-[11px] font-mono uppercase text-muted tracking-wider">
            <Command.Item
              onSelect={() => runCommand(() => router.push("/"))}
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-ink hover:bg-surface-elevated cursor-pointer"
            >
              <Users className="w-4 h-4 text-accent" />
              <span>Add People & Import</span>
            </Command.Item>
            <Command.Item
              onSelect={() => runCommand(() => router.push("/dating"))}
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-ink hover:bg-surface-elevated cursor-pointer"
            >
              <Flame className="w-4 h-4 text-friction" />
              <span>Dating Arena</span>
            </Command.Item>
            <Command.Item
              onSelect={() => runCommand(() => router.push("/rankings"))}
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-ink hover:bg-surface-elevated cursor-pointer"
            >
              <Trophy className="w-4 h-4 text-spark" />
              <span>Rankings Leaderboard</span>
            </Command.Item>
            <Command.Item
              onSelect={() => runCommand(() => router.push("/demo"))}
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-ink hover:bg-surface-elevated cursor-pointer"
            >
              <Compass className="w-4 h-4 text-accent" />
              <span>Guided Demo Tour</span>
            </Command.Item>
          </Command.Group>

          <Command.Group heading="Actions" className="px-2 py-1 text-[11px] font-mono uppercase text-muted tracking-wider mt-2">
            <Command.Item
              onSelect={() =>
                runCommand(async () => {
                  try {
                    await api.startRun();
                    router.push("/dating");
                  } catch (e) {
                    console.error(e);
                  }
                })
              }
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-ink hover:bg-surface-elevated cursor-pointer"
            >
              <Play className="w-4 h-4 text-spark" />
              <span>Start Dating Run</span>
            </Command.Item>
            <Command.Item
              onSelect={() =>
                runCommand(async () => {
                  try {
                    const res = await fetch("/demo_run.json");
                    const data = await res.json();
                    await api.importRun(data);
                    router.push("/rankings");
                  } catch (e) {
                    console.error(e);
                  }
                })
              }
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-ink hover:bg-surface-elevated cursor-pointer"
            >
              <RotateCcw className="w-4 h-4 text-accent" />
              <span>Load Pre-computed Demo Run</span>
            </Command.Item>
          </Command.Group>

          {people.length > 0 && (
            <Command.Group heading="People" className="px-2 py-1 text-[11px] font-mono uppercase text-muted tracking-wider mt-2">
              {people.slice(0, 15).map((p) => (
                <Command.Item
                  key={p.id}
                  onSelect={() => runCommand(() => router.push(`/people/${p.id}`))}
                  className="flex items-center justify-between px-3 py-2 rounded-xl text-ink hover:bg-surface-elevated cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-6 h-6 rounded-full bg-surface-elevated border border-hairline flex items-center justify-center text-xs font-mono">
                      {p.name.charAt(0)}
                    </div>
                    <span>{p.name}</span>
                  </div>
                  <span className="text-[11px] font-mono text-muted">
                    {p.status}
                  </span>
                </Command.Item>
              ))}
            </Command.Group>
          )}
        </Command.List>

        <div className="flex items-center justify-between px-3 py-2 border-t border-hairline text-[11px] font-mono text-muted">
          <span>Navigate with arrows</span>
          <span>Press Enter to select</span>
        </div>
      </Command>
    </div>
  );
}
