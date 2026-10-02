import { createApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import "./style.css";
const routes = [
  {
    path: "/",
    component: () => import("./views/HomeView.vue"),
    meta: { title: "工作台概览", group: "概览" },
  },
  {
    path: "/workbench",
    component: () => import("./views/WorkbenchView.vue"),
    meta: { title: "创建算法任务", group: "能力复刻" },
  },
  {
    path: "/runs/:id",
    component: () => import("./views/RunView.vue"),
    meta: { title: "验证报告", group: "能力复刻" },
  },
  {
    path: "/knowledge",
    component: () => import("./views/KnowledgeView.vue"),
    meta: { title: "知识探索", group: "能力知识库" },
  },
  {
    path: "/history",
    component: () => import("./views/HistoryView.vue"),
    meta: { title: "运行与报告", group: "验证中心" },
  },
  {
    path: "/settings",
    component: () => import("./views/SettingsView.vue"),
    meta: { title: "模型与环境", group: "系统" },
  },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];
const router = createRouter({
  history: createWebHashHistory("/app/"),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});
router.afterEach((to) => {
  document.title = `${String(to.meta.title)} · AxiomForge 知衡`;
});
createApp(App).use(router).mount("#app");
