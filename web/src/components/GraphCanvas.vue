<script setup lang="ts">
import {
  computed,
  getCurrentInstance,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import * as d3 from "d3";
import { Expand, Minus, Plus, RotateCcw, Tags } from "@lucide/vue";
import {
  kindColor,
  kindLabel,
  type GraphEdge,
  type GraphNode,
} from "../lib/graph";

const props = defineProps<{
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedId?: string;
  focusId?: string;
}>();
const emit = defineEmits<{ select: [node: GraphNode] }>();
interface SimNode extends GraphNode, d3.SimulationNodeDatum {}
interface SimEdge extends d3.SimulationLinkDatum<SimNode> {
  edge: GraphEdge;
  offset: number;
}
const root = ref<HTMLDivElement>();
const svgElement = ref<SVGSVGElement>();
const hovered = ref<GraphNode | null>(null);
const hoverPosition = ref({ left: 0, top: 0 });
const showLabels = ref(true);
let labelsChosenByUser = false;
const markerId = `graph-arrow-${getCurrentInstance()?.uid || 0}`;
const hoverSummary = computed(() => {
  const p = hovered.value?.properties || {};
  return String(
    p.summary ||
      p.description ||
      p.status ||
      "点击节点查看来源、属性与关联证据",
  );
});
let simulation: d3.Simulation<SimNode, SimEdge> | undefined;
let zoom: d3.ZoomBehavior<SVGSVGElement, unknown> | undefined;
let svg: d3.Selection<SVGSVGElement, unknown, null, undefined> | undefined;
let nodeGroups:
  d3.Selection<SVGGElement, SimNode, SVGGElement, unknown> | undefined;
let edgeGroups:
  d3.Selection<SVGGElement, SimEdge, SVGGElement, unknown> | undefined;
let resizeObserver: ResizeObserver | undefined;
let width = 700;
let height = 560;
let activeNodes: SimNode[] = [];
let initialFitTimer: ReturnType<typeof setTimeout> | undefined;

// Small line glyphs remain distinct when labels overlap or the graph is zoomed out.
const glyphs: Record<string, string> = {
  Capability: "M12 3 3 8l9 5 9-5-9-5M3 12l9 5 9-5M3 16l9 5 9-5",
  Algorithm: "m8 6-6 6 6 6m8-12 6 6-6 6m-3-15-2 18",
  Source: "M14 2H5v20h14V7l-5-5v5h5M8 12h8M8 16h8",
  ValidationRun: "m4 12 5 5L20 6",
  Artifact:
    "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z M14 2v6h6 M10 13l-2 2 2 2 M14 13l2 2-2 2",
  Metric: "M3 12h4l3-8 4 16 3-8h4",
  FailureExperience: "M12 3 2 21h20L12 3m0 5v6m0 3v1",
  DatasetVersion: "M4 5h16v14H4zM4 10h16M9 5v14M15 5v14",
  Transform: "M4 7h16m-4-4 4 4-4 4M20 17H4m4-4-4 4 4 4",
  Environment: "M4 5h16v12H4zM8 21h8m-4-4v4",
  TaskType: "M4 4h16v16H4zM8 8h8M8 12h8M8 16h4",
};
const endpoint = (value: string | number | SimNode): SimNode =>
  value as SimNode;

function edgeGeometry(edge: SimEdge) {
  const source = endpoint(edge.source),
    target = endpoint(edge.target);
  const sx = source.x || 0,
    sy = source.y || 0,
    tx = target.x || 0,
    ty = target.y || 0;
  const dx = tx - sx,
    dy = ty - sy,
    length = Math.max(Math.hypot(dx, dy), 1);
  const bendX = (sx + tx) / 2 - (dy / length) * edge.offset;
  const bendY = (sy + ty) / 2 + (dx / length) * edge.offset;
  const startLength = Math.max(Math.hypot(bendX - sx, bendY - sy), 1);
  const endLength = Math.max(Math.hypot(tx - bendX, ty - bendY), 1);
  const r = 26;
  return {
    path: `M${sx + ((bendX - sx) / startLength) * r},${sy + ((bendY - sy) / startLength) * r} Q${bendX},${bendY} ${tx - ((tx - bendX) / endLength) * (r + 7)},${ty - ((ty - bendY) / endLength) * (r + 7)}`,
    x: (sx + 2 * bendX + tx) / 4,
    y: (sy + 2 * bendY + ty) / 4,
  };
}

function highlight() {
  const selected = props.selectedId;
  const neighbors = new Set<string>(selected ? [selected] : []);
  props.edges.forEach((edge) => {
    if (edge.source === selected || edge.target === selected) {
      neighbors.add(edge.source);
      neighbors.add(edge.target);
    }
  });
  nodeGroups
    ?.attr("opacity", (node) =>
      !selected || neighbors.has(node.id) ? 1 : 0.38,
    )
    .attr("aria-pressed", (node) => String(node.id === selected));
  nodeGroups
    ?.select<SVGCircleElement>("circle.node-halo")
    .attr("stroke", (node) =>
      node.id === selected ? kindColor(node.kind) : "transparent",
    )
    .attr("stroke-width", (node) => (node.id === selected ? 2 : 0));
  edgeGroups?.attr("opacity", (edge) =>
    !selected || edge.edge.source === selected || edge.edge.target === selected
      ? 1
      : 0.17,
  );
  edgeGroups
    ?.select("path")
    .attr("stroke", (edge) =>
      edge.edge.source === selected || edge.edge.target === selected
        ? "#0d9488"
        : "#acb9c5",
    );
}

function reveal(event: MouseEvent | FocusEvent, node: GraphNode) {
  hovered.value = node;
  const bounds = root.value?.getBoundingClientRect();
  if (event instanceof MouseEvent && bounds) {
    hoverPosition.value = {
      left: Math.min(event.clientX - bounds.left + 14, width - 266),
      top: Math.max(
        60,
        Math.min(event.clientY - bounds.top + 14, height - 150),
      ),
    };
  } else {
    hoverPosition.value = { left: 20, top: 68 };
  }
}

function build() {
  if (!svgElement.value || !root.value) return;
  simulation?.stop();
  if (initialFitTimer) clearTimeout(initialFitTimer);
  hovered.value = null;
  if (!labelsChosenByUser)
    showLabels.value = props.nodes.length <= 20 && props.edges.length <= 30;
  width = root.value.clientWidth || 700;
  height = root.value.clientHeight || 560;
  const previous = new Map(activeNodes.map((node) => [node.id, node]));
  activeNodes = props.nodes.map((node) => ({
    ...node,
    x: previous.get(node.id)?.x,
    y: previous.get(node.id)?.y,
  }));
  const nodeIds = new Set(activeNodes.map((node) => node.id));
  const pairs = new Map<string, number>();
  const links: SimEdge[] = props.edges
    .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
    .map((edge) => {
      const pair = [edge.source, edge.target].sort().join("|");
      const index = pairs.get(pair) || 0;
      pairs.set(pair, index + 1);
      return {
        source: edge.source,
        target: edge.target,
        edge,
        offset: index === 0 ? 0 : Math.ceil(index / 2) * (index % 2 ? 38 : -38),
      };
    });
  svg = d3.select(svgElement.value);
  svg.selectAll("*").remove();
  svg.attr("viewBox", `0 0 ${width} ${height}`);
  const defs = svg.append("defs");
  defs
    .append("marker")
    .attr("id", markerId)
    .attr("viewBox", "0 -4 8 8")
    .attr("refX", 7)
    .attr("refY", 0)
    .attr("markerWidth", 7)
    .attr("markerHeight", 7)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-4L8,0L0,4Z")
    .attr("fill", "#8fa3b3");
  const viewport = svg.append("g");
  zoom = d3
    .zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.18, 3])
    .on("zoom", (event) => viewport.attr("transform", event.transform));
  svg.call(zoom).on("dblclick.zoom", null);
  edgeGroups = viewport
    .append("g")
    .selectAll<SVGGElement, SimEdge>("g")
    .data(links)
    .join("g");
  edgeGroups
    .append("path")
    .attr("fill", "none")
    .attr("stroke", "#acb9c5")
    .attr("stroke-width", 1.3)
    .attr("marker-end", `url(#${markerId})`);
  edgeGroups
    .append("text")
    .attr("class", "edge-label")
    .attr("text-anchor", "middle")
    .attr("dy", "-5")
    .text((edge) => edge.edge.relation_label || edge.edge.relation)
    .style("display", showLabels.value ? "" : "none");
  edgeGroups
    .append("title")
    .text((edge) => edge.edge.relation_label || edge.edge.relation);
  nodeGroups = viewport
    .append("g")
    .selectAll<SVGGElement, SimNode>("g")
    .data(activeNodes, (node) => node.id)
    .join("g")
    .attr("class", "graph-node")
    .attr("role", "button")
    .attr("tabindex", 0)
    .attr(
      "aria-label",
      (node) =>
        `${node.kind_label || kindLabel(node.kind)}：${node.label}，点击查看详情`,
    )
    .on("click", (_event, node) => emit("select", node))
    .on("keydown", (event: KeyboardEvent, node) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        emit("select", node);
      }
    })
    .on("mouseenter", reveal)
    .on("focus", reveal)
    .on("mouseleave", () => {
      hovered.value = null;
    })
    .on("blur", () => {
      hovered.value = null;
    });
  nodeGroups
    .append("circle")
    .attr("class", "node-halo")
    .attr("r", 32)
    .attr("fill", "#fff")
    .attr("fill-opacity", 0.86);
  nodeGroups
    .append("circle")
    .attr("r", 25)
    .attr("fill", (node) => kindColor(node.kind))
    .attr("stroke", "#fff")
    .attr("stroke-width", 2.5);
  nodeGroups
    .append("path")
    .attr("d", (node) => glyphs[node.kind] || glyphs.Capability!)
    .attr("transform", "translate(-11,-11) scale(.92)")
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5)
    .attr("fill", "none")
    .attr("stroke-linecap", "round")
    .attr("stroke-linejoin", "round")
    .attr("pointer-events", "none");
  nodeGroups
    .append("text")
    .attr("class", "node-label")
    .attr("text-anchor", "middle")
    .attr("dy", 44)
    .text((node) =>
      node.label.length > 14 ? `${node.label.slice(0, 13)}…` : node.label,
    );
  nodeGroups
    .append("title")
    .text(
      (node) => `${node.label} · ${node.kind_label || kindLabel(node.kind)}`,
    );
  simulation = d3
    .forceSimulation<SimNode>(activeNodes)
    .force(
      "link",
      d3
        .forceLink<SimNode, SimEdge>(links)
        .id((node) => node.id)
        .distance(160)
        .strength(0.38),
    )
    .force("charge", d3.forceManyBody<SimNode>().strength(-570))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide<SimNode>().radius(57))
    .force("x", d3.forceX<SimNode>(width / 2).strength(0.025))
    .force("y", d3.forceY<SimNode>(height / 2).strength(0.035))
    .on("tick", () => {
      nodeGroups?.attr("transform", (node) => `translate(${node.x},${node.y})`);
      edgeGroups?.select("path").attr("d", (edge) => edgeGeometry(edge).path);
      edgeGroups
        ?.select("text")
        .attr("x", (edge) => edgeGeometry(edge).x)
        .attr("y", (edge) => edgeGeometry(edge).y);
    });
  nodeGroups.call(
    d3
      .drag<SVGGElement, SimNode>()
      .on("start", (event, node) => {
        if (!event.active) simulation?.alphaTarget(0.2).restart();
        node.fx = node.x;
        node.fy = node.y;
        hovered.value = null;
      })
      .on("drag", (event, node) => {
        node.fx = event.x;
        node.fy = event.y;
      })
      .on("end", (event) => {
        if (!event.active) simulation?.alphaTarget(0);
      }),
  );
  highlight();
  initialFitTimer = setTimeout(fit, 500);
}

function fit() {
  if (!svg || !zoom || !activeNodes.length) return;
  const xs = activeNodes.map((node) => node.x || 0),
    ys = activeNodes.map((node) => node.y || 0);
  const x0 = Math.min(...xs) - 75,
    x1 = Math.max(...xs) + 75;
  const y0 = Math.min(...ys) - 70,
    y1 = Math.max(...ys) + 75;
  const scale = Math.min(
    1.2,
    (width - 50) / Math.max(x1 - x0, 1),
    (height - 130) / Math.max(y1 - y0, 1),
  );
  svg
    .transition()
    .duration(300)
    .call(
      zoom.transform,
      d3.zoomIdentity
        .translate(
          width / 2 - (scale * (x0 + x1)) / 2,
          height / 2 + 15 - (scale * (y0 + y1)) / 2,
        )
        .scale(scale),
    );
}
function scaleBy(amount: number) {
  if (svg && zoom) svg.transition().duration(200).call(zoom.scaleBy, amount);
}
function toggleLabels() {
  labelsChosenByUser = true;
  showLabels.value = !showLabels.value;
}
function resetLayout() {
  if (initialFitTimer) clearTimeout(initialFitTimer);
  activeNodes.forEach((node) => {
    node.fx = null;
    node.fy = null;
  });
  simulation?.alpha(1).restart();
  initialFitTimer = setTimeout(fit, 500);
}
watch(
  () => [props.nodes, props.edges],
  () => nextTick(build),
);
watch(() => props.selectedId, highlight);
watch(showLabels, (value) =>
  edgeGroups?.select("text").style("display", value ? "" : "none"),
);
onMounted(() => {
  build();
  resizeObserver = new ResizeObserver(() => {
    if (!root.value || !svg) return;
    const changed =
      width !== root.value.clientWidth || height !== root.value.clientHeight;
    width = root.value.clientWidth;
    height = root.value.clientHeight;
    svg.attr("viewBox", `0 0 ${width} ${height}`);
    if (changed) fit();
  });
  if (root.value) resizeObserver.observe(root.value);
});
onBeforeUnmount(() => {
  simulation?.stop();
  resizeObserver?.disconnect();
  if (initialFitTimer) clearTimeout(initialFitTimer);
  svg?.on(".zoom", null);
});
</script>

<template>
  <div ref="root" class="graph-canvas">
    <div class="canvas-tools" aria-label="图谱画布工具">
      <button
        class="canvas-button"
        title="适应画布"
        aria-label="适应画布"
        @click="fit"
      >
        <Expand :size="16" /><span>适应画布</span>
      </button>
      <button
        class="canvas-button"
        title="放大"
        aria-label="放大图谱"
        @click="scaleBy(1.3)"
      >
        <Plus :size="16" />
      </button>
      <button
        class="canvas-button"
        title="缩小"
        aria-label="缩小图谱"
        @click="scaleBy(0.77)"
      >
        <Minus :size="16" />
      </button>
      <button
        class="canvas-button"
        title="重新排列节点"
        aria-label="重新排列节点"
        @click="resetLayout"
      >
        <RotateCcw :size="16" />
      </button>
      <button
        class="canvas-button label-toggle"
        :class="{ active: showLabels }"
        :aria-pressed="showLabels"
        @click="toggleLabels"
      >
        <Tags :size="16" /><span>关系名称</span>
      </button>
    </div>
    <svg
      ref="svgElement"
      class="graph-svg"
      role="group"
      aria-label="可交互知识图谱。拖动画布移动，滚轮缩放，点击或按回车选择节点。"
    />
    <div
      v-if="hovered"
      class="node-tooltip"
      :style="{
        left: `${hoverPosition.left}px`,
        top: `${hoverPosition.top}px`,
      }"
      role="tooltip"
    >
      <span class="tooltip-kind" :style="{ color: kindColor(hovered.kind) }">{{
        hovered.kind_label || kindLabel(hovered.kind)
      }}</span>
      <strong>{{ hovered.label }}</strong>
      <p>{{ hoverSummary }}</p>
    </div>
    <div class="canvas-hint">
      <span class="hint-dot" />拖动节点调整位置 · 滚轮缩放 · 点击查看证据
    </div>
  </div>
</template>

<style scoped>
.graph-canvas {
  position: relative;
  width: 100%;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  background-color: #fbfcfd;
  background-image: radial-gradient(#cfd9df 0.8px, transparent 0.8px);
  background-size: 20px 20px;
}
.graph-svg {
  display: block;
  width: 100%;
  height: 100%;
  min-height: 0;
  cursor: grab;
  touch-action: none;
}
.graph-svg:active {
  cursor: grabbing;
}
.canvas-tools {
  position: absolute;
  z-index: 2;
  top: 16px;
  left: 16px;
  right: 16px;
  display: flex;
  gap: 5px;
  align-items: center;
  pointer-events: none;
}
.canvas-button {
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 34px;
  padding: 0 9px;
  color: #526576;
  background: #fff;
  border: 1px solid #dde5eb;
  border-radius: 7px;
  box-shadow: 0 2px 4px #172b3a05;
  font: 500 12px inherit;
  cursor: pointer;
}
.canvas-button:hover,
.canvas-button.active {
  color: #0d8178;
  background: #f0fdfa;
  border-color: #a8dcd4;
}
.label-toggle {
  margin-left: auto;
}
.canvas-button:focus-visible {
  outline: 3px solid #83d6cc;
  outline-offset: 2px;
}
.canvas-hint {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 7px 12px;
  border: 1px solid #e5ebef;
  border-radius: 20px;
  color: #6b7d8c;
  font-size: 11px;
  background: #fffffff0;
  pointer-events: none;
}
.hint-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #0d9488;
}
.node-tooltip {
  position: absolute;
  z-index: 5;
  width: 246px;
  padding: 14px 16px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #dce5eb;
  box-shadow: 0 8px 32px #172b3a1f;
  pointer-events: none;
}
.node-tooltip strong {
  display: block;
  color: #172b3a;
  font-size: 13px;
  margin: 5px 0;
  overflow-wrap: anywhere;
}
.node-tooltip p {
  font-size: 12px;
  line-height: 1.6;
  color: #657786;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.tooltip-kind {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
:deep(.graph-node) {
  cursor: pointer;
  outline: none;
  transition: opacity 0.15s;
}
:deep(.graph-node:focus-visible .node-halo) {
  stroke: #172b3a;
  stroke-width: 3;
}
:deep(.node-label) {
  fill: #30485a;
  font-family: inherit;
  font-size: 11px;
  font-weight: 600;
  paint-order: stroke;
  stroke: #fbfcfd;
  stroke-width: 4px;
  stroke-linejoin: round;
  pointer-events: none;
}
:deep(.edge-label) {
  fill: #6d7f8d;
  font-family: inherit;
  font-size: 9px;
  paint-order: stroke;
  stroke: #fbfcfd;
  stroke-width: 4px;
  stroke-linejoin: round;
  pointer-events: none;
}
@media (max-width: 720px) {
  .canvas-tools {
    left: 10px;
    right: 10px;
  }
  .canvas-button {
    padding: 0 7px;
  }
  .canvas-hint {
    font-size: 10px;
    padding: 6px 8px;
  }
}
</style>
