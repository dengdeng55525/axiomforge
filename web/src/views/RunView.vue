<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronRight,
  Circle,
  CircleAlert,
  Code2,
  Copy,
  Download,
  ExternalLink,
  FileJson,
  FileText,
  GitBranch,
  Layers3,
  LoaderCircle,
  Network,
  PauseCircle,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Timer,
  XCircle,
} from "@lucide/vue";
import { api, download } from "../lib/api";
import {
  type Json,
  dateTime,
  datasetLabel,
  errorText,
  metric,
  modeLabel,
  shortId,
  stateLabel,
} from "../lib/format";

const route = useRoute();
const report = ref<Json | null>(null);
const loading = ref(true);
const loadError = ref("");
const actionError = ref("");
const notice = ref("");
const actionBusy = ref("");
const inspectedId = ref("");
const code = ref("");
const codeLoading = ref(false);
const codeError = ref("");
const codeVisible = ref(false);
const cancelRequested = ref(false);
let pollTimer: ReturnType<typeof setTimeout> | undefined;
let reportController: AbortController | undefined;
let codeController: AbortController | undefined;
let disposed = false;
const runId = computed(() => String(route.params.id || ""));
const arr = (value: unknown): Json[] =>
  Array.isArray(value)
    ? value.filter((item) => item && typeof item === "object")
    : [];
const list = (value: unknown): unknown[] => (Array.isArray(value) ? value : []);
const finite = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);
const textValue = (value: unknown) =>
  typeof value === "string"
    ? value
    : JSON.stringify(value, null, 2) || "未记录";
const pretty = (value: unknown) => JSON.stringify(value ?? {}, null, 2);
const statusName = (value: unknown) =>
  value === "finalizing" ? "正在归档" : stateLabel(value);
const activeStatus = (value: unknown) =>
  ["queued", "running", "finalizing"].includes(String(value));
const isActive = computed(() => activeStatus(report.value?.status));
const candidates = computed(() => arr(report.value?.candidates));
const selected = computed(() =>
  candidates.value.find(
    (item) => item.candidate_id === report.value?.selected_candidate_id,
  ),
);
const inspected = computed(() =>
  candidates.value.find((item) => item.candidate_id === inspectedId.value),
);
const metrics = computed<Json>(() => selected.value?.metrics || {});
const passedCount = computed(
  () => candidates.value.filter((item) => item.status === "passed").length,
);
const events = computed(() => arr(report.value?.events));
const evidence = computed(() => arr(report.value?.evidence));
const attempts = computed(() => arr(inspected.value?.attempts));
const repairs = computed(() => arr(inspected.value?.repairs));
const selectedEvidence = computed(() => {
  const ids = list(inspected.value?.plan?.evidence_ids);
  return ids.length
    ? evidence.value.filter((item) =>
        ids.includes(item.capability_id || item.id),
      )
    : evidence.value;
});
const primaryLabel = computed(() =>
  report.value?.task_spec?.primary_metric === "average_precision" ||
  !report.value?.task_spec?.primary_metric
    ? "平均精度 AP"
    : String(report.value.task_spec.primary_metric),
);
const primaryValue = computed(
  () =>
    metrics.value[
      report.value?.task_spec?.primary_metric || "average_precision"
    ],
);
const quality = (value: unknown) =>
  ({
    above_prevalence: "AP 高于基线",
    at_or_below_prevalence: "AP 未超过基线",
    below_prevalence: "AP 未超过基线",
    baseline_or_worse: "AP 未超过基线",
    not_evaluated: "质量尚未评估",
  })[String(value)] || "质量尚未评估";
const reportHeading = computed(() => {
  const status = report.value?.status;
  if (status === "queued") return "任务已进入队列";
  if (status === "running") return "Agent 正在构建与验证算法";
  if (status === "finalizing") return "评估已结束，正在归档证据";
  if (status === "cancelled") return "运行已取消，已产生的证据仍可查看";
  if (status === "failed") return "本次运行未完成验证目标";
  if (status === "passed" && selected.value) return "算法验证完成，报告已就绪";
  return "运行记录与验证报告";
});
const headline = computed(() => {
  if (isActive.value)
    return "页面会随真实执行事件自动更新。候选完成评估后，将展示验证结果与选择依据。";
  if (report.value?.status !== "passed")
    return (
      report.value?.failure_reason ||
      "当前没有可交付的最终验证结论，请展开执行证据查看已完成的检查。"
    );
  if (!selected.value) return "记录中缺少选中候选，无法给出最终算法结论。";
  const base = metrics.value.dummy_average_precision;
  return `本次选中 ${algorithmName(selected.value)}，${primaryLabel.value} 为 ${metric(primaryValue.value)}${finite(base) ? `，类别占比基线为 ${metric(base)}` : ""}。${quality(selected.value.quality_status || report.value?.quality_status)}。`;
});
const recommendation = computed(() => {
  if (report.value?.status !== "passed" || !selected.value)
    return "先查看失败原因或已完成的候选检查，调整需求或配置后重新运行。";
  if (report.value?.mode === "mock" || report.value?.provider === "mock")
    return "当前是 Mock 工程流程演示。可检查生成代码与验证链路；LLM 生成能力需要切换真实接口后单独评估。";
  if (selected.value.quality_status !== "above_prevalence")
    return "当前 AP 未证实超过基线，建议继续检查特征、数据划分与候选方案，再进行独立评估。";
  if (metrics.value.f1_threshold_0_5 === 0)
    return "可继续评估概率排序效果。当前阈值 0.5 下 F1 为 0，投入业务前需要选择阈值并完成独立测试。";
  return "可进入代码审查与独立测试阶段。当前结果来自验证集，仍需确认业务阈值、泛化表现与部署条件。";
});
function algorithmName(candidate: Json) {
  const name = (
    {
      logistic: "逻辑回归",
      forest: "随机森林",
      random_forest: "随机森林",
      naive_bayes: "朴素贝叶斯",
      nb: "朴素贝叶斯",
    } as Record<string, string>
  )[candidate.plan?.algorithm];
  return (
    name ||
    candidate.model_metadata?.classifier_class ||
    candidate.plan?.algorithm ||
    candidate.candidate_id ||
    "未命名候选"
  );
}
function variantName(candidate: Json) {
  return (
    (
      {
        default: "默认方案",
        balanced: "类别平衡",
        regularized: "正则化",
        shallower: "浅层树",
      } as Record<string, string>
    )[candidate.plan?.variant] ||
    candidate.plan?.variant ||
    "方案"
  );
}
const tone = (value: unknown) =>
  value === "passed" || value === "above_prevalence"
    ? "good"
    : ["failed", "error"].includes(String(value))
      ? "bad"
      : ["running", "queued", "finalizing"].includes(String(value))
        ? "working"
        : "neutral";
const signed = (value: unknown) =>
  finite(value) ? `${value >= 0 ? "+" : ""}${metric(value)}` : "—";
const scoreWidth = (value: unknown) =>
  finite(value) ? `${Math.max(0, Math.min(value, 1)) * 100}%` : "0%";
const liftMaximum = computed(() =>
  Math.max(
    1,
    ...candidates.value.map((item) =>
      finite(item.metrics?.lift_at_10pct) ? item.metrics.lift_at_10pct : 0,
    ),
  ),
);
const liftWidth = (value: unknown) =>
  finite(value) ? `${(Math.max(0, value) / liftMaximum.value) * 100}%` : "0%";
const checkNames: Record<string, string> = {
  source_policy: "代码构造器安全策略",
  plan_consistency: "代码与计划一致",
  dataset_integrity: "数据完整性与划分",
  labels_withheld: "验证标签隔离",
  worker_execution: "独立进程执行",
  prediction_contract: "概率输出与行标识",
  single_row: "单条预测一致",
  repeat_prediction: "重复预测稳定",
  empty_batch_wrapper: "空批次处理",
  unknown_category: "未知类别处理",
  missing_numeric: "缺失数值处理",
  empty_text: "空文本处理",
  clean_environment: "执行环境隔离",
  ap_above_dummy: "AP 超过类别占比基线",
  host_evaluation: "独立宿主评分",
  variant_consistency: "参数变体一致",
  candidate_diversity: "候选差异性",
};
const dimensions = computed(() => {
  const checks = arr(inspected.value?.checks);
  const textTask =
    report.value?.task_spec?.task_type === "text_binary_classification" ||
    report.value?.dataset_id === "sms";
  const groups = [
    {
      title: "功能正确性",
      note: "计划、数据与独立评分",
      keys: [
        "source_policy",
        "plan_consistency",
        "dataset_integrity",
        "labels_withheld",
        "host_evaluation",
      ],
    },
    {
      title: "接口规范",
      note: "概率输出、单条与空批次",
      keys: ["prediction_contract", "single_row", "empty_batch_wrapper"],
    },
    {
      title: "运行稳定性",
      note: "进程执行与边界输入",
      keys: [
        "worker_execution",
        "repeat_prediction",
        "clean_environment",
        ...(textTask
          ? ["empty_text"]
          : ["unknown_category", "missing_numeric"]),
      ],
    },
    {
      title: "指标表现",
      note: "验证集 AP 建议性门槛",
      keys: ["ap_above_dummy"],
    },
  ];
  return groups.map((group) => {
    const items = checks.filter((item) => group.keys.includes(item.name));
    const failed = items.some((item) => item.passed === false);
    const passed = items.filter((item) => item.passed === true).length;
    const complete =
      passed === group.keys.length && items.length === group.keys.length;
    return {
      ...group,
      items,
      passed,
      state: failed ? "failed" : complete ? "passed" : "unknown",
      label: failed
        ? "存在未通过项"
        : complete
          ? "已记录通过"
          : items.length
            ? "检查未完整"
            : "尚无检查记录",
    };
  });
});
const stages = computed(() => {
  const types = new Set(
    events.value.map((item) => item.event_type || item.type),
  );
  const hasRole = (role: string) =>
    events.value.some((item) => item.data?.role === role);
  return [
    { title: "理解需求", done: types.has("SPEC_VALIDATED"), disabled: false },
    {
      title: "检索知识",
      done:
        types.has("KNOWLEDGE_RETRIEVED") &&
        report.value?.request?.use_retrieval !== false,
      disabled: report.value?.request?.use_retrieval === false,
    },
    {
      title: "规划方案",
      done: types.has("CANDIDATE_PLANNED"),
      disabled: false,
    },
    {
      title: "生成代码",
      done: types.has("VALIDATING") || hasRole("coder"),
      disabled: false,
    },
    { title: "自动验证", done: types.has("VERIFIED"), disabled: false },
    {
      title: "修复优化",
      done: types.has("REPAIR_PLANNED") || types.has("BEAM_EXPANDED"),
      disabled:
        !types.has("REPAIR_PLANNED") &&
        !types.has("BEAM_EXPANDED") &&
        !isActive.value,
    },
    {
      title: "知识沉淀",
      done:
        types.has("RECORDED") &&
        report.value?.knowledge_writeback?.run_saved === true,
      disabled: false,
    },
    {
      title: "形成报告",
      done: !isActive.value && !!report.value?.finished_at,
      disabled: false,
    },
  ];
});
const eventNames: Record<string, string> = {
  RECEIVED: "接收任务",
  SPEC_VALIDATED: "需求校验完成",
  KNOWLEDGE_RETRIEVED: "检索能力知识",
  CANDIDATE_PLANNED: "规划候选方案",
  LLM_RESPONSE: "模型响应",
  VALIDATING: "开始验证",
  VERIFIED: "候选验证结束",
  REPAIR_PLANNED: "生成修复方案",
  BEAM_EXPANDED: "扩展搜索候选",
  COMPARED: "完成候选比较",
  RECORDED: "写入知识库",
  FAILURE_INJECTED: "注入演示故障",
  PLAN_REJECTED: "计划被校验拒绝",
  RESPONSE_SCHEMA_REJECTED: "模型响应格式未通过",
};
const roleNames: Record<string, string> = {
  interpreter: "需求理解",
  planner: "方案规划",
  coder: "代码生成",
  repair_coder: "代码修复",
  reviewer: "错误诊断",
  curator: "结果总结",
};
const currentActivity = computed(() => {
  const last = events.value.at(-1);
  return last
    ? `${eventNames[last.event_type || last.type] || last.event_type || last.type}${last.data?.candidate_id ? ` · ${last.data.candidate_id}` : ""}`
    : "等待执行事件";
});
function evidenceNode(item: Json) {
  return `capability:${item.capability_id || item.id}:v${item.version || 1}`;
}
function safeSource(value: unknown) {
  if (typeof value !== "string") return undefined;
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) &&
      !url.username &&
      !url.password
      ? url.href
      : undefined;
  } catch {
    return undefined;
  }
}
function stopPolling() {
  if (pollTimer) clearTimeout(pollTimer);
  pollTimer = undefined;
}
async function refresh(initial = false) {
  stopPolling();
  reportController?.abort();
  const controller = new AbortController();
  reportController = controller;
  const identity = runId.value;
  if (initial) loading.value = true;
  try {
    const result = await api<Json>(`/runs/${encodeURIComponent(identity)}`, {
      signal: controller.signal,
    });
    if (disposed || controller.signal.aborted || identity !== runId.value)
      return;
    report.value = result;
    loadError.value = "";
    if (
      !candidates.value.some((item) => item.candidate_id === inspectedId.value)
    )
      inspectedId.value =
        result.selected_candidate_id || candidates.value[0]?.candidate_id || "";
    if (activeStatus(result.status))
      pollTimer = setTimeout(() => void refresh(), 2500);
  } catch (error) {
    if (disposed || controller.signal.aborted || identity !== runId.value)
      return;
    loadError.value = errorText(error);
    if (isActive.value) pollTimer = setTimeout(() => void refresh(), 5000);
  } finally {
    if (!disposed && !controller.signal.aborted && identity === runId.value)
      loading.value = false;
  }
}
async function cancel() {
  if (!isActive.value || cancelRequested.value || actionBusy.value) return;
  const identity = runId.value;
  actionBusy.value = "cancel";
  actionError.value = "";
  notice.value = "";
  try {
    const result = await api<Json>(
      `/runs/${encodeURIComponent(identity)}/cancel`,
      { method: "POST" },
    );
    if (identity !== runId.value || disposed) return;
    cancelRequested.value = result.cancel_requested === true;
    notice.value = result.cancel_requested
      ? "已提交取消请求，正在等待当前步骤安全结束。"
      : "任务状态已变化，正在刷新结果。";
    await refresh();
  } catch (error) {
    if (identity === runId.value && !disposed)
      actionError.value = errorText(error);
  } finally {
    if (identity === runId.value) actionBusy.value = "";
  }
}
async function saveReport(kind: "json" | "md") {
  const identity = runId.value;
  actionBusy.value = kind;
  actionError.value = "";
  try {
    await download(
      `/runs/${encodeURIComponent(identity)}/${kind === "json" ? "report" : "report.md"}`,
      `algoforge-${identity}.${kind}`,
    );
  } catch (error) {
    if (identity === runId.value && !disposed)
      actionError.value = errorText(error);
  } finally {
    if (identity === runId.value) actionBusy.value = "";
  }
}
async function copyId() {
  try {
    await navigator.clipboard.writeText(runId.value);
    notice.value = "已复制完整运行 ID。";
  } catch {
    actionError.value = "浏览器未允许复制，请从下方运行标识选中并复制。";
  }
}
function openHtml() {
  window.open(
    `/runs/${encodeURIComponent(runId.value)}/report.html`,
    "_blank",
    "noopener,noreferrer",
  );
}
async function loadCode() {
  codeController?.abort();
  code.value = "";
  codeError.value = "";
  if (!codeVisible.value || !inspected.value?.artifact_id) {
    codeLoading.value = false;
    return;
  }
  const controller = new AbortController();
  codeController = controller;
  const identity = runId.value;
  const candidate = inspectedId.value;
  codeLoading.value = true;
  try {
    const result = await api<Json>(
      `/runs/${encodeURIComponent(identity)}/artifacts/${encodeURIComponent(inspected.value.artifact_id)}`,
      { signal: controller.signal },
    );
    if (
      !disposed &&
      !controller.signal.aborted &&
      identity === runId.value &&
      candidate === inspectedId.value
    )
      code.value = result.code || "";
  } catch (error) {
    if (
      !disposed &&
      !controller.signal.aborted &&
      identity === runId.value &&
      candidate === inspectedId.value
    )
      codeError.value = errorText(error);
  } finally {
    if (!controller.signal.aborted) codeLoading.value = false;
  }
}
function toggleCode(event: Event) {
  codeVisible.value = (event.target as HTMLDetailsElement).open;
  void loadCode();
}
function saveCode() {
  const url = URL.createObjectURL(
    new Blob([code.value], { type: "text/x-python;charset=utf-8" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${inspectedId.value.replace(/[^a-zA-Z0-9_-]/g, "_")}.py`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
watch(
  () =>
    [
      runId.value,
      inspectedId.value,
      inspected.value?.artifact_id,
      inspected.value?.code_sha256,
    ].join("/"),
  () => {
    code.value = "";
    void loadCode();
  },
);
watch(
  runId,
  () => {
    stopPolling();
    reportController?.abort();
    codeController?.abort();
    report.value = null;
    inspectedId.value = "";
    code.value = "";
    codeError.value = "";
    codeVisible.value = false;
    loadError.value = "";
    actionError.value = "";
    notice.value = "";
    actionBusy.value = "";
    cancelRequested.value = false;
    void refresh(true);
  },
  { immediate: true },
);
onBeforeUnmount(() => {
  disposed = true;
  stopPolling();
  reportController?.abort();
  codeController?.abort();
});
</script>

<template>
  <div class="run-page">
    <div class="page-heading report-page-heading">
      <div>
        <RouterLink to="/history" class="back-link"
          ><ArrowLeft :size="15" /> 所有运行</RouterLink
        >
        <p class="eyebrow">VALIDATION REPORT</p>
        <h1>验证报告</h1>
        <p class="muted">从算法选择到可复核的验证证据。</p>
      </div>
      <div v-if="report" class="report-actions">
        <button class="btn btn-ghost" @click="copyId">
          <Copy :size="15" /> 复制 ID
        </button>
        <button
          class="btn btn-ghost"
          :disabled="!!actionBusy"
          @click="saveReport('md')"
        >
          <Download :size="15" /> Markdown
        </button>
        <button
          class="btn btn-ghost"
          :disabled="!!actionBusy"
          @click="saveReport('json')"
        >
          <FileJson :size="15" /> JSON
        </button>
        <button class="btn btn-primary" @click="openHtml">
          <ExternalLink :size="15" /> 打开 / 打印报告
        </button>
      </div>
    </div>
    <div v-if="loadError" class="message-box bad" role="alert">
      <CircleAlert :size="19" />
      <div>
        <strong>未能获取最新运行记录</strong>
        <p>
          {{ loadError }}{{ report ? " 页面保留上次成功获取的数据。" : "" }}
        </p>
      </div>
      <button class="btn btn-ghost" @click="refresh(!report)">重试</button>
    </div>
    <div v-if="actionError" class="message-box bad" role="alert">
      <CircleAlert :size="18" />
      <p>{{ actionError }}</p>
      <button
        class="icon-button"
        aria-label="关闭提示"
        @click="actionError = ''"
      >
        <XCircle :size="17" />
      </button>
    </div>
    <div v-if="notice" class="message-box neutral" role="status">
      <CheckCircle2 :size="18" />
      <p>{{ notice }}</p>
    </div>
    <div v-if="loading" class="panel empty-state">
      <LoaderCircle class="spin" :size="26" />
      <h2>正在读取验证报告</h2>
      <p class="muted">加载候选结果、指标和执行证据。</p>
    </div>
    <div v-else-if="!report && !loadError" class="panel empty-state">
      <FileText :size="30" />
      <h2>尚无运行记录</h2>
      <RouterLink class="btn btn-primary" to="/workbench">创建任务</RouterLink>
    </div>
    <template v-if="report">
      <section class="panel result-hero" :class="tone(report.status)">
        <div class="result-topline">
          <div class="result-badges">
            <span class="badge" :class="tone(report.status)"
              ><LoaderCircle
                v-if="isActive"
                :size="13"
                class="spin"
              /><CheckCircle2
                v-else-if="report.status === 'passed'"
                :size="13"
              /><XCircle
                v-else-if="report.status === 'failed'"
                :size="13"
              /><PauseCircle v-else :size="13" />{{
                statusName(report.status)
              }}</span
            ><span class="badge mode-badge">{{ modeLabel(report) }}</span
            ><span class="muted">{{ datasetLabel(report.dataset_id) }}</span>
          </div>
          <span class="run-identity" :title="runId"
            >RUN {{ shortId(runId) }} · {{ dateTime(report.created_at) }}</span
          >
        </div>
        <div class="result-heading">
          <div>
            <h2>{{ reportHeading }}</h2>
            <p class="headline">{{ headline }}</p>
          </div>
          <div class="result-mark">
            <LoaderCircle v-if="isActive" class="spin" :size="35" /><ShieldCheck
              v-else-if="report.status === 'passed'"
              :size="35"
            /><CircleAlert v-else :size="35" />
          </div>
        </div>
        <div v-if="isActive" class="live-activity" role="status">
          <span class="live-dot"></span>{{ currentActivity
          }}<button
            v-if="report.status !== 'finalizing'"
            class="btn btn-ghost"
            :disabled="cancelRequested || !!actionBusy"
            @click="cancel"
          >
            <PauseCircle :size="15" />{{
              cancelRequested ? "正在取消…" : "取消运行"
            }}</button
          ><span v-else class="muted">正在保存报告</span>
        </div>
        <div v-else class="decision-note">
          <Sparkles :size="18" />
          <div>
            <strong>下一步建议</strong>
            <p>{{ recommendation }}</p>
          </div>
          <RouterLink
            class="btn btn-ghost"
            :to="{ path: '/workbench', query: { from: runId } }"
            ><RefreshCw :size="14" />调整后重试</RouterLink
          >
        </div>
      </section>

      <div class="report-metrics">
        <article class="panel metric-card primary-metric">
          <span>{{ primaryLabel }}</span
          ><strong>{{ metric(primaryValue) }}</strong
          ><small>选中候选 · 验证集</small>
        </article>
        <article class="panel metric-card">
          <span>类别占比基线</span
          ><strong>{{ metric(metrics.dummy_average_precision) }}</strong
          ><small>Dummy AP · 同一验证集</small>
        </article>
        <article class="panel metric-card">
          <span>AP 较基线提升</span
          ><strong
            :class="
              finite(metrics.ap_improvement_over_dummy) &&
              metrics.ap_improvement_over_dummy > 0
                ? 'positive-value'
                : ''
            "
            >{{ signed(metrics.ap_improvement_over_dummy) }}</strong
          ><small>AP 绝对差值</small>
        </article>
        <article class="panel metric-card">
          <span>候选通过检查</span
          ><strong
            >{{ passedCount }}<em> / {{ candidates.length }}</em></strong
          ><small>功能与接口通过 ≠ 生产就绪</small>
        </article>
      </div>
      <p class="evaluation-note">
        <CircleAlert :size="15" />{{
          report.provenance?.sealed_test_scored === false ||
          metrics.sealed_test_scored === false
            ? "当前仅展示验证集指标，封存测试集尚未评分。"
            : "评估范围请以数据溯源记录为准；缺失指标不视为通过。"
        }}
        <span v-if="report.mode === 'mock' || report.provider === 'mock'"
          >Mock 模式不代表真实 LLM 效果。</span
        >
      </p>

      <section class="panel candidate-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">CANDIDATE COMPARISON</p>
            <h2>候选方案比较</h2>
            <p class="muted">先查看比较结果，再选择一个候选检查代码与证据。</p>
          </div>
          <span class="badge">{{ candidates.length }} 个候选</span>
        </div>
        <div v-if="!candidates.length" class="empty-state compact-empty">
          <Layers3 :size="28" />
          <h3>{{ isActive ? "候选方案正在准备中" : "本次未生成候选" }}</h3>
          <p class="muted">
            {{
              isActive
                ? "完成需求理解与方案规划后会在这里显示。"
                : "展开执行记录查看终止原因，或调整任务后重新运行。"
            }}
          </p>
        </div>
        <template v-else>
          <div class="comparison-charts">
            <div class="comparison-chart">
              <div class="chart-title">
                <strong>平均精度 AP</strong><span>固定范围 0–1，越高越好</span>
              </div>
              <div class="chart-axis">
                <span>0</span><span>0.5</span><span>1</span>
              </div>
              <div
                v-for="candidate in candidates"
                :key="candidate.candidate_id"
                class="chart-row"
              >
                <span :title="candidate.candidate_id"
                  >{{ algorithmName(candidate) }} ·
                  {{ variantName(candidate) }}</span
                >
                <div class="bar-track">
                  <div
                    class="bar-score"
                    :class="{
                      chosen:
                        candidate.candidate_id === report.selected_candidate_id,
                    }"
                    :style="{
                      width: scoreWidth(candidate.metrics?.average_precision),
                    }"
                  ></div>
                  <i
                    v-if="finite(candidate.metrics?.dummy_average_precision)"
                    class="baseline-line"
                    :style="{
                      left: scoreWidth(
                        candidate.metrics.dummy_average_precision,
                      ),
                    }"
                    title="类别占比基线"
                  ></i>
                </div>
                <b>{{ metric(candidate.metrics?.average_precision) }}</b>
              </div>
              <p class="chart-caption">
                细竖线表示各候选的 Dummy AP 基线；缺失分数显示为「—」。
              </p>
            </div>
            <div class="comparison-chart">
              <div class="chart-title">
                <strong>前 10% 名单提升度</strong
                ><span>Lift · 独立倍数刻度</span>
              </div>
              <div class="chart-axis">
                <span>0×</span><span>{{ metric(liftMaximum / 2, 1) }}×</span
                ><span>{{ metric(liftMaximum, 1) }}×</span>
              </div>
              <div
                v-for="candidate in candidates"
                :key="candidate.candidate_id"
                class="chart-row"
              >
                <span :title="candidate.candidate_id"
                  >{{ algorithmName(candidate) }} ·
                  {{ variantName(candidate) }}</span
                >
                <div class="bar-track">
                  <div
                    class="bar-lift"
                    :style="{
                      width: liftWidth(candidate.metrics?.lift_at_10pct),
                    }"
                  ></div>
                  <i
                    class="baseline-line"
                    :style="{ left: `${100 / liftMaximum}%` }"
                    title="随机名单的 1 倍基线"
                  ></i>
                </div>
                <b
                  >{{ metric(candidate.metrics?.lift_at_10pct, 2)
                  }}{{ finite(candidate.metrics?.lift_at_10pct) ? "×" : "" }}</b
                >
              </div>
              <p class="chart-caption">
                1× 为随机名单基线；该图使用独立刻度，与 AP 不共用轴。
              </p>
            </div>
          </div>
          <p class="table-hint">左右滑动表格，查看完整指标。</p>
          <div
            class="table-scroll"
            tabindex="0"
            role="region"
            aria-label="候选指标对比，可左右滚动"
          >
            <table class="candidates-table">
              <caption class="sr-only">
                候选验证结果。选择候选可更新下方检查、代码和证据详情。
              </caption>
              <thead>
                <tr>
                  <th scope="col">查看</th>
                  <th scope="col">候选算法</th>
                  <th scope="col">检查状态</th>
                  <th scope="col">AP</th>
                  <th scope="col">ROC-AUC</th>
                  <th scope="col">F1 @ 0.5</th>
                  <th scope="col">Lift @ 10%</th>
                  <th scope="col">训练耗时</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="candidate in candidates"
                  :key="candidate.candidate_id"
                  :class="{ inspected: inspectedId === candidate.candidate_id }"
                >
                  <td>
                    <input
                      v-model="inspectedId"
                      type="radio"
                      name="candidate"
                      :value="candidate.candidate_id"
                      :aria-label="`查看候选 ${candidate.candidate_id}`"
                    />
                  </td>
                  <th scope="row">
                    <label
                      class="candidate-name"
                      @click="inspectedId = candidate.candidate_id"
                      >{{ algorithmName(candidate) }}
                      <span
                        v-if="
                          candidate.candidate_id ===
                          report.selected_candidate_id
                        "
                        class="winner-label"
                        ><Check :size="11" />本次选中</span
                      ></label
                    ><small
                      >{{ variantName(candidate) }} ·
                      {{ candidate.candidate_id }}</small
                    >
                  </th>
                  <td>
                    <span class="badge" :class="tone(candidate.status)">{{
                      statusName(candidate.status)
                    }}</span>
                  </td>
                  <td>{{ metric(candidate.metrics?.average_precision) }}</td>
                  <td>{{ metric(candidate.metrics?.roc_auc) }}</td>
                  <td>{{ metric(candidate.metrics?.f1_threshold_0_5) }}</td>
                  <td>{{ metric(candidate.metrics?.lift_at_10pct, 2) }}</td>
                  <td>
                    {{
                      finite(candidate.resources?.fit_seconds)
                        ? `${metric(candidate.resources.fit_seconds, 2)} s`
                        : "—"
                    }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </section>

      <section v-if="inspected" class="panel candidate-detail">
        <div class="section-heading">
          <div>
            <p class="eyebrow">VALIDATION DETAIL</p>
            <h2>
              {{ algorithmName(inspected) }}
              <span class="detail-variant">{{ variantName(inspected) }}</span>
            </h2>
            <p class="muted">
              正在查看 {{ inspected.candidate_id
              }}{{
                inspected.candidate_id === report.selected_candidate_id
                  ? " · 本次运行选中的候选"
                  : " · 此选择仅切换详情，不更改运行结果"
              }}
            </p>
          </div>
          <span class="badge" :class="tone(inspected.status)">{{
            statusName(inspected.status)
          }}</span>
        </div>
        <p v-if="inspected.plan?.rationale" class="rationale">
          <GitBranch :size="18" /><span
            ><strong>设计依据</strong>{{ inspected.plan.rationale }}</span
          >
        </p>
        <div v-if="inspected.error" class="message-box bad" role="status">
          <CircleAlert :size="18" />
          <div>
            <strong>{{ inspected.error.type || "候选验证失败" }}</strong>
            <p>{{ inspected.error.message || textValue(inspected.error) }}</p>
          </div>
        </div>
        <div class="validation-dimensions">
          <article
            v-for="dimension in dimensions"
            :key="dimension.title"
            class="validation-dimension"
            :class="tone(dimension.state)"
          >
            <div>
              <CheckCircle2
                v-if="dimension.state === 'passed'"
                :size="19"
              /><XCircle
                v-else-if="dimension.state === 'failed'"
                :size="19"
              /><Circle v-else :size="19" />
              <h3>{{ dimension.title }}</h3>
            </div>
            <strong>{{ dimension.label }}</strong>
            <p>{{ dimension.note }}</p>
            <span
              >{{ dimension.passed }} / {{ dimension.keys.length }} 项通过</span
            >
          </article>
        </div>
        <details class="disclosure">
          <summary>
            <ShieldCheck :size="18" /><span
              >逐项验证证据<small
                >{{ arr(inspected.checks).length }} 个已记录检查</small
              ></span
            ><ChevronRight :size="17" />
          </summary>
          <div class="disclosure-content">
            <div v-if="!arr(inspected.checks).length" class="muted">
              尚无检查记录。没有记录不代表检查已通过。
            </div>
            <div
              v-for="(check, index) in arr(inspected.checks)"
              :key="`${check.name}-${index}`"
              class="check-row"
            >
              <CheckCircle2
                v-if="check.passed === true"
                :size="17"
                class="positive-value"
              /><XCircle
                v-else-if="check.passed === false"
                :size="17"
                class="negative-value"
              /><Circle v-else :size="17" />
              <div>
                <strong>{{ checkNames[check.name] || check.name }}</strong>
                <p>{{ check.detail || "此检查未附加文字说明。" }}</p>
              </div>
              <span class="badge">{{
                check.mandatory === true
                  ? "必须通过"
                  : check.mandatory === false
                    ? "建议性门槛"
                    : "要求未记录"
              }}</span>
            </div>
          </div>
        </details>
        <details :key="`code-${runId}`" class="disclosure" @toggle="toggleCode">
          <summary>
            <Code2 :size="18" /><span
              >生成代码<small>查看与下载 Python 制品</small></span
            ><ChevronRight :size="17" />
          </summary>
          <div class="disclosure-content">
            <div v-if="codeLoading" class="muted">
              <LoaderCircle class="spin" :size="16" /> 正在读取代码…
            </div>
            <div v-else-if="codeError" class="message-box bad" role="alert">
              <p>{{ codeError }} 制品可能未保存或仅包含历史证据。</p>
              <button class="btn btn-ghost" @click="loadCode">重试</button>
            </div>
            <div v-else-if="!inspected.artifact_id || !code" class="muted">
              当前候选没有可读取的代码制品。
            </div>
            <template v-else
              ><div class="code-toolbar">
                <span class="muted"
                  >只读代码 · {{ inspected.candidate_id }}</span
                ><button class="btn btn-ghost" @click="saveCode">
                  <Download :size="15" />下载 .py
                </button>
              </div>
              <pre class="code-block"><code>{{ code }}</code></pre>
              <p class="hash-line">
                SHA256 {{ inspected.code_sha256 || "未记录" }}
              </p>
              <p class="muted">
                执行方式：受限 AST
                构造器与资源限制子进程；不具备完整操作系统沙箱隔离。
              </p></template
            >
          </div>
        </details>
        <details class="disclosure">
          <summary>
            <RefreshCw :size="18" /><span
              >修复与执行尝试<small
                >{{ attempts.length }} 次尝试 ·
                {{ repairs.length }} 条修复诊断</small
              ></span
            ><ChevronRight :size="17" />
          </summary>
          <div class="disclosure-content">
            <p v-if="inspected.injected_failure" class="annotation">
              该候选包含人为注入的接口故障，用于演示修复流程；不属于自然发生的模型错误。
            </p>
            <p v-if="!attempts.length" class="muted">尚无执行尝试记录。</p>
            <article
              v-for="(attempt, index) in attempts"
              :key="index"
              class="attempt-card"
            >
              <div>
                <strong>{{
                  attempt.attempt === 0
                    ? "初始生成"
                    : `第 ${attempt.attempt} 次修复后验证`
                }}</strong
                ><span class="badge" :class="tone(attempt.status)">{{
                  statusName(attempt.status)
                }}</span>
              </div>
              <p v-if="attempt.error">
                {{ attempt.error.type }} · {{ attempt.error.message }}
              </p>
              <p v-else>
                AP {{ metric(attempt.metrics?.average_precision) }} ·
                {{
                  arr(attempt.checks).filter((item) => item.passed === true)
                    .length
                }}/{{ arr(attempt.checks).length }} 个已记录检查通过
              </p>
              <span class="hash-line"
                >代码 SHA256 {{ attempt.code_sha256 || "未记录" }}</span
              >
            </article>
            <article
              v-for="(repair, index) in repairs"
              :key="`repair-${index}`"
              class="repair-card"
            >
              <h4>
                修复诊断 {{ index + 1 }}
                <span class="badge">{{
                  repair.validated === true
                    ? "修复后验证通过"
                    : "未证实修复有效"
                }}</span>
              </h4>
              <p><strong>原因：</strong>{{ repair.diagnosis || "未记录" }}</p>
              <p><strong>修复：</strong>{{ repair.fix || "未记录" }}</p>
            </article>
          </div>
        </details>
        <details class="disclosure">
          <summary>
            <Network :size="18" /><span
              >知识依据与来源<small
                >{{ selectedEvidence.length }} 张关联能力卡片</small
              ></span
            ><ChevronRight :size="17" />
          </summary>
          <div class="disclosure-content">
            <p class="muted">
              检索到的能力提供实现依据；来源关联本身不等于算法已经验证。
            </p>
            <p v-if="!selectedEvidence.length" class="muted">
              当前候选没有记录关联知识，可能关闭了检索或尚未完成检索。
            </p>
            <div class="evidence-grid">
              <article
                v-for="item in selectedEvidence"
                :key="item.capability_id || item.id"
                class="evidence-card"
              >
                <div>
                  <Network :size="18" /><span class="badge"
                    >v{{ item.version || 1 }}</span
                  >
                </div>
                <h3>{{ item.name || item.capability_id || item.id }}</h3>
                <p>{{ item.summary || "未提供能力摘要" }}</p>
                <div class="evidence-meta">
                  <span>{{
                    item.graph_used === true ? "图谱参与检索" : "能力检索"
                  }}</span
                  ><span>{{ list(item.evidence).length }} 个来源</span>
                </div>
                <ul v-if="list(item.evidence).length" class="source-list">
                  <li
                    v-for="(source, index) in arr(item.evidence)"
                    :key="index"
                  >
                    <a
                      v-if="safeSource(source.uri)"
                      :href="safeSource(source.uri)"
                      target="_blank"
                      rel="noopener noreferrer"
                      >{{
                        source.locator?.path || source.source_id || source.uri
                      }}<ExternalLink :size="11" /></a
                    ><span v-else>{{
                      source.locator?.path || source.source_id || "来源记录"
                    }}</span
                    ><small v-if="source.locator?.line_start"
                      >第 {{ source.locator.line_start
                      }}{{
                        source.locator.line_end
                          ? `–${source.locator.line_end}`
                          : ""
                      }}
                      行</small
                    >
                  </li>
                </ul>
                <RouterLink
                  class="graph-link"
                  :to="{
                    path: '/knowledge',
                    query: { focus: evidenceNode(item) },
                  }"
                  >在知识图谱中追溯<ArrowRight :size="14"
                /></RouterLink>
              </article>
            </div>
            <details v-if="evidence.length" class="nested-disclosure">
              <summary>查看原始检索分数与关系路径</summary>
              <pre class="json-block">{{ pretty(selectedEvidence) }}</pre>
            </details>
          </div>
        </details>
      </section>

      <section class="panel process-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">PROCESS & PROVENANCE</p>
            <h2>流程与溯源</h2>
            <p class="muted">保留真实执行证据，中间过程按需展开。</p>
          </div>
          <span class="badge">{{ events.length }} 条事件</span>
        </div>
        <div class="stage-strip" aria-label="已记录的执行阶段">
          <div
            v-for="(stage, index) in stages"
            :key="stage.title"
            class="stage-item"
            :class="{ done: stage.done, skipped: stage.disabled }"
          >
            <div>
              <Check v-if="stage.done" :size="14" /><span v-else>{{
                String(index + 1).padStart(2, "0")
              }}</span>
            </div>
            <strong>{{ stage.title }}</strong
            ><small>{{
              stage.done
                ? "已有记录"
                : stage.disabled
                  ? "未启用 / 未发生"
                  : "尚无记录"
            }}</small>
          </div>
        </div>
        <details class="disclosure">
          <summary>
            <FileText :size="18" /><span
              >原始需求、理解与规划<small
                >查看输入约束和候选选择依据</small
              ></span
            ><ChevronRight :size="17" />
          </summary>
          <div class="disclosure-content">
            <h3>用户需求</h3>
            <blockquote>{{ report.description || "未记录" }}</blockquote>
            <template v-if="report.interpretation"
              ><h3>Agent 理解的目标</h3>
              <p>{{ report.interpretation.objective || "未记录" }}</p>
              <div class="interpretation-grid">
                <div>
                  <h4>约束</h4>
                  <ul>
                    <li
                      v-for="(value, index) in list(
                        report.interpretation.constraints,
                      )"
                      :key="index"
                    >
                      {{ textValue(value) }}
                    </li>
                  </ul>
                </div>
                <div>
                  <h4>假设</h4>
                  <ul>
                    <li
                      v-for="(value, index) in list(
                        report.interpretation.assumptions,
                      )"
                      :key="index"
                    >
                      {{ textValue(value) }}
                    </li>
                  </ul>
                </div>
              </div></template
            >
            <h3>结果解释</h3>
            <p class="long-text">
              {{ report.explanation?.summary || "尚无结果解释。" }}
            </p>
            <div v-if="report.search_tree?.length" class="search-ancestry">
              <h3>搜索候选关系</h3>
              <p
                v-for="node in arr(report.search_tree)"
                :key="node.candidate_id"
              >
                <GitBranch :size="14" />{{ node.parent_id || "初始方案" }}
                <ArrowRight :size="13" />{{ node.candidate_id
                }}<span class="badge">{{
                  node.pruned === true
                    ? "未保留在最终 Beam"
                    : node.pruned === false
                      ? "保留在最终 Beam"
                      : statusName(node.status)
                }}</span>
              </p>
            </div>
          </div>
        </details>
        <details class="disclosure">
          <summary>
            <Timer :size="18" /><span
              >Agent 执行时间线<small
                >真实事件，不展示推测的完成百分比</small
              ></span
            ><ChevronRight :size="17" />
          </summary>
          <div class="disclosure-content">
            <ol v-if="events.length" class="event-timeline">
              <li
                v-for="(event, index) in events"
                :key="`${event.sequence}-${index}`"
              >
                <span class="timeline-dot"></span>
                <div>
                  <div class="event-topline">
                    <strong>{{
                      eventNames[event.event_type || event.type] ||
                      event.event_type ||
                      event.type
                    }}</strong
                    ><time>{{ dateTime(event.created_at) }}</time>
                  </div>
                  <p>
                    {{
                      event.data?.role
                        ? roleNames[event.data.role] || event.data.role
                        : ""
                    }}{{
                      event.data?.candidate_id
                        ? ` · ${event.data.candidate_id}`
                        : ""
                    }}{{
                      event.data?.status
                        ? ` · ${statusName(event.data.status)}`
                        : ""
                    }}{{
                      event.data?.attempt != null
                        ? ` · 尝试 ${event.data.attempt}`
                        : ""
                    }}
                  </p>
                  <details class="nested-disclosure">
                    <summary>事件详情</summary>
                    <pre class="json-block">{{ pretty(event.data) }}</pre>
                  </details>
                </div>
              </li>
            </ol>
            <p v-else class="muted">尚无已记录的执行事件。</p>
          </div>
        </details>
        <details class="disclosure">
          <summary>
            <Layers3 :size="18" /><span
              >资源、数据与知识沉淀<small
                >Token、耗时、划分协议和回写结果</small
              ></span
            ><ChevronRight :size="17" />
          </summary>
          <div class="disclosure-content">
            <dl class="resource-grid">
              <div>
                <dt>端到端耗时</dt>
                <dd>
                  {{
                    finite(report.timing?.wall_seconds)
                      ? `${metric(report.timing.wall_seconds, 1)} s`
                      : "未记录"
                  }}
                </dd>
              </div>
              <div>
                <dt>LLM 调用</dt>
                <dd>{{ report.usage?.calls ?? "未记录" }}</dd>
              </div>
              <div>
                <dt>输入 / 输出 Token</dt>
                <dd>
                  {{ report.usage?.input_tokens ?? "—" }} /
                  {{ report.usage?.output_tokens ?? "—" }}
                </dd>
              </div>
              <div>
                <dt>使用模型</dt>
                <dd>{{ report.model || "未记录" }}</dd>
              </div>
              <div>
                <dt>训练 / 验证样本</dt>
                <dd>
                  {{ report.data_summary?.train_rows ?? "—" }} /
                  {{ report.data_summary?.validation_rows ?? "—" }}
                </dd>
              </div>
              <div>
                <dt>运行已回写知识库</dt>
                <dd>
                  {{
                    report.knowledge_writeback?.run_saved === true
                      ? "是"
                      : "尚未确认"
                  }}
                </dd>
              </div>
              <div>
                <dt>沉淀失败 / 修复经验</dt>
                <dd>
                  {{ list(report.knowledge_writeback?.experiences).length }} 条
                </dd>
              </div>
              <div>
                <dt>当前候选峰值内存</dt>
                <dd>
                  {{
                    finite(inspected?.resources?.peak_rss_mib)
                      ? `${metric(inspected?.resources?.peak_rss_mib, 1)} MiB`
                      : "未记录"
                  }}
                </dd>
              </div>
            </dl>
            <RouterLink
              v-if="report.knowledge_writeback?.run_saved === true"
              class="graph-link"
              :to="{ path: '/knowledge', query: { focus: `run:${runId}` } }"
              >查看本次运行的知识图谱关联<ArrowRight :size="14"
            /></RouterLink>
            <details class="nested-disclosure">
              <summary>数据与环境溯源原始记录</summary>
              <pre class="json-block">{{
                pretty({
                  provenance: report.provenance,
                  request: report.request,
                  usage: report.usage,
                  resources: inspected?.resources,
                  containment: inspected?.containment,
                  knowledge_writeback: report.knowledge_writeback,
                })
              }}</pre>
            </details>
          </div>
        </details>
        <details class="disclosure">
          <summary>
            <CircleAlert :size="18" /><span
              >解释边界与注意事项<small
                >{{ list(report.warnings).length }} 条运行提示</small
              ></span
            ><ChevronRight :size="17" />
          </summary>
          <div class="disclosure-content">
            <h3>解释边界</h3>
            <ul>
              <li
                v-for="(value, index) in list(report.explanation?.limitations)"
                :key="index"
              >
                {{ textValue(value) }}
              </li>
            </ul>
            <h3>运行提示</h3>
            <ul>
              <li v-for="(value, index) in list(report.warnings)" :key="index">
                {{ textValue(value) }}
              </li>
            </ul>
            <p
              v-if="
                !list(report.warnings).length &&
                !list(report.explanation?.limitations).length
              "
              class="muted"
            >
              没有记录附加提示。请结合检查项与验证范围判断结果。
            </p>
          </div>
        </details>
        <details class="disclosure">
          <summary>
            <FileJson :size="18" /><span
              >完整 JSON 审计记录<small>用于复现、接口集成与校验</small></span
            ><ChevronRight :size="17" />
          </summary>
          <div class="disclosure-content">
            <button
              class="btn btn-ghost"
              :disabled="!!actionBusy"
              @click="saveReport('json')"
            >
              <Download :size="15" />下载完整 JSON
            </button>
            <pre class="json-block">{{ pretty(report) }}</pre>
          </div>
        </details>
      </section>
      <footer class="report-footer">
        <span
          >运行标识 <code>{{ runId }}</code></span
        ><span>{{
          report.finished_at
            ? `结束于 ${dateTime(report.finished_at)}`
            : "运行尚未结束"
        }}</span>
      </footer>
    </template>
  </div>
</template>

<style scoped>
.run-page {
  min-width: 0;
  display: grid;
  gap: 22px;
  max-width: 1480px;
  margin: 0 auto;
}
.run-page > * {
  min-width: 0;
}
.report-page-heading {
  gap: 20px;
}
.report-page-heading h1 {
  margin: 6px 0 9px;
}
.report-page-heading .eyebrow {
  margin-top: 20px;
}
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #637087;
  text-decoration: none;
}
.report-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.report-actions .btn {
  white-space: nowrap;
  font-size: 12px;
}
.message-box {
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid #e1e6ed;
  border-radius: 12px;
  padding: 15px 18px;
  background: #f7f9fc;
  font-size: 13px;
}
.message-box > svg {
  flex-shrink: 0;
}
.message-box > div,
.message-box > p {
  flex: 1;
}
.message-box p {
  margin: 3px 0;
  line-height: 1.7;
  overflow-wrap: anywhere;
}
.message-box.bad {
  background: #fff5f4;
  border-color: #f5d4d0;
  color: #983e38;
}
.message-box .btn {
  flex-shrink: 0;
}
.result-hero {
  padding: 28px 30px;
  border-top: 3px solid #63758f !important;
  background: linear-gradient(120deg, #fff 60%, #f4f7fb) !important;
}
.result-hero.good {
  border-top-color: #1f9674 !important;
  background: linear-gradient(120deg, #fff 60%, #f2faf7) !important;
}
.result-hero.working {
  border-top-color: #526ce7 !important;
}
.result-hero.bad {
  border-top-color: #d36c61 !important;
}
.result-topline,
.result-badges,
.result-heading,
.result-badges .badge {
  display: flex;
  align-items: center;
  gap: 10px;
}
.result-topline {
  justify-content: space-between;
  flex-wrap: wrap;
}
.result-badges {
  font-size: 12px;
  flex-wrap: wrap;
}
.run-identity {
  font-size: 11px;
  color: #7b8798;
  font-family: ui-monospace, monospace;
}
.result-heading {
  justify-content: space-between;
  gap: 25px;
  margin: 24px 0;
}
.result-heading h2 {
  font-size: 24px;
  letter-spacing: -0.4px;
  margin: 0 0 12px;
  line-height: 1.45;
}
.headline {
  font-size: 14px;
  line-height: 1.9;
  margin: 0;
  color: #526077;
  max-width: 920px;
}
.result-mark {
  width: 70px;
  height: 70px;
  flex-shrink: 0;
  border: 1px solid #e3eee8;
  background: #fff;
  border-radius: 20px;
  display: grid;
  place-items: center;
  color: #279473;
}
.bad .result-mark {
  color: #c16355;
  border-color: #eddeda;
}
.working .result-mark {
  color: #586cdc;
}
.decision-note {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  border-top: 1px solid #e8edf0;
  padding-top: 18px;
  font-size: 12px;
  color: #566b62;
}
.decision-note > svg {
  flex-shrink: 0;
  margin-top: 1px;
}
.decision-note > div {
  flex: 1;
}
.decision-note strong {
  font-size: 12px;
  color: #314a40;
}
.decision-note p {
  line-height: 1.8;
  margin: 4px 0 0;
}
.decision-note .btn {
  white-space: nowrap;
  align-self: center;
  font-size: 12px;
}
.live-activity {
  display: flex;
  align-items: center;
  gap: 10px;
  border-top: 1px solid #e8edf0;
  padding-top: 15px;
  font-size: 13px;
}
.live-activity > .btn,
.live-activity > span:last-child {
  margin-left: auto;
}
.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #6375df;
  box-shadow: 0 0 0 4px #eef0ff;
  flex-shrink: 0;
}
.report-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}
.metric-card {
  padding: 21px 23px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.metric-card > span {
  color: #6b778c;
  font-size: 12px;
}
.metric-card > strong {
  font-size: 29px;
  font-weight: 650;
  letter-spacing: -0.8px;
  font-variant-numeric: tabular-nums;
  color: #253148;
}
.metric-card strong em {
  font-style: normal;
  color: #a0a8b6;
  font-size: 19px;
}
.metric-card > small {
  color: #929aa8;
  font-size: 11px;
}
.primary-metric {
  background: #f3f5ff !important;
  border-color: #e0e5ff !important;
}
.primary-metric > strong {
  color: #5366cc;
}
.positive-value {
  color: #228665 !important;
}
.negative-value {
  color: #bd554b !important;
}
.evaluation-note {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px;
  font-size: 12px;
  color: #7c8796;
  margin: -6px 0 0;
  line-height: 1.7;
}
.evaluation-note svg {
  flex-shrink: 0;
}
.candidate-section,
.candidate-detail,
.process-section {
  padding: 26px;
}
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
}
.section-heading h2 {
  font-size: 19px;
  margin: 7px 0 8px;
}
.section-heading p {
  margin: 0;
  font-size: 12px;
  line-height: 1.7;
}
.section-heading .eyebrow {
  font-size: 10px;
  letter-spacing: 1.4px;
}
.section-heading > .badge {
  white-space: nowrap;
}
.comparison-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
  margin-bottom: 26px;
}
.comparison-chart {
  min-width: 0;
}
.chart-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.chart-title > span {
  font-size: 10px;
  color: #8e98a7;
}
.chart-axis {
  display: flex;
  justify-content: space-between;
  margin: 15px 56px 8px 124px;
  font-size: 10px;
  color: #adb5c0;
}
.chart-row {
  display: grid;
  grid-template-columns: 114px minmax(0, 1fr) 48px;
  gap: 10px;
  align-items: center;
  margin: 13px 0;
}
.chart-row > span {
  font-size: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #6b778b;
}
.chart-row > b {
  font-size: 11px;
  font-weight: 550;
  color: #657088;
  font-variant-numeric: tabular-nums;
  text-align: right;
}
.bar-track {
  height: 9px;
  background: #f1f3f7;
  border-radius: 3px;
  position: relative;
}
.bar-score,
.bar-lift {
  height: 100%;
  border-radius: 3px;
  min-width: 0;
  background: #b9c2ee;
  transition: width 0.3s;
}
.bar-score.chosen {
  background: #6478da;
}
.bar-lift {
  background: #76bda9;
}
.baseline-line {
  position: absolute;
  height: 15px;
  top: -3px;
  width: 1px;
  background: #84909f;
}
.chart-caption {
  font-size: 10px;
  line-height: 1.7;
  color: #929cab;
  margin: 16px 0 0;
}
.table-hint {
  display: none;
  font-size: 10px;
  color: #8d99aa;
}
.table-scroll {
  overflow-x: auto;
  border: 1px solid #e9edf3;
  border-radius: 11px;
}
.candidates-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  white-space: nowrap;
  font-size: 12px;
}
.candidates-table thead {
  background: #f8f9fc;
  color: #8993a4;
}
.candidates-table th,
.candidates-table td {
  padding: 14px 12px;
  border-bottom: 1px solid #edf0f4;
  font-weight: 450;
}
.candidates-table tbody tr:last-child > * {
  border-bottom: 0;
}
.candidates-table tbody tr.inspected {
  background: #f5f7ff;
}
.candidates-table input {
  accent-color: #5e72d9;
  cursor: pointer;
  width: 15px;
  height: 15px;
}
.candidates-table td {
  font-variant-numeric: tabular-nums;
  color: #627088;
}
.candidate-name {
  display: flex;
  gap: 7px;
  align-items: center;
  cursor: pointer;
  color: #334159;
  font-size: 12px;
  font-weight: 550;
}
.candidates-table small {
  display: block;
  font-size: 10px;
  color: #95a0b1;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 5px;
}
.winner-label {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 9px;
  background: #eaf0ff;
  color: #5770c4;
  border-radius: 4px;
  padding: 3px 5px;
}
.detail-variant {
  font-size: 12px;
  font-weight: 450;
  color: #929dae;
  margin-left: 7px;
}
.rationale {
  display: flex;
  gap: 10px;
  color: #71809a;
  font-size: 13px;
  line-height: 1.9;
  padding: 17px 18px;
  background: #f8f9fc;
  border-radius: 10px;
  margin: 0 0 22px;
}
.rationale svg {
  flex-shrink: 0;
  margin-top: 3px;
}
.rationale strong {
  display: block;
  font-size: 11px;
  letter-spacing: 0.5px;
  color: #3f506d;
  margin-bottom: 2px;
}
.validation-dimensions {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 20px 0 24px;
}
.validation-dimension {
  padding: 17px 15px;
  border: 1px solid #e5eaf0;
  border-radius: 11px;
}
.validation-dimension > div {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #7b8799;
}
.validation-dimension.good > div {
  color: #358b73;
}
.validation-dimension.bad > div {
  color: #c5665b;
}
.validation-dimension h3 {
  font-size: 12px;
  margin: 0;
  color: #47556c;
}
.validation-dimension > strong {
  display: block;
  font-size: 12px;
  margin: 14px 0 7px;
  color: #34455c;
}
.validation-dimension p {
  font-size: 10px;
  color: #959fad;
  margin: 0 0 9px;
}
.validation-dimension > span {
  font-size: 10px;
  color: #81918d;
}
.disclosure {
  border-top: 1px solid #edf0f4;
}
.disclosure > summary {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 18px 1px;
  list-style: none;
  cursor: pointer;
  color: #77849a;
}
.disclosure > summary::-webkit-details-marker {
  display: none;
}
.disclosure > summary > span {
  flex: 1;
  font-size: 13px;
  font-weight: 550;
  color: #45536b;
}
.disclosure > summary small {
  font-weight: 400;
  font-size: 11px;
  color: #9aa3b2;
  margin-left: 12px;
}
.disclosure > summary > svg:last-child {
  transition: transform 0.2s;
}
.disclosure[open] > summary > svg:last-child {
  transform: rotate(90deg);
}
.disclosure-content {
  padding: 2px 0 23px;
  color: #67778e;
  font-size: 13px;
  line-height: 1.9;
}
.disclosure-content h3 {
  font-size: 13px;
  margin: 20px 0 8px;
  color: #40516a;
}
.disclosure-content h3:first-child {
  margin-top: 0;
}
.disclosure-content h4 {
  font-size: 12px;
  color: #566a84;
}
.disclosure-content ul {
  padding-left: 20px;
}
.disclosure-content li {
  margin: 5px 0;
  overflow-wrap: anywhere;
}
.check-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 13px 0;
  border-top: 1px dashed #edf0f4;
}
.check-row > svg {
  flex-shrink: 0;
  margin-top: 3px;
}
.check-row > div {
  flex: 1;
  min-width: 0;
}
.check-row strong {
  font-size: 12px;
  color: #55657a;
}
.check-row p {
  font-size: 11px;
  line-height: 1.8;
  margin: 3px 0 0;
  overflow-wrap: anywhere;
}
.check-row > .badge {
  font-size: 10px;
  white-space: nowrap;
}
.code-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 15px;
}
.code-block,
.json-block {
  max-height: 480px;
  overflow: auto;
  border-radius: 10px;
  padding: 20px;
  line-height: 1.8;
  font-size: 11px;
  tab-size: 4;
  white-space: pre;
  font-family: ui-monospace, SFMono-Regular, monospace;
}
.code-block {
  background: #20293b;
  color: #d7e1ed;
}
.json-block {
  background: #f5f7fa;
  color: #596b83;
  border: 1px solid #e9eef4;
}
.hash-line {
  font-family: ui-monospace, monospace;
  overflow-wrap: anywhere;
  color: #95a0af;
  font-size: 10px;
  display: block;
}
.annotation {
  padding: 12px;
  background: #fff8eb;
  border-radius: 8px;
  color: #997744;
  font-size: 12px;
}
.attempt-card {
  border-left: 2px solid #dce3f0;
  padding: 12px 17px;
  margin: 12px 0;
  background: #fafbfd;
  border-radius: 0 8px 8px 0;
}
.attempt-card > div {
  display: flex;
  align-items: center;
  gap: 12px;
}
.attempt-card strong {
  font-size: 12px;
  color: #485a76;
}
.attempt-card p {
  font-size: 12px;
  line-height: 1.8;
  overflow-wrap: anywhere;
}
.repair-card {
  border: 1px solid #e9edf3;
  padding: 16px;
  border-radius: 9px;
  margin-top: 12px;
}
.repair-card h4 {
  margin: 0 0 10px;
}
.repair-card p {
  font-size: 12px;
  line-height: 1.8;
  margin: 8px 0;
  overflow-wrap: anywhere;
}
.evidence-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 17px;
}
.evidence-card {
  border: 1px solid #e5eaf3;
  border-radius: 11px;
  padding: 19px;
  display: flex;
  flex-direction: column;
}
.evidence-card > div:first-child {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #7c8eb0;
}
.evidence-card h3 {
  font-size: 13px;
  margin: 14px 0 8px;
}
.evidence-card p {
  font-size: 11px;
  color: #8190a4;
  line-height: 1.9;
  margin: 0 0 14px;
  overflow-wrap: anywhere;
}
.evidence-meta {
  display: flex;
  gap: 12px;
  color: #a0abba;
  font-size: 10px;
}
.source-list {
  font-size: 10px;
  line-height: 1.6;
  margin: 10px 0 17px !important;
  padding-left: 14px !important;
  overflow-wrap: anywhere;
}
.source-list a {
  color: #6f83b0;
  display: inline;
  word-break: break-all;
}
.source-list svg {
  display: inline;
  margin-left: 4px;
}
.source-list small {
  display: block;
  font-size: 10px;
  color: #a0a9b5;
}
.graph-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #5a72c0 !important;
  font-size: 11px;
  text-decoration: none;
  margin-top: auto;
}
.stage-strip {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 8px;
  padding-bottom: 27px;
}
.stage-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  gap: 8px;
  text-align: center;
}
.stage-item:before {
  content: "";
  height: 1px;
  background: #edf0f6;
  position: absolute;
  top: 15px;
  left: 65%;
  width: 70%;
}
.stage-item:last-child:before {
  display: none;
}
.stage-item > div {
  width: 30px;
  height: 30px;
  border: 1px solid #e3e8f1;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #a1abbb;
  background: white;
  z-index: 1;
  font-size: 10px;
}
.stage-item.done > div {
  background: #eff7f4;
  border-color: #d6e9e1;
  color: #49967c;
}
.stage-item > strong {
  font-size: 10px;
  color: #8995a7;
  font-weight: 500;
}
.stage-item.done > strong {
  color: #526c62;
}
.stage-item > small {
  font-size: 8px;
  color: #aab3c0;
}
.stage-item.skipped > div {
  border-style: dashed;
}
.nested-disclosure {
  margin: 14px 0 0;
  font-size: 11px;
  color: #8693a7;
}
.nested-disclosure > summary {
  cursor: pointer;
  padding: 5px 0;
}
.nested-disclosure .json-block {
  font-size: 10px;
}
.interpretation-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px;
}
.interpretation-grid h4 {
  margin: 15px 0 8px;
}
.interpretation-grid ul {
  font-size: 12px;
}
.disclosure-content blockquote {
  margin: 0;
  padding: 15px 18px;
  background: #f7f9fc;
  border-left: 3px solid #d9e2f3;
  border-radius: 0 8px 8px 0;
  white-space: pre-wrap;
  font-size: 12px;
}
.long-text {
  font-size: 12px;
  line-height: 2;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.search-ancestry p {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  flex-wrap: wrap;
  overflow-wrap: anywhere;
}
.search-ancestry .badge {
  font-size: 9px;
}
.event-timeline {
  list-style: none;
  margin: 0;
  padding: 0 0 0 11px;
}
.event-timeline > li {
  border-left: 1px solid #e2e8f1;
  padding: 0 0 20px 22px;
  position: relative;
  margin: 0;
}
.event-timeline > li:last-child {
  border-left-color: transparent;
}
.timeline-dot {
  position: absolute;
  left: -4px;
  top: 7px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #b2bfd7;
  box-shadow: 0 0 0 4px white;
}
.event-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.event-topline strong {
  font-size: 12px;
  color: #4f627f;
}
.event-topline time {
  font-size: 10px;
  color: #a1aabc;
  white-space: nowrap;
}
.event-timeline p {
  font-size: 11px;
  margin: 3px 0;
  color: #8c98a9;
}
.event-timeline .nested-disclosure {
  margin-top: 0;
}
.resource-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 24px 17px;
  margin: 0 0 25px;
}
.resource-grid dt {
  font-size: 10px;
  color: #8d9bad;
}
.resource-grid dd {
  font-size: 14px;
  color: #4d6080;
  margin: 6px 0 0;
  word-break: break-all;
}
.report-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #a2abba;
  font-size: 10px;
  padding: 0 4px 20px;
  flex-wrap: wrap;
}
.report-footer code {
  margin-left: 6px;
  word-break: break-all;
}
.compact-empty {
  padding: 38px;
}
.badge.good {
  color: #298267;
  background: #eaf6f0;
}
.badge.bad {
  color: #b7594e;
  background: #fff0ee;
}
.badge.working {
  color: #6275ca;
  background: #edf1ff;
}
.badge.neutral {
  color: #7c899e;
  background: #f0f3f8;
}
.mode-badge {
  background: #eef1f7;
  color: #718097;
}
.spin {
  animation: run-spin 1.2s linear infinite;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
@keyframes run-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (max-width: 1100px) {
  .report-actions {
    max-width: 400px;
    justify-content: flex-end;
  }
  .report-metrics {
    gap: 12px;
  }
  .metric-card {
    padding: 18px;
  }
  .comparison-charts {
    gap: 20px;
  }
  .chart-row {
    grid-template-columns: 88px minmax(0, 1fr) 43px;
    gap: 8px;
  }
  .chart-axis {
    margin-left: 96px;
    margin-right: 51px;
  }
  .validation-dimensions {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .resource-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 760px) {
  .table-hint {
    display: block;
  }
  .run-page {
    gap: 17px;
  }
  .report-page-heading {
    align-items: flex-start;
    flex-direction: column;
  }
  .report-actions {
    justify-content: flex-start;
    max-width: none;
  }
  .report-actions .btn {
    font-size: 11px;
  }
  .result-hero,
  .candidate-section,
  .candidate-detail,
  .process-section {
    padding: 20px;
  }
  .result-heading h2 {
    font-size: 20px;
  }
  .result-heading {
    gap: 14px;
  }
  .result-mark {
    width: 49px;
    height: 49px;
    border-radius: 14px;
  }
  .result-mark svg {
    width: 25px;
  }
  .result-topline {
    gap: 14px;
  }
  .run-identity {
    font-size: 9px;
  }
  .result-badges {
    gap: 6px;
  }
  .headline {
    font-size: 12px;
  }
  .decision-note {
    flex-wrap: wrap;
    font-size: 11px;
  }
  .decision-note > .btn {
    margin-left: 27px;
  }
  .decision-note > div {
    flex-basis: calc(100% - 35px);
  }
  .report-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .metric-card {
    padding: 17px;
    gap: 10px;
  }
  .metric-card > span {
    font-size: 10px;
  }
  .metric-card > strong {
    font-size: 25px;
  }
  .metric-card > small {
    font-size: 9px;
    line-height: 1.6;
  }
  .evaluation-note {
    font-size: 10px;
    align-items: flex-start;
  }
  .comparison-charts {
    grid-template-columns: 1fr;
    gap: 23px;
  }
  .chart-row {
    grid-template-columns: 110px minmax(0, 1fr) 45px;
  }
  .chart-axis {
    margin-left: 118px;
    margin-right: 53px;
  }
  .section-heading h2 {
    font-size: 17px;
  }
  .section-heading p {
    font-size: 11px;
  }
  .section-heading > .badge {
    font-size: 10px;
  }
  .validation-dimensions {
    gap: 10px;
  }
  .validation-dimension {
    padding: 14px 12px;
  }
  .validation-dimension h3 {
    font-size: 11px;
  }
  .validation-dimension > strong {
    font-size: 11px;
  }
  .disclosure > summary {
    gap: 8px;
  }
  .disclosure > summary > span {
    font-size: 12px;
  }
  .disclosure > summary small {
    display: block;
    margin: 5px 0 0;
    font-size: 10px;
    line-height: 1.5;
  }
  .evidence-grid {
    grid-template-columns: 1fr;
  }
  .stage-strip {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 20px 8px;
  }
  .stage-item:nth-child(4):before {
    display: none;
  }
  .stage-item > strong {
    font-size: 10px;
  }
  .interpretation-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  .code-block,
  .json-block {
    padding: 14px;
    font-size: 10px;
  }
  .check-row > .badge {
    font-size: 8px;
    padding: 3px 5px;
  }
  .live-activity {
    font-size: 11px;
    flex-wrap: wrap;
  }
  .event-topline {
    align-items: flex-start;
  }
  .event-topline strong {
    font-size: 11px;
  }
  .event-topline time {
    font-size: 9px;
  }
  .resource-grid {
    gap: 20px 12px;
  }
  .resource-grid dd {
    font-size: 12px;
  }
  .report-footer {
    font-size: 9px;
  }
  .message-box {
    align-items: flex-start;
    flex-wrap: wrap;
    padding: 13px;
    font-size: 12px;
  }
  .message-box .btn {
    font-size: 11px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .spin {
    animation: none;
  }
  .bar-score,
  .bar-lift,
  .disclosure > summary > svg:last-child {
    transition: none;
  }
}
</style>
