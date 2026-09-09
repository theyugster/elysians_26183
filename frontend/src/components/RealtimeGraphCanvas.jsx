import React, { useRef, useEffect, useState, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Maximize2 } from 'lucide-react';
import { PRUNED_DUST_NODE, PRUNED_DUST_LINK } from '../services/api';

export default function RealtimeGraphCanvas({
  traceData,
  selectedNode,
  onSelectNode,
  dustThreshold = 3.0,
  isPlaying = true,
  playbackSpeed = 1.0,
}) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);

  // Physics Simulation & Position State
  const nodesRef = useRef([]);
  const linksRef = useRef([]);
  const particlesRef = useRef([]);
  const animFrameIdRef = useRef(null);

  // Viewport Transform (Pan & Zoom)
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const isDraggingCanvasRef = useRef(false);
  const draggedNodeRef = useRef(null);
  const dragStartRef = useRef({ x: 0, y: 0 });

  // Hover Tooltip State
  const [hoveredLink, setHoveredLink] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // Initialize and Update Graph Topology
  useEffect(() => {
    if (!traceData || !traceData.nodes) return;

    const width = containerRef.current?.clientWidth || 900;
    const height = containerRef.current?.clientHeight || 540;

    // Determine nodes to display based on dustThreshold
    let displayNodes = [...traceData.nodes];
    let displayLinks = [...traceData.links];

    // If dust threshold <= 1.0%, show 0xDust_Pruned as active, otherwise show as pruned ghost node
    const isDustIncluded = dustThreshold <= 1.0;
    const dustExists = displayNodes.some(n => n.id === PRUNED_DUST_NODE.id);

    if (!dustExists) {
      displayNodes.push({
        ...PRUNED_DUST_NODE,
        isPruned: !isDustIncluded,
      });
      displayLinks.push({
        ...PRUNED_DUST_LINK,
        isPruned: !isDustIncluded,
      });
    } else {
      displayNodes = displayNodes.map(n => 
        n.id === PRUNED_DUST_NODE.id ? { ...n, isPruned: !isDustIncluded } : n
      );
      displayLinks = displayLinks.map(l => 
        l.target === PRUNED_DUST_NODE.id ? { ...l, isPruned: !isDustIncluded } : l
      );
    }

    // Topological Column Placement by BFS Depth
    const depthMap = new Map();
    const targetId = traceData.target;
    depthMap.set(targetId, 0);

    // Queue BFS for depths
    const queue = [targetId];
    const visited = new Set([targetId]);

    while (queue.length > 0) {
      const curr = queue.shift();
      const currDepth = depthMap.get(curr);
      displayLinks.forEach(link => {
        if (link.source === curr && !visited.has(link.target)) {
          visited.add(link.target);
          depthMap.set(link.target, currDepth + 1);
          queue.push(link.target);
        }
      });
    }

    // Ensure terminal exchange is in the last column
    displayNodes.forEach(n => {
      if (n.type === 'exchange') depthMap.set(n.id, 4);
      if (n.id === '0xDust_Pruned') depthMap.set(n.id, 1);
    });

    // Group by column
    const columns = new Map();
    displayNodes.forEach(n => {
      const d = depthMap.get(n.id) ?? 2;
      if (!columns.has(d)) columns.set(d, []);
      columns.get(d).push(n);
    });

    const maxDepth = Math.max(...Array.from(depthMap.values()), 4);
    const paddingX = 110;
    const paddingY = 80;
    const availableWidth = Math.max(650, width - paddingX * 2);
    const colSpacing = availableWidth / maxDepth;

    // Build or preserve physics node positions
    const existingNodeMap = new Map(nodesRef.current.map(n => [n.id, n]));

    const computedNodes = displayNodes.map(node => {
      const existing = existingNodeMap.get(node.id);
      const depth = depthMap.get(node.id) ?? 2;
      const nodesInCol = columns.get(depth) || [node];
      const idxInCol = nodesInCol.findIndex(n => n.id === node.id);

      const targetX = paddingX + depth * colSpacing;
      const colHeight = height - paddingY * 2;
      const targetY = paddingY + (idxInCol + 1) * (colHeight / (nodesInCol.length + 1));

      return {
        ...node,
        x: existing ? existing.x : targetX,
        y: existing ? existing.y : targetY,
        vx: existing ? existing.vx : 0,
        vy: existing ? existing.vy : 0,
        targetX,
        targetY,
        radius: node.type === 'exchange' ? 24 : (node.type === 'victim' ? 22 : 18),
      };
    });

    nodesRef.current = computedNodes;
    linksRef.current = displayLinks;

    // Reset or initialize flowing particles
    particlesRef.current = displayLinks.map(link => ({
      link,
      progress: Math.random(),
      speed: 0.006 * playbackSpeed,
    }));
  }, [traceData, dustThreshold, playbackSpeed]);

  // Main Canvas Render & Animation Loop (60 FPS)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let running = true;

    const render = () => {
      if (!running) return;

      const width = canvas.width = containerRef.current?.clientWidth || 900;
      const height = canvas.height = containerRef.current?.clientHeight || 540;

      ctx.clearRect(0, 0, width, height);

      ctx.save();
      // Apply Pan & Zoom
      ctx.translate(transform.x, transform.y);
      ctx.scale(transform.k, transform.k);

      const nodes = nodesRef.current;
      const links = linksRef.current;
      const nodeMap = new Map(nodes.map(n => [n.id, n]));

      // Physics Relaxation Step
      nodes.forEach(node => {
        if (node === draggedNodeRef.current) return; // User is manually dragging

        // Spring force towards anchor target
        const dx = node.targetX - node.x;
        const dy = node.targetY - node.y;
        node.vx = (node.vx + dx * 0.04) * 0.82;
        node.vy = (node.vy + dy * 0.04) * 0.82;

        // Node repulsion
        nodes.forEach(other => {
          if (node === other) return;
          const distDx = node.x - other.x;
          const distDy = node.y - other.y;
          const dist = Math.hypot(distDx, distDy) || 1;
          if (dist < 80) {
            const force = (80 - dist) * 0.02;
            node.vx += (distDx / dist) * force;
            node.vy += (distDy / dist) * force;
          }
        });

        node.x += node.vx;
        node.y += node.vy;
      });

      // 1. Draw Links (Curves & Pruned styling)
      links.forEach(link => {
        const source = nodeMap.get(link.source);
        const target = nodeMap.get(link.target);
        if (!source || !target) return;

        const fScore = link.fraud_score !== undefined ? link.fraud_score : (link.suspiciousScore || 50);
        const isHighRisk = fScore >= 70 || target.type === 'exchange';
        const isSuspicious = fScore >= 40 && !isHighRisk;
        const isPruned = link.isPruned;

        // Bezier Curve
        const midX = (source.x + target.x) / 2;
        const dx = target.x - source.x;
        const cp1x = source.x + dx * 0.45;
        const cp1y = source.y;
        const cp2x = source.x + dx * 0.55;
        const cp2y = target.y;

        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, target.x, target.y);

        if (isPruned) {
          ctx.strokeStyle = '#cbd5e1';
          ctx.lineWidth = 1.5;
          ctx.setLineDash([5, 5]);
        } else if (isHighRisk) {
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 2.8;
          ctx.setLineDash([]);
        } else if (isSuspicious) {
          ctx.strokeStyle = '#f59e0b';
          ctx.lineWidth = 2.2;
          ctx.setLineDash([]);
        } else {
          ctx.strokeStyle = '#94a3b8';
          ctx.lineWidth = 1.8;
          ctx.setLineDash([]);
        }
        ctx.stroke();
        ctx.setLineDash([]); // reset

        // Draw Flowing Particle Pulses if Playing
        if (isPlaying && !isPruned) {
          const p = particlesRef.current.find(item => item.link === link);
          if (p) {
            p.progress = (p.progress + p.speed * playbackSpeed) % 1;

            // Compute point on cubic bezier at progress t
            const t = p.progress;
            const px = Math.pow(1 - t, 3) * source.x +
              3 * Math.pow(1 - t, 2) * t * cp1x +
              3 * (1 - t) * Math.pow(t, 2) * cp2x +
              Math.pow(t, 3) * target.x;
            const py = Math.pow(1 - t, 3) * source.y +
              3 * Math.pow(1 - t, 2) * t * cp1y +
              3 * (1 - t) * Math.pow(t, 2) * cp2y +
              Math.pow(t, 3) * target.y;

            // Particle Glow & Core
            const particleColor = isHighRisk ? '#dc2626' : (isSuspicious ? '#d97706' : '#2563eb');
            const shadowColor = isHighRisk ? '#ef4444' : (isSuspicious ? '#f59e0b' : '#3b82f6');
            ctx.beginPath();
            ctx.arc(px, py, isHighRisk ? 4.5 : 3.5, 0, Math.PI * 2);
            ctx.fillStyle = particleColor;
            ctx.shadowColor = shadowColor;
            ctx.shadowBlur = 8;
            ctx.fill();
            ctx.shadowBlur = 0; // reset
          }
        }

        // Draw Amount Badge on Link Midpoint
        const badgeX = (source.x + target.x) / 2;
        const badgeY = (source.y + target.y) / 2 - 8;

        const isTerminal = target.type === 'exchange' || isHighRisk;
        ctx.fillStyle = '#ffffff';
        ctx.strokeStyle = isTerminal ? '#fecaca' : '#e2e8f0';
        ctx.lineWidth = 1.2;

        const badgeWidth = 90;
        const badgeHeight = 18;
        const rx = badgeX - badgeWidth / 2;
        const ry = badgeY - badgeHeight / 2;

        ctx.beginPath();
        if (typeof ctx.roundRect === 'function') {
          ctx.roundRect(rx, ry, badgeWidth, badgeHeight, 9);
        } else {
          ctx.rect(rx, ry, badgeWidth, badgeHeight);
        }
        ctx.fill();
        ctx.stroke();

        ctx.font = '600 9.5px "JetBrains Mono", monospace';
        ctx.fillStyle = isTerminal ? '#b91c1c' : '#334155';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(link.amount, badgeX, badgeY);
      });

      // 2. Draw Nodes
      nodes.forEach(node => {
        const isSelected = selectedNode && selectedNode.id === node.id;
        const isPruned = node.isPruned;

        let strokeColor = '#3b82f6';
        let badgeColor = '#2563eb';
        let initialLetter = 'M';

        if (node.type === 'exchange') {
          strokeColor = '#ef4444';
          badgeColor = '#ef4444';
          initialLetter = 'V';
        } else if (node.type === 'victim') {
          strokeColor = '#2563eb';
          badgeColor = '#2563eb';
          initialLetter = 'VI';
        } else if (node.type === 'dust' || isPruned) {
          strokeColor = '#94a3b8';
          badgeColor = '#64748b';
          initialLetter = 'D';
        } else if (node.id === '0xConsol_99') {
          strokeColor = '#8b5cf6';
          badgeColor = '#8b5cf6';
          initialLetter = 'C';
        } else {
          strokeColor = '#f59e0b';
          badgeColor = '#d97706';
          initialLetter = 'M';
        }

        // Pulse Beacon on Terminal VASP
        if (node.type === 'exchange' && !isPruned) {
          const pulse = (Date.now() % 2000) / 2000;
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + pulse * 18, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(239, 68, 68, ${0.4 * (1 - pulse)})`;
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Selection Aura
        if (isSelected) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 8, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(37, 99, 235, 0.14)';
          ctx.fill();
        }

        // Main Node Circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = isSelected ? 3.5 : 2.5;
        if (isPruned) ctx.setLineDash([3, 3]);
        ctx.fill();
        ctx.stroke();
        ctx.setLineDash([]);

        // Icon Character inside Node
        ctx.font = '700 12px "Inter", sans-serif';
        ctx.fillStyle = strokeColor;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(initialLetter, node.x, node.y);

        // Primary Label (Above)
        ctx.font = '700 10.5px "Inter", sans-serif';
        ctx.fillStyle = isPruned ? '#94a3b8' : '#0f172a';
        ctx.fillText(
          node.label.length > 20 ? `${node.label.slice(0, 18)}...` : node.label,
          node.x,
          node.y - node.radius - 12
        );

        // Address & Balance (Below)
        ctx.font = '500 9.5px "JetBrains Mono", monospace';
        ctx.fillStyle = '#64748b';
        ctx.fillText(`${node.id} (${node.balance})`, node.x, node.y + node.radius + 14);

        // Threat Score Badge on Top-Right Corner
        if (!isPruned) {
          const bx = node.x + node.radius - 4;
          const by = node.y - node.radius - 2;

          ctx.fillStyle = badgeColor;
          ctx.beginPath();
          ctx.roundRect(bx, by, 22, 14, 4);
          ctx.fill();

          ctx.font = '700 8.5px "Inter", sans-serif';
          ctx.fillStyle = '#ffffff';
          ctx.fillText(`${node.riskScore}`, bx + 11, by + 7);
        }
      });

      ctx.restore();

      animFrameIdRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      running = false;
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current);
    };
  }, [transform, selectedNode, isPlaying, playbackSpeed]);

  // Canvas Mouse & Interaction Handlers
  const getCanvasCoords = useCallback((e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;
    // Invert transform
    const x = (clientX - transform.x) / transform.k;
    const y = (clientY - transform.y) / transform.k;
    return { x, y, clientX, clientY };
  }, [transform]);

  const handleMouseDown = (e) => {
    const { x, y, clientX, clientY } = getCanvasCoords(e);

    // Check if clicked a node
    const clickedNode = nodesRef.current.find(n => {
      const dist = Math.hypot(n.x - x, n.y - y);
      return dist <= n.radius + 5;
    });

    if (clickedNode) {
      draggedNodeRef.current = clickedNode;
      onSelectNode(clickedNode);
    } else {
      isDraggingCanvasRef.current = true;
      dragStartRef.current = { x: clientX - transform.x, y: clientY - transform.y };
    }
  };

  const handleMouseMove = (e) => {
    const { x, y, clientX, clientY } = getCanvasCoords(e);

    if (draggedNodeRef.current) {
      draggedNodeRef.current.x = x;
      draggedNodeRef.current.y = y;
      draggedNodeRef.current.targetX = x;
      draggedNodeRef.current.targetY = y;
      return;
    }

    if (isDraggingCanvasRef.current) {
      setTransform(prev => ({
        ...prev,
        x: clientX - dragStartRef.current.x,
        y: clientY - dragStartRef.current.y,
      }));
      return;
    }

    // Check link hover for tooltip
    const nodeMap = new Map(nodesRef.current.map(n => [n.id, n]));
    const foundLink = linksRef.current.find(link => {
      const src = nodeMap.get(link.source);
      const tgt = nodeMap.get(link.target);
      if (!src || !tgt) return false;
      // Approximate line distance
      const midX = (src.x + tgt.x) / 2;
      const midY = (src.y + tgt.y) / 2;
      return Math.hypot(midX - x, midY - y) < 20;
    });

    if (foundLink) {
      setHoveredLink(foundLink);
      setTooltipPos({ x: clientX + 15, y: clientY - 30 });
    } else {
      setHoveredLink(null);
    }
  };

  const handleMouseUp = () => {
    draggedNodeRef.current = null;
    isDraggingCanvasRef.current = false;
  };

  const handleZoom = (delta) => {
    setTransform(prev => ({
      ...prev,
      k: Math.min(2.2, Math.max(0.4, prev.k + delta)),
    }));
  };

  const handleReset = () => {
    setTransform({ x: 0, y: 0, k: 1 });
  };

  return (
    <div className="canvas-interactive-viewport" ref={containerRef}>
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isDraggingCanvasRef.current ? 'grabbing' : 'grab' }}
      />

      {/* Real-Time Floating Controls */}
      <div className="canvas-floating-toolbar">
        <button className="btn-tool-action" onClick={() => handleZoom(0.15)} title="Zoom In">
          <ZoomIn size={14} />
        </button>
        <button className="btn-tool-action" onClick={() => handleZoom(-0.15)} title="Zoom Out">
          <ZoomOut size={14} />
        </button>
        <button className="btn-tool-action" onClick={handleReset} title="Reset Camera">
          <RotateCcw size={14} />
        </button>
      </div>

      {/* Hover Tooltip */}
      {hoveredLink && (
        <div
          style={{
            position: 'absolute',
            left: tooltipPos.x,
            top: tooltipPos.y,
            backgroundColor: '#ffffff',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-lg)',
            padding: '8px 12px',
            fontSize: '0.74rem',
            pointerEvents: 'none',
            zIndex: 30,
            whiteSpace: 'nowrap',
          }}
        >
          <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
            Tx: <span style={{ fontFamily: 'var(--font-mono)' }}>{hoveredLink.txHash}</span>
          </div>
          <div style={{ color: 'var(--primary)', fontWeight: 600 }}>Amount: {hoveredLink.amount}</div>
          <div style={{ color: 'var(--text-muted)' }}>Forwarding Latency: {hoveredLink.latency}</div>
        </div>
      )}
    </div>
  );
}
