<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  Sparkles,
  Send,
  Landmark,
  MessageSquareText,
  Network,
  ChevronDown,
  ShieldCheck,
  Database,
  SlidersHorizontal,
  Check,
  Bot,
  Cpu,
  FlaskConical,
  ArrowRight,
  ArrowUpRight,
  LoaderCircle,
  Save,
  FileCheck2,
  X,
} from "@lucide/vue";
import { ApiError, api } from "../lib/api";
import { errorText, type Json } from "../lib/format";
const route = useRoute(),
  router = useRouter(),
  config = ref<Json | null>(null),
  error = ref(""),
  submitting = ref(false),
  loading = ref(true),
  seedLoading = ref(true),
  ambiguousSubmit = ref(false);
let disposed = false;
const defaults: Record<string, string> = {
  bank: "预测客户是否订购银行定期存款。仅使用通话前可得特征，禁止使用 duration。比较两个算法候选，按验证集 AP 选择方案，并输出功能检查、来源依据、资源消耗和验证报告。",
  sms: "构建短信垃圾信息分类能力。比较 TF-IDF 与逻辑回归、朴素贝叶斯方案，保持训练、验证、测试隔离，报告 AP、F1 及接口稳定性检查结果。",
};
const dataset = ref(route.query.dataset === "sms" ? "sms" : "bank"),
  provider = ref("deepseek"),
  description = ref(""),
  maxCandidates = ref(2),
  maxRepairs = ref(2),
  search = ref("compare"),
  useGraph = ref(true),
  useRetrieval = ref(true),
  orchestration = ref("multi_role"),
  maxSeconds = ref(900),
  injectFailure = ref(false),
  scenarioNotice = ref(""),
  capability = ref<Json | null>(null),
  restored = ref(false),
  capabilityVersion = ref<number | null>(null);
const data = computed(() =>
  config.value?.datasets?.find((d: Json) => d.id === dataset.value),
);
const providers = computed<Json[]>(
  () => config.value?.providers?.providers || [],
);
const selectedProvider = computed(() =>
  providers.value.find((p) => p.id === provider.value),
);
const valid = computed(
  () =>
    !!config.value &&
    !loading.value &&
    !seedLoading.value &&
    description.value.trim().length >= 5 &&
    description.value.length <= 8000 &&
    !submitting.value &&
    Number.isInteger(Number(maxSeconds.value)) &&
    Number(maxSeconds.value) >= 10 &&
    Number(maxSeconds.value) <= 1800 &&
    data.value?.available === true &&
    !!selectedProvider.value &&
    (provider.value !== "deepseek" ||
      selectedProvider.value.available === true) &&
    !ambiguousSubmit.value,
);
const providerNames: Record<string, string> = {
  deepseek: "DeepSeek API",
  local_http: "本地大模型",
  mock: "Mock 演示",
};
const providerTips: Record<string, string> = {
  deepseek: "使用已配置的云端 LLM 接口",
  local_http: "14B · OpenAI 兼容 HTTP 服务",
  mock: "离线验证工程流程，不代表 LLM 效果",
};
function applyExample(id: string) {
  if (seedLoading.value || submitting.value || ambiguousSubmit.value) return;
  dataset.value = id;
  description.value = defaults[id];
  capability.value = null;
  restored.value = false;
  scenarioNotice.value = "";
}
function changeDataset() {
  if (seedLoading.value || submitting.value || ambiguousSubmit.value) return;
  if (Object.values(defaults).includes(description.value)) {
    description.value = defaults[dataset.value];
    scenarioNotice.value = "已同步切换示例需求。";
  } else if (description.value.trim()) {
    scenarioNotice.value = "已切换数据场景，请确认下方需求仍适用于所选数据。";
  }
  capability.value = null;
}
watch([description, dataset], ([value, id]) => {
  try {
    sessionStorage.setItem(
      "algoforge-draft",
      JSON.stringify({ description: value, dataset: id }),
    );
  } catch {
    /* Session storage can be disabled. */
  }
});
async function load() {
  if (disposed) return;
  loading.value = true;
  error.value = "";
  try {
    const result = await api<Json>("/config");
    if (!disposed) config.value = result;
  } catch (e) {
    if (!disposed) error.value = errorText(e);
  } finally {
    if (!disposed) loading.value = false;
  }
}
onMounted(async () => {
  await load();
  if (disposed) return;
  try {
    if (typeof route.query.from === "string") {
      const previous = await api(
        "/runs/" + encodeURIComponent(route.query.from),
      );
      const req = previous.request || {};
      description.value = previous.description || "";
      dataset.value = previous.dataset_id || "bank";
      provider.value = req.provider || previous.provider || "deepseek";
      maxCandidates.value = req.max_candidates ?? 2;
      maxRepairs.value = req.max_repairs ?? 2;
      useGraph.value = req.use_graph ?? true;
      useRetrieval.value = req.use_retrieval ?? true;
      search.value = req.search || "compare";
      orchestration.value = req.orchestration || "multi_role";
      maxSeconds.value = req.max_seconds ?? 900;
      injectFailure.value = req.inject_failure ?? false;
    } else if (typeof route.query.capability === "string") {
      const version = Number(route.query.version);
      capabilityVersion.value =
        Number.isInteger(version) && version > 0 ? version : null;
      const detail = await api(
        "/capabilities/" +
          encodeURIComponent(route.query.capability) +
          (capabilityVersion.value
            ? `?version=${capabilityVersion.value}`
            : ""),
      );
      capability.value = detail.card || detail.capability || detail;
      const card = capability.value!;
      dataset.value = (card.task_types || []).includes(
        "text_binary_classification",
      )
        ? "sms"
        : "bank";
      description.value =
        `${defaults[dataset.value]}\n参考能力：${card.name || route.query.capability}。${card.summary || ""}`.slice(
          0,
          8000,
        );
    } else if (route.query.dataset) {
      applyExample(dataset.value);
    } else {
      try {
        const draft = JSON.parse(
          sessionStorage.getItem("algoforge-draft") || "null",
        );
        if (draft?.description) {
          description.value = draft.description;
          dataset.value = draft.dataset === "sms" ? "sms" : "bank";
          restored.value = true;
        }
      } catch {
        /* An invalid draft is ignored. */
      }
    }
  } catch (e) {
    if (!disposed) error.value = errorText(e);
  } finally {
    if (!disposed) seedLoading.value = false;
  }
});
onBeforeUnmount(() => {
  disposed = true;
});
async function submit() {
  if (!valid.value) return;
  submitting.value = true;
  error.value = "";
  try {
    const run = await api("/runs", {
      method: "POST",
      body: JSON.stringify({
        description: description.value.trim(),
        dataset_id: dataset.value,
        provider: provider.value,
        max_candidates: Number(maxCandidates.value),
        max_repairs: Number(maxRepairs.value),
        search: search.value,
        use_graph: useGraph.value,
        use_retrieval: useRetrieval.value,
        orchestration: orchestration.value,
        max_seconds: Number(maxSeconds.value),
        inject_failure: injectFailure.value,
      }),
    });
    if (!run?.run_id) {
      ambiguousSubmit.value = true;
      error.value =
        "服务没有返回运行编号，无法确认任务是否已创建。请先到历史记录核对，再决定是否重新提交。";
      return;
    }
    try {
      sessionStorage.removeItem("algoforge-draft");
    } catch {}
    if (!disposed) await router.push("/runs/" + run.run_id);
  } catch (e) {
    const apiError = e instanceof ApiError ? e : undefined;
    const ambiguous =
      apiError?.ambiguous === true ||
      (apiError?.status !== undefined && apiError.status >= 500);
    if (ambiguous) {
      ambiguousSubmit.value = true;
      error.value =
        "提交结果不确定：服务可能已经创建任务，但响应没有可靠返回。请先到历史记录核对，确认没有新任务后再重新提交。";
    } else {
      error.value = errorText(e);
    }
  } finally {
    if (!disposed) submitting.value = false;
  }
}
function keyboard(event: KeyboardEvent) {
  if (event.isComposing) return;
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    void submit();
  }
}
</script>
<template>
  <div class="page-heading">
    <div>
      <span class="eyebrow">CREATE A CAPABILITY</span>
      <h1>描述需求，其余交给能力工厂</h1>
      <p>选择场景与推理后端，Agent 将检索知识、生成候选并完成独立验证。</p>
    </div>
    <RouterLink to="/history" class="btn"
      ><FileCheck2 :size="16" />历史报告</RouterLink
    >
  </div>
  <div v-if="ambiguousSubmit" class="alert error" role="alert">
    <strong>无法确认任务是否已创建</strong>
    <p>{{ error }}</p>
    <RouterLink class="text-link" to="/history">前往历史记录核对</RouterLink>
  </div>
  <div v-else-if="error" class="alert error" role="alert">
    {{ error }}
    <button v-if="!config" class="text-link" @click="load">重试连接</button>
  </div>
  <div class="create-layout">
    <section class="task-composer panel">
      <div class="composer-header">
        <span class="assistant-avatar"><Sparkles :size="22" /></span>
        <div>
          <h2>今天，你想构建什么能力？</h2>
          <p>写下业务目标、输入数据和约束，或从一个示例开始。</p>
        </div>
        <span class="badge">Agent 工作流</span>
      </div>
      <div class="starter-options">
        <button
          :disabled="submitting || seedLoading || ambiguousSubmit"
          @click="applyExample('bank')"
        >
          <Landmark :size="16" /><span>银行营销预测</span
          ><ArrowUpRight :size="13" /></button
        ><button
          :disabled="submitting || seedLoading || ambiguousSubmit"
          @click="applyExample('sms')"
        >
          <MessageSquareText :size="16" /><span>短信垃圾分类</span
          ><ArrowUpRight :size="13" />
        </button>
      </div>
      <form @submit.prevent="submit">
        <div class="prompt-area">
          <label for="task-description">你的能力需求</label
          ><textarea
            id="task-description"
            v-model="description"
            rows="8"
            maxlength="8000"
            :disabled="submitting || seedLoading || ambiguousSubmit"
            placeholder="例如：我想预测哪些银行客户更可能订购定期存款。只能使用通话前已知的特征，比较不同算法，并说明选择依据……"
            @keydown="keyboard"
          ></textarea>
          <div class="prompt-footer">
            <span v-if="restored"><Save :size="12" />已恢复本次会话草稿</span
            ><span v-else>包含业务目标和限制，有助于生成更合适的方案</span
            ><span>{{ description.length }} / 8000</span>
          </div>
        </div>
        <div v-if="capability" class="capability-context">
          <Network :size="16" />
          <div>
            已引用能力 <b>{{ capability.name }}</b>
            <span v-if="capabilityVersion || capability.version"
              >v{{ capabilityVersion || capability.version }}</span
            >
            <small>作为需求上下文，检索与验证仍按任务协议执行</small>
          </div>
          <button
            type="button"
            class="icon-button"
            aria-label="移除能力标签"
            :disabled="submitting || seedLoading || ambiguousSubmit"
            @click="capability = null"
          >
            <X :size="15" />
          </button>
        </div>
        <div class="composer-settings">
          <div class="form-row">
            <label class="field"
              >任务数据<select
                aria-label="任务数据"
                v-model="dataset"
                :disabled="submitting || seedLoading || ambiguousSubmit"
                @change="changeDataset"
              >
                <option value="bank">银行营销响应 · 表格分类</option>
                <option value="sms">短信垃圾信息 · 文本分类</option>
              </select></label
            ><label class="field"
              >候选策略<select
                aria-label="候选策略"
                v-model="search"
                :disabled="submitting || seedLoading || ambiguousSubmit"
              >
                <option value="compare">并列比较 · 评估多种算法</option>
                <option value="beam">Beam Search · 有界搜索优化</option>
              </select></label
            >
          </div>
          <p v-if="scenarioNotice" class="provider-note" role="status">
            {{ scenarioNotice }}
          </p>
          <div class="provider-heading">
            <b>推理后端</b
            ><RouterLink to="/settings"
              >连接设置 <ArrowUpRight :size="12"
            /></RouterLink>
          </div>
          <div v-if="loading" class="muted">正在读取后端配置…</div>
          <div class="provider-options">
            <label
              v-for="p in providers"
              :key="p.id"
              :class="['provider-option', { selected: provider === p.id }]"
              ><input
                v-model="provider"
                type="radio"
                :value="p.id"
                name="provider"
                :disabled="
                  submitting || seedLoading || ambiguousSubmit
                " /><component
                :is="
                  p.id === 'deepseek'
                    ? Bot
                    : p.id === 'local_http'
                      ? Cpu
                      : FlaskConical
                "
                :size="19" /><b>{{ providerNames[p.id] || p.label }}</b
              ><small>{{ providerTips[p.id] }}</small
              ><span class="provider-status">{{
                p.id === "local_http"
                  ? "接入待验证"
                  : p.available
                    ? "可用"
                    : "未配置凭证"
              }}</span
              ><Check
                v-if="provider === p.id"
                :size="14"
                class="provider-check"
            /></label>
          </div>
          <p v-if="provider === 'mock'" class="provider-note">
            Mock 会实际执行算法验证，但生成流程来自固定规则，不计作真实 LLM
            结果。
          </p>
          <p v-if="provider === 'local_http'" class="provider-note">
            需先启动本地 14B
            推理服务并配置后端。此处不下载权重；连接或响应异常会显示在运行报告中。
          </p>
          <details>
            <summary>
              <SlidersHorizontal :size="15" /> 高级设置
              <span class="muted">候选上限、修复与检索</span>
            </summary>
            <div class="form-row advanced-fields">
              <label class="field"
                >候选上限<select
                  v-model.number="maxCandidates"
                  :disabled="submitting || seedLoading || ambiguousSubmit"
                >
                  <option v-for="n in [1, 2, 3, 4, 5, 6]" :key="n" :value="n">
                    {{ n }} 个候选
                  </option>
                </select></label
              ><label class="field"
                >每个候选最多修复<select
                  v-model.number="maxRepairs"
                  :disabled="submitting || seedLoading || ambiguousSubmit"
                >
                  <option v-for="n in [0, 1, 2]" :key="n" :value="n">
                    {{ n }} 次
                  </option>
                </select></label
              ><label class="field"
                >编排方式<select
                  v-model="orchestration"
                  :disabled="submitting || seedLoading || ambiguousSubmit"
                >
                  <option value="multi_role">多角色协作</option>
                  <option value="single_shot">单次生成（消融）</option>
                </select></label
              ><label class="field"
                >总运行预算（秒）<input
                  v-model.number="maxSeconds"
                  :disabled="submitting || seedLoading || ambiguousSubmit"
                  type="number"
                  min="10"
                  max="1800"
                  required
              /></label>
            </div>
            <p class="advanced-caption">
              {{
                orchestration === "single_shot"
                  ? "单次生成只创建一个初始方案，不进行 Beam 扩展。"
                  : search === "compare"
                    ? "并列比较最多生成两个初始候选；更多候选请使用 Beam Search。"
                    : "Beam Search 在预算内扩展并比较候选变体。"
              }}
            </p>
            <div class="advanced-checks">
              <label class="checkbox-line"
                ><input
                  v-model="useGraph"
                  type="checkbox"
                  :disabled="submitting || seedLoading || ambiguousSubmit"
                />使用图谱关系增强检索</label
              ><label class="checkbox-line"
                ><input
                  v-model="useRetrieval"
                  type="checkbox"
                  :disabled="submitting || seedLoading || ambiguousSubmit"
                />注入来源证据上下文</label
              ><label class="checkbox-line"
                ><input
                  v-model="injectFailure"
                  type="checkbox"
                  :disabled="submitting || seedLoading || ambiguousSubmit"
                />注入标记故障（仅演示修复）</label
              >
            </div>
            <p class="advanced-caption">
              预算是上限，不保证一定生成全部候选。故障注入与自然失败在报告中分开记录。
            </p>
          </details>
        </div>
        <div class="composer-submit">
          <span><ShieldCheck :size="14" />固定数据协议 · 独立验证</span
          ><button type="submit" class="btn btn-primary" :disabled="!valid">
            <LoaderCircle v-if="submitting" :size="16" class="spin" /><Send
              v-else
              :size="16"
            />{{ submitting ? "正在提交…" : "开始构建与验证" }}
          </button>
        </div>
        <p class="shortcut-note">
          Ctrl / ⌘ + Enter 提交 · Enter 换行 · 支持中文输入法
        </p>
      </form>
    </section>
    <aside class="task-context">
      <section class="panel panel-pad data-card">
        <div class="section-heading">
          <h3><Database :size="16" class="section-icon" />本次数据协议</h3>
          <span :class="['badge', data?.available ? 'success' : 'warning']">{{
            data?.available ? "数据就绪" : "待检查"
          }}</span>
        </div>
        <b class="data-name">{{ data?.label || "正在读取数据契约" }}</b>
        <p>
          {{
            dataset === "bank"
              ? "仅使用通话前可获得的特征，阻止 duration 等信息泄漏。"
              : "按归一化文本分组去重，避免相同内容跨训练与验证切分。"
          }}
        </p>
        <dl v-if="data">
          <div>
            <dt>训练样本</dt>
            <dd>{{ data.train_rows?.toLocaleString() ?? "—" }}</dd>
          </div>
          <div>
            <dt>验证样本</dt>
            <dd>{{ data.validation_rows?.toLocaleString() ?? "—" }}</dd>
          </div>
          <div>
            <dt>封存测试集</dt>
            <dd>{{ data.sealed_test_rows?.toLocaleString() ?? "—" }}</dd>
          </div>
          <div>
            <dt>主评价指标</dt>
            <dd>AP</dd>
          </div>
        </dl>
        <div class="protocol-note">
          <ShieldCheck :size="15" /><span
            >封存测试集不参与候选选择。运行结果为验证集观测。</span
          >
        </div>
      </section>
      <section class="panel panel-pad delivery-card">
        <h3>你将获得</h3>
        <div
          v-for="item in [
            {
              title: '可运行的算法代码',
              text: '候选实现与代码哈希',
              icon: Bot,
            },
            {
              title: '清晰的验证报告',
              text: '指标、基线、检查与选择依据',
              icon: FileCheck2,
            },
            {
              title: '可追溯的知识证据',
              text: '来源、版本与修复经验',
              icon: Network,
            },
          ]"
          :key="item.title"
          class="delivery-item"
        >
          <component :is="item.icon" :size="17" />
          <div>
            <b>{{ item.title }}</b
            ><small>{{ item.text }}</small>
          </div>
        </div>
      </section>
      <div class="context-note">
        任务提交后会持续在后端运行。你可以离开页面，再从“运行与报告”返回查看。
      </div>
    </aside>
  </div>
</template>
<style scoped>
.create-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 290px;
  gap: 24px;
  align-items: start;
}
.composer-header {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 27px 28px 20px;
}
.composer-header h2 {
  font-size: 19px;
  margin: 0 0 6px;
}
.composer-header p {
  font-size: 11px;
  margin: 0;
  color: #8d9da5;
}
.composer-header > .badge {
  margin-left: auto;
  font-size: 10px;
}
.assistant-avatar {
  width: 45px;
  height: 45px;
  display: grid;
  place-items: center;
  color: #2d9d88;
  background: #eaf7f1;
  border: 1px solid #dcefe4;
  border-radius: 12px;
}
.starter-options {
  display: flex;
  gap: 10px;
  padding: 0 28px 22px;
}
.starter-options button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fafcfc;
  border: 1px solid #e5edee;
  border-radius: 7px;
  padding: 8px 10px;
  font-size: 11px;
  color: #6a8490;
}
.starter-options button > svg:first-child {
  color: #79a99a;
}
.prompt-area {
  margin: 0 28px;
  border: 1px solid #dde9e4;
  border-radius: 10px;
  overflow: hidden;
  background: #fdfefe;
}
.prompt-area:focus-within {
  border-color: #6aba9e;
  box-shadow: 0 0 0 3px #21a47f0a;
}
.prompt-area > label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  padding: 17px 18px 0;
  color: #719186;
}
.prompt-area textarea {
  width: 100%;
  border: 0;
  outline: none !important;
  padding: 12px 18px;
  background: transparent;
  font-size: 13px;
  min-height: 190px;
}
.prompt-area textarea::placeholder {
  color: #b4c0c3;
  line-height: 2;
}
.prompt-footer {
  padding: 9px 18px 12px;
  color: #a2b3b5;
  font-size: 9px;
  display: flex;
  justify-content: space-between;
  gap: 20px;
}
.prompt-footer svg {
  margin-right: 4px;
}
.composer-settings {
  padding: 24px 28px 6px;
}
.provider-heading {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin: 25px 0 12px;
}
.provider-heading > a {
  font-size: 10px;
  color: #7aa395;
}
.provider-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.provider-option {
  position: relative;
  padding: 15px 13px;
  border: 1px solid #e4ebed;
  border-radius: 9px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 7px;
  color: #7b8f96;
  min-height: 135px;
}
.provider-option.selected {
  border-color: #4eaa91;
  background: #f4fbf7;
}
.provider-option > input {
  position: absolute;
  opacity: 0;
  width: 1px;
  height: 1px;
}
.provider-option:focus-within {
  outline: 3px solid #8bd1bf;
}
.provider-option > b {
  font-size: 12px;
  color: #345749;
}
.provider-option > small {
  font-size: 9px;
  color: #a2b0b5;
  font-weight: 400;
  line-height: 1.7;
}
.provider-check {
  position: absolute;
  right: 10px;
  top: 12px;
  color: #23937b;
}
.provider-status {
  font-size: 9px;
  color: #91a39c;
}
.provider-note {
  font-size: 10px;
  line-height: 1.8;
  color: #a68558;
  margin: 12px 0;
}
.composer-settings details {
  margin: 20px 0 12px;
  padding: 14px;
  border: 0;
  border-top: 1px solid #eaf0ee;
  border-bottom: 1px solid #eaf0ee;
  border-radius: 0;
}
.composer-settings summary {
  font-size: 11px;
  color: #748991;
}
.composer-settings summary svg {
  margin: 0 6px;
}
.composer-settings summary > span {
  font-size: 10px;
  margin-left: 10px;
  font-weight: 400;
}
.advanced-fields {
  padding: 12px 0;
}
.advanced-checks {
  display: grid;
  gap: 12px;
  margin: 15px 0;
}
.advanced-caption {
  font-size: 10px;
  color: #95a3ab;
  margin: 15px 0 0;
}
.composer-submit {
  padding: 12px 28px 3px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.composer-submit > span {
  font-size: 10px;
  color: #8faaa0;
}
.composer-submit > span svg {
  margin-right: 5px;
}
.shortcut-note {
  font-size: 9px;
  text-align: right;
  color: #afbabd;
  margin: 8px 28px 20px;
}
.task-context {
  display: grid;
  gap: 18px;
}
.data-card {
  padding: 22px;
}
.data-card h3 {
  font-size: 13px;
}
.data-card .badge {
  font-size: 9px;
}
.data-name {
  display: block;
  font-size: 12px;
  color: #5b8070;
}
.data-card p {
  font-size: 11px;
  line-height: 1.85;
  color: #96a6ad;
  margin-top: 10px;
  margin-bottom: 17px;
}
.data-card dl {
  font-size: 11px;
  margin: 18px 0;
}
.data-card dl > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 0;
  border-bottom: 1px solid #f1f4f3;
}
.data-card dt {
  color: #95a5ad;
}
.data-card dd {
  margin: 0;
  color: #667e77;
  font-variant-numeric: tabular-nums;
}
.protocol-note {
  display: flex;
  gap: 8px;
  line-height: 1.8;
  font-size: 10px;
  color: #91a59a;
  background: #f6faf7;
  border-radius: 6px;
  padding: 11px;
}
.protocol-note svg {
  margin-top: 3px;
}
.delivery-card h3 {
  font-size: 13px;
}
.delivery-item {
  display: flex;
  gap: 12px;
  margin: 22px 0;
  color: #80a998;
}
.delivery-item:last-child {
  margin-bottom: 2px;
}
.delivery-item b {
  font-size: 11px;
  color: #6f827b;
  font-weight: 500;
  display: block;
}
.delivery-item small {
  font-size: 9px;
  display: block;
  color: #a8b5ba;
  margin-top: 5px;
}
.context-note {
  padding: 0 14px;
  font-size: 10px;
  line-height: 1.9;
  color: #a0b0b6;
}
.capability-context {
  display: flex;
  gap: 8px;
  align-items: center;
  background: #eef8f3;
  color: #4b8f78;
  padding: 12px 15px;
  margin: 14px 28px;
  border-radius: 8px;
  font-size: 11px;
}
.capability-context small {
  display: block;
  font-size: 9px;
  color: #91ac9e;
  margin-top: 5px;
}
.capability-context button {
  margin-left: auto;
}
@media (max-width: 1150px) {
  .create-layout {
    grid-template-columns: minmax(0, 1fr) 240px;
    gap: 18px;
  }
  .composer-header,
  .composer-settings {
    padding: 22px 20px;
  }
  .prompt-area {
    margin: 0 20px;
  }
  .starter-options {
    padding-left: 20px;
  }
  .composer-header > .badge {
    display: none;
  }
  .provider-option {
    padding: 12px 9px;
  }
  .data-card {
    padding: 18px;
  }
}
@media (max-width: 1000px) {
  .create-layout {
    grid-template-columns: 1fr;
  }
  .task-context {
    grid-template-columns: 1fr 1fr;
  }
  .context-note {
    grid-column: 1/-1;
  }
}
@media (max-width: 550px) {
  .task-context {
    grid-template-columns: 1fr;
  }
  .provider-options {
    grid-template-columns: 1fr;
  }
  .provider-option {
    min-height: 90px;
    padding-left: 45px;
  }
  .provider-option > svg:first-of-type {
    position: absolute;
    left: 13px;
    top: 18px;
  }
  .composer-header h2 {
    font-size: 16px;
  }
  .composer-header p {
    font-size: 10px;
  }
  .composer-submit {
    padding: 10px 20px;
    align-items: stretch;
    flex-direction: column;
  }
  .composer-submit > .btn {
    width: 100%;
  }
  .prompt-footer > span:first-child {
    max-width: 65%;
  }
}
</style>
