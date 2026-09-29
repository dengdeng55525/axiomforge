<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  Files,
  Plus,
  Search,
  ArrowUpRight,
  RefreshCw,
  SlidersHorizontal,
  X,
} from "@lucide/vue";
import { api } from "../lib/api";
import {
  datasetLabel,
  stateLabel,
  modeLabel,
  dateTime,
  shortId,
  errorText,
  type Json,
} from "../lib/format";
const runs = ref<Json[]>([]),
  loading = ref(true),
  error = ref(""),
  query = ref(""),
  dataset = ref("all"),
  status = ref("all"),
  mode = ref("all");
async function load() {
  loading.value = true;
  error.value = "";
  try {
    runs.value = (await api("/runs")).runs || [];
  } catch (e) {
    error.value = errorText(e);
  } finally {
    loading.value = false;
  }
}
onMounted(load);
const filtered = computed(() =>
  runs.value.filter(
    (r) =>
      (dataset.value === "all" || r.dataset_id === dataset.value) &&
      (status.value === "all" || r.status === status.value) &&
      (mode.value === "all" ||
        (mode.value === "mock" ? r.mode === "mock" : r.mode !== "mock")) &&
      `${r.description} ${r.run_id} ${r.model}`
        .toLowerCase()
        .includes(query.value.toLowerCase()),
  ),
);
function reset() {
  query.value = "";
  dataset.value = "all";
  status.value = "all";
  mode.value = "all";
}
</script>
<template>
  <div class="page-heading">
    <div>
      <span class="eyebrow">RUNS & REPORTS</span>
      <h1>每一次运行，都是可追溯的记录</h1>
      <p>查看进展、比较候选、下载报告，或基于历史需求发起新任务。</p>
    </div>
    <RouterLink to="/workbench" class="btn btn-primary"
      ><Plus :size="16" />创建新任务</RouterLink
    >
  </div>
  <section class="panel panel-pad">
    <div class="section-heading">
      <h2>
        运行与报告 <span class="badge">{{ runs.length }}</span>
      </h2>
      <button class="btn btn-small" @click="load" :disabled="loading">
        <RefreshCw :size="14" :class="{ spin: loading }" />刷新
      </button>
    </div>
    <div v-if="error" class="alert error" role="alert">{{ error }}</div>
    <div class="filterbar">
      <input
        v-model="query"
        aria-label="搜索运行"
        placeholder="搜索需求、运行编号或模型…"
      /><select v-model="dataset" aria-label="筛选场景">
        <option value="all">全部场景</option>
        <option value="bank">银行营销响应</option>
        <option value="sms">短信垃圾分类</option></select
      ><select v-model="status" aria-label="筛选状态">
        <option value="all">全部状态</option>
        <option value="passed">验证通过</option>
        <option value="running">执行中</option>
        <option value="finalizing">正在沉淀</option>
        <option value="queued">排队中</option>
        <option value="failed">未通过</option>
        <option value="cancelled">已取消</option></select
      ><select v-model="mode" aria-label="筛选执行方式">
        <option value="all">全部执行方式</option>
        <option value="real">非 Mock 运行</option>
        <option value="mock">Mock 演示</option></select
      ><button class="btn btn-ghost btn-small" @click="reset">重置筛选</button>
    </div>
    <div v-if="loading" class="loading-state">
      <RefreshCw :size="20" class="spin" /> 正在读取历史记录
    </div>
    <div v-else-if="!error && !filtered.length" class="empty-state">
      <Files :size="34" />
      <h3>{{ runs.length ? "没有符合筛选条件的运行" : "还没有运行记录" }}</h3>
      <p>
        {{
          runs.length
            ? "调整筛选条件，或清空搜索后再试。"
            : "创建一个任务，运行状态与验证报告会保存在这里。"
        }}
      </p>
      <button v-if="runs.length" class="btn" @click="reset">清空筛选</button>
    </div>
    <div v-else-if="!error" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>任务 / 运行编号</th>
            <th>场景</th>
            <th>执行方式</th>
            <th>状态</th>
            <th>候选数</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="run in filtered" :key="run.run_id">
            <td>
              <RouterLink :to="`/runs/${run.run_id}`" class="table-title">{{
                run.description || "未命名任务"
              }}</RouterLink
              ><span class="table-sub mono">{{ shortId(run.run_id) }}</span>
            </td>
            <td>{{ datasetLabel(run.dataset_id) }}</td>
            <td>
              <span :class="['badge', run.mode === 'mock' ? 'mock' : '']">{{
                modeLabel(run)
              }}</span>
            </td>
            <td>
              <span :class="['badge', run.status]">{{
                stateLabel(run.status)
              }}</span>
            </td>
            <td>{{ run.candidates?.length ?? "—" }}</td>
            <td class="muted">{{ dateTime(run.created_at) }}</td>
            <td class="history-actions">
              <RouterLink :to="`/runs/${run.run_id}`" class="text-link"
                >查看报告 <ArrowUpRight :size="13" /></RouterLink
              ><RouterLink
                :to="`/workbench?from=${run.run_id}`"
                class="text-link subdued"
                >复用需求</RouterLink
              >
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="!error" class="history-foot">
      <span
        >显示 {{ filtered.length }} / {{ runs.length }} 条记录（最近 50
        次）</span
      ><span>真实 API、Mock 与历史回放分别标注，不合并声称模型效果。</span>
    </div>
  </section>
</template>
<style scoped>
.history-foot {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: #a0adb3;
  font-size: 10px;
  border-top: 1px solid #eef2f3;
  padding-top: 18px;
  margin-top: 12px;
}
.history-actions {
  white-space: nowrap;
}
.history-actions a {
  display: flex;
  font-size: 11px;
  margin: 5px 0;
}
.subdued {
  color: #a0b0b6;
}
.table-title {
  max-width: 360px;
}
@media (max-width: 750px) {
  .history-foot {
    flex-direction: column;
  }
  .table-title {
    max-width: 220px;
  }
}
</style>
