<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  Boxes,
  LayoutDashboard,
  Sparkles,
  Network,
  Files,
  Settings2,
  ChevronRight,
  ArrowUpRight,
  Menu,
  X,
  CircleHelp,
  RefreshCw,
} from "@lucide/vue";
import { api } from "./lib/api";
const route = useRoute(),
  router = useRouter(),
  mobileOpen = ref(false),
  healthy = ref<boolean | null>(null);
const nav = [
  { path: "/", name: "工作台概览", icon: LayoutDashboard },
  { path: "/workbench", name: "创建算法任务", icon: Sparkles },
  { path: "/history", name: "运行与报告", icon: Files },
  { path: "/knowledge", name: "知识探索", icon: Network },
  { path: "/settings", name: "模型与环境", icon: Settings2 },
];
const active = (path: string) =>
  path === "/"
    ? route.path === "/"
    : path === "/history"
      ? route.path.startsWith("/runs/") || route.path === path
      : route.path === path;
const help = ref(false),
  helpDialog = ref<HTMLElement | null>(null);
let priorFocus: HTMLElement | null = null;
watch(help, async (opened) => {
  if (opened) {
    priorFocus =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    await nextTick();
    helpDialog.value?.querySelector<HTMLButtonElement>("button")?.focus();
  } else {
    priorFocus?.focus();
  }
});
function focusMain() {
  document.getElementById("main-content")?.focus();
}
function dialogKeys(event: KeyboardEvent) {
  if (event.key === "Escape") {
    help.value = false;
    return;
  }
  if (event.key !== "Tab") return;
  const controls = helpDialog.value?.querySelectorAll<HTMLElement>(
    'button,a[href],input,select,textarea,[tabindex="0"]',
  );
  if (!controls?.length) return;
  const first = controls[0],
    last = controls[controls.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
async function check() {
  try {
    healthy.value = (await api("/health")).status === "ok";
  } catch {
    healthy.value = false;
  }
}
let timer: ReturnType<typeof setInterval>;
onMounted(() => {
  check();
  timer = setInterval(check, 30000);
});
onUnmounted(() => clearInterval(timer));
const pageTitle = computed(() => route.meta.title || "工作台概览");
</script>
<template>
  <a class="skip-link" href="#main-content" @click.prevent="focusMain"
    >跳转到主要内容</a
  >
  <button
    v-if="mobileOpen"
    class="sidebar-backdrop"
    aria-label="关闭导航"
    @click="mobileOpen = false"
  ></button>
  <aside class="sidebar" :class="{ open: mobileOpen }">
    <RouterLink to="/" class="brand" @click="mobileOpen = false"
      ><span class="brand-mark"><Boxes :size="25" /></span>
      <div><b>AlgoForge</b><span>算法能力工厂</span></div></RouterLink
    >
    <div class="workspace-label">
      <span class="workspace-dot"></span>研发工作空间<span
        class="badge version-badge"
        >v0.2</span
      >
    </div>
    <span class="nav-caption">WORKSPACE</span>
    <nav aria-label="主导航">
      <RouterLink
        v-for="item in nav"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: active(item.path) }"
        @click="mobileOpen = false"
        ><component :is="item.icon" :size="19" /><span>{{ item.name }}</span
        ><ChevronRight v-if="active(item.path)" :size="15" class="nav-arrow"
      /></RouterLink>
    </nav>
    <div class="sidebar-guide">
      <span class="mini-label">从需求到可验证的能力</span>
      <p>让每一次生成<br />都有依据与回响。</p>
      <RouterLink to="/workbench"
        >开启新任务 <ArrowUpRight :size="16"
      /></RouterLink>
      <div class="guide-orbits"></div>
    </div>
    <div class="sidebar-footer">
      <span class="avatar">AF</span>
      <div><b>本地研发环境</b><span>API / 本地模型兼容</span></div>
      <Settings2 :size="16" />
    </div>
  </aside>
  <div class="workspace">
    <header class="topbar">
      <div class="breadcrumb">
        <button
          class="icon-button mobile-menu"
          aria-label="打开导航"
          @click="mobileOpen = true"
        >
          <Menu :size="20" /></button
        ><span>研发工作空间</span><ChevronRight :size="14" /><b>{{
          pageTitle
        }}</b>
      </div>
      <div class="topbar-actions">
        <button
          class="service-indicator"
          @click="check"
          :title="healthy ? '点击重新检查连接' : '检查 API 服务是否已启动'"
        >
          <span
            :class="[
              'status-dot',
              healthy === true ? 'online' : healthy === false ? 'offline' : '',
            ]"
          ></span
          >{{
            healthy === true
              ? "服务已连接"
              : healthy === false
                ? "服务未连接"
                : "正在连接"
          }}</button
        ><span class="topbar-divider"></span
        ><button
          class="icon-button"
          aria-label="使用指南"
          title="使用指南"
          @click="help = true"
        >
          <CircleHelp :size="20" />
        </button>
      </div>
    </header>
    <main id="main-content" tabindex="-1"><RouterView /></main>
    <footer class="workspace-footer">
      <span>AlgoForge · 可追溯的算法研发</span
      ><span>能力抽取 → 复刻 → 验证 → 沉淀</span>
    </footer>
  </div>
  <div
    v-if="help"
    class="modal-backdrop"
    @click.self="help = false"
    @keydown.esc="help = false"
  >
    <section
      ref="helpDialog"
      class="modal panel"
      @keydown="dialogKeys"
      role="dialog"
      aria-modal="true"
      aria-labelledby="help-title"
    >
      <div class="section-heading">
        <h2 id="help-title">从这里开始</h2>
        <button class="icon-button" aria-label="关闭指南" @click="help = false">
          <X :size="20" />
        </button>
      </div>
      <ol class="help-steps">
        <li>
          <b>描述算法需求</b>
          <p>选择公开数据和推理后端，再用自然语言描述目标。可从示例开始。</p>
        </li>
        <li>
          <b>跟踪自动执行</b>
          <p>查看实际 Agent 事件；运行中可取消，不用保持页面打开。</p>
        </li>
        <li>
          <b>阅读验证报告</b>
          <p>比较候选和基线，展开检查与修复证据，下载代码和报告。</p>
        </li>
        <li>
          <b>探索知识与来源</b>
          <p>点击图谱节点查看来源，聚焦一跳或两跳邻域，将能力加入新任务。</p>
        </li>
      </ol>
      <button
        class="btn btn-primary"
        @click="
          help = false;
          router.push('/workbench');
        "
      >
        创建第一个任务 <ArrowUpRight :size="16" />
      </button>
    </section>
  </div>
</template>
