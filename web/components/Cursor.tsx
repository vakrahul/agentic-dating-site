"use client";

import { useEffect, useRef, useState } from "react";

// 32x32 frame coordinates in the 256x128 sprite sheet
const SPRITE_SETS: Record<string, number[][]> = {
  idle: [[-3, -3]],
  alert: [[-7, -3]],
  scratchSelf: [
    [-5, 0],
    [-6, 0],
    [-7, 0],
  ],
  scratchWallN: [
    [0, 0],
    [0, -1],
  ],
  scratchWallS: [
    [-7, -1],
    [-6, -2],
  ],
  scratchWallE: [
    [-2, -2],
    [-2, -3],
  ],
  scratchWallW: [
    [-4, 0],
    [-4, -1],
  ],
  tired: [[-3, -2]],
  sleeping: [
    [-2, 0],
    [-2, -1],
  ],
  N: [
    [-1, -2],
    [-1, -3],
  ],
  NE: [
    [0, -2],
    [0, -3],
  ],
  E: [
    [-3, 0],
    [-3, -1],
  ],
  SE: [
    [-5, -1],
    [-5, -2],
  ],
  S: [
    [-6, -3],
    [-7, -2],
  ],
  SW: [
    [-5, -3],
    [-6, -1],
  ],
  W: [
    [-4, -2],
    [-4, -3],
  ],
  NW: [
    [-1, 0],
    [-1, -1],
  ],
};

// Web Audio API Synthesizer for Mechanical Tick Sound on Interaction
let audioCtx: AudioContext | null = null;
function playTickSound(isDouble = false) {
  try {
    const AudioCtx =
      typeof window !== "undefined"
        ? window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
        : null;
    if (!AudioCtx) return;
    if (!audioCtx) audioCtx = new AudioCtx();
    if (audioCtx.state === "suspended") audioCtx.resume();

    const emitTick = (time: number, freq: number, isTock: boolean) => {
      if (!audioCtx) return;
      const osc = audioCtx.createOscillator();
      const oscGain = audioCtx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(freq, time);
      oscGain.gain.setValueAtTime(0.25, time);
      oscGain.gain.exponentialRampToValueAtTime(0.0001, time + 0.025);
      osc.connect(oscGain);

      const bufferSize = Math.floor(audioCtx.sampleRate * 0.015);
      const noiseBuffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
      const output = noiseBuffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        output[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufferSize * 0.2));
      }
      const noise = audioCtx.createBufferSource();
      noise.buffer = noiseBuffer;
      const noiseFilter = audioCtx.createBiquadFilter();
      noiseFilter.type = "bandpass";
      noiseFilter.frequency.setValueAtTime(isTock ? 3400 : 2500, time);
      noiseFilter.Q.setValueAtTime(4.5, time);
      const noiseGain = audioCtx.createGain();
      noiseGain.gain.setValueAtTime(0.3, time);
      noiseGain.gain.exponentialRampToValueAtTime(0.0001, time + 0.015);
      noise.connect(noiseFilter);
      noiseFilter.connect(noiseGain);

      oscGain.connect(audioCtx.destination);
      noiseGain.connect(audioCtx.destination);

      osc.start(time);
      osc.stop(time + 0.03);
      noise.start(time);
      noise.stop(time + 0.02);
    };

    const now = audioCtx.currentTime;
    if (isDouble) {
      emitTick(now, 1900, false);
      emitTick(now + 0.075, 2700, true);
    } else {
      emitTick(now, 2200, false);
    }
  } catch {
    // Audio policy fallback
  }
}

export function Cursor() {
  const characterRef = useRef<HTMLDivElement | null>(null);
  const bubbleRef = useRef<HTMLDivElement | null>(null);

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (typeof window === "undefined") return;

    // Respect reduced motion & touch screens
    const isCoarse = window.matchMedia("(pointer: coarse)").matches;
    const isReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (isCoarse || isReduced) return;

    const el = characterRef.current;
    const bubble = bubbleRef.current;
    if (!el) return;

    let posX = Math.min(Math.max(64, window.innerWidth - 120), 400);
    let posY = Math.min(Math.max(64, window.innerHeight - 120), 400);
    let targetX = posX;
    let targetY = posY;

    let frameCount = 0;
    let idleTime = 0;
    let idleAnimation: string | null = null;
    let idleAnimationFrame = 0;
    let isReacting = false;
    const speed = 10;

    let bubbleTimer: NodeJS.Timeout | null = null;
    const showBubble = (text: string, duration = 1200) => {
      if (!bubble) return;
      if (bubbleTimer) clearTimeout(bubbleTimer);
      bubble.textContent = text;
      bubble.style.opacity = "1";
      bubble.style.transform = "translateX(-50%) translateY(-6px) scale(1)";
      bubbleTimer = setTimeout(() => {
        bubble.style.opacity = "0";
        bubble.style.transform = "translateX(-50%) translateY(4px) scale(0.85)";
      }, duration);
    };

    const setSprite = (name: string, frame: number) => {
      const set = SPRITE_SETS[name] || SPRITE_SETS.idle;
      const coords = set[frame % set.length];
      el.style.backgroundPosition = `${coords[0] * 32}px ${coords[1] * 32}px`;
    };

    const resetIdleAnimation = () => {
      idleAnimation = null;
      idleAnimationFrame = 0;
    };

    const handleIdle = () => {
      if (isReacting) return;
      idleTime += 1;

      // Every ~15-20 seconds choose an idle animation
      if (idleTime > 10 && Math.floor(Math.random() * 160) === 0 && idleAnimation === null) {
        const available = ["sleeping", "scratchSelf"];
        if (posX < 32) available.push("scratchWallW");
        if (posY < 32) available.push("scratchWallN");
        if (posX > window.innerWidth - 32) available.push("scratchWallE");
        if (posY > window.innerHeight - 32) available.push("scratchWallS");
        idleAnimation = available[Math.floor(Math.random() * available.length)];
      }

      switch (idleAnimation) {
        case "sleeping":
          if (idleAnimationFrame < 8) {
            setSprite("tired", 0);
            break;
          }
          setSprite("sleeping", Math.floor(idleAnimationFrame / 4));
          if (idleAnimationFrame > 192) {
            resetIdleAnimation();
          }
          break;
        case "scratchWallN":
        case "scratchWallS":
        case "scratchWallE":
        case "scratchWallW":
        case "scratchSelf":
          setSprite(idleAnimation, idleAnimationFrame);
          if (idleAnimationFrame > 9) {
            resetIdleAnimation();
          }
          break;
        default:
          setSprite("idle", 0);
          return;
      }
      idleAnimationFrame += 1;
    };

    const handleMouseMove = (e: MouseEvent) => {
      targetX = e.clientX;
      targetY = e.clientY;
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    let lastFrameTimestamp = 0;
    let animId: number | null = null;

    const tick = (timestamp: number) => {
      if (!lastFrameTimestamp) lastFrameTimestamp = timestamp;

      // Update frame roughly every 100ms (~10fps sprite pacing for authentic retro companion feel)
      if (timestamp - lastFrameTimestamp > 95) {
        lastFrameTimestamp = timestamp;

        frameCount += 1;
        const diffX = posX - targetX;
        const diffY = posY - targetY;
        const distance = Math.sqrt(diffX ** 2 + diffY ** 2);

        if (distance < speed || distance < 48) {
          handleIdle();
        } else {
          idleAnimation = null;
          idleAnimationFrame = 0;

          if (idleTime > 1) {
            setSprite("alert", 0);
            idleTime = Math.min(idleTime, 7);
            idleTime -= 1;
          } else {
            let direction = "";
            direction += diffY / distance > 0.5 ? "N" : "";
            direction += diffY / distance < -0.5 ? "S" : "";
            direction += diffX / distance > 0.5 ? "W" : "";
            direction += diffX / distance < -0.5 ? "E" : "";
            setSprite(direction || "idle", frameCount);

            posX -= (diffX / distance) * speed;
            posY -= (diffY / distance) * speed;

            posX = Math.min(Math.max(16, posX), window.innerWidth - 16);
            posY = Math.min(Math.max(16, posY), window.innerHeight - 16);

            el.style.left = `${posX - 16}px`;
            el.style.top = `${posY - 16}px`;
          }
        }
      }

      animId = requestAnimationFrame(tick);
    };

    animId = requestAnimationFrame(tick);

    // Interactive Click Handler
    const handleClick = (e: MouseEvent) => {
      e.stopPropagation();
      playTickSound(false);

      idleTime = 0;
      idleAnimation = null;
      idleAnimationFrame = 0;
      setSprite("alert", 0);
      isReacting = true;

      el.style.transform = "scale(1.25) translateY(-10px)";
      const greetings = ["Konnichiwa!", "Hai!", "Matching agents!", "Signal locked!", "Ready!"];
      const randomGreeting = greetings[Math.floor(Math.random() * greetings.length)];
      showBubble(randomGreeting, 1100);

      setTimeout(() => {
        el.style.transform = "scale(1) translateY(0)";
        isReacting = false;
      }, 240);
    };

    el.addEventListener("click", handleClick);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      el.removeEventListener("click", handleClick);
      if (animId) cancelAnimationFrame(animId);
      if (bubbleTimer) clearTimeout(bubbleTimer);
    };
  }, [mounted]);

  if (!mounted) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-[99998] overflow-visible">
      <div
        ref={characterRef}
        aria-label="Anime Girl Cursor Companion"
        title="Anime Girl Companion - Click to interact!"
        className="fixed w-8 h-8 pointer-events-auto cursor-pointer select-none"
        style={{
          left: "-100px",
          top: "-100px",
          backgroundImage: "url(/characters/sakura.png)",
          backgroundRepeat: "no-repeat",
          imageRendering: "pixelated",
          transition: "transform 0.18s cubic-bezier(0.34, 1.56, 0.64, 1)",
        }}
      >
        {/* Reaction Speech Bubble */}
        <div
          ref={bubbleRef}
          className="absolute bottom-[calc(100%+6px)] left-1/2 -translate-x-1/2 pointer-events-none opacity-0 transition-all duration-200 ease-out z-[99999] px-2 py-1 rounded-md bg-surface-elevated/95 border border-hairline shadow-glass text-[11px] font-mono text-spark whitespace-nowrap"
          style={{
            transform: "translateX(-50%) translateY(4px) scale(0.85)",
          }}
        />
      </div>
    </div>
  );
}
