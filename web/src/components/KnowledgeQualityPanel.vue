<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Database,
  FileWarning,
  Info,
  GitBranch as GitBranchIcon,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from "@lucide/vue";
import { api, ApiError } from "../lib/api";

type Json = Record<string, any>;

interface QualityCheck {
  id?: string;
  status?: string;
  message?: string;
  severity?: string;
  details?: Json;
}

const result = ref<Json | null>(null);
const loading = ref(false);
const error = ref("");
let controller: AbortController | undefined;
let requestToken = 0;
let disposed = false;

const summary = computed<Json>(() =>
  result.value?.summary && typeof result.value.summary === "object"
    ? result.value.summary
    : {},
);
const checks = computed<QualityCheck[]>(() =>
  Array.isArray(result.value?.checks)
    ? result.value.checks.filter(
        (item: unknown): item is QualityCheck =>
          !!item && typeof item === "object",
      )
    : [],
);
const issues = computed<Json[]>(() =>
  Array.isArray(result.value?.issues)
    ? result.value.issues.filter(
        (item: unknown): item is Json => !!item && typeof item === "object",
      )
    : [],
);
const warnings = computed<Json[]>(() =>
  Array.isArray(result.value?.warnings)
    ? result.value.warnings.filter(
        (item: unknown): item is Json => !!item && typeof item === "object",
      )
    : [],
);
const checkPassed = computed(() =>
  typeof summary.value.checks_passed === "number"
    ? summary.value.checks_passed
    : checks.value.filter((item) => item.status === "passed").length,
);
const hasResult = computed(() => !!result.value);
const isEmpty = computed(
  () =>
    result.value?.status === "not_evaluated" ||
    result.value?.status === "empty",
);
const statusText = computed(() => {
  const status = String(result.value?.status || "idle");
  return (
    (
      {
        passed: "完整性检查通过",
        failed: "发现需要处理的问题",
        not_evaluated: "未评估",
        empty: "知识库为空",
        idle: "尚未检查",
      } as Record<string, string>
    )[status] || "检查结果已返回"
  );
});
const statusClass = computed(() => {
  const status = String(result.value?.status || "idle");
  if (status === "passed") return "good";
  if (status === "failed") return "bad";
  if (status === "not_evaluated" || status === "empty") return "neutral";
  return "idle";
});

const checkLabels: Record<string, string> = {
  snapshot_populated: "知识快照已建立",
  snapshot_shape: "知识快照记录结构",
  version_record_shape: "能力版本记录结构",
  source_record_shape: "来源记录与哈希",
  source_citations: "能力来源可追溯",
  card_status_task_contract: "能力状态与任务契约",
  version_continuity: "版本连续性",
  content_hash_integrity: "能力内容哈希",
  duplicate_content: "重复内容检测",
  graph_reference_integrity: "图节点与边引用",
  graph_semantics: "图谱语义关系",
  verified_experience_evidence: "已验证经验的运行证据",
  latest_view_consistency: "最新能力视图",
};

const labelForCheck = (item: QualityCheck) =>
  checkLabels[String(item.id || "")] || safeText(item.id || "完整性检查");
const messageFor = (item: QualityCheck) =>
  safeText(item.message || "未提供检查说明");
const pretty = (value: unknown) => JSON.stringify(safeAudit(value), null, 2);
const count = (key: string) =>
  typeof summary.value[key] === "number" ? summary.value[key] : "—";
function checkStatus(item: QualityCheck) {
  return (
    (
      {
        passed: "通过",
        warning: "提示",
        failed: "失败",
        not_evaluated: "未评估",
      } as Record<string, string>
    )[String(item.status)] || "未评估"
  );
}
function safeText(value: unknown) {
  return String(value)
    .slice(0, 3000)
    .replace(/\b(?:sk|pk)-[a-z0-9_-]{8,}\b/gi, "[凭证已隐藏]")
    .replace(/\bBearer\s+\S+/gi, "Bearer [已隐藏]")
    .replace(/https?:\/\/[^\s"']+/gi, "[来源地址已隐藏]")
    .replace(/\/(?:root|home|etc|tmp|var)\/[^\s"']+/g, "[本地路径已隐藏]");
}
function safeAudit(value: unknown, depth = 0): unknown {
  if (depth > 6) return "[内容已折叠]";
  if (typeof value === "string") return safeText(value);
  if (Array.isArray(value))
    return value.slice(0, 100).map((item) => safeAudit(item, depth + 1));
  if (value && typeof value === "object")
    return Object.fromEntries(
      Object.entries(value)
        .slice(0, 100)
        .map(([key, item]) => [
          key,
          /(?:api[_-]?key|secret|password|authorization|token|prompt|response|source_code|content|code)/i.test(
            key,
          ) && key !== "content_sha256"
            ? "[敏感字段已隐藏]"
            : safeAudit(item, depth + 1),
        ]),
    );
  return value;
}

function abortRequest() {
  controller?.abort();
  controller = undefined;
}

async function runQualityCheck() {
  abortRequest();
  const token = ++requestToken;
  const request = new AbortController();
  controller = request;
  loading.value = true;
  error.value = "";
  try {
    const value = await api<Json>("/knowledge/quality", {
      signal: request.signal,
    });
    if (disposed || token !== requestToken || request.signal.aborted) return;
    result.value = value;
  } catch (cause) {
    if (disposed || token !== requestToken || request.signal.aborted) return;
    error.value =
      cause instanceof ApiError && cause.status === 404
        ? "当前服务尚未提供知识完整性检查接口，请确认后端版本。"
        : "知识完整性检查暂未完成，请检查服务状态后重试。";
    result.value = null;
  } finally {
    if (!disposed && token === requestToken) loading.value = false;
  }
}

onBeforeUnmount(() => {
  disposed = true;
  requestToken += 1;
  abortRequest();
});
</script>

<template>
  <section
    class="knowledge-quality-panel panel"
    data-testid="knowledge-quality-panel"
  >
    <div class="quality-heading">
      <div>
        <p class="eyebrow">KNOWLEDGE INTEGRITY</p>
        <h2>知识完整性检查</h2>
        <p class="quality-subtitle">
          按需核验来源、版本、哈希与图谱关系。检查只读运行，不会改变知识库，也不会阻塞图谱探索。
        </p>
      </div>
      <button
        class="btn btn-ghost quality-action"
        :disabled="loading"
        @click="runQualityCheck"
      >
        <LoaderCircle v-if="loading" :size="15" class="spinning" />
        <RefreshCw v-else :size="15" />
        {{ loading ? "正在检查…" : hasResult ? "重新检查" : "检查知识完整性" }}
      </button>
    </div>

    <div v-if="error" class="quality-error" role="alert">
      <XCircle :size="17" /><span>{{ error }}</span>
      <button class="text-button" @click="runQualityCheck">重试</button>
    </div>

    <div v-if="!hasResult && !error" class="quality-idle">
      <ShieldCheck :size="23" />
      <div>
        <strong>检查按需执行</strong>
        <p>先浏览图谱和能力卡；准备答辩或提交前，再执行一次只读完整性检查。</p>
      </div>
    </div>

    <template v-if="hasResult">
      <div class="quality-status" :class="statusClass">
        <CheckCircle2 v-if="statusClass === 'good'" :size="18" />
        <AlertTriangle v-else-if="statusClass === 'bad'" :size="18" />
        <FileWarning v-else :size="18" />
        <div>
          <strong>{{ statusText }}</strong>
          <p v-if="isEmpty">当前没有可供核验的能力版本，先运行知识导入。</p>
          <p v-else>
            {{ checkPassed }} / {{ summary.checks ?? checks.length }} 项检查通过
            <span v-if="result?.schema_version"
              >· schema {{ result.schema_version }}</span
            >
          </p>
        </div>
      </div>

      <div class="quality-summary" aria-label="知识完整性摘要">
        <div>
          <Database :size="15" /><strong>{{ count("cards") }}</strong
          ><span>能力卡</span>
        </div>
        <div>
          <ClipboardCheck :size="15" /><strong>{{ count("versions") }}</strong
          ><span>版本</span>
        </div>
        <div>
          <FileWarning :size="15" /><strong>{{ count("sources") }}</strong
          ><span>来源</span>
        </div>
        <div>
          <Database :size="15" /><strong>{{ count("nodes") }}</strong
          ><span>节点</span>
        </div>
        <div>
          <GitBranchIcon :size="15" /><strong>{{ count("edges") }}</strong
          ><span>关系</span>
        </div>
      </div>

      <details class="quality-details" :key="requestToken">
        <summary><ChevronRight :size="15" />逐项检查与问题明细</summary>
        <div class="quality-check-list">
          <article
            v-for="item in checks"
            :key="item.id"
            class="quality-check"
            :class="item.status"
          >
            <CheckCircle2 v-if="item.status === 'passed'" :size="15" />
            <Info v-else-if="item.status === 'not_evaluated'" :size="15" />
            <AlertTriangle v-else :size="15" />
            <div>
              <strong>{{ labelForCheck(item) }}</strong>
              <p>{{ messageFor(item) }}</p>
            </div>
            <span>{{ checkStatus(item) }}</span>
          </article>
          <p v-if="!checks.length" class="quality-empty-detail">
            没有可展示的逐项检查记录。
          </p>
        </div>
        <div v-if="issues.length || warnings.length" class="quality-issues">
          <h3><AlertTriangle :size="15" />发现的问题</h3>
          <details v-if="issues.length">
            <summary>错误 {{ issues.length }} 项（查看 JSON）</summary>
            <pre>{{ pretty(issues) }}</pre>
          </details>
          <details v-if="warnings.length">
            <summary>提示 {{ warnings.length }} 项（查看 JSON）</summary>
            <pre>{{ pretty(warnings) }}</pre>
          </details>
        </div>
      </details>
    </template>
  </section>
</template>

<style scoped>
.knowledge-quality-panel {
  padding: 22px 24px;
  margin-bottom: 22px;
}
.quality-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}
.quality-heading h2 {
  margin: 4px 0 5px;
  font-size: 17px;
}
.quality-subtitle {
  margin: 0;
  color: #82919c;
  font-size: 11px;
  line-height: 1.7;
  max-width: 680px;
}
.quality-action {
  min-width: 132px;
}
.quality-idle,
.quality-error,
.quality-status {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 18px;
  padding: 13px 15px;
  border-radius: 10px;
  font-size: 12px;
}
.quality-idle {
  background: #f6fafb;
  border: 1px dashed #dbe7eb;
  color: #607784;
}
.quality-idle svg,
.quality-error svg,
.quality-status > svg {
  flex-shrink: 0;
  margin-top: 2px;
}
.quality-idle p,
.quality-status p {
  margin: 3px 0 0;
  color: #82919c;
  font-size: 11px;
  line-height: 1.7;
}
.quality-error {
  background: #fff5f4;
  border: 1px solid #f1d2ce;
  color: #a44e46;
  align-items: center;
}
.quality-error .text-button {
  margin-left: auto;
}
.quality-status.good {
  color: #227a61;
  background: #f1faf6;
  border: 1px solid #cde9dc;
}
.quality-status.bad {
  color: #a34a42;
  background: #fff6f3;
  border: 1px solid #f0d2ca;
}
.quality-status.neutral,
.quality-status.idle {
  color: #697e8a;
  background: #f7f9fb;
  border: 1px solid #e0e8ec;
}
.quality-summary {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin-top: 14px;
}
.quality-summary > div {
  display: grid;
  grid-template-columns: auto 1fr;
  column-gap: 7px;
  row-gap: 2px;
  align-items: center;
  padding: 10px;
  border: 1px solid #edf1f3;
  border-radius: 8px;
  color: #7c8e99;
  background: #fcfdfd;
}
.quality-summary svg {
  grid-row: span 2;
  color: #0d9488;
}
.quality-summary strong {
  color: #344e5e;
  font-size: 16px;
  line-height: 1;
}
.quality-summary span {
  font-size: 10px;
}
.quality-details {
  margin-top: 15px;
  border-top: 1px solid #edf1f3;
  padding-top: 12px;
}
.quality-details > summary {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #516b7a;
  font-size: 11px;
  cursor: pointer;
  list-style: none;
}
.quality-details > summary::-webkit-details-marker {
  display: none;
}
.quality-details[open] > summary svg {
  transform: rotate(90deg);
}
.quality-check-list {
  display: grid;
  gap: 7px;
  margin-top: 12px;
}
.quality-check {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 9px;
  align-items: start;
  padding: 10px 11px;
  border: 1px solid #edf1f3;
  border-radius: 8px;
  background: #fff;
}
.quality-check.passed svg {
  color: #208a6b;
}
.quality-check.failed svg,
.quality-check.warning svg {
  color: #c27b35;
}
.quality-check strong {
  color: #445d6c;
  font-size: 11px;
}
.quality-check p {
  margin: 2px 0 0;
  color: #8796a0;
  font-size: 10px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.quality-check > span {
  color: #8796a0;
  font-size: 10px;
  white-space: nowrap;
}
.quality-check.failed > span {
  color: #b64f46;
}
.quality-check.passed > span {
  color: #2b8a6c;
}
.quality-issues {
  margin-top: 13px;
  border-top: 1px dashed #e7edef;
  padding-top: 12px;
}
.quality-issues h3 {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #687d89;
  font-size: 11px;
  margin: 0 0 8px;
}
.quality-issues details {
  margin-top: 6px;
}
.quality-issues summary {
  color: #6f828e;
  font-size: 10px;
  cursor: pointer;
}
.quality-issues pre {
  max-height: 220px;
  overflow: auto;
  padding: 11px;
  border-radius: 7px;
  background: #f7f9fb;
  color: #647986;
  font:
    10px/1.6 ui-monospace,
    SFMono-Regular,
    Menlo,
    monospace;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.quality-empty-detail {
  color: #8796a0;
  font-size: 11px;
  margin: 4px 0;
}
@media (max-width: 760px) {
  .knowledge-quality-panel {
    padding: 18px;
  }
  .quality-heading {
    flex-direction: column;
  }
  .quality-action {
    width: 100%;
  }
  .quality-summary {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .quality-summary > div {
    padding: 8px;
  }
  .quality-summary strong {
    font-size: 14px;
  }
}
</style>
