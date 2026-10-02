"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Add people" },
  { href: "/dating", label: "Live" },
  { href: "/rankings", label: "Rankings" },
  { href: "/demo", label: "Demo" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-20 border-b border-line bg-bg/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-5 px-4 py-2.5">
        <Link href="/" className="font-mono text-[13px] font-semibold tracking-tight text-ink">
          PROXY
        </Link>
        <span className="text-micro text-muted">agentic dating</span>
        <nav className="ml-auto flex items-center gap-1">
          {LINKS.map((link) => {
            const active =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href.split("/").slice(0, 2).join("/"));
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded px-2.5 py-1 text-dense transition-colors ${
                  active ? "bg-panel2 text-ink" : "text-muted hover:text-ink"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
