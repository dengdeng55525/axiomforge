<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  Bot,
  Cpu,
  FlaskConical,
  ShieldCheck,
  RefreshCw,
  ArrowUpRight,
  Server,
  CheckCircle2,
  Info,
} from "@lucide/vue";
import { api } from "../lib/api";
import { errorText, type Json } from "../lib/format";
const config = ref<Json | null>(null),
  profiles = ref<Json | null>(null),
  loading = ref(true),
  error = ref("");
async function load() {
  loading.value = true;
  error.value = "";
  try {
    [config.value, profiles.value] = await Promise.all([
      api("/config"),
      api("/inference/profiles"),
    ]);
  } catch (e) {
    error.value = errorText(e);
  } finally {
    loading.value = false;
  }
}
onMounted(load);
const providers = computed<Json[]>(
  () => config.value?.providers?.providers || [],
);
const commands =
  "LOCAL_LLM_BASE_URL=http://127.0.0.1:8100/v1\nLOCAL_LLM_MODEL=coder_a\nLOCAL_LLM_PROFILE=four_gpu_14b";
</script>
<template>
  <div class="page-heading">
    <div>
      <span class="eyebrow">MODEL & ENVIRONMENT</span>
      <h1>模型与运行环境</h1>
      <p>
        了解当前后端连接与执行边界。密钥只在服务端配置，页面不会接收或显示密钥。
      </p>
    </div>
    <button class="btn" @click="load" :disabled="loading">
      <RefreshCw :size="15" :class="{ spin: loading }" />刷新配置
    </button>
  </div>
  <div v-if="error" class="alert error" role="alert">{{ error }}</div>
  <div v-if="loading" class="loading-state">正在读取环境配置…</div>
  <div class="backend-grid">
    <section
      v-for="p in providers"
      :key="p.id"
      class="panel panel-pad backend-card"
    >
      <span class="backend-icon"
        ><component
          :is="
            p.id === 'deepseek'
              ? Bot
              : p.id === 'local_http'
                ? Cpu
                : FlaskConical
          "
          :size="25"
      /></span>
      <div class="section-heading">
        <h2>{{ p.label }}</h2>
        <span
          :class="[
            'badge',
            p.id === 'local_http'
              ? 'warning'
              : p.available
                ? 'success'
                : 'warning',
          ]"
          >{{
            p.id === "local_http"
              ? "接入待验证"
              : p.available
                ? "已配置"
                : "未配置"
          }}</span
        >
      </div>
      <p>
        {{
          p.id === "deepseek"
            ? "通过真实 API 完成理解、规划、生成和修复。"
            : p.id === "local_http"
              ? "预留 OpenAI 兼容接口，支持后续部署本地 14B 模型。"
              : "固定规则生成候选，用于离线复现与工程测试。"
        }}
      </p>
      <dl>
        <dt>模型</dt>
        <dd>{{ p.model || "未记录" }}</dd>
        <dt>服务地址</dt>
        <dd>
          {{
            p.endpoint ||
            (p.id === "mock" ? "无需网络请求" : "未配置或地址无效")
          }}
        </dd>
      </dl>
      <p v-if="p.id === 'local_http'" class="small-note">
        配置存在不等于推理服务已启动。此页面未执行连通性或 GPU 吞吐测试。
      </p>
    </section>
  </div>
  <div class="grid-two settings-lower">
    <section class="panel panel-pad">
      <h2><Cpu :size="18" class="section-icon" />本地 14B · 四卡接入计划</h2>
      <p class="muted">
        4 × RTX
        4090D，每卡一个量化模型服务副本。单卡先运行，随后按配置扩展；模型权重与推理服务由部署者管理。
      </p>
      <div class="gpu-grid">
        <div v-for="n in 4" :key="n">
          <Cpu :size="20" /><b>GPU {{ n - 1 }}</b
          ><small>服务端口 {{ 8100 + n - 1 }}</small
          ><span class="badge warning">规划配置</span>
        </div>
      </div>
      <details>
        <summary>查看后端环境变量示例</summary>
        <pre>{{ commands }}</pre>
        <p class="muted">
          修改项目根目录 .env 后重启 API。服务部署步骤见 deploy/README.md 和
          scripts/plan_inference.py。
        </p>
      </details>
      <div class="alert info">
        这里只展示部署配置，没有下载权重、启动 GPU 服务或实测多卡性能。
      </div>
    </section>
    <section class="panel panel-pad">
      <h2><ShieldCheck :size="18" class="section-icon" />运行边界与数据约束</h2>
      <ul class="boundary-list">
        <li>
          <CheckCircle2 :size="17" />
          <div>
            <b>受限构造器语法检查</b>
            <p>生成代码通过 AST 策略检查，算法在受资源约束的独立进程验证。</p>
          </div>
        </li>
        <li>
          <CheckCircle2 :size="17" />
          <div>
            <b>统一验证与预算</b>
            <p>
              候选最多
              {{
                config?.limits?.max_candidates?.max ?? "—"
              }}
              个，每候选最多修复
              {{
                config?.limits?.max_repairs?.max ?? "—"
              }}
              次。缺失的观测不会填零或判为通过。
            </p>
          </div>
        </li>
        <li>
          <CheckCircle2 :size="17" />
          <div>
            <b>验证集与封存测试集分离</b>
            <p>候选搜索只使用验证集指标，封存测试集不用于优化和选择。</p>
          </div>
        </li>
        <li>
          <Info :size="17" />
          <div>
            <b>原型执行器的边界</b>
            <p>
              当前不是完整操作系统或容器安全沙箱；原型通过不等同于业务上线验收。
            </p>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>
<style scoped>
.backend-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}
.backend-card {
  min-width: 0;
}
.backend-icon {
  display: grid;
  place-items: center;
  width: 47px;
  height: 47px;
  background: #edf8f3;
  color: #499b81;
  border: 1px solid #deede5;
  border-radius: 12px;
  margin-bottom: 21px;
}
.backend-card h2 {
  font-size: 16px;
}
.backend-card > .section-heading {
  margin-bottom: 12px;
}
.backend-card p {
  font-size: 12px;
  color: #92a1aa;
  line-height: 1.9;
}
.backend-card dl {
  font-size: 11px;
  line-height: 1.9;
  border-top: 1px solid #eef2f1;
  padding-top: 15px;
}
.backend-card dt {
  color: #a3b0b5;
  font-size: 10px;
}
.backend-card dd {
  margin: 3px 0 13px;
  color: #637f75;
  overflow-wrap: anywhere;
}
.backend-card .small-note {
  font-size: 10px;
  color: #ac975f;
}
.settings-lower {
  margin-top: 24px;
  align-items: start;
}
.settings-lower > .panel > p {
  font-size: 12px;
  line-height: 1.9;
}
.gpu-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin: 24px 0;
}
.gpu-grid > div {
  display: flex;
  align-items: center;
  flex-direction: column;
  gap: 10px;
  padding: 16px 5px;
  border: 1px solid #e5edee;
  border-radius: 8px;
  color: #76a08d;
}
.gpu-grid b {
  font-size: 11px;
}
.gpu-grid small {
  font-size: 9px;
  color: #9cafb2;
}
.gpu-grid .badge {
  font-size: 8px;
}
.boundary-list {
  list-style: none;
  padding: 0;
  margin: 25px 0 0;
}
.boundary-list li {
  display: flex;
  gap: 14px;
  margin: 24px 0;
  color: #74a28f;
}
.boundary-list b {
  font-size: 12px;
  color: #607c73;
  font-weight: 550;
}
.boundary-list p {
  font-size: 11px;
  color: #9eafb3;
  line-height: 1.9;
  margin: 7px 0 0;
}
@media (max-width: 1150px) {
  .backend-grid {
    grid-template-columns: 1fr;
  }
  .backend-card {
    display: block;
  }
  .backend-card .backend-icon {
    float: left;
    margin-right: 15px;
  }
  .settings-lower {
    grid-template-columns: 1fr;
  }
}
</style>
