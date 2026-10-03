<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  ArrowRight,
  ArrowUpRight,
  Plus,
  Network,
  Workflow,
  CheckCheck,
  Files,
  Landmark,
  MessageSquareText,
  Code2,
  Search,
  ShieldCheck,
  BookOpenCheck,
  RefreshCw,
  ChevronRight,
} from "@lucide/vue";
import { api } from "../lib/api";
import logoUrl from "../assets/logo.png";
import {
  datasetLabel,
  stateLabel,
  modeLabel,
  dateTime,
  shortId,
  errorText,
  type Json,
} from "../lib/format";
const router = useRouter(),
  runs = ref<Json[]>([]),
  cards = ref<Json[]>([]),
  graph = ref<Json | null>(null),
  loading = ref(true),
  error = ref("");
async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [r, c, g] = await Promise.all([
      api("/runs"),
      api("/capabilities"),
      api("/graph"),
    ]);
    runs.value = r.runs || [];
    cards.value = c.capabilities || [];
    graph.value = g;
  } catch (e) {
    error.value = errorText(e);
  } finally {
    loading.value = false;
  }
}
onMounted(load);
const completed = computed(
  () =>
    runs.value.filter((r) => ["passed", "completed"].includes(r.status)).length,
);
const active = computed(
  () =>
    runs.value.filter((r) =>
      ["running", "queued", "finalizing"].includes(r.status),
    ).length,
);
const stats = computed(() => [
  {
    label: "运行记录",
    value: runs.value.length,
    detail: "最近 50 次运行",
    icon: Workflow,
  },
  {
    label: "已通过验证",
    value: completed.value,
    detail: "按运行状态统计 · 含模拟",
    icon: CheckCheck,
  },
  {
    label: "可检索能力",
    value: cards.value.length,
    detail: "当前能力卡与版本",
    icon: BookOpenCheck,
  },
  {
    label: "知识关系",
    value: graph.value?.edges?.length,
    detail: "来自持久化知识图谱",
    icon: Network,
  },
]);
</script>
<template>
  <div class="page-heading">
    <div>
      <span class="eyebrow">ALGORITHM CAPABILITY WORKSPACE</span>
      <h1>把想法，变成可验证的算法能力</h1>
      <p>从描述需求开始，连接知识、生成代码，让每一步都有证据。</p>
    </div>
    <RouterLink to="/workbench" class="btn btn-primary"
      ><Plus :size="16" />创建新任务</RouterLink
    >
  </div>
  <div v-if="error" class="alert error" role="alert">
    {{ error }} <button class="text-link" @click="load">重新连接</button>
  </div>
  <section class="overview-hero panel">
    <div class="hero-copy">
      <span class="hero-badge"
        ><span class="status-dot online"></span>多角色 Agent · 知识增强 ·
        自动验证</span
      >
      <h2>让知识成为能力，<br />让结果经得起验证。</h2>
      <p>
        一个工作台，串联算法开发的完整闭环。<br />公开数据、可执行代码与可追溯报告，始终在一起。
      </p>
      <RouterLink to="/workbench" class="btn btn-primary"
        >开始能力复刻 <ArrowRight :size="15" /></RouterLink
      ><RouterLink to="/knowledge" class="hero-secondary"
        >探索知识图谱 <ArrowUpRight :size="14"
      /></RouterLink>
    </div>
    <div
      class="hero-flow"
      aria-label="需求进入算法工厂，经过知识检索、代码生成和验证后成为算法能力"
    >
      <div class="flow-grid"></div>
      <div class="orbit orbit-one"></div>
      <div class="orbit orbit-two"></div>
      <div class="flow-center">
        <img :src="logoUrl" alt="AxiomForge 标志" class="flow-logo" />
        <b>AxiomForge</b><small>知衡 · 能力编排引擎</small>
      </div>
      <div class="flow-node node-one">
        <span><MessageSquareText :size="17" /></span>
        <div><b>描述需求</b><small>自然语言输入</small></div>
      </div>
      <div class="flow-node node-two">
        <span><Network :size="17" /></span>
        <div><b>知识检索</b><small>找到实现依据</small></div>
      </div>
      <div class="flow-node node-three">
        <span><Code2 :size="17" /></span>
        <div><b>生成与修复</b><small>可运行的代码</small></div>
      </div>
      <div class="flow-node node-four">
        <span><ShieldCheck :size="17" /></span>
        <div><b>验证与沉淀</b><small>积累可复用能力</small></div>
      </div>
    </div>
  </section>
  <div class="metric-grid">
    <div v-for="stat in stats" :key="stat.label" class="stat-card panel">
      <div>
        <div class="stat-label">{{ stat.label }}</div>
        <div class="stat-number">
          {{ loading || error ? "—" : (stat.value ?? "—") }}
        </div>
        <div class="stat-description">{{ stat.detail }}</div>
      </div>
      <span class="stat-icon"><component :is="stat.icon" :size="20" /></span>
    </div>
  </div>
  <div class="home-columns">
    <section class="panel panel-pad scenario-panel">
      <div class="section-heading">
        <div>
          <h2>从一个场景开始</h2>
          <p>基于真实公开数据的可复现任务</p>
        </div>
        <span class="badge">2 个行业场景</span>
      </div>
      <div class="scenario-grid">
        <button
          class="scenario-card"
          @click="router.push('/workbench?dataset=bank')"
        >
          <div class="scenario-top">
            <span class="scenario-icon"><Landmark :size="22" /></span
            ><ArrowUpRight :size="17" />
          </div>
          <h3>银行营销响应预测</h3>
          <p>哪些客户更可能订购定期存款？<br />从通话前特征中发现有效信号。</p>
          <span class="scenario-tag"
            >表格分类 <span>·</span> UCI Bank Marketing</span
          ></button
        ><button
          class="scenario-card sms"
          @click="router.push('/workbench?dataset=sms')"
        >
          <div class="scenario-top">
            <span class="scenario-icon"><MessageSquareText :size="22" /></span
            ><ArrowUpRight :size="17" />
          </div>
          <h3>短信垃圾信息识别</h3>
          <p>让文本分类能力迁移到新场景，<br />比较 TF-IDF 与多种分类算法。</p>
          <span class="scenario-tag">文本分类 <span>·</span> UCI SMS Spam</span>
        </button>
      </div>
    </section>
    <section class="panel panel-pad process-panel">
      <div class="section-heading">
        <h2>一条完整的能力链路</h2>
        <Workflow :size="18" class="muted" />
      </div>
      <div
        class="process-step"
        v-for="(step, i) in [
          {
            title: '理解需求，召回知识',
            text: '将业务目标与能力来源关联',
            icon: Search,
          },
          {
            title: '规划方案，生成代码',
            text: '多角色协作与候选方案比较',
            icon: Code2,
          },
          {
            title: '独立验证，按需修复',
            text: '功能、接口、稳定性与指标检查',
            icon: ShieldCheck,
          },
          {
            title: '交付报告，沉淀经验',
            text: '保留制品、版本与验证依据',
            icon: BookOpenCheck,
          },
        ]"
        :key="i"
      >
        <span class="process-number">0{{ i + 1 }}</span>
        <div>
          <b>{{ step.title }}</b>
          <p>{{ step.text }}</p>
        </div>
        <component :is="step.icon" :size="16" />
      </div>
    </section>
  </div>
  <section class="panel recent-panel">
    <div class="section-heading">
      <div>
        <h2>最近运行</h2>
        <p>
          {{
            active ? `${active} 个任务正在处理` : "从历史运行继续查看验证结果"
          }}
        </p>
      </div>
      <RouterLink to="/history" class="text-link"
        >全部记录 <ChevronRight :size="15"
      /></RouterLink>
    </div>
    <div v-if="loading" class="loading-state">
      <RefreshCw class="spin" :size="20" /> 正在读取运行记录
    </div>
    <div v-else-if="!error && !runs.length" class="empty-state">
      <Files :size="30" />
      <h3>第一份验证报告，从一个需求开始</h3>
      <p>还没有运行记录。选择上方场景，或者创建自定义任务。</p>
    </div>
    <div v-else-if="!error" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>任务 / 运行编号</th>
            <th>行业场景</th>
            <th>执行方式</th>
            <th>状态</th>
            <th>创建时间</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="run in runs.slice(0, 5)" :key="run.run_id">
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
            <td class="muted">{{ dateTime(run.created_at) }}</td>
            <td>
              <RouterLink :to="`/runs/${run.run_id}`" class="text-link"
                >查看报告 <ArrowUpRight :size="14"
              /></RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
<style scoped>
.overview-hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 287px;
  overflow: hidden;
  background: linear-gradient(110deg, #f1f9f6, #eef8f3 45%, #f5faf8);
  border-color: #dfede5;
  margin-bottom: 24px;
}
.hero-copy {
  padding: 29px 34px;
  position: relative;
  z-index: 1;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 9px;
  font-weight: 500;
  color: #75a391;
  border: 1px solid #dcece3;
  background: #ffffff80;
  border-radius: 20px;
  padding: 5px 10px;
  margin-bottom: 16px;
}
.hero-badge .status-dot {
  width: 5px;
  height: 5px;
}
.hero-copy h2 {
  font-size: 27px;
  line-height: 1.65;
  color: #264f43;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}
.hero-copy p {
  font-size: 11px;
  line-height: 1.9;
  color: #88a197;
  margin-bottom: 19px;
}
.hero-copy .btn {
  font-size: 11px;
  padding: 8px 13px;
  min-height: 35px;
}
.hero-secondary {
  font-size: 11px;
  color: #679186;
  margin-left: 18px;
}
.hero-secondary svg {
  margin-left: 4px;
}
.hero-flow {
  position: relative;
  min-height: 285px;
  overflow: hidden;
}
.flow-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(#cde0d5 1px, transparent 1px);
  background-size: 18px 18px;
  mask-image: radial-gradient(ellipse, #0007, transparent 75%);
}
.flow-center {
  position: absolute;
  left: 50%;
  top: 49%;
  transform: translate(-50%, -50%);
  width: 114px;
  height: 115px;
  background: linear-gradient(135deg, #fff, #e3f3eb);
  border: 1px solid #d1e6d9;
  box-shadow: 0 14px 28px #1c644b0c;
  border-radius: 23px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #2f8b70;
  z-index: 2;
}
.flow-logo {
  width: 37px;
  height: 37px;
  object-fit: contain;
}
.flow-center b {
  font-size: 15px;
  margin-top: 5px;
  color: #367960;
}
.flow-center small {
  font-size: 8px;
  color: #8bab9b;
  margin-top: 5px;
  letter-spacing: 1px;
}
.orbit {
  position: absolute;
  top: 50%;
  left: 50%;
  border: 1px dashed #bedbcd;
  border-radius: 50%;
  transform: translate(-50%, -50%) rotate(-18deg);
  width: 300px;
  height: 195px;
}
.orbit-two {
  transform: translate(-50%, -50%) rotate(30deg);
  width: 350px;
  height: 245px;
  opacity: 0.6;
}
.flow-node {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #e0ece4;
  box-shadow: 0 4px 14px #215c4108;
  background: #ffffffee;
  border-radius: 9px;
  padding: 11px 13px;
  z-index: 3;
  min-width: 140px;
}
.flow-node > span {
  background: #edf8f1;
  border: 1px solid #e2efe6;
  border-radius: 7px;
  display: grid;
  place-items: center;
  width: 30px;
  height: 32px;
  color: #63a083;
}
.flow-node b {
  font-size: 10px;
  display: block;
  color: #5e7d6e;
}
.flow-node small {
  display: block;
  font-size: 8px;
  color: #9aafa4;
  margin-top: 4px;
}
.node-one {
  top: 36px;
  left: 15%;
}
.node-two {
  top: 80px;
  right: 5%;
}
.node-three {
  bottom: 37px;
  left: 8%;
}
.node-four {
  bottom: 22px;
  right: 10%;
}
.home-columns {
  display: grid;
  grid-template-columns: 1.8fr 1fr;
  gap: 22px;
  margin-bottom: 25px;
}
.scenario-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.scenario-card {
  text-align: left;
  border: 1px solid #e5eceb;
  border-radius: 10px;
  background: #fff;
  padding: 18px;
  transition:
    background 0.15s,
    border-color 0.15s;
}
.scenario-card:hover {
  background: #f5fbf8;
  border-color: #bedfcf;
}
.scenario-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #b7c4c6;
  margin-bottom: 13px;
}
.scenario-icon {
  display: grid;
  place-items: center;
  width: 39px;
  height: 39px;
  border-radius: 9px;
  background: #eaf6f0;
  color: #5aa089;
}
.scenario-card.sms .scenario-icon {
  background: #edf2fc;
  color: #7792c0;
}
.scenario-card h3 {
  font-size: 14px;
  margin-bottom: 9px;
}
.scenario-card p {
  font-size: 11px;
  line-height: 1.9;
  color: #97a5ac;
  margin-bottom: 17px;
}
.scenario-tag {
  font-size: 9px;
  color: #7b9096;
  display: flex;
  gap: 7px;
  border-top: 1px solid #edf1f0;
  padding-top: 12px;
}
.scenario-tag > span {
  color: #ced8d8;
}
.process-panel {
  padding: 24px 24px 16px;
}
.process-panel h2 {
  font-size: 16px;
}
.process-step {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 17px 0;
  position: relative;
}
.process-number {
  font-size: 9px;
  width: 24px;
  height: 24px;
  background: #f2f7f5;
  border: 1px solid #e1ebe5;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #8eaaa0;
  z-index: 1;
}
.process-step:not(:last-child)::after {
  content: "";
  height: 35px;
  width: 1px;
  background: #e8efeb;
  position: absolute;
  left: 12px;
  top: 20px;
}
.process-step b {
  font-size: 11px;
  font-weight: 550;
}
.process-step p {
  font-size: 9px;
  color: #9babb2;
  margin: 5px 0 0;
}
.process-step > svg {
  color: #9bbcaf;
  margin-left: auto;
}
.recent-panel {
  overflow: hidden;
}
.recent-panel > .section-heading {
  padding: 23px 24px 18px;
  margin-bottom: 0;
}
.recent-panel h2 {
  font-size: 17px;
}
@media (max-width: 1200px) {
  .hero-copy {
    padding: 25px;
  }
  .hero-copy h2 {
    font-size: 24px;
  }
  .flow-node {
    min-width: 120px;
    padding: 10px;
  }
  .node-two {
    right: 1%;
  }
  .node-one {
    left: 5%;
  }
  .node-three {
    left: 0;
  }
  .home-columns {
    grid-template-columns: 1.65fr 1fr;
  }
  .scenario-card {
    padding: 15px;
  }
  .process-panel {
    padding: 24px 18px;
  }
  .process-step > svg {
    display: none;
  }
}
@media (max-width: 1000px) {
  .home-columns {
    grid-template-columns: 1fr;
  }
  .process-panel {
    display: none;
  }
  .overview-hero {
    grid-template-columns: 1.1fr 1fr;
  }
  .hero-flow {
    transform: scale(0.85);
  }
  .hero-secondary {
    margin-left: 10px;
  }
}
@media (max-width: 600px) {
  .overview-hero {
    display: block;
  }
  .hero-flow {
    display: none;
  }
  .hero-copy {
    padding: 24px;
  }
  .hero-copy h2 {
    font-size: 25px;
  }
  .scenario-grid {
    grid-template-columns: 1fr;
  }
  .hero-secondary {
    margin-left: 15px;
  }
}
</style>
