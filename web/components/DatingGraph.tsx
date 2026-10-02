"use client";

import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";

export interface GraphNode extends d3.SimulationNodeDatum {
  id: number;
  name: string;
  avatar?: string;
  x?: number;
  y?: number;
}

export interface GraphEdge extends d3.SimulationLinkDatum<GraphNode> {
  source: GraphNode | number;
  target: GraphNode | number;
  score: number;
  chemistry?: number;
  active?: boolean;
}

export function DatingGraph({
  nodesData,
  edgesData,
  activePair,
  onSelectNode,
}: {
  nodesData: { id: number; name: string }[];
  edgesData: { aId: number; bId: number; score: number; chemistry?: number }[];
  activePair?: { aId: number; bId: number; spark?: boolean; friction?: boolean } | null;
  onSelectNode?: (nodeId: number) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [selectedNode, setSelectedNode] = useState<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || nodesData.length === 0) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = (canvas.width = canvas.parentElement?.clientWidth || 800);
    let height = (canvas.height = canvas.parentElement?.clientHeight || 600);

    const handleResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };
    window.addEventListener("resize", handleResize);

    // Deep copy nodes & edges for D3 simulation
    const nodes: GraphNode[] = nodesData.map((d) => ({ ...d }));
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    const links: GraphEdge[] = edgesData
      .filter((e) => nodeMap.has(e.aId) && nodeMap.has(e.bId))
      .map((e) => ({
        source: nodeMap.get(e.aId)!,
        target: nodeMap.get(e.bId)!,
        score: e.score,
        chemistry: e.chemistry || e.score,
      }));

    // Setup D3 Force Simulation
    const simulation = d3
      .forceSimulation<GraphNode>(nodes)
      .force("charge", d3.forceManyBody().strength(-180))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force(
        "link",
        d3
          .forceLink<GraphNode, GraphEdge>(links)
          .id((d) => d.id)
          .distance(110)
      )
      .force("collide", d3.forceCollide(32))
      .alphaDecay(0.02);

    let transform = { x: 0, y: 0, k: 1 };
    let isDragging = false;
    let dragStart = { x: 0, y: 0 };

    // Pan & Zoom
    const handleMouseDown = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left - transform.x) / transform.k;
      const mouseY = (e.clientY - rect.top - transform.y) / transform.k;

      // Check if clicked a node
      for (const node of nodes) {
        if (node.x != null && node.y != null) {
          const dist = Math.hypot(node.x - mouseX, node.y - mouseY);
          if (dist < 20) {
            const nextSelect = selectedNode === node.id ? null : node.id;
            setSelectedNode(nextSelect);
            if (onSelectNode) onSelectNode(node.id);
            return;
          }
        }
      }

      isDragging = true;
      dragStart = { x: e.clientX - transform.x, y: e.clientY - transform.y };
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      transform.x = e.clientX - dragStart.x;
      transform.y = e.clientY - dragStart.y;
    };

    const handleMouseUp = () => {
      isDragging = false;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
      const newK = Math.max(0.4, Math.min(2.5, transform.k * zoomFactor));
      transform.k = newK;
    };

    canvas.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    canvas.addEventListener("wheel", handleWheel, { passive: false });

    let animId: number;

    const render = () => {
      ctx.save();
      ctx.clearRect(0, 0, width, height);

      ctx.translate(transform.x, transform.y);
      ctx.scale(transform.k, transform.k);

      const isLight = document.documentElement.getAttribute("data-theme") === "light";

      // Draw Edges
      for (const link of links) {
        const src = link.source as GraphNode;
        const tgt = link.target as GraphNode;
        if (src.x == null || src.y == null || tgt.x == null || tgt.y == null) continue;

        const isConnectedToSelected =
          selectedNode == null || src.id === selectedNode || tgt.id === selectedNode;

        const isActiveDate =
          activePair &&
          ((src.id === activePair.aId && tgt.id === activePair.bId) ||
            (src.id === activePair.bId && tgt.id === activePair.aId));

        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);

        if (isActiveDate) {
          ctx.strokeStyle = activePair.spark
            ? isLight ? "#059669" : "#7CFFB2"
            : isLight ? "#E11D48" : "#FF5C7A";
          ctx.lineWidth = 4;
          ctx.shadowColor = ctx.strokeStyle;
          ctx.shadowBlur = 12;
        } else if (!isConnectedToSelected) {
          ctx.strokeStyle = isLight ? "rgba(15, 23, 42, 0.04)" : "rgba(255, 255, 255, 0.02)";
          ctx.lineWidth = 0.5;
        } else {
          // Thickness proportional to score (0 to 100)
          const weight = Math.max(0.8, (link.score / 100) * 3);
          const color = isLight
            ? link.score >= 70
              ? "rgba(5, 150, 105, 0.35)"
              : link.score >= 50
              ? "rgba(37, 99, 235, 0.28)"
              : "rgba(225, 29, 72, 0.25)"
            : link.score >= 70
            ? "rgba(124, 255, 178, 0.28)"
            : link.score >= 50
            ? "rgba(139, 139, 255, 0.2)"
            : "rgba(255, 92, 122, 0.18)";
          ctx.strokeStyle = color;
          ctx.lineWidth = weight;
        }

        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      // Draw Nodes
      for (const node of nodes) {
        if (node.x == null || node.y == null) continue;

        const isSelected = selectedNode === node.id;
        const isDimmed =
          selectedNode != null &&
          !isSelected &&
          !links.some(
            (l) =>
              ((l.source as GraphNode).id === node.id &&
                (l.target as GraphNode).id === selectedNode) ||
              ((l.target as GraphNode).id === node.id &&
                (l.source as GraphNode).id === selectedNode)
          );

        const isActiveInDate =
          activePair && (node.id === activePair.aId || node.id === activePair.bId);

        const radius = isSelected ? 18 : isActiveInDate ? 16 : 13;

        // Node Glow
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        if (isDimmed) {
          ctx.fillStyle = isLight ? "rgba(241, 245, 249, 0.5)" : "rgba(14, 14, 19, 0.4)";
          ctx.strokeStyle = isLight ? "rgba(15, 23, 42, 0.08)" : "rgba(255, 255, 255, 0.05)";
        } else if (isActiveInDate) {
          ctx.fillStyle = isLight ? "#FFFFFF" : "#14141C";
          ctx.strokeStyle = activePair.spark
            ? isLight ? "#059669" : "#7CFFB2"
            : isLight ? "#E11D48" : "#FF5C7A";
          ctx.shadowColor = ctx.strokeStyle;
          ctx.shadowBlur = 16;
        } else if (isSelected) {
          ctx.fillStyle = isLight ? "#2563EB" : "#8B8BFF";
          ctx.strokeStyle = "#FFFFFF";
          ctx.shadowColor = isLight ? "#2563EB" : "#8B8BFF";
          ctx.shadowBlur = 14;
        } else {
          ctx.fillStyle = isLight ? "#FFFFFF" : "#0E0E13";
          ctx.strokeStyle = isLight ? "rgba(15, 23, 42, 0.16)" : "rgba(255, 255, 255, 0.2)";
        }

        ctx.lineWidth = 1.5;
        ctx.fill();
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Node Monogram or Name
        if (!isDimmed) {
          ctx.fillStyle = isSelected
            ? "#FFFFFF"
            : isLight
            ? "#0F172A"
            : "rgba(244, 244, 247, 0.85)";
          ctx.font = "bold 10px 'JetBrains Mono', monospace";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(node.name.charAt(0), node.x, node.y);

          // Name label below
          ctx.font = "11px 'Inter Tight', sans-serif";
          ctx.fillStyle = isSelected
            ? isLight ? "#2563EB" : "#FFFFFF"
            : isLight ? "rgba(15, 23, 42, 0.75)" : "rgba(125, 125, 145, 0.8)";
          ctx.fillText(node.name, node.x, node.y + radius + 11);
        }
      }

      ctx.restore();
      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
      simulation.stop();
      window.removeEventListener("resize", handleResize);
      canvas.removeEventListener("mousedown", handleMouseDown);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      canvas.removeEventListener("wheel", handleWheel);
    };
  }, [nodesData, edgesData, activePair, selectedNode, onSelectNode]);

  return (
    <div className="relative w-full h-[520px] rounded-2xl overflow-hidden glass-card border border-hairline bg-bg/90">
      <canvas ref={canvasRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
      <div className="absolute top-4 left-4 flex items-center gap-2 pointer-events-none">
        <span className="text-[11px] font-mono text-muted uppercase tracking-wider bg-surface-elevated/80 px-2.5 py-1 rounded-full border border-hairline backdrop-blur-md">
          Scroll to zoom • Drag to pan • Click to inspect web
        </span>
      </div>
    </div>
  );
}
