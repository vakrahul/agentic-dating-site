# "Signal" — Design System & Frontend Architecture for Proxy

"Signal" is a premier design language engineered specifically for **Proxy**, the autonomous agentic dating site. It treats every candidate as an autonomous signal emitter, decoding their authentic desires, stated intentions, lived habits, and mutual chemistry into an intuitive, award-caliber interface.

---

## 1. Aesthetic Foundations

### 1.1 Dual Theme Architecture
* **Primary (Default): Architectural Light Design Theme**
  - **Base Canvas (`#FAFBFC`)**: Ultra-clean, unpolluted architectural white.
  - **Cards & Surfaces (`#FFFFFF`)**: Pure white frosted glass planes with subtle hairline borders (`rgba(15, 23, 42, 0.08)`).
  - **Deep Ink (`#0F172A`)**: Rich obsidian text ensuring WCAG AAA legibility and contrast across all card planes.
  - **Brand Gradient Spectrum (`#1D4ED8` → `#3B82F6` → `#EA580C`)**: Royal blue through bright sapphire to vivid saffron orange gradient accenting the brand monogram, wordmarks, and interactive highlights.
  - **Spark (`#059669`) & Friction (`#E11D48`)**: Calibrated high-contrast semantic tones for mutual chemistry and divergence.
  - **Zero Flashlight Glare**: The radial cursor-following white flashlight glow (`.pointer-glow::before`) has been permanently eliminated in favor of clean, crisp border chamfer transitions.

* **Secondary: Signal Dark Theme**
  - **Base (`#07070A`)**: Ultra-deep near-black grounding all components.
  - **Surfaces (`#0E0E13` / `#14141C`)**: Layered dark planes with hairline borders (`rgba(255, 255, 255, 0.07)`).
  - **Signal Colors**: Spark emerald (`#7CFFB2`), Friction coral (`#FF5C7A`), and Accent periwinkle (`#8B8BFF`).

### 1.2 Interactive Anime Companion Cursor
* Handcrafted anime girl companion sprite (`sakura.png`, 32×32px frame coordinate system) following the cursor dynamically.
* 8-way directional run animations towards the pointer, idle fidgeting, alert orientation, and sleeping states when inactive.
* Interactive click handler with Web Audio API mechanical clockwork synthesis and contextual speech bubble reactions ("Signal locked!", "Konnichiwa!", "Ready!").

### 1.3 Typography & Numerals
* **Display & Body**: **Inter Tight Variable** (`@fontsource-variable/inter-tight`). Tight tracking (`-0.04em` on titles) combined with scale contrast.
* **Code & Data**: **JetBrains Mono** (`@fontsource/jetbrains-mono`). Used for raw verbatim quotes, turn numbers, confidence bars, timestamps, and candidate slugs.
* **Tabular Figures**: Every numeric counter, slope delta, and rating is locked to `font-variant-numeric: tabular-nums` to eliminate jitter during count-up animations.

---

## 2. Motion System (`web/lib/motion.ts`)

| Token | Curve / Spring Spec | Intended Usage |
| :--- | :--- | :--- |
| **Ease-Out Expo** | `cubic-bezier(0.16, 1, 0.3, 1)` | Page entrances, slide-ups, card reveals (600–900ms) |
| **Spring Interactive** | `{ stiffness: 260, damping: 30 }` | Magnetic buttons, hover expansion, filter reflow |
| **Spring Snappy** | `{ stiffness: 350, damping: 28 }` | Active tab indicator & companion reactions |
| **Stagger** | `40ms – 60ms` | List rows, candidate grid, breakdown bars |

### Accessibility & Reduced Motion
Every animation strictly queries `(prefers-reduced-motion: reduce)`. When detected:
- 3D / particle simulations are bypassed.
- Motion transforms are replaced with clean instant opacity fades.
- Smooth scrolling is disabled in favor of native instant jumps.

---

## 3. Screen Specifications

### 1. Add People (`/`)
* **Assembling Wordmark**: Staggered letter-by-letter masked slide-up for "Proxy".
* **Particle Canvas**: Dynamic HTML5 Canvas rendering 25–40 drifting agent nodes with mouse attraction and proximity edge connections.
* **Terminal-Spreadsheet Input**: Live inline URL syntax verification with morphing check/cross icons, height spring row additions, and an exploding paste-many parser.
* **Segmented Status Pill**: Displays real-time progress (`Queued` → `Scraping` → `Analyzing` → `Done`) with shimmer sweep animation.

### 2. Candidate Profile (`/people/[id]`)
* **Rolling Counters**: Odometer count-ups for followers, post counts, and experience roles.
* **Say / Do Gap (Signature Element)**: Split comparison between LinkedIn "Stated Self" and Instagram "Lived Self" with color-coded agreement / divergence vectors.
* **Interactive Trait Radar**: 6-axis SVG radar polygon morphing on entrance; hovering vertices reveals contextual supporting claims.
* **Verifiable Claims**: Filterable claims with confidence meters, source chips, and verbatim highlighted quotes in mono.

### 3. Dating Arena (`/dating`)
* **Force Graph Centerpiece**: Full-canvas interactive D3 force simulation with pan/zoom and node focus. Pairs pull together on active dates, pulsing spark-green or friction-red.
* **Funnel Progress Bar**: Visual elimination tracking Speed Dates (Round 1) → Deep Dates (Round 2) → Final Verdict.
* **Live Feed & Transcript Ticker**: Real-time sliding list of finished dates and typewriter transcript stream with referee highlight flashes.

### 4. Rankings & Leaderboard (`/rankings/[id]`)
* **Person Switcher Carousel**: Keyboard navigation (`Left` / `Right` arrows) to seamlessly flip between candidates.
* **Slope Graph**: Slope indicator showing initial similarity rank vs. final dating rank with delta changes (`+4`, `-2`).
* **Word-by-Word "Why" Text**: Staggered word reveal with inline turn citation links (`Turn #3`) jumping directly into the replay.

### 5. Pair Replay (`/pair/[a]/[b]`)
* **Split Screen**: Person A and Person B profiles flanking central alternating dialogue bubbles.
* **Running Chemistry Sparkline**: SVG tension line tracking warmth across conversation turns.
* **Scrubber & Playback**: Timeline slider, speed control (1x, 2x, 4x), keyboard shortcuts (`Space` to toggle, `Arrows` to step).
* **Referee Synthesis**: Radial circular progress rings for Chemistry, Values, Lifestyle, Ambition, and Interests.

### 6. Demo Showcase (`/demo`)
* **Cinematic Auto-Tour**: Automated narrative walkthrough with caption banner through all 4 phases of the system.
* **16:9 Record Mode**: Locks resolution-safe layout and hides dev UI, perfectly calibrated for a flawless 3-minute video presentation.

---

## 4. Engineering Verification
* **TypeScript**: 100% strict type safety across all components and API schemas.
* **Mobile Ready**: Fully fluid responsive grid from 360px mobile viewport up to 4K displays.
* **Performance**: Zero layout shift, GPU-accelerated transforms, and 60fps requestAnimationFrame loops.
