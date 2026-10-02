import type { Metadata } from "next";
import "./globals.css";
import { TopBar } from "../components/TopBar";
import { Cursor } from "../components/Cursor";
import { CommandPalette } from "../components/CommandPalette";
import { SmoothScroll } from "../components/SmoothScroll";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "Proxy — Autonomous Agentic Dating Site",
  description:
    "Each person is represented by an agent. The agents date on their behalf and rank who fits best.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="light" className="light" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const theme = localStorage.getItem('proxy_theme') || 'light';
                document.documentElement.setAttribute('data-theme', theme);
                document.documentElement.className = theme;
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body className="bg-bg text-ink min-h-screen flex flex-col font-sans selection:bg-accent/20 selection:text-ink antialiased transition-colors duration-200">
        <SmoothScroll>
          <Cursor />
          <CommandPalette />
          <TopBar />
          <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 py-8">
            {children}
          </main>
          <Toaster
            position="bottom-right"
            toastOptions={{
              className: "glass-card border border-hairline text-ink text-xs font-mono shadow-glass",
            }}
          />
        </SmoothScroll>
      </body>
    </html>
  );
}
