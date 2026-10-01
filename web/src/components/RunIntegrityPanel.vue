<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Code2,
  Database,
  FileCheck2,
  FileText,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from "@lucide/vue";
import { api, ApiError } from "../lib/api";
import type { Json } from "../lib/format";

const props = defineProps<{ runId: string }>();

interface Artifact {
  path?: string;
  kind?: string;
  size_bytes?: number;
  sha256?: string | null;
  expected_sha256?: string | null;
  recorded_sha256?: string | null;
  integrity?: string;
  matches_recorded?: boolean | null;
  error?: string;
}

const result = ref<Json | null>(null);
const loading = ref(false);
const error = ref("");
let controller: AbortController | undefined;
let requestToken = 0;
let disposed = false;

const artifacts = computed<Artifact[]>(() =>
  Array.isArray(result.value?.artifacts)
    ? result.value.artifacts.filter(
        (item: unknown): item is Artifact => !!item && typeof item === "object",
      )
    : [],
);
const missing = computed<string[]>(() =>
  Array.isArray(result.value?.missing_expected_paths)
    ? result.value.missing_expected_paths.map(String).filter(Boolean)
    : [],
);
const status = computed(() => String(result.value?.status || "idle"));
const unrecordedCount = computed(
  () =>
    artifacts.value.filter(
      (item) =>
        !hasRecordedHash(item.expected_sha256 || item.recorded_sha256) &&
        integrity(item) !== "mismatch",
    ).length,
);
const statusText = computed(
  () =>
    ({
      complete: unrecordedCount.value
        ? "预期制品清单完整，部分未留预期哈希"
        : "预期制品清单完整",
      partial: "制品证据不完整",
      missing: "运行制品缺失",
      failed: "制品核验失败",
      idle: "尚未核验制品",
    })[status.value] || "制品核验结果已返回",
);
const statusClass = computed(() =>
  status.value === "complete"
    ? unrecordedCount.value
      ? "idle"
      : "good"
    : status.value === "idle"
      ? "idle"
      : "bad",
);
const verifiedCount = computed(
  () => artifacts.value.filter((item) => integrity(item) === "verified").length,
);
const failedCount = computed(
  () =>
    artifacts.value.filter(
      (item) => integrity(item) === "mismatch" || item.error,
    ).length,
);
const hasResult = computed(() => !!result.value);
const categoryLabels: Record<string, string> = {
  input: "输入数据",
  code: "生成代码",
  validation: "验证证据",
  report: "报告制品",
};
const categoryIcons: Record<string, unknown> = {
  input: Database,
  code: Code2,
  validation: ClipboardCheck,
  report: FileText,
};
const checkPath = (value: unknown) => {
  const path = String(value || "").replace(/[\u0000-\u001f]/g, "");
  if (
    !path ||
    path.length > 240 ||
    path.startsWith("/") ||
    path.includes("..") ||
    /[:\\]|\b(?:sk|pk)-[a-z0-9_-]{8,}/i.test(path)
  )
    return "未记录路径";
  return path;
};
const checkHash = (value: unknown) =>
  typeof value === "string" && /^[0-9a-f]{64}$/i.test(value) ? value : "未记录";
const hasRecordedHash = (value: unknown) =>
  typeof value === "string" && /^[0-9a-f]{64}$/i.test(value);
const formatBytes = (value: unknown) => {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0)
    return "—";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KiB`;
  return `${(value / 1024 / 1024).toFixed(1)} MiB`;
};
function integrity(item: Artifact) {
  if (["missing", "not_found", "file_missing"].includes(String(item.error)))
    return "missing";
  if (item.error) return "read_error";
  if (["verified", "mismatch", "unrecorded"].includes(String(item.integrity)))
    return String(item.integrity);
  if (item.matches_recorded === true) return "verified";
  if (item.matches_recorded === false) return "mismatch";
  return "unrecorded";
}
function integrityLabel(item: Artifact) {
  return (
    (
      {
        verified: "哈希一致",
        mismatch: "哈希不一致",
        missing: "制品缺失",
        read_error: "读取失败",
        unrecorded: "未记录预期哈希",
      } as Record<string, string>
    )[integrity(item)] || "未记录"
  );
}
function integrityClass(item: Artifact) {
  return integrity(item);
}
function categoryLabel(value: unknown) {
  return categoryLabels[String(value || "")] || "其他制品";
}
function categoryIcon(value: unknown) {
  return categoryIcons[String(value || "")] || FileCheck2;
}
function abortRequest() {
  controller?.abort();
  controller = undefined;
}
function errorLabel(item: Artifact) {
  if (["missing", "not_found", "file_missing"].includes(String(item.error)))
    return "预期路径下未找到制品文件。";
  if (item.error === "size_limit" || item.error === "total_size_limit")
    return "读取达到资源上限，本次未完成文件核验。";
  return "无法安全读取此制品，请检查文件状态后重新核验。";
}
function resetForRun() {
  requestToken += 1;
  abortRequest();
  result.value = null;
  error.value = "";
  loading.value = false;
}
async function verifyIntegrity() {
  if (!props.runId) return;
  abortRequest();
  const run = props.runId;
  const token = ++requestToken;
  const request = new AbortController();
  controller = request;
  loading.value = true;
  error.value = "";
  try {
    const value = await api<Json>(
      `/runs/${encodeURIComponent(run)}/reproducibility`,
      { signal: request.signal },
    );
    if (
      disposed ||
      token !== requestToken ||
      request.signal.aborted ||
      run !== props.runId
    )
      return;
    if (value.run_id !== run) throw new Error("Run identity mismatch");
    result.value = value;
  } catch (cause) {
    if (
      disposed ||
      token !== requestToken ||
      request.signal.aborted ||
      run !== props.runId
    )
      return;
    error.value =
      cause instanceof ApiError && cause.status === 404
        ? "当前运行或制品核验接口不可用，请检查运行记录与服务版本。"
        : "制品核验暂未完成，请检查服务状态后重试。";
    result.value = null;
  } finally {
    if (!disposed && token === requestToken && run === props.runId)
      loading.value = false;
  }
}

watch(() => props.runId, resetForRun);
onBeforeUnmount(() => {
  disposed = true;
  requestToken += 1;
  abortRequest();
});
</script>

<template>
  <section class="run-integrity-panel panel" data-testid="run-integrity-panel">
    <div class="integrity-heading">
      <div>
        <p class="eyebrow">ARTIFACT INTEGRITY</p>
        <h2>制品哈希与来源完整性</h2>
        <p class="integrity-subtitle">
          对输入、代码、验证证据和报告逐项计算
          SHA-256，并与运行记录中的预期指纹比对。
        </p>
      </div>
      <button
        class="btn btn-ghost integrity-action"
        :disabled="loading || !props.runId"
        @click="verifyIntegrity"
      >
        <LoaderCircle v-if="loading" :size="15" class="spinning" />
        <RefreshCw v-else :size="15" />
        {{ loading ? "正在核验…" : hasResult ? "重新核验" : "核验制品完整性" }}
      </button>
    </div>

    <div v-if="error" class="integrity-error" role="alert">
      <XCircle :size="17" /><span>{{ error }}</span>
      <button class="text-button" @click="verifyIntegrity">重试</button>
    </div>

    <div v-if="!hasResult && !error" class="integrity-idle">
      <ShieldCheck :size="23" />
      <div>
        <strong>核验按需执行</strong>
        <p>
          查看报告不会重复扫描文件；需要复核来源时，点击按钮生成一次只读制品清单。
        </p>
      </div>
    </div>

    <template v-if="hasResult">
      <div class="integrity-status" :class="statusClass">
        <CheckCircle2 v-if="statusClass === 'good'" :size="18" />
        <AlertTriangle v-else :size="18" />
        <div>
          <strong>{{ statusText }}</strong>
          <p>
            {{ result?.artifact_count ?? artifacts.length }} 个制品 ·
            {{ verifiedCount }} 项哈希一致
            <span v-if="failedCount"> · {{ failedCount }} 项需要处理</span>
            <span v-if="result?.truncated"> · 结果已截断</span>
          </p>
          <p v-if="unrecordedCount">
            {{ unrecordedCount }}
            项未记录预期哈希，仅保存当前文件指纹，尚无一致性结论。
          </p>
          <p v-if="status === 'complete'">
            清单完整表示预期文件已读取；哈希一致性以逐项比对结果为准。
          </p>
        </div>
      </div>

      <details class="integrity-details" :key="requestToken">
        <summary><ChevronRight :size="15" />查看四类制品的核验明细</summary>
        <div class="artifact-list">
          <article
            v-for="(item, index) in artifacts"
            :key="`${item.path}-${index}`"
            class="artifact-row"
            :class="integrityClass(item)"
          >
            <component
              :is="categoryIcon(item.kind)"
              :size="16"
              class="artifact-icon"
            />
            <div class="artifact-main">
              <div class="artifact-title">
                <strong>{{ categoryLabel(item.kind) }}</strong
                ><span>{{ integrityLabel(item) }}</span>
              </div>
              <p class="artifact-path">
                {{ checkPath(item.path) }} · {{ formatBytes(item.size_bytes) }}
              </p>
              <details class="artifact-hashes">
                <summary>查看哈希与来源记录</summary>
                <dl>
                  <div>
                    <dt>实际 SHA-256</dt>
                    <dd>{{ checkHash(item.sha256) }}</dd>
                  </div>
                  <div>
                    <dt>预期 SHA-256</dt>
                    <dd>
                      {{
                        checkHash(item.expected_sha256 || item.recorded_sha256)
                      }}
                    </dd>
                  </div>
                </dl>
                <p v-if="item.error" class="artifact-error">
                  {{ errorLabel(item) }}
                </p>
              </details>
            </div>
          </article>
          <p v-if="!artifacts.length" class="integrity-empty">
            没有可核验的制品记录。
          </p>
        </div>
        <details v-if="missing.length" class="missing-paths">
          <summary>
            <AlertTriangle :size="14" />缺少预期制品 {{ missing.length }} 项
          </summary>
          <ul>
            <li v-for="path in missing" :key="path">{{ checkPath(path) }}</li>
          </ul>
        </details>
      </details>
    </template>
  </section>
</template>

<style scoped>
.run-integrity-panel {
  padding: 22px 24px;
}
.integrity-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}
.integrity-heading h2 {
  margin: 4px 0 5px;
  font-size: 17px;
}
.integrity-subtitle {
  margin: 0;
  color: #82919c;
  font-size: 11px;
  line-height: 1.7;
  max-width: 680px;
}
.integrity-action {
  min-width: 132px;
}
.integrity-idle,
.integrity-error,
.integrity-status {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 18px;
  padding: 13px 15px;
  border-radius: 10px;
  font-size: 12px;
}
.integrity-idle {
  background: #f6fafb;
  border: 1px dashed #dbe7eb;
  color: #607784;
}
.integrity-idle svg,
.integrity-error svg,
.integrity-status > svg {
  flex-shrink: 0;
  margin-top: 2px;
}
.integrity-idle p,
.integrity-status p {
  margin: 3px 0 0;
  color: #82919c;
  font-size: 11px;
  line-height: 1.7;
}
.integrity-error {
  background: #fff5f4;
  border: 1px solid #f1d2ce;
  color: #a44e46;
  align-items: center;
}
.integrity-error .text-button {
  margin-left: auto;
}
.integrity-status.good {
  color: #227a61;
  background: #f1faf6;
  border: 1px solid #cde9dc;
}
.integrity-status.bad {
  color: #a34a42;
  background: #fff6f3;
  border: 1px solid #f0d2ca;
}
.integrity-status.idle {
  color: #697e8a;
  background: #f7f9fb;
  border: 1px solid #e0e8ec;
}
.integrity-details {
  margin-top: 15px;
  border-top: 1px solid #edf1f3;
  padding-top: 12px;
}
.integrity-details > summary,
.missing-paths > summary,
.artifact-hashes > summary {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #516b7a;
  font-size: 11px;
  cursor: pointer;
  list-style: none;
}
.integrity-details > summary::-webkit-details-marker,
.missing-paths > summary::-webkit-details-marker,
.artifact-hashes > summary::-webkit-details-marker {
  display: none;
}
.integrity-details[open] > summary svg {
  transform: rotate(90deg);
}
.artifact-list {
  display: grid;
  gap: 7px;
  margin-top: 12px;
}
.artifact-row {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  padding: 11px;
  border: 1px solid #edf1f3;
  border-radius: 8px;
  background: #fff;
}
.artifact-row.verified .artifact-icon {
  color: #23886b;
}
.artifact-row.mismatch .artifact-icon {
  color: #b64f46;
}
.artifact-row.unrecorded .artifact-icon {
  color: #b47d37;
}
.artifact-row.missing .artifact-icon,
.artifact-row.read_error .artifact-icon {
  color: #b64f46;
}
.artifact-main {
  min-width: 0;
}
.artifact-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.artifact-title strong {
  color: #445d6c;
  font-size: 11px;
}
.artifact-title span {
  color: #7a8b95;
  font-size: 10px;
  white-space: nowrap;
}
.artifact-row.mismatch .artifact-title span {
  color: #b64f46;
}
.artifact-row.verified .artifact-title span {
  color: #278669;
}
.artifact-path {
  margin: 3px 0 7px;
  color: #8796a0;
  font-size: 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  overflow-wrap: anywhere;
}
.artifact-hashes {
  border-top: 1px dashed #e8edef;
  padding-top: 7px;
}
.artifact-hashes > summary {
  font-size: 10px;
  color: #738792;
}
.artifact-hashes dl {
  display: grid;
  gap: 4px;
  margin: 7px 0 0;
}
.artifact-hashes dl > div {
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: 8px;
  font-size: 9px;
}
.artifact-hashes dt {
  color: #8a99a2;
}
.artifact-hashes dd {
  color: #647986;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  margin: 0;
  overflow-wrap: anywhere;
}
.artifact-error {
  margin: 6px 0 0;
  color: #a34a42;
  font-size: 10px;
}
.missing-paths {
  margin-top: 12px;
  border-top: 1px dashed #ebd8d3;
  padding-top: 10px;
}
.missing-paths > summary {
  color: #a34a42;
}
.missing-paths ul {
  margin: 7px 0 0;
  padding-left: 21px;
  color: #a34a42;
  font:
    10px/1.7 ui-monospace,
    SFMono-Regular,
    Menlo,
    monospace;
}
.integrity-empty {
  color: #8796a0;
  font-size: 11px;
  margin: 4px 0;
}
@media (max-width: 760px) {
  .run-integrity-panel {
    padding: 18px;
  }
  .integrity-heading {
    flex-direction: column;
  }
  .integrity-action {
    width: 100%;
  }
  .artifact-title {
    align-items: flex-start;
    flex-direction: column;
    gap: 3px;
  }
  .artifact-hashes dl > div {
    grid-template-columns: 1fr;
    gap: 2px;
  }
}
</style>
