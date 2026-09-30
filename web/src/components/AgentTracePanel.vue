<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import {
  Activity,
  Bot,
  ChevronRight,
  CircleAlert,
  Clock3,
  Eye,
  GitBranch,
  Layers3,
  RotateCcw,
  Search,
  Timer,
  Wrench,
} from "@lucide/vue";
import { api } from "../lib/api";
import {
  dateTime,
  errorText,
  metric,
  stateLabel,
  type Json,
} from "../lib/format";

type Trace = Json;
const props = defineProps<{ report: Json | null; runId: string }>();

const expanded = ref(false);
const replayTrace = ref<Trace | null>(null);
const throughSequence = ref<number | null>(null);
const replayLoading = ref(false);
const replayError = ref("");
const controller = ref<AbortController | undefined>();
let requestToken = 0;
let disposed = false;

const liveTrace = computed<Trace>(() =>
  props.report?.agent_trace && typeof props.report.agent_trace === "object"
    ? props.report.agent_trace
    : {},
);
const replaying = computed(() => throughSequence.value !== null);
const trace = computed<Trace>(() =>
  replaying.value ? replayTrace.value || {} : liveTrace.value,
);
const spans = computed<Json[]>(() =>
  Array.isArray(trace.value.spans)
    ? trace.value.spans.filter(
        (item: unknown) => item && typeof item === "object",
      )
    : [],
);
const events = computed<Json[]>(() =>
  Array.isArray(trace.value.events)
    ? trace.value.events.filter(
        (item: unknown) => item && typeof item === "object",
      )
    : [],
);
const framework = computed(() => trace.value.framework || {});
const budget = computed<Json>(
  () =>
    trace.value.budget || (!replaying.value ? props.report?.usage : null) || {},
);
const evidence = computed<Json>(() => trace.value.evidence || {});
const eventCount = computed(() => {
  const value = trace.value.total_event_count ?? trace.value.event_count;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  return events.value.length ? events.value.length : null;
});
const cursor = computed(() => {
  const value = trace.value.cursor_sequence;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  return null;
});
const maxSequence = computed(() => {
  const value = liveTrace.value.cursor_sequence;
  if (typeof value === "number" && Number.isInteger(value) && value >= 0)
    return value;
  const sequences: number[] = Array.isArray(liveTrace.value.events)
    ? liveTrace.value.events
        .map((event: Json) => event.sequence)
        .filter(
          (sequence: unknown): sequence is number =>
            typeof sequence === "number" &&
            Number.isInteger(sequence) &&
            sequence >= 0,
        )
    : [];
  return sequences.length ? Math.max(...sequences) : 0;
});
const agentCount = computed(
  () => spans.value.filter((span) => span.kind === "agent").length,
);
const toolCount = computed(
  () => spans.value.filter((span) => span.kind === "tool").length,
);
const roleCount = computed(
  () =>
    new Set(
      spans.value
        .filter((span) => span.kind === "agent" && span.role)
        .map((span) => span.role),
    ).size,
);
const hasSpanRecords = computed(() => Array.isArray(trace.value.spans));
const hasEvidenceRecords = computed(() =>
  Array.isArray(evidence.value.capability_ids),
);
const inputTokens = computed(() => budget.value.input_tokens);
const outputTokens = computed(() => budget.value.output_tokens);
const cachedInputTokens = computed(() => budget.value.cached_input_tokens);
const totalTokens = computed(() =>
  typeof inputTokens.value === "number" &&
  typeof outputTokens.value === "number"
    ? inputTokens.value + outputTokens.value
    : null,
);
const calls = computed(() => budget.value.calls);
const maxCalls = computed(() => budget.value.max_calls);
const callsPercent = computed(() => ratio(calls.value, maxCalls.value));
const wallSeconds = computed(() => budget.value.wall_seconds);
const maxSeconds = computed(() => budget.value.max_seconds);
const wallPercent = computed(() => ratio(wallSeconds.value, maxSeconds.value));
const capabilityIds = computed<string[]>(() => {
  const ids = evidence.value.capability_ids;
  return Array.isArray(ids) ? ids.map(String).filter(Boolean) : [];
});

function ratio(value: unknown, maximum: unknown) {
  if (
    typeof value !== "number" ||
    !Number.isFinite(value) ||
    typeof maximum !== "number" ||
    !Number.isFinite(maximum) ||
    maximum <= 0
  )
    return null;
  return Math.min(100, Math.max(0, (value / maximum) * 100));
}
function statusLabel(value: unknown) {
  return value === "rejected" ? "校验未通过" : stateLabel(value);
}
function spanLabel(span: Json) {
  if (span.kind === "tool")
    return span.name === "search_capabilities"
      ? "能力知识检索"
      : span.name || "知识检索工具";
  const labels: Record<string, string> = {
    interpreter: "需求理解",
    planner: "方案规划",
    coder: "代码生成",
    repair_coder: "代码修复",
    reviewer: "错误诊断",
    curator: "结果总结",
  };
  return labels[span.role] || span.role || span.name || "Agent 步骤";
}
function spanClass(span: Json) {
  return span.status === "completed"
    ? "completed"
    : ["failed", "rejected", "cancelled"].includes(String(span.status))
      ? "failed"
      : "running";
}
function isLegacy(span: Json) {
  return span.started_at == null && span.start_sequence == null;
}
function spanTime(span: Json) {
  if (
    typeof span.duration_seconds === "number" &&
    Number.isFinite(span.duration_seconds)
  )
    return `${metric(span.duration_seconds, 2)} s`;
  return "未记录耗时";
}
function outputSummary(span: Json) {
  const summary = span.output_summary || {};
  const keys = Array.isArray(summary.result_keys)
    ? summary.result_keys.slice(0, 4).join("、")
    : "";
  const returned =
    summary.returned_count == null ? "" : `返回 ${summary.returned_count} 项`;
  return (
    [keys ? `字段 ${keys}` : "", returned].filter(Boolean).join(" · ") ||
    (span.status === "running"
      ? "等待角色或工具返回结果"
      : "查看事件记录追溯此步骤")
  );
}
function countLabel(value: unknown, fallback: unknown = undefined) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof fallback === "number" && Number.isFinite(fallback))
    return fallback;
  return "—";
}
function abortReplay() {
  controller.value?.abort();
  controller.value = undefined;
}
async function loadReplay(sequence: number) {
  if (!props.runId) return;
  abortReplay();
  const currentRun = props.runId;
  const token = ++requestToken;
  const request = new AbortController();
  controller.value = request;
  replayLoading.value = true;
  replayError.value = "";
  replayTrace.value = null;
  throughSequence.value = sequence;
  try {
    const result = await api<Trace>(
      `/runs/${encodeURIComponent(currentRun)}/agent-trace?through_sequence=${encodeURIComponent(sequence)}`,
      { signal: request.signal },
    );
    if (
      disposed ||
      request.signal.aborted ||
      token !== requestToken ||
      currentRun !== props.runId
    )
      return;
    replayTrace.value = result;
  } catch (error) {
    if (
      disposed ||
      request.signal.aborted ||
      token !== requestToken ||
      currentRun !== props.runId
    )
      return;
    replayError.value = errorText(error);
  } finally {
    if (!disposed && token === requestToken && currentRun === props.runId)
      replayLoading.value = false;
  }
}
function onSlider(event: Event) {
  const value = Number((event.target as HTMLInputElement).value);
  if (Number.isFinite(value)) void loadReplay(value);
}
function resetReplay() {
  abortReplay();
  requestToken += 1;
  throughSequence.value = null;
  replayTrace.value = null;
  replayError.value = "";
  replayLoading.value = false;
}
watch(
  () => props.runId,
  () => resetReplay(),
);
watch(
  () => props.report?.agent_trace,
  () => {
    if (!replaying.value) replayError.value = "";
  },
);
onBeforeUnmount(() => {
  disposed = true;
  abortReplay();
});
</script>

<template>
  <section class="panel agent-trace-panel" data-testid="agent-trace-panel">
    <div class="agent-trace-heading">
      <div>
        <p class="eyebrow">AGENT OBSERVABILITY</p>
        <h2><Activity :size="19" />Agent 观测台</h2>
        <p class="muted">
          按真实事件查看角色、工具、预算与知识引用。回放只读取历史投影，不会新发模型请求。
        </p>
      </div>
      <div class="agent-trace-actions">
        <span class="badge" :class="replaying ? 'working' : 'neutral'">
          <Eye :size="13" />{{
            replayLoading
              ? `正在读取 #${throughSequence}`
              : replayTrace
                ? `回放至 #${cursor}`
                : replaying
                  ? "回放读取失败"
                  : "最新事件"
          }}
        </span>
        <button
          v-if="replaying"
          class="btn btn-ghost"
          type="button"
          @click="resetReplay"
        >
          <RotateCcw :size="14" />返回最新
        </button>
      </div>
    </div>
    <div class="agent-trace-summary" aria-label="Agent 观测摘要">
      <div class="trace-stat">
        <Bot :size="16" /><span>Agent 角色</span
        ><strong>{{ hasSpanRecords ? roleCount : "—" }}</strong
        ><small>{{ agentCount ? `${agentCount} 个 span` : "尚无记录" }}</small>
      </div>
      <div class="trace-stat">
        <Search :size="16" /><span>工具检索</span
        ><strong>{{
          countLabel(
            evidence.retrieval_count,
            hasSpanRecords ? toolCount : undefined,
          )
        }}</strong
        ><small
          >{{
            countLabel(
              evidence.count,
              hasEvidenceRecords ? capabilityIds.length : undefined,
            )
          }}
          张能力卡片</small
        >
      </div>
      <div class="trace-stat">
        <Layers3 :size="16" /><span>Token 消耗</span
        ><strong>{{ totalTokens == null ? "—" : totalTokens }}</strong
        ><small
          >{{ inputTokens ?? "—" }} 输入 · {{ outputTokens ?? "—" }} 输出 · 缓存
          {{ cachedInputTokens ?? "—" }}</small
        >
      </div>
      <div class="trace-stat">
        <Timer :size="16" /><span>事件游标</span
        ><strong>{{ cursor == null ? "—" : cursor }}</strong
        ><small>{{
          eventCount == null ? "尚无事件" : `共 ${eventCount} 条事件`
        }}</small>
      </div>
    </div>
    <details
      class="trace-details"
      :open="expanded"
      @toggle="expanded = ($event.target as HTMLDetailsElement).open"
    >
      <summary>
        <ChevronRight :size="17" /><span
          >展开时序与预算详情<small
            >{{ framework.name || "框架未记录"
            }}{{ framework.version ? ` · ${framework.version}` : "" }}</small
          ></span
        >
      </summary>
      <div class="trace-content">
        <div v-if="replayError" class="trace-error" role="alert">
          <CircleAlert :size="17" /><span>{{ replayError }}</span
          ><button
            class="btn btn-ghost"
            type="button"
            @click="loadReplay(throughSequence ?? 0)"
          >
            重试
          </button>
        </div>
        <div class="trace-replay-bar">
          <div class="trace-replay-title">
            <GitBranch :size="16" /><strong>事件回放</strong
            ><span>拖动游标查看某一时刻的可观测状态</span>
          </div>
          <div class="trace-slider-row">
            <span>0</span
            ><input
              :value="throughSequence ?? cursor ?? 0"
              type="range"
              min="0"
              :max="maxSequence"
              step="1"
              aria-label="回放事件游标"
              :disabled="!liveTrace.total_event_count || maxSequence === 0"
              @input="onSlider"
            /><span>{{ maxSequence }}</span
            ><span v-if="replayLoading" class="trace-loading">读取中…</span>
          </div>
        </div>
        <div class="trace-budget-grid">
          <div class="trace-budget-card">
            <div>
              <strong>调用预算</strong
              ><span>{{ calls ?? "—" }} / {{ maxCalls ?? "—" }}</span>
            </div>
            <div class="budget-track">
              <i :style="{ width: `${callsPercent ?? 0}%` }"></i>
            </div>
            <small>{{
              callsPercent == null
                ? "上限未记录"
                : `${metric(callsPercent, 0)}% 已使用`
            }}</small>
          </div>
          <div class="trace-budget-card">
            <div>
              <strong>时间预算</strong
              ><span
                >{{ wallSeconds == null ? "—" : `${metric(wallSeconds, 1)} s` }}
                /
                {{
                  maxSeconds == null ? "—" : `${metric(maxSeconds, 1)} s`
                }}</span
              >
            </div>
            <div class="budget-track">
              <i :style="{ width: `${wallPercent ?? 0}%` }"></i>
            </div>
            <small>{{
              wallPercent == null
                ? "上限未记录"
                : `${metric(wallPercent, 0)}% 已使用`
            }}</small>
          </div>
        </div>
        <div v-if="capabilityIds.length" class="trace-evidence">
          <strong>能力引用</strong
          ><span v-for="id in capabilityIds" :key="id" class="evidence-chip">{{
            id
          }}</span>
        </div>
        <ol v-if="spans.length" class="agent-span-list">
          <li
            v-for="span in spans"
            :key="span.span_id || `${span.name}-${span.start_sequence}`"
            class="agent-span"
            :class="spanClass(span)"
          >
            <div class="span-marker">
              <Wrench v-if="span.kind === 'tool'" :size="15" /><Bot
                v-else
                :size="15"
              />
            </div>
            <div class="span-main">
              <div class="span-topline">
                <strong>{{ spanLabel(span) }}</strong
                ><span class="span-kind">{{
                  span.kind === "tool" ? "TOOL" : "AGENT"
                }}</span
                ><span class="badge" :class="spanClass(span)">{{
                  statusLabel(span.status)
                }}</span>
              </div>
              <p>
                {{ span.name && span.role ? span.name : outputSummary(span) }}
              </p>
              <small v-if="span.role && span.name">{{
                outputSummary(span)
              }}</small>
              <div class="span-meta">
                <span v-if="span.attempt != null">尝试 {{ span.attempt }}</span
                ><span v-if="span.candidate_id">{{ span.candidate_id }}</span
                ><span>{{ spanTime(span) }}</span
                ><span v-if="span.started_at">{{
                  dateTime(span.started_at)
                }}</span
                ><span v-if="isLegacy(span)" class="legacy-label"
                  >历史完成记录 · 开始时间未记录</span
                >
              </div>
              <p v-if="span.error_type" class="span-error">
                {{ span.error_type }}
              </p>
            </div>
          </li>
        </ol>
        <p v-else class="trace-empty">
          <Clock3 :size="18" />尚无 Agent
          span。运行开始后，这里会显示角色与工具的真实开始、结束和错误状态。
        </p>
        <details v-if="events.length" class="nested-disclosure trace-events">
          <summary>事件摘要（{{ events.length }}）</summary>
          <ol>
            <li
              v-for="event in events"
              :key="`${event.sequence}-${event.event_type}`"
            >
              <span class="event-sequence">#{{ event.sequence }}</span
              ><strong>{{ event.event_type || event.type }}</strong
              ><span v-if="event.role || event.name" class="event-role">{{
                event.role || event.name
              }}</span
              ><time>{{ dateTime(event.created_at) }}</time
              ><span v-if="event.status" class="badge">{{
                statusLabel(event.status)
              }}</span>
            </li>
          </ol>
        </details>
      </div>
    </details>
  </section>
</template>

<style scoped>
.agent-trace-panel {
  padding: 24px 26px;
  background: linear-gradient(135deg, #fff 0%, #f7fbfb 100%);
  border-color: #dce9e8;
}
.agent-trace-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}
.agent-trace-heading h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 7px 0 8px;
  font-size: 19px;
  color: #1c3740;
}
.agent-trace-heading h2 svg {
  color: #198f88;
}
.agent-trace-heading p {
  margin: 0;
  line-height: 1.7;
  font-size: 12px;
}
.agent-trace-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.agent-trace-actions .badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}
.agent-trace-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 20px;
}
.trace-stat {
  min-width: 0;
  padding: 14px 15px;
  border: 1px solid #e2ecec;
  border-radius: 12px;
  background: #fbfdfd;
  display: grid;
  grid-template-columns: 18px 1fr;
  column-gap: 8px;
  row-gap: 3px;
}
.trace-stat > svg {
  grid-row: span 3;
  color: #2c9a91;
  margin-top: 2px;
}
.trace-stat span {
  font-size: 11px;
  color: #6d7e85;
}
.trace-stat strong {
  font-size: 20px;
  line-height: 1.2;
  color: #203c45;
  font-variant-numeric: tabular-nums;
}
.trace-stat small {
  color: #8a999e;
  font-size: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.trace-details {
  margin-top: 18px;
  border-top: 1px solid #e5eeee;
}
.trace-details > summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 16px;
  cursor: pointer;
  list-style: none;
  color: #2b5b62;
  font-size: 13px;
}
.trace-details > summary::-webkit-details-marker {
  display: none;
}
.trace-details[open] > summary > svg {
  transform: rotate(90deg);
}
.trace-details summary small {
  display: block;
  margin-top: 3px;
  color: #8b999e;
  font-size: 10px;
}
.trace-content {
  padding-top: 16px;
  display: grid;
  gap: 16px;
}
.trace-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #f2d2ce;
  color: #9b4942;
  background: #fff6f4;
  font-size: 12px;
}
.trace-error span {
  flex: 1;
}
.trace-replay-bar {
  padding: 14px 16px;
  border: 1px solid #e2ebf1;
  border-radius: 12px;
  background: #f8fbfd;
}
.trace-replay-title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  color: #36556a;
}
.trace-replay-title svg {
  color: #5c78c8;
}
.trace-replay-title span {
  color: #7c8b96;
  font-size: 11px;
}
.trace-slider-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  color: #8c9aa2;
  font-size: 10px;
}
.trace-slider-row input {
  flex: 1;
  min-width: 100px;
  accent-color: #2d9992;
}
.trace-loading {
  color: #6678cf;
  white-space: nowrap;
}
.trace-budget-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.trace-budget-card {
  padding: 13px 15px;
  border: 1px solid #e7eded;
  border-radius: 11px;
  background: #fff;
}
.trace-budget-card > div:first-child {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
  color: #718087;
}
.trace-budget-card strong {
  color: #35515a;
}
.budget-track {
  height: 6px;
  margin: 11px 0 7px;
  overflow: hidden;
  border-radius: 99px;
  background: #e9eeee;
}
.budget-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #58b7a0, #4b7acb);
}
.trace-budget-card small {
  color: #94a0a5;
  font-size: 10px;
}
.trace-evidence {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 11px;
  color: #61767c;
}
.evidence-chip {
  padding: 4px 7px;
  border-radius: 6px;
  background: #eef8f6;
  color: #247c73;
  font-family: ui-monospace, monospace;
  font-size: 10px;
}
.agent-span-list {
  display: grid;
  gap: 9px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.agent-span {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr);
  gap: 9px;
  padding: 12px;
  border: 1px solid #e6ecee;
  border-left: 3px solid #8fa4aa;
  border-radius: 10px;
  background: #fff;
}
.agent-span.completed {
  border-left-color: #31a17c;
}
.agent-span.failed {
  border-left-color: #d16b60;
  background: #fffafa;
}
.agent-span.running {
  border-left-color: #6275d9;
  background: #fbfcff;
}
.span-marker {
  width: 27px;
  height: 27px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: #eef4f4;
  color: #43747c;
}
.agent-span.failed .span-marker {
  color: #b4554c;
  background: #fff0ee;
}
.agent-span.running .span-marker {
  color: #5a6dcc;
  background: #eef0ff;
}
.span-topline {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
}
.span-topline strong {
  color: #29434d;
  font-size: 12px;
}
.span-kind {
  color: #8b9aa0;
  font-size: 9px;
  letter-spacing: 0.8px;
}
.span-topline .badge {
  font-size: 9px;
  padding: 3px 6px;
}
.span-main p {
  margin: 5px 0 0;
  color: #677980;
  font-size: 11px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.span-main > small {
  display: block;
  margin-top: 2px;
  color: #94a0a5;
  font-size: 10px;
}
.span-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 9px;
  margin-top: 8px;
  color: #8b999e;
  font-size: 10px;
}
.legacy-label {
  color: #9b8762;
}
.span-error {
  color: #b34c43 !important;
}
.trace-empty {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 18px;
  border: 1px dashed #d8e4e6;
  border-radius: 10px;
  color: #7c8d93;
  font-size: 12px;
}
.trace-events {
  margin-top: 2px;
}
.trace-events ol {
  display: grid;
  gap: 6px;
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
}
.trace-events li {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 7px 0;
  border-bottom: 1px solid #edf1f2;
  font-size: 11px;
}
.trace-events li time {
  color: #96a1a6;
  margin-left: auto;
}
.event-sequence {
  color: #5f79ca;
  font-family: ui-monospace, monospace;
}
.event-role {
  color: #6f8187;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 5px;
  background: #f0f5f5;
}
@media (max-width: 760px) {
  .agent-trace-panel {
    padding: 20px;
  }
  .agent-trace-heading {
    flex-direction: column;
  }
  .agent-trace-actions {
    justify-content: flex-start;
  }
  .agent-trace-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .trace-budget-grid {
    grid-template-columns: 1fr;
  }
  .trace-replay-title {
    align-items: flex-start;
    flex-wrap: wrap;
  }
  .trace-replay-title span {
    flex-basis: 100%;
    margin-left: 23px;
  }
  .trace-events li time {
    margin-left: 0;
  }
}
</style>
