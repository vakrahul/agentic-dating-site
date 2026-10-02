"use client";

import { useEffect, useRef } from "react";

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  colorLight: string;
  colorDark: string;
}

export function ParticleHero() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const isReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (isReduced) return;

    let animId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    const mouse = { x: -1000, y: -1000, radius: 180 };
    const handleMouseMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };
    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    // 32 soft drifting nodes representing autonomous agents
    const nodeCount = Math.min(36, Math.max(20, Math.floor(width / 45)));
    const nodes: Node[] = [];
    const colorsLight = [
      "rgba(5, 150, 105, 0.65)", // emerald spark
      "rgba(37, 99, 235, 0.65)", // brand blue
      "rgba(234, 88, 12, 0.65)", // brand orange
      "rgba(15, 23, 42, 0.4)", // obsidian
    ];
    const colorsDark = [
      "rgba(124, 255, 178, 0.6)", // spark
      "rgba(139, 139, 255, 0.6)", // accent
      "rgba(255, 92, 122, 0.4)", // friction
      "rgba(255, 255, 255, 0.5)", // neutral
    ];

    for (let i = 0; i < nodeCount; i++) {
      const idx = Math.floor(Math.random() * colorsDark.length);
      nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.7,
        vy: (Math.random() - 0.5) * 0.7,
        radius: Math.random() * 2.5 + 2,
        colorLight: colorsLight[idx],
        colorDark: colorsDark[idx],
      });
    }

    const draw = () => {
      ctx.clearRect(0, 0, width, height);
      const isLight = document.documentElement.getAttribute("data-theme") === "light";

      // Connect near nodes with faint lines
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.hypot(dx, dy);

          if (dist < 140) {
            const alpha = (1 - dist / 140) * 0.15;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = isLight
              ? `rgba(37, 99, 235, ${alpha * 1.1})`
              : `rgba(255, 255, 255, ${alpha})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }

      // Update and draw nodes
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];

        // Cursor attraction (agents drawn toward discovery)
        const dx = mouse.x - node.x;
        const dy = mouse.y - node.y;
        const dist = Math.hypot(dx, dy);

        if (dist < mouse.radius && dist > 1) {
          const force = (1 - dist / mouse.radius) * 0.45;
          node.vx += (dx / dist) * force;
          node.vy += (dy / dist) * force;
        }

        // Apply friction & boundary wrap
        node.vx *= 0.98;
        node.vy *= 0.98;
        node.x += node.vx;
        node.y += node.vy;

        if (node.x < 0) node.x = width;
        if (node.x > width) node.x = 0;
        if (node.y < 0) node.y = height;
        if (node.y > height) node.y = 0;

        // Draw particle node
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fillStyle = isLight ? node.colorLight : node.colorDark;
        ctx.fill();
      }

      animId = requestAnimationFrame(draw);
    };

    animId = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-0 opacity-80"
    />
  );
}
