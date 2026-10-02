<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  ArrowDownLeft,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Database,
  FileCode2,
  FileText,
  Filter,
  Focus,
  GitBranch,
  History,
  Info,
  Layers3,
  LoaderCircle,
  Network,
  RefreshCw,
  Search,
  SlidersHorizontal,
} from "@lucide/vue";
import GraphCanvas from "../components/GraphCanvas.vue";
import KnowledgeQualityPanel from "../components/KnowledgeQualityPanel.vue";
import { api } from "../lib/api";
import {
  displayValue,
  kindColor,
  kindLabel,
  sourceLocation,
  statusLabel,
  taskLabel,
  type GraphEdge,
  type GraphNode,
} from "../lib/graph";

type Json = Record<string, any>;
interface Facet {
  value: string;
  label: string;
  count: number;
}
interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  focus: GraphNode | null;
  facets: { kinds: Facet[]; relations: Facet[] };
  stats: Json;
  truncated: boolean;
  evidence: Json | null;
  filters: Json;
}
const route = useRoute();
const tab = ref<"graph" | "capabilities">("graph");
const graph = ref<GraphResponse | null>(null);
const capabilities = ref<Json[]>([]);
const loading = ref(true);
const error = ref("");
const detailError = ref("");
const detailLoading = ref(false);
const selected = ref<GraphNode | null>(null);
const selectedEvidence = ref<Json | null>(null);
const selectedDetail = ref<Json | null>(null);
const focusId = ref("");
const hops = ref(1);
const search = ref("");
const kinds = ref<string[]>([]);
const relations = ref<string[]>([]);
const capabilityQuery = ref("");
const capabilityTask = ref("");
const capabilityStatus = ref("");
const showFilters = ref(false);
let graphRequest = 0;
let detailRequest = 0;
let searchTimer: ReturnType<typeof setTimeout> | undefined;
let graphAbort: AbortController | undefined;
let detailAbort: AbortController | undefined;
let initialized = false;

const stats = computed(() => graph.value?.stats || {});
const focusedNode = computed(() => graph.value?.focus);
const selectedCapability = computed(() => selectedDetail.value?.capability);
const selectedId = computed(() => selected.value?.id || "");
const selectedProperties = computed(() =>
  Object.entries(selected.value?.properties || {}).filter(
    ([key]) => !["content", "code", "source_code"].includes(key),
  ),
);
const totalFilters = computed(
  () =>
    kinds.value.length + relations.value.length + (search.value.trim() ? 1 : 0),
);
const filteredCapabilities = computed(() =>
  capabilities.value.filter((card) => {
    const text =
      `${card.name} ${card.summary} ${(card.tags || []).join(" ")}`.toLocaleLowerCase();
    return (
      (!capabilityQuery.value ||
        text.includes(capabilityQuery.value.toLocaleLowerCase())) &&
      (!capabilityTask.value ||
        (card.task_types || []).includes(capabilityTask.value)) &&
      (!capabilityStatus.value || card.status === capabilityStatus.value)
    );
  }),
);
const taskOptions = computed(() => [
  ...new Set<string>(
    capabilities.value.flatMap((card) => card.task_types || []),
  ),
]);
const statusOptions = computed(() => [
  ...new Set<string>(
    capabilities.value.map((card) => card.status).filter(Boolean),
  ),
]);
const selectedRelations = computed(() => {
  const nodes = new Map(
    (graph.value?.nodes || []).map((node) => [node.id, node]),
  );
  return (graph.value?.edges || [])
    .filter(
      (edge) =>
        edge.source === selectedId.value || edge.target === selectedId.value,
    )
    .map((edge) => {
      const outgoing = edge.source === selectedId.value;
      const otherId = outgoing ? edge.target : edge.source;
      return { ...edge, outgoing, otherId, other: nodes.get(otherId) };
    });
});
const propertyLabels: Record<string, string> = {
  capability_id: "能力 ID",
  version: "版本",
  status: "状态",
  origin: "生成方式",
  run_id: "运行 ID",
  source_id: "来源 ID",
  source_key: "来源标识",
  source_type: "来源类型",
  locator: "来源定位",
  content_sha256: "内容指纹",
  sha256: "SHA256",
  source_sha256: "来源指纹",
  url: "来源链接",
  path: "相对路径",
  repository: "代码仓库",
  created_at: "创建时间",
  candidate_id: "候选 ID",
  description: "说明",
  summary: "摘要",
  mode: "运行模式",
  quality_status: "质量状态",
  provider: "模型来源",
  dataset_id: "数据集",
  task_type: "任务类型",
  error: "错误信息",
  solution: "修复经验",
};
const currentNodeLabel = computed(
  () => selected.value?.kind_label || kindLabel(selected.value?.kind || ""),
);
const errorText = (cause: unknown) =>
  cause instanceof Error ? cause.message : "加载失败，请重试。";
const nodeIdFor = (card: Json) =>
  `capability:${card.capability_id || card.id}:v${card.version || 1}`;
function metricText(value: unknown) {
  return typeof value === "number" ? value.toFixed(4) : displayValue(value);
}
function safeUrl(value: unknown) {
  try {
    const u = new URL(String(value));
    return ["http:", "https:"].includes(u.protocol) ? u.href : "";
  } catch {
    return "";
  }
}
function toggleFilter(values: string[], value: string) {
  const index = values.indexOf(value);
  if (index === -1) values.push(value);
  else values.splice(index, 1);
  loadGraph();
}

async function initialize() {
  loading.value = true;
  error.value = "";
  try {
    const result = await api<Json>("/capabilities");
    capabilities.value = result.capabilities || [];
    const requestedId =
      typeof route.query.capability === "string" ? route.query.capability : "";
    const initial =
      capabilities.value.find((card) => card.capability_id === requestedId) ||
      capabilities.value.find(
        (card) => card.capability_id === "bank-precontact-policy",
      ) ||
      capabilities.value[0];
    if (!initialized) {
      if (typeof route.query.focus === "string" && route.query.focus)
        focusId.value = route.query.focus;
      else if (initial) {
        focusId.value = nodeIdFor(initial);
        // Start with the capability definition; experiment evidence remains available in the inspector.
        if (!requestedId)
          relations.value = ["SOLVES", "DERIVED_FROM", "USES", "REQUIRES"];
      }
      initialized = true;
    }
    await loadGraph();
  } catch (cause) {
    error.value = errorText(cause);
    loading.value = false;
  }
}

async function loadGraph() {
  const request = ++graphRequest;
  graphAbort?.abort();
  graphAbort = new AbortController();
  loading.value = true;
  error.value = "";
  const query = new URLSearchParams({
    hops: String(hops.value),
    limit: "80",
    edge_limit: "160",
  });
  if (focusId.value) query.set("focus", focusId.value);
  if (search.value.trim()) query.set("q", search.value.trim());
  if (kinds.value.length) query.set("kinds", kinds.value.join(","));
  if (relations.value.length) query.set("relations", relations.value.join(","));
  try {
    const result = await api<GraphResponse>(`/graph/explore?${query}`, {
      signal: graphAbort.signal,
    });
    if (request !== graphRequest) return;
    graph.value = result;
    const retained = result.nodes.find((node) => node.id === selectedId.value);
    const next = retained || result.focus || result.nodes[0];
    if (next)
      await selectNode(
        next,
        next.id === result.focus?.id ? result.evidence : undefined,
      );
    else {
      selected.value = null;
      selectedEvidence.value = null;
      selectedDetail.value = null;
    }
  } catch (cause) {
    if (request === graphRequest) error.value = errorText(cause);
  } finally {
    if (request === graphRequest) loading.value = false;
  }
}

async function selectNode(node: GraphNode, evidence?: Json | null) {
  const request = ++detailRequest;
  detailAbort?.abort();
  detailAbort = new AbortController();
  selected.value = node;
  selectedEvidence.value = evidence || null;
  selectedDetail.value = null;
  detailLoading.value = true;
  detailError.value = "";
  try {
    if (node.kind === "Capability" && node.properties.capability_id) {
      const id = encodeURIComponent(String(node.properties.capability_id));
      const query = node.properties.version
        ? `?version=${node.properties.version}`
        : "";
      const detail = await api<Json>(`/capabilities/${id}${query}`, {
        signal: detailAbort.signal,
      });
      if (request !== detailRequest) return;
      selectedDetail.value = detail;
      selectedEvidence.value = detail.evidence;
    } else if (!evidence) {
      const result = await api<GraphResponse>(
        `/graph/explore?focus=${encodeURIComponent(node.id)}&hops=1&limit=1&edge_limit=0`,
        { signal: detailAbort.signal },
      );
      if (request !== detailRequest) return;
      selectedEvidence.value = result.evidence;
    }
  } catch (cause) {
    if (request === detailRequest) detailError.value = errorText(cause);
  } finally {
    if (request === detailRequest) detailLoading.value = false;
  }
}
async function selectCard(card: Json) {
  await selectNode({
    id: nodeIdFor(card),
    label: card.name,
    kind: "Capability",
    properties: {
      capability_id: card.capability_id || card.id,
      version: card.version,
      status: card.status,
      origin: card.origin,
    },
  });
}
function applyFocus(id: string, depth = hops.value) {
  focusId.value = id;
  hops.value = depth;
  tab.value = "graph";
  loadGraph();
}
function overview() {
  focusId.value = "";
  kinds.value = [];
  relations.value = [];
  search.value = "";
  loadGraph();
}
function clearFilters() {
  kinds.value = [];
  relations.value = [];
  search.value = "";
  loadGraph();
}
function queueSearch() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(loadGraph, 350);
}
function chooseTab(value: "graph" | "capabilities") {
  tab.value = value;
  if (
    value === "capabilities" &&
    !selectedCapability.value &&
    capabilities.value[0]
  )
    selectCard(capabilities.value[0]);
}
function showVersion(event: Event) {
  const version = (event.target as HTMLSelectElement).value;
  const node = selectedDetail.value?.versions.find(
    (item: Json) => String(item.version) === version,
  );
  if (node && selected.value)
    selectNode({
      ...selected.value,
      id: node.node_id,
      properties: { ...selected.value.properties, version: Number(version) },
    });
}
onMounted(initialize);
watch(
  () => [route.query.focus, route.query.capability],
  ([focus, capability]) => {
    if (typeof focus === "string" && focus) applyFocus(focus);
    else if (typeof capability === "string" && capability) {
      const card = capabilities.value.find(
        (item) => item.capability_id === capability || item.id === capability,
      );
      if (card) applyFocus(nodeIdFor(card));
    }
  },
);
onBeforeUnmount(() => {
  graphRequest++;
  detailRequest++;
  graphAbort?.abort();
  detailAbort?.abort();
  if (searchTimer) clearTimeout(searchTimer);
});
</script>

<template>
  <div class="knowledge-page">
    <header class="page-heading knowledge-heading">
      <div>
        <p class="eyebrow">KNOWLEDGE EXPLORER</p>
        <h1>让每一项能力，都有据可循</h1>
        <p class="muted">
          连接算法、来源与验证结果。从一项能力出发，探索它的实现依据。
        </p>
      </div>
      <button class="btn btn-ghost" :disabled="loading" @click="initialize">
        <RefreshCw :size="16" :class="{ spinning: loading }" />刷新知识库
      </button>
    </header>

    <div class="knowledge-summary">
      <div>
        <span class="summary-icon teal"><Layers3 :size="20" /></span
        ><span
          ><strong>{{ capabilities.length }}</strong
          ><small>可检索能力</small></span
        >
      </div>
      <div>
        <span class="summary-icon blue"><Network :size="20" /></span
        ><span
          ><strong>{{ stats.total_nodes ?? "—" }}</strong
          ><small>知识节点</small></span
        >
      </div>
      <div>
        <span class="summary-icon amber"><GitBranch :size="20" /></span
        ><span
          ><strong>{{ stats.total_edges ?? "—" }}</strong
          ><small>语义关系</small></span
        >
      </div>
      <p>
        <Info :size="15" />可按需检查来源、版本、哈希与关系，核验结果供
        CI、质量检查和运行审计使用。
      </p>
    </div>

    <KnowledgeQualityPanel />

    <div class="knowledge-tabs" role="tablist" aria-label="知识库视图">
      <button
        id="graph-tab"
        role="tab"
        :aria-selected="tab === 'graph'"
        aria-controls="graph-panel"
        :class="{ active: tab === 'graph' }"
        @click="chooseTab('graph')"
      >
        <Network :size="17" />知识图谱
      </button>
      <button
        id="capabilities-tab"
        role="tab"
        :aria-selected="tab === 'capabilities'"
        aria-controls="capabilities-panel"
        :class="{ active: tab === 'capabilities' }"
        @click="chooseTab('capabilities')"
      >
        <BookOpen :size="17" />能力库<span>{{ capabilities.length }}</span>
      </button>
      <span class="tabs-note">点击探索 · 查看证据 · 复用能力</span>
    </div>

    <div v-if="error" class="error-box" role="alert">
      <Info :size="20" />
      <div>
        <strong>知识库暂时无法加载</strong>
        <p>{{ error }}</p>
      </div>
      <button class="btn btn-ghost" @click="initialize">重新加载</button>
    </div>

    <div
      class="knowledge-workspace"
      :class="{ 'library-workspace': tab === 'capabilities' }"
    >
      <section
        v-if="tab === 'graph'"
        id="graph-panel"
        class="explorer panel"
        role="tabpanel"
        aria-labelledby="graph-tab"
      >
        <div class="explorer-title">
          <div class="explorer-breadcrumb">
            <span>知识图谱</span><ChevronRight :size="14" /><strong>{{
              focusedNode?.label || "全局概览"
            }}</strong>
          </div>
          <button
            class="icon-button mobile-filter"
            title="显示筛选器"
            aria-label="显示筛选器"
            @click="showFilters = !showFilters"
          >
            <SlidersHorizontal :size="17" />
          </button>
          <button v-if="focusId" class="text-button" @click="overview">
            返回概览<ArrowUpRight :size="14" />
          </button>
        </div>
        <div class="explorer-body">
          <aside
            class="filter-rail"
            :class="{ 'filters-visible': showFilters }"
            aria-label="图谱筛选"
          >
            <div class="filter-title">
              <Filter :size="15" /><strong>筛选与图例</strong
              ><button
                v-if="totalFilters"
                class="text-button"
                @click="clearFilters"
              >
                清空
              </button>
            </div>
            <label class="graph-search"
              ><Search :size="15" /><input
                v-model="search"
                type="search"
                placeholder="搜索节点与属性"
                aria-label="搜索图谱节点"
                @input="queueSearch"
            /></label>
            <div v-if="focusId" class="focus-depth">
              <span>探索范围</span>
              <div>
                <button
                  v-for="depth in [1, 2]"
                  :key="depth"
                  :class="{ active: hops === depth }"
                  :aria-pressed="hops === depth"
                  @click="
                    hops = depth;
                    loadGraph();
                  "
                >
                  {{ depth }} 跳邻域
                </button>
              </div>
            </div>
            <details open class="filter-section">
              <summary>
                节点类型<span>{{ graph?.facets.kinds.length || 0 }}</span>
              </summary>
              <label
                v-for="facet in graph?.facets.kinds || []"
                :key="facet.value"
                class="facet-row"
                ><input
                  type="checkbox"
                  :checked="kinds.includes(facet.value)"
                  @change="toggleFilter(kinds, facet.value)"
                /><span
                  class="kind-dot"
                  :style="{ background: kindColor(facet.value) }"
                /><span>{{ facet.label }}</span
                ><small>{{ facet.count }}</small></label
              >
            </details>
            <details class="filter-section" open>
              <summary>
                关系类型<span>{{ graph?.facets.relations.length || 0 }}</span>
              </summary>
              <label
                v-for="facet in graph?.facets.relations || []"
                :key="facet.value"
                class="facet-row"
                ><input
                  type="checkbox"
                  :checked="relations.includes(facet.value)"
                  @change="toggleFilter(relations, facet.value)"
                /><ArrowRight :size="13" class="muted" /><span>{{
                  facet.label
                }}</span
                ><small>{{ facet.count }}</small></label
              >
            </details>
            <p class="filter-help">
              不勾选表示显示全部。关系筛选会改变探索路径；当前中心节点始终保留。
            </p>
          </aside>
          <div class="canvas-wrap">
            <div v-if="loading" class="canvas-loading" role="status">
              <LoaderCircle :size="24" class="spinning" /><span
                >正在读取知识与证据…</span
              >
            </div>
            <GraphCanvas
              v-if="graph?.nodes.length"
              :nodes="graph.nodes"
              :edges="graph.edges"
              :selected-id="selectedId"
              :focus-id="focusId"
              @select="selectNode"
            />
            <div v-else-if="!loading" class="empty-state graph-empty">
              <Network :size="38" />
              <h3>没有符合条件的节点</h3>
              <p>
                {{
                  totalFilters
                    ? "尝试清除筛选条件，或返回全局概览。"
                    : "知识抽取或任务验证完成后，相关知识会出现在这里。"
                }}
              </p>
              <button
                v-if="totalFilters"
                class="btn btn-ghost"
                @click="clearFilters"
              >
                清除筛选
              </button>
            </div>
            <div class="graph-footer">
              <span
                >当前显示
                <strong>{{ stats.returned_nodes || 0 }}</strong> 个节点 ·
                <strong>{{ stats.returned_edges || 0 }}</strong> 条关系</span
              ><span v-if="stats.hidden_by_filters"
                >筛选隐藏 {{ stats.hidden_by_filters }} 个节点</span
              ><span v-else>箭头表示关系方向</span>
            </div>
          </div>
        </div>
        <div v-if="graph?.truncated" class="truncation-note" role="status">
          <Info :size="15" />当前视图省略了 {{ stats.omitted_nodes }} 个节点、{{
            stats.omitted_edges
          }}
          条关系。选中节点并聚焦邻域，可继续探索。
        </div>
        <div
          v-if="graph?.filters.focus_retained_outside_filters"
          class="truncation-note"
        >
          <Focus :size="15" />当前中心节点不符合筛选条件，已保留用于定位。
        </div>
      </section>

      <section
        v-else
        id="capabilities-panel"
        class="capability-library"
        role="tabpanel"
        aria-labelledby="capabilities-tab"
      >
        <div class="library-toolbar panel">
          <label class="graph-search library-search"
            ><Search :size="17" /><input
              v-model="capabilityQuery"
              type="search"
              placeholder="搜索能力名称、说明或标签"
              aria-label="搜索算法能力" /></label
          ><select v-model="capabilityTask" aria-label="按任务类型筛选">
            <option value="">全部任务类型</option>
            <option v-for="type in taskOptions" :key="type" :value="type">
              {{ taskLabel(type) }}
            </option></select
          ><select v-model="capabilityStatus" aria-label="按能力状态筛选">
            <option value="">全部状态</option>
            <option
              v-for="status in statusOptions"
              :key="status"
              :value="status"
            >
              {{ statusLabel(status) }}
            </option>
          </select>
        </div>
        <p class="library-count">
          {{ filteredCapabilities.length }} 项能力
          <span>每张卡片保留来源、约束与版本信息</span>
        </p>
        <div class="capability-grid">
          <button
            v-for="card in filteredCapabilities"
            :key="card.capability_id"
            class="capability-card panel"
            :class="{ selected: selectedId === nodeIdFor(card) }"
            @click="selectCard(card)"
          >
            <div class="card-top">
              <span class="card-icon"><Layers3 :size="21" /></span
              ><span class="version-badge">v{{ card.version || 1 }}</span>
            </div>
            <h3>{{ card.name }}</h3>
            <p>{{ card.summary }}</p>
            <div class="card-tags">
              <span v-for="type in card.task_types || []" :key="type">{{
                taskLabel(type)
              }}</span
              ><span>{{ statusLabel(card.status) }}</span>
            </div>
            <div class="card-bottom">
              <span
                ><FileText :size="13" />{{
                  card.evidence?.length || 0
                }}
                个来源依据</span
              ><span>查看详情<ArrowUpRight :size="15" /></span>
            </div>
          </button>
        </div>
        <div
          v-if="!filteredCapabilities.length && !loading"
          class="empty-state panel"
        >
          <BookOpen :size="36" />
          <h3>没有匹配的能力</h3>
          <p>尝试更换关键词或任务类型。</p>
        </div>
      </section>

      <aside class="inspector panel" aria-label="节点详情与证据">
        <div class="inspector-heading">
          <span
            ><FileText :size="16" />{{
              tab === "graph" ? "节点详情" : "能力详情"
            }}</span
          ><span class="live-dot">实时知识</span>
        </div>
        <div v-if="selected" class="inspector-body">
          <div
            class="selected-type"
            :style="{ color: kindColor(selected.kind) }"
          >
            <span
              class="kind-dot"
              :style="{ background: kindColor(selected.kind) }"
            />{{ currentNodeLabel
            }}<span v-if="selected.properties.version"
              >v{{ selected.properties.version }}</span
            >
          </div>
          <h2>{{ selected.label }}</h2>
          <p v-if="selectedCapability?.summary" class="selected-description">
            {{ selectedCapability.summary }}
          </p>
          <div v-if="selected.properties.status" class="selected-status">
            <CheckCircle2 :size="14" />{{
              statusLabel(selected.properties.status)
            }}
          </div>
          <div class="inspector-actions">
            <button class="btn btn-ghost" @click="applyFocus(selected.id, 1)">
              <Focus :size="15" />聚焦此节点</button
            ><RouterLink
              v-if="
                selected.kind === 'Capability' &&
                selected.properties.capability_id
              "
              class="btn btn-primary"
              :to="{
                path: '/workbench',
                query: {
                  capability: String(selected.properties.capability_id),
                  ...(selected.properties.version
                    ? { version: String(selected.properties.version) }
                    : {}),
                },
              }"
              >用于新任务<ArrowRight :size="15"
            /></RouterLink>
          </div>
          <div v-if="detailLoading" class="detail-loading" role="status">
            <LoaderCircle :size="15" class="spinning" />正在读取来源与验证证据
          </div>
          <div v-if="detailError" class="detail-error" role="alert">
            <p>{{ detailError }}</p>
            <button class="text-button" @click="selectNode(selected)">
              重试详情
            </button>
          </div>

          <template v-if="selectedCapability">
            <section class="inspector-section">
              <h3><Layers3 :size="15" />适用范围</h3>
              <div class="card-tags">
                <span
                  v-for="type in selectedCapability.task_types || []"
                  :key="type"
                  >{{ taskLabel(type) }}</span
                >
              </div>
              <p
                v-if="selectedCapability.preconditions?.length"
                class="body-text"
              >
                {{ displayValue(selectedCapability.preconditions) }}
              </p>
              <p v-else class="small-muted">
                尚未记录额外前置条件，请结合来源确认适用范围。
              </p>
            </section>
            <details class="evidence-collapse">
              <summary><Database :size="15" />输入、输出与依赖</summary>
              <dl class="property-list">
                <div>
                  <dt>输入契约</dt>
                  <dd>{{ displayValue(selectedCapability.input_schema) }}</dd>
                </div>
                <div>
                  <dt>输出契约</dt>
                  <dd>{{ displayValue(selectedCapability.output_schema) }}</dd>
                </div>
                <div>
                  <dt>依赖环境</dt>
                  <dd>{{ displayValue(selectedCapability.dependencies) }}</dd>
                </div>
              </dl>
            </details>
          </template>

          <section
            v-if="selectedEvidence"
            class="inspector-section evidence-section"
          >
            <h3>
              <FileText :size="15" />知识来源<span>{{
                selectedEvidence.counts?.sources?.total ??
                selectedEvidence.sources?.length ??
                0
              }}</span>
            </h3>
            <div
              v-for="source in selectedEvidence.sources || []"
              :key="source.node_id"
              class="evidence-item"
            >
              <strong>{{ source.label }}</strong>
              <p
                v-if="sourceLocation(source.properties).file"
                class="source-file"
              >
                {{ sourceLocation(source.properties).file }}
              </p>
              <p
                v-if="sourceLocation(source.properties).symbol"
                class="source-symbol"
              >
                {{ sourceLocation(source.properties).symbol }}
              </p>
              <p v-if="sourceLocation(source.properties).lines">
                {{ sourceLocation(source.properties).lines }}
              </p>
              <p
                v-if="
                  !sourceLocation(source.properties).file &&
                  !sourceLocation(source.properties).symbol
                "
                class="small-muted"
              >
                {{ source.properties?.source_type || "来源材料" }}
              </p>
              <a
                v-if="safeUrl(source.properties?.uri || source.properties?.url)"
                :href="safeUrl(source.properties.uri || source.properties.url)"
                target="_blank"
                rel="noopener noreferrer"
                >查看原始来源<ArrowUpRight :size="12"
              /></a>
              <details>
                <summary>查看来源定位与关联路径</summary>
                <dl class="property-list">
                  <div v-for="(value, key) in source.properties" :key="key">
                    <dt>{{ propertyLabels[key] || key }}</dt>
                    <dd>{{ displayValue(value) }}</dd>
                  </div>
                </dl>
                <p class="path-proof">
                  {{
                    (source.path || [])
                      .map((edge: Json) => edge.relation_label || edge.relation)
                      .join(" → ") || "当前节点即来源"
                  }}
                </p>
              </details>
            </div>
            <p v-if="!selectedEvidence.sources?.length" class="small-muted">
              暂无通过来源关系连接的材料。
            </p>
          </section>

          <section v-if="selectedEvidence" class="inspector-section">
            <h3>
              <CheckCircle2 :size="15" />关联验证记录<span>{{
                selectedEvidence.counts?.validations?.total ??
                selectedEvidence.validations?.length ??
                0
              }}</span>
            </h3>
            <p class="evidence-explainer">
              记录展示通过制品关联的实际运行。关联记录不代表当前能力已通过语义验证。
            </p>
            <article
              v-for="validation in selectedEvidence.validations || []"
              :key="validation.node_id"
              class="validation-card"
            >
              <div class="validation-top">
                <strong>{{ validation.dataset_id || "验证运行" }}</strong
                ><span class="mode-badge">{{
                  validation.mode === "mock"
                    ? "Mock 演示"
                    : validation.mode === "real"
                      ? "真实调用"
                      : "模式未记录"
                }}</span>
              </div>
              <p>
                {{ statusLabel(validation.status) }} ·
                {{ validation.provider || "来源未记录" }}
              </p>
              <template v-if="validation.report_available"
                ><div class="validation-metric">
                  <span>{{
                    validation.primary_metric || "average_precision"
                  }}</span
                  ><strong>{{
                    metricText(
                      validation.metrics?.[
                        validation.primary_metric || "average_precision"
                      ],
                    )
                  }}</strong>
                </div>
                <p class="small-muted">{{ validation.quality_label }}</p>
                <p class="check-count">
                  检查通过 {{ validation.checks?.passed ?? 0 }} /
                  {{ validation.checks?.total ?? 0 }} 项
                </p>
                <RouterLink
                  class="text-button"
                  :to="`/runs/${validation.run_id}`"
                  >查看完整验证报告<ArrowRight :size="14" /></RouterLink
              ></template>
              <p v-else class="small-muted">该记录的完整报告暂不可用。</p>
              <details>
                <summary>查看证据路径</summary>
                <p class="path-proof">
                  {{
                    (validation.path || [])
                      .map((edge: Json) => edge.relation_label || edge.relation)
                      .join(" → ") || "当前节点即验证运行"
                  }}
                </p>
                <p class="small-muted">运行 ID：{{ validation.run_id }}</p>
                <p v-if="validation.selected_candidate_id" class="small-muted">
                  运行选中候选：{{ validation.selected_candidate_id }}
                </p>
                <p class="small-muted">指标属于该次运行选中的候选。</p>
              </details>
            </article>
            <p v-if="!selectedEvidence.validations?.length" class="small-muted">
              暂无直接关联的验证记录。使用此能力完成任务后，可查看回写证据。
            </p>
          </section>

          <details
            v-if="selectedEvidence?.artifacts?.length"
            class="evidence-collapse"
          >
            <summary>
              <FileCode2 :size="15" />关联代码制品<span>{{
                selectedEvidence.counts?.artifacts?.total ??
                selectedEvidence.artifacts.length
              }}</span>
            </summary>
            <div
              v-for="artifact in selectedEvidence.artifacts"
              :key="artifact.node_id"
              class="evidence-item"
            >
              <strong>{{ artifact.label }}</strong>
              <dl class="property-list">
                <div v-for="(value, key) in artifact.properties" :key="key">
                  <dt>{{ propertyLabels[key] || key }}</dt>
                  <dd>{{ displayValue(value) }}</dd>
                </div>
              </dl>
            </div>
          </details>
          <details
            v-if="selectedEvidence?.failure_experiences?.length"
            class="evidence-collapse"
          >
            <summary>
              <History :size="15" />失败与修复经验<span>{{
                selectedEvidence.failure_experiences.length
              }}</span>
            </summary>
            <div
              v-for="experience in selectedEvidence.failure_experiences"
              :key="experience.node_id"
              class="evidence-item"
            >
              <strong>{{ experience.label }}</strong>
              <dl class="property-list">
                <div v-for="(value, key) in experience.properties" :key="key">
                  <dt>{{ propertyLabels[key] || key }}</dt>
                  <dd>{{ displayValue(value) }}</dd>
                </div>
              </dl>
            </div>
          </details>
          <p
            v-if="selectedEvidence?.truncated"
            class="small-muted evidence-limit"
          >
            证据较多，当前仅展示部分。请聚焦具体节点查看。
          </p>

          <section
            v-if="selectedRelations.length && tab === 'graph'"
            class="inspector-section"
          >
            <h3>
              <GitBranch :size="15" />画布中的关联<span>{{
                selectedRelations.length
              }}</span>
            </h3>
            <button
              v-for="edge in selectedRelations"
              :key="edge.id"
              class="relation-item"
              @click="edge.other && selectNode(edge.other)"
            >
              <ArrowUpRight v-if="edge.outgoing" :size="16" /><ArrowDownLeft
                v-else
                :size="16"
              /><span
                ><small
                  >{{ edge.outgoing ? "出向" : "入向" }} ·
                  {{ edge.relation_label || edge.relation }}</small
                ><strong>{{ edge.other?.label || edge.otherId }}</strong></span
              ><ChevronRight :size="14" />
            </button>
          </section>

          <details
            v-if="selectedDetail?.versions?.length"
            class="evidence-collapse"
          >
            <summary>
              <History :size="15" />能力版本<span>{{
                selectedDetail.version_count
              }}</span>
            </summary>
            <label class="version-selector"
              >当前版本<select
                :value="String(selected.properties.version)"
                @change="showVersion"
              >
                <option
                  v-for="version in selectedDetail.versions"
                  :key="version.version"
                  :value="String(version.version)"
                >
                  v{{ version.version }} · {{ statusLabel(version.status) }}
                </option>
              </select></label
            >
            <p class="small-muted">
              每个版本保留独立内容指纹，历史记录不会被新版本覆盖。
            </p>
          </details>
          <details class="evidence-collapse">
            <summary><SlidersHorizontal :size="15" />节点属性与标识</summary>
            <dl class="property-list">
              <div>
                <dt>节点 ID</dt>
                <dd>{{ selected.id }}</dd>
              </div>
              <div v-for="[key, value] in selectedProperties" :key="key">
                <dt>{{ propertyLabels[key] || key }}</dt>
                <dd>{{ displayValue(value) }}</dd>
              </div>
            </dl>
          </details>
        </div>
        <div v-else class="inspector-empty">
          <Focus :size="34" />
          <h3>从一个节点开始</h3>
          <p>点击图谱节点或能力卡片，查看来源、适用条件与验证记录。</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.knowledge-page {
  min-width: 0;
  --explorer-height: clamp(500px, calc(100vh - 420px), 620px);
}
.knowledge-heading {
  align-items: center;
}
.knowledge-heading h1 {
  font-size: 27px;
}
.knowledge-summary {
  display: flex;
  align-items: center;
  gap: 35px;
  margin: 24px 0 25px;
}
.knowledge-summary > div {
  display: flex;
  align-items: center;
  gap: 12px;
}
.summary-icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
}
.teal {
  background: #e4f5f1;
  color: #0d9488;
}
.blue {
  background: #eaf0fb;
  color: #4d79c7;
}
.amber {
  background: #fff3df;
  color: #bc892b;
}
.knowledge-summary strong {
  display: block;
  font-size: 24px;
  line-height: 1.15;
  color: #172b3a;
  letter-spacing: -0.04em;
}
.knowledge-summary small {
  color: #7b8a98;
  font-size: 11px;
  display: block;
  margin-top: 5px;
}
.knowledge-summary > p {
  margin-left: auto;
  max-width: 265px;
  font-size: 11px;
  color: #82909a;
  display: flex;
  gap: 8px;
  line-height: 1.65;
}
.knowledge-summary > p svg {
  flex-shrink: 0;
  margin-top: 3px;
}
.knowledge-tabs {
  display: flex;
  align-items: center;
  gap: 26px;
  border-bottom: 1px solid #dce5eb;
  margin-bottom: 22px;
}
.knowledge-tabs > button {
  background: none;
  border: 0;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  padding: 13px 1px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #718391;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}
.knowledge-tabs > button.active {
  color: #0d9488;
  border-bottom-color: #0d9488;
}
.knowledge-tabs button > span {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 5px;
  background: #e9eff1;
  color: #6c7e89;
}
.tabs-note {
  margin-left: auto;
  color: #8a98a3;
  font-size: 11px;
}
.knowledge-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 312px;
  gap: 18px;
  align-items: start;
}
.explorer {
  overflow: hidden;
  padding: 0;
  min-width: 0;
}
.explorer-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 58px;
  padding: 14px 18px;
  border-bottom: 1px solid #e6ecef;
}
.explorer-breadcrumb {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 12px;
  min-width: 0;
}
.explorer-breadcrumb > span {
  color: #81909b;
  white-space: nowrap;
}
.explorer-breadcrumb > strong {
  color: #344c5c;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  font-size: 12px;
}
.explorer-title > .text-button {
  margin-left: auto;
  white-space: nowrap;
  flex-shrink: 0;
}
.explorer-body {
  display: flex;
  height: var(--explorer-height);
  min-height: 0;
  overflow: hidden;
}
.filter-rail {
  height: 100%;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #dce5eb transparent;
  width: 184px;
  flex: 0 0 184px;
  padding: 19px 15px;
  border-right: 1px solid #e6ecef;
  background: #fff;
}
.filter-title {
  display: flex;
  gap: 7px;
  align-items: center;
  font-size: 12px;
  color: #425868;
  margin-bottom: 16px;
}
.filter-title .text-button {
  margin-left: auto;
  font-size: 10px;
}
.graph-search {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #e0e7ec;
  border-radius: 7px;
  padding: 8px 9px;
  color: #94a1ac;
  background: #fbfcfd;
}
.graph-search:focus-within {
  border-color: #0d9488;
  box-shadow: 0 0 0 2px #0d948817;
}
.graph-search svg {
  flex-shrink: 0;
}
.graph-search input {
  min-width: 0;
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  color: #3f5666;
  font-size: 11px;
  padding: 0;
  box-shadow: none;
}
.focus-depth {
  margin-top: 19px;
}
.focus-depth > span {
  font-size: 10px;
  font-weight: 700;
  color: #8a98a3;
}
.focus-depth > div {
  display: flex;
  gap: 5px;
  margin-top: 7px;
}
.focus-depth button {
  flex: 1;
  border: 1px solid #e2e8ed;
  background: #fff;
  border-radius: 6px;
  padding: 5px;
  font-size: 10px;
  color: #82909a;
  cursor: pointer;
}
.focus-depth button.active {
  color: #0d8178;
  border-color: #9fd6ce;
  background: #effaf7;
}
.filter-section {
  border-top: 1px solid #edf1f4;
  margin-top: 18px;
  padding-top: 14px;
}
.filter-section > summary {
  font-size: 11px;
  font-weight: 700;
  color: #5b6f7d;
  cursor: pointer;
  margin-bottom: 13px;
}
.filter-section > summary > span {
  float: right;
  font-size: 10px;
  color: #9ca8b0;
  font-weight: 400;
}
.facet-row {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 7px 0;
  font-size: 11px;
  color: #526777;
  cursor: pointer;
}
.facet-row input {
  width: 12px;
  height: 12px;
  min-width: 12px;
  accent-color: #0d9488;
  margin: 0;
  padding: 0;
}
.facet-row small {
  margin-left: auto;
  color: #a1aeb7;
  font-size: 9px;
}
.kind-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.filter-help {
  color: #9aa6af;
  font-size: 10px;
  line-height: 1.7;
  margin: 17px 0 0;
}
.canvas-wrap {
  position: relative;
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}
.canvas-wrap > :deep(.graph-canvas) {
  flex: 1;
  min-height: 0;
}
.canvas-loading {
  position: absolute;
  inset: 0 0 44px;
  z-index: 6;
  background: #ffffffd9;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  gap: 10px;
  font-size: 12px;
  color: #0d9488;
}
.graph-footer {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 13px 15px;
  border-top: 1px solid #e9eef1;
  font-size: 10px;
  color: #8b99a4;
  background: #fff;
}
.graph-footer strong {
  color: #4a6273;
  font-weight: 600;
}
.graph-empty {
  flex: 1;
  min-height: 0;
}
.truncation-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  background: #fff9ed;
  border-top: 1px solid #f3e7ca;
  color: #937234;
  font-size: 11px;
  line-height: 1.65;
}
.truncation-note svg {
  flex-shrink: 0;
  margin-top: 2px;
}
.mobile-filter {
  display: none;
}
.inspector {
  min-width: 0;
  max-height: calc(var(--explorer-height) + 62px);
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}
.inspector-heading {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 19px;
  border-bottom: 1px solid #e6ecef;
}
.inspector-heading > span:first-child {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-weight: 600;
  color: #526777;
  font-size: 12px;
}
.live-dot {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 9px;
  color: #91a09f;
}
.live-dot::before {
  content: "";
  width: 5px;
  height: 5px;
  background: #1cb199;
  border-radius: 50%;
}
.inspector-body {
  padding: 21px 19px;
  min-height: 0;
  max-height: var(--explorer-height);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #dae4e9 transparent;
}
.selected-type {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
}
.selected-type > span:last-child:not(.kind-dot) {
  margin-left: auto;
  color: #94a2ac;
  font-weight: 500;
  font-size: 10px;
}
.inspector-body > h2 {
  color: #172b3a;
  font-size: 18px;
  line-height: 1.6;
  margin: 11px 0 9px;
  overflow-wrap: anywhere;
}
.selected-description {
  color: #718391;
  line-height: 1.8;
  font-size: 13px;
  margin: 0 0 12px;
}
.selected-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  color: #536d7a;
  padding: 4px 7px;
  border: 1px solid #e0e9ed;
  border-radius: 5px;
  background: #f8fafb;
}
.inspector-actions {
  display: flex;
  gap: 8px;
  margin-top: 18px;
  flex-wrap: wrap;
}
.inspector-actions .btn {
  min-height: 34px;
  font-size: 10px;
  padding: 7px 9px;
  gap: 5px;
  flex: 1;
  white-space: nowrap;
  justify-content: center;
}
.inspector-section {
  border-top: 1px solid #edf1f4;
  padding-top: 19px;
  margin-top: 20px;
}
.inspector-section h3 {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #40596a;
  font-size: 12px;
  font-weight: 600;
  margin: 0 0 13px;
}
.inspector-section h3 > span {
  font-size: 9px;
  color: #8b9ba7;
  background: #f0f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: auto;
}
.body-text {
  color: #637b8c;
  font-size: 12px;
  line-height: 1.7;
}
.small-muted {
  color: #7b8c99;
  font-size: 11px;
  line-height: 1.75;
  overflow-wrap: anywhere;
}
.evidence-explainer {
  color: #82949f;
  font-size: 11px;
  line-height: 1.75;
  margin: -3px 0 13px;
}
.evidence-item {
  padding: 11px 0;
  border-bottom: 1px dashed #e5ecef;
}
.evidence-item:first-of-type {
  padding-top: 0;
}
.evidence-item:last-child {
  border-bottom: 0;
}
.evidence-item > strong {
  display: block;
  color: #4e6575;
  font-size: 12px;
  line-height: 1.65;
  overflow-wrap: anywhere;
}
.evidence-item > p {
  font-size: 10px;
  color: #8899a6;
  margin: 5px 0;
  overflow-wrap: anywhere;
}
.evidence-item > a {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #0d9488;
  text-decoration: none;
  font-size: 10px;
  margin: 4px 0;
}
.evidence-item details {
  margin-top: 8px;
}
.evidence-item details > summary,
.validation-card details > summary {
  color: #8b9ba7;
  font-size: 9px;
  cursor: pointer;
}
.evidence-collapse {
  border-top: 1px solid #edf1f4;
  padding: 15px 0 0;
  margin-top: 15px;
}
.evidence-collapse > summary {
  color: #7b8e9c;
  font-size: 11px;
  cursor: pointer;
  list-style: none;
  display: flex;
  align-items: center;
  gap: 7px;
}
.evidence-collapse > summary::after {
  content: "+";
  margin-left: auto;
  font-size: 15px;
  color: #90a1ac;
}
.evidence-collapse[open] > summary::after {
  content: "−";
}
.evidence-collapse > summary > span {
  font-size: 9px;
  color: #9aa8b2;
}
.evidence-collapse > summary {
  margin-bottom: 10px;
}
.property-list {
  margin: 10px 0;
}
.property-list > div {
  margin: 0 0 11px;
}
.property-list dt {
  color: #98a5af;
  font-size: 9px;
  margin-bottom: 3px;
}
.property-list dd {
  color: #627b8c;
  font-size: 11px;
  line-height: 1.8;
  margin: 0;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}
.path-proof {
  font-size: 10px;
  color: #0d8c82;
  background: #f1f9f7;
  border-radius: 5px;
  padding: 7px 9px;
  line-height: 1.7;
}
.validation-card {
  padding: 12px;
  background: #f8fafb;
  border: 1px solid #e7edf1;
  border-radius: 8px;
  margin-top: 10px;
}
.validation-top {
  display: flex;
  gap: 6px;
  align-items: center;
  justify-content: space-between;
}
.validation-top > strong {
  font-size: 12px;
  color: #405c6f;
}
.mode-badge {
  font-size: 9px;
  color: #6f8796;
  border: 1px solid #dde6ec;
  border-radius: 4px;
  padding: 2px 5px;
  white-space: nowrap;
}
.validation-card > p {
  color: #7c8d99;
  font-size: 11px;
  margin: 7px 0;
}
.validation-metric {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-top: 13px;
}
.validation-metric > span {
  color: #8a9ba8;
  font-size: 9px;
}
.validation-metric > strong {
  color: #274c5b;
  font-size: 19px;
}
.validation-card .check-count {
  color: #57897b;
}
.validation-card details {
  margin-top: 12px;
}
.validation-card .text-button {
  font-size: 10px;
}
.text-button {
  padding: 0;
  background: transparent;
  border: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #0d9488;
  font-size: 11px;
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
}
.text-button:hover {
  color: #0a7168;
}
.relation-item {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  background: #fff;
  padding: 9px 0;
  text-align: left;
  border: 0;
  border-bottom: 1px dashed #e8eef2;
  color: #8fa0ad;
  cursor: pointer;
}
.relation-item:hover {
  color: #0d9488;
}
.relation-item > span {
  flex: 1;
  min-width: 0;
}
.relation-item small {
  display: block;
  color: #98a7b1;
  font-size: 9px;
  margin-bottom: 3px;
}
.relation-item strong {
  font-size: 11px;
  color: #627988;
  font-weight: 500;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.version-selector {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #8395a2;
  font-size: 10px;
  gap: 8px;
  margin-top: 14px;
}
.version-selector select {
  min-width: 0;
  max-width: 180px;
  font-size: 10px;
  padding: 5px 7px;
}
.inspector-empty {
  text-align: center;
  padding: 80px 27px;
  color: #a1b4bf;
}
.inspector-empty > h3 {
  color: #627d8f;
  font-size: 14px;
  font-weight: 500;
}
.inspector-empty > p {
  font-size: 12px;
  line-height: 1.8;
  color: #9aabb7;
}
.capability-library {
  min-width: 0;
}
.library-toolbar {
  display: flex;
  align-items: center;
  padding: 13px;
  gap: 10px;
}
.library-search {
  flex: 1;
}
.library-search input {
  font-size: 12px;
}
.library-toolbar select {
  font-size: 11px;
  min-width: 115px;
  padding: 9px 8px;
  color: #637b8b;
  border: 1px solid #e0e7ec;
  border-radius: 6px;
  background: #fff;
}
.library-count {
  font-size: 11px;
  color: #596f80;
  margin: 20px 2px 13px;
}
.library-count > span {
  color: #9aa7b1;
  margin-left: 10px;
}
.capability-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 15px;
}
.capability-card {
  padding: 21px 20px 0;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}
.capability-card:hover,
.capability-card.selected {
  border-color: #73c6bb;
  box-shadow: 0 3px 13px #0d94880b;
}
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid #d0ebe5;
  border-radius: 10px;
  color: #0d9488;
  background: #f0faf7;
}
.version-badge {
  color: #9ba9b4;
  font-size: 10px;
  border: 1px solid #e5ebf0;
  padding: 3px 6px;
  border-radius: 4px;
}
.capability-card h3 {
  font-size: 15px;
  line-height: 1.6;
  color: #2d495a;
  margin: 15px 0 8px;
}
.capability-card > p {
  font-size: 12px;
  line-height: 1.85;
  color: #8495a2;
  margin: 0 0 15px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 60px;
}
.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.card-tags > span {
  font-size: 9px;
  color: #78918f;
  padding: 4px 6px;
  background: #f2f7f6;
  border-radius: 4px;
  line-height: 1.2;
}
.card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-top: 1px solid #edf1f4;
  margin-top: 19px;
}
.card-bottom > span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #9aa8b3;
  font-size: 9px;
}
.card-bottom > span:last-child {
  color: #0d9488;
}
.error-box {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #fff7f5;
  border: 1px solid #f0d7d0;
  border-radius: 10px;
  color: #ad6453;
  padding: 16px 20px;
  margin-bottom: 20px;
}
.error-box strong {
  font-size: 13px;
}
.error-box p {
  font-size: 12px;
  margin: 5px 0 0;
}
.error-box button {
  margin-left: auto;
}
.detail-loading {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #0d9488;
  font-size: 10px;
  margin: 15px 0;
}
.detail-error {
  background: #fff5f2;
  border-radius: 6px;
  padding: 10px;
  font-size: 11px;
  color: #b07060;
  margin-top: 12px;
}
.spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
@media (min-width: 1600px) {
  .knowledge-workspace {
    grid-template-columns: minmax(0, 1fr) 340px;
  }
  .filter-rail {
    width: 204px;
    flex-basis: 204px;
  }
  .facet-row {
    font-size: 11px;
  }
  .inspector-body {
    padding: 23px;
  }
}
@media (max-width: 1250px) {
  .knowledge-workspace {
    grid-template-columns: minmax(0, 1fr) 280px;
    gap: 14px;
  }
  .filter-rail {
    width: 158px;
    flex-basis: 158px;
    padding-left: 11px;
    padding-right: 11px;
  }
  .facet-row {
    font-size: 10px;
    gap: 5px;
  }
  .knowledge-summary {
    gap: 25px;
  }
  .knowledge-summary > p {
    display: none;
  }
  .inspector-body {
    padding: 17px;
  }
  .library-toolbar {
    flex-wrap: wrap;
  }
  .library-search {
    flex-basis: 100%;
  }
  .capability-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 1100px) {
  .knowledge-workspace {
    grid-template-columns: 1fr;
  }
  .inspector-body {
    max-height: 600px;
  }
  .filter-rail {
    flex-basis: 188px;
    width: 188px;
    padding: 19px 16px;
  }
  .facet-row {
    font-size: 11px;
  }
  .capability-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .library-toolbar {
    flex-wrap: nowrap;
  }
  .library-search {
    flex-basis: auto;
  }
}
@media (max-width: 720px) {
  .knowledge-heading {
    align-items: start;
    gap: 16px;
  }
  .knowledge-heading h1 {
    font-size: 22px;
  }
  .knowledge-heading > .btn {
    font-size: 0;
    padding: 9px;
  }
  .knowledge-heading > .btn svg {
    width: 17px;
  }
  .knowledge-summary {
    gap: 18px;
  }
  .summary-icon {
    width: 32px;
    height: 32px;
    border-radius: 9px;
  }
  .summary-icon svg {
    width: 16px;
  }
  .knowledge-summary > div {
    gap: 8px;
  }
  .knowledge-summary strong {
    font-size: 21px;
  }
  .knowledge-summary small {
    font-size: 9px;
  }
  .tabs-note {
    display: none;
  }
  .explorer-body {
    height: auto;
    min-height: 470px;
    flex-direction: column;
  }
  .canvas-wrap {
    height: 470px;
    min-height: 470px;
    flex: none;
  }
  .filter-rail {
    display: none;
  }
  .filter-rail.filters-visible {
    display: block;
    width: 100%;
    flex-basis: auto;
    border-bottom: 1px solid #e5ebef;
    max-height: 400px;
    overflow-y: auto;
  }
  .mobile-filter {
    display: flex;
    margin-left: auto;
  }
  .explorer-title {
    padding: 13px;
  }
  .explorer-title > .text-button {
    margin-left: 0;
    font-size: 10px;
  }
  .explorer-breadcrumb {
    font-size: 10px;
    gap: 5px;
  }
  .explorer-breadcrumb > strong {
    font-size: 10px;
  }
  .graph-footer {
    font-size: 9px;
    padding: 11px;
  }
  .graph-footer > span:last-child {
    display: none;
  }
  .capability-grid {
    grid-template-columns: 1fr;
  }
  .library-toolbar {
    flex-wrap: wrap;
  }
  .library-search {
    flex-basis: 100%;
  }
  .library-toolbar select {
    flex: 1;
  }
  .library-count > span {
    display: none;
  }
  .error-box {
    flex-wrap: wrap;
  }
  .error-box button {
    margin-left: 0;
  }
  .graph-empty {
    min-height: 420px;
  }
}
</style>
