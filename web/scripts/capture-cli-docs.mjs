/**
 * Capture the command-line surface from a disposable, offline workspace.
 *
 * Run from the repository root with:
 *   node web/scripts/capture-cli-docs.mjs
 *
 * The command runner uses `axiomforge` with the mock provider, copies the
 * public fixtures into a temporary root, removes credential and proxy
 * variables, and never touches the repository SQLite database.  Screenshots
 * contain selected fields from the real JSON emitted by each command so the
 * documentation remains readable at normal zoom.
 */
import { chromium } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../..",
);
const output = path.join(root, "docs/images");
const cli = path.join(root, ".venv/bin/axiomforge");
const runIdPattern = /"run_id":\s*"([a-f0-9]{32})"/;
const temporaryRoot = await fs.mkdtemp(path.join(os.tmpdir(), "axiomforge-cli-docs-"));

const copy = async (name) => {
  await fs.cp(path.join(root, name), path.join(temporaryRoot, name), {
    recursive: true,
  });
};
for (const name of ["data", "docs", "knowledge", "configs"]) await copy(name);
await fs.mkdir(path.join(temporaryRoot, "artifacts"), { recursive: true });

const env = { ...process.env, ALGOFORGE_ROOT: temporaryRoot };
for (const key of [
  "DEEPSEEK_API_KEY",
  "OPENAI_API_KEY",
  "LOCAL_LLM_API_KEY",
  "OPENAI_PROXY_URL",
  "HTTP_PROXY",
  "HTTPS_PROXY",
  "ALL_PROXY",
  "http_proxy",
  "https_proxy",
  "all_proxy",
])
  delete env[key];

const command = (args, { allowFailure = false } = {}) => {
  try {
    return execFileSync(cli, args, {
      cwd: root,
      env,
      encoding: "utf8",
      maxBuffer: 64 * 1024 * 1024,
    }).trim();
  } catch (error) {
    if (!allowFailure) throw error;
    return String(error.stdout || error.output?.[1] || "").trim();
  }
};

const init = JSON.parse(command(["init", "--provider", "mock"]));
const runOutput = command([
  "run",
  "--description",
  "Build a traceable bank response classifier with calibrated probabilities and AP validation",
  "--dataset",
  "bank",
  "--provider",
  "mock",
  "--max-candidates",
  "2",
  "--max-repairs",
  "1",
  "--search",
  "compare",
]);
const run = JSON.parse(runOutput);
const runId = run.run_id.match(runIdPattern)?.[1] || run.run_id;
const doctor = JSON.parse(command(["doctor"]));
const status = JSON.parse(command(["status", "--recent", "2"]));
const cases = JSON.parse(command(["harness", "cases"]));
const suite = JSON.parse(command(["harness", "suite", runId], { allowFailure: true }));
const replay = JSON.parse(command(["harness", "replay", runId, "--through", "12"]));
const graphOutput = command([
  "export-graph",
  "--output",
  path.join(temporaryRoot, "artifacts/graph-export.json"),
]);
const reportOutput = command([
  "report",
  runId,
  "--format",
  "markdown",
  "--output",
  path.join(temporaryRoot, "artifacts/report-export.md"),
]);
const analysis = JSON.parse(command(["analyze-run", runId]));

const replaceTemp = (value) =>
  String(value).replaceAll(temporaryRoot, "$ALGOFORGE_ROOT");
const pretty = (value) => replaceTemp(JSON.stringify(value, null, 2));
const escape = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

const commandLine = (text) =>
  `<div class="command"><span class="prompt">$</span><span>${escape(text)}</span></div>`;
const outputBlock = (value, className = "") =>
  `<pre class="output ${className}">${escape(value)}</pre>`;
const shell = ({ eyebrow, title, subtitle, body }) => `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><style>
  :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; background: #07121f; color: #e8f1f5; }
  .canvas { width: 1800px; min-height: 1100px; padding: 52px 72px 64px; background:
    radial-gradient(circle at 84% 12%, rgba(25, 190, 168, .14), transparent 32%),
    linear-gradient(135deg, #07121f 0%, #0c1a29 55%, #0c1824 100%); }
  .masthead { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 38px; }
  .brand { display:flex; gap:16px; align-items:center; }
  .mark { width:52px; height:52px; border-radius:16px; display:grid; place-items:center; color:#06231f; background:linear-gradient(135deg,#58e5cc,#0ba895); font-size:28px; font-weight:900; box-shadow:0 8px 28px rgba(14, 194, 166, .3); }
  .brand-name { font-size:24px; font-weight:800; letter-spacing:.02em; }
  .brand-sub { margin-top:3px; color:#8ea5af; font-size:13px; letter-spacing:.08em; }
  .pill { border:1px solid rgba(109, 232, 210, .3); background:rgba(39, 197, 172, .10); border-radius:999px; color:#9ef1e1; padding:10px 16px; font-size:13px; }
  .eyebrow { color:#66e0ce; text-transform:uppercase; letter-spacing:.18em; font-weight:700; font-size:13px; margin-bottom:12px; }
  h1 { margin:0; font-size:42px; line-height:1.15; letter-spacing:-.035em; }
  .subtitle { color:#9db0ba; margin:14px 0 28px; font-size:18px; line-height:1.55; max-width:1200px; }
  .terminal { border-radius:22px; border:1px solid rgba(153, 206, 213, .18); background:rgba(7, 17, 29, .82); box-shadow:0 24px 70px rgba(0,0,0,.32); overflow:hidden; }
  .terminal-bar { display:flex; align-items:center; gap:8px; height:48px; padding:0 20px; border-bottom:1px solid rgba(153,206,213,.12); background:rgba(25,46,58,.55); }
  .dot { width:10px; height:10px; border-radius:50%; display:block; }
  .dot.red{background:#fb7185}.dot.yellow{background:#fbbf24}.dot.green{background:#34d399}
  .terminal-label { margin-left:10px; color:#9db2bd; font:600 12px ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing:.08em; }
  .body { padding:26px 30px 32px; }
  .command { display:flex; gap:14px; align-items:flex-start; color:#b4f8ed; font:600 17px/1.5 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; margin: 0 0 12px; }
  .prompt { color:#41dfbd; user-select:none; }
  .output { white-space:pre-wrap; overflow-wrap:anywhere; margin:0 0 26px; color:#cfdee3; font:500 15px/1.56 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
  .output.compact { color:#dce9eb; }
  .grid { display:grid; grid-template-columns: 1fr 1fr; gap:20px; }
  .panel { border:1px solid rgba(153,206,213,.16); border-radius:16px; padding:22px; background:rgba(14,31,44,.64); }
  .panel h2 { margin:0 0 15px; font-size:16px; color:#b4f8ed; }
  .kv { display:grid; grid-template-columns: 190px 1fr; gap:8px 18px; font:500 14px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; }
  .kv .key { color:#7e9ba5; }.kv .value { color:#e3f4f2; }
  .metric-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:22px; }
  .metric { border-radius:14px; padding:16px; background:rgba(35,65,77,.42); border:1px solid rgba(159,218,215,.12); }
  .metric-label { color:#87a4ad; font-size:12px; margin-bottom:8px; }.metric-value { color:#9ef1e1; font-size:26px; font-weight:800; }
  .tag { display:inline-block; margin:0 6px 6px 0; border-radius:999px; padding:5px 10px; color:#9cebdd; background:rgba(33,176,151,.13); border:1px solid rgba(79,226,199,.20); font-size:12px; }
  .footer { margin-top:28px; color:#6f8e9a; font:500 12px ui-monospace, SFMono-Regular, Menlo, monospace; }
  .split { display:grid; grid-template-columns:1fr 1fr; gap:22px; align-items:start; }
  .timeline { display:flex; flex-direction:column; gap:10px; }
  .event { display:grid; grid-template-columns:25px 1fr auto; gap:12px; align-items:center; border:1px solid rgba(150,212,211,.12); border-radius:11px; padding:10px 13px; background:rgba(22,49,61,.55); font:500 13px ui-monospace, SFMono-Regular, Menlo, monospace; }
  .event .num { color:#66e0ce; }.event .name { color:#d8eef0; }.event .status { color:#9de6d7; }
  .wide { grid-column:1 / -1; }
</style></head><body><main class="canvas">
  <header class="masthead"><div class="brand"><div class="mark">A</div><div><div class="brand-name">AxiomForge · 知衡</div><div class="brand-sub">ALGORITHM CAPABILITY FACTORY · OFFLINE CLI EVIDENCE</div></div></div><div class="pill">offline fixture · no provider call</div></header>
  <div class="eyebrow">${escape(eyebrow)}</div><h1>${escape(title)}</h1><p class="subtitle">${escape(subtitle)}</p>
  ${body}
</main></body></html>`;

const candidateSummary = run.candidates.map((candidate) => ({
  candidate_id: candidate.id,
  status: candidate.status,
  average_precision: Number(candidate.metrics.average_precision.toFixed(4)),
  roc_auc: Number(candidate.metrics.roc_auc.toFixed(4)),
  lift_at_10pct: Number(candidate.metrics.lift_at_10pct.toFixed(4)),
  repairs: candidate.repairs,
}));
const doctorView = {
  schema_version: doctor.schema_version,
  provider: doctor.provider,
  credential_configured: doctor.credential_configured,
  executor: doctor.executor,
  arbitrary_python_execution: doctor.arbitrary_python_execution,
  local_provider: {
    profile: doctor.local_provider.profile,
    status: doctor.local_provider.status,
    base_urls: doctor.local_provider.base_urls,
    served_model: doctor.local_provider.served_model,
  },
  datasets: doctor.datasets,
  gpu_status: {
    schema_version: doctor.gpu_status.schema_version,
    status: doctor.gpu_status.status,
    expected_count: doctor.gpu_status.expected_count,
    visible_count: doctor.gpu_status.visible_count,
    enabled_count: doctor.gpu_status.enabled_count,
    message: doctor.gpu_status.message,
  },
  checks: doctor.checks,
};
const statusView = {
  schema_version: status.schema_version,
  package: status.package,
  runtime: {
    framework: status.runtime.framework,
    version: status.runtime.version,
    retrieval_tool: status.runtime.retrieval_tool,
    evaluation_harness: status.runtime.evaluation_harness,
  },
  providers: status.providers.map((item) => ({
    id: item.id,
    kind: item.kind,
    configured: item.configured,
    model: item.model,
  })),
  gpu_status: {
    status: status.gpu_status.status,
    expected_count: status.gpu_status.expected_count,
    visible_count: status.gpu_status.visible_count,
    enabled_count: status.gpu_status.enabled_count,
  },
  knowledge: {
    status: status.knowledge.status,
    capabilities: status.knowledge.capabilities,
    nodes: status.knowledge.nodes,
    edges: status.knowledge.edges,
    runs: status.knowledge.runs,
  },
  datasets: status.datasets,
  executables: status.executables,
};
const caseView = cases.cases.map((item) => ({
  id: item.id,
  title: item.title,
  dataset_id: item.dataset_id,
  required_event_types: item.required_event_types.length,
  required_roles: item.required_roles.length,
  checks:
    item.required_event_types.length +
    item.required_roles.length +
    Number(Boolean(item.require_repair_evidence)) +
    Number(Boolean(item.require_selected_candidate)),
}));
const suiteSummary = {
  schema_version: suite.schema_version,
  run_id: suite.run_id,
  passed: suite.passed,
  score: suite.score,
  case_count: suite.case_count,
  passed_cases: suite.passed_cases,
  failed_case_ids: suite.failed_case_ids,
};
const replayView = {
  schema_version: replay.schema_version,
  run_id: replay.run_id,
  status: replay.status,
  mode: replay.mode,
  event_count: replay.event_count,
  total_event_count: replay.total_event_count,
  cursor_sequence: replay.cursor_sequence,
  is_replay: replay.is_replay,
  spans: replay.spans.map((span) => ({ name: span.name, role: span.role, status: span.status, attempt: span.attempt })),
};
const analysisView = {
  schema_version: analysis.schema_version,
  analysis_version: analysis.analysis_version,
  run_id: analysis.run_id,
  selected_candidate_id: analysis.selected_candidate_id,
  frontier_candidate_ids: analysis.frontier_candidate_ids,
  measurement_repetitions: analysis.measurement_repetitions,
  candidates: analysis.candidates.map((item) => ({
    candidate_id: item.candidate_id,
    average_precision: Number(item.average_precision.toFixed(4)),
    fit_seconds: Number(item.fit_seconds.toFixed(4)),
    peak_rss_mib: Number(item.peak_rss_mib.toFixed(2)),
    dominated_by: item.dominated_by,
  })),
};

const pages = [
  {
    filename: "cli-init.png",
    title: "CLI 初始化知识底座",
    eyebrow: "01 · initialize",
    subtitle: "以 mock provider 建立可复现的种子能力、来源索引和版本化知识底座。",
    body: `<section class="terminal"><div class="terminal-bar"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i><span class="terminal-label">axiomforge · init</span></div><div class="body">${commandLine("axiomforge init --provider mock")}${outputBlock(pretty(init), "compact")}<div class="footer">source: actual .venv/bin/axiomforge output · temporary root · sqlite writes isolated to /tmp</div></div></section>`,
    command: "axiomforge init --provider mock",
    sourceOutput: JSON.stringify(init),
  },
  {
    filename: "cli-doctor.png",
    title: "CLI 环境诊断与安全边界",
    eyebrow: "02 · doctor",
    subtitle: "诊断模型、数据集、执行器和 4 卡探测状态；凭据只呈现配置状态。",
    body: `<section class="terminal"><div class="terminal-bar"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i><span class="terminal-label">axiomforge · doctor</span></div><div class="body">${commandLine("axiomforge doctor")}${outputBlock(pretty(doctorView))}<div class="footer">process-local GPU probe · credentials redacted · external API calls disabled</div></div></section>`,
    command: "axiomforge doctor",
    sourceOutput: JSON.stringify(doctor),
  },
  {
    filename: "cli-status.png",
    title: "CLI 运行状态总览",
    eyebrow: "03 · status",
    subtitle: "从一个只读命令查看 LangChain 运行层、模型入口、图谱规模、数据集与 GPU 槽位。",
    body: `<section class="terminal"><div class="terminal-bar"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i><span class="terminal-label">axiomforge · status</span></div><div class="body">${commandLine("axiomforge status --recent 2")}${outputBlock(pretty(statusView))}<div class="footer">read-only snapshot · recent runs are loaded from the disposable local knowledge store</div></div></section>`,
    command: "axiomforge status --recent 2",
    sourceOutput: JSON.stringify(status),
  },
  {
    filename: "cli-run.png",
    title: "CLI 运行完整能力闭环",
    eyebrow: "04 · run",
    subtitle: "一次命令完成需求理解、知识检索、候选比较、验证和报告沉淀，输出可追溯 run_id。",
    body: `<section class="terminal"><div class="terminal-bar"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i><span class="terminal-label">axiomforge · run</span></div><div class="body">${commandLine("axiomforge run --description \"Build a traceable bank response classifier...\" --dataset bank --provider mock --max-candidates 2 --max-repairs 1 --search compare")}
      <div class="metric-row"><div class="metric"><div class="metric-label">run_id</div><div class="metric-value" style="font-size:18px">${escape(runId.slice(0, 8))}…</div></div><div class="metric"><div class="metric-label">status</div><div class="metric-value">${escape(run.status)}</div></div><div class="metric"><div class="metric-label">provider</div><div class="metric-value">${escape(run.mode)}</div></div><div class="metric"><div class="metric-label">selected</div><div class="metric-value">${escape(run.selected_candidate_id)}</div></div></div>
      ${outputBlock(pretty({ run_id: run.run_id, status: run.status, mode: run.mode, model: run.model, selected_candidate_id: run.selected_candidate_id, candidates: candidateSummary, usage: run.usage, report_paths: run.report_paths }), "compact")}<div class="footer">actual command output · deterministic mock provider · candidate metrics preserved from validation</div></div></section>`,
    command: "axiomforge run --provider mock --dataset bank --search compare",
    sourceOutput: runOutput,
  },
  {
    filename: "cli-harness-cases.png",
    title: "CLI Harness 用例目录",
    eyebrow: "05 · harness cases",
    subtitle: "评测规则以版本化 JSON 注册，覆盖端到端闭环、失败修复、跨任务迁移与轨迹脱敏。",
    body: `<section class="terminal"><div class="terminal-bar"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i><span class="terminal-label">axiomforge · harness cases</span></div><div class="body">${commandLine("axiomforge harness cases")}${outputBlock(pretty({ schema_version: cases.schema_version, path: cases.path, cases: caseView }))}<div class="footer">actual command output projected into a readable catalogue · no model call · no generated-code execution</div></div></section>`,
    command: "axiomforge harness cases",
    sourceOutput: JSON.stringify(cases),
  },
  {
    filename: "cli-harness-suite-replay.png",
    title: "CLI Harness 聚合评测与游标回放",
    eyebrow: "06 · suite + replay",
    subtitle: "先聚合检查多个评测用例，再沿固定游标回放前 12 个事件，定位角色交接与工具边界。",
    body: `<div class="split"><section class="terminal"><div class="terminal-bar"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i><span class="terminal-label">axiomforge · harness suite</span></div><div class="body">${commandLine(`axiomforge harness suite ${runId}`)}${outputBlock(pretty(suiteSummary))}</div></section><section class="terminal"><div class="terminal-bar"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i><span class="terminal-label">axiomforge · harness replay</span></div><div class="body">${commandLine(`axiomforge harness replay ${runId} --through 12`)}${outputBlock(pretty(replayView))}</div></section><section class="panel wide"><h2>回放游标中的 Agent spans</h2><div class="timeline">${replay.spans.map((span, index) => `<div class="event"><span class="num">${String(index + 1).padStart(2, "0")}</span><span class="name">${escape(span.role)} · ${escape(span.name)}</span><span class="status">${escape(span.status)}</span></div>`).join("")}</div></section></div>`,
    command: `axiomforge harness suite ${runId} && axiomforge harness replay ${runId} --through 12`,
    sourceOutput: `${JSON.stringify(suite)}\n${JSON.stringify(replay)}`,
  },
  {
    filename: "cli-export-report-analyze.png",
    title: "CLI 图谱、报告与资源分析",
    eyebrow: "07 · artifacts",
    subtitle: "将能力图谱导出为可移植 JSON，重新生成 Markdown 报告，并计算候选方案的 Pareto 前沿。",
    body: `<div class="split"><section class="terminal"><div class="terminal-bar"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i><span class="terminal-label">graph export</span></div><div class="body">${commandLine("axiomforge export-graph --output artifacts/graph-export.json")}${outputBlock(replaceTemp(graphOutput))}</div></section><section class="terminal"><div class="terminal-bar"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i><span class="terminal-label">report</span></div><div class="body">${commandLine(`axiomforge report ${runId} --format markdown --output artifacts/report-export.md`)}${outputBlock(replaceTemp(reportOutput))}</div></section><section class="terminal wide"><div class="terminal-bar"><i class="dot red"></i><i class="dot yellow"></i><i class="dot green"></i><span class="terminal-label">analyze-run</span></div><div class="body">${commandLine(`axiomforge analyze-run ${runId}`)}${outputBlock(pretty(analysisView))}<div class="footer">portable artifact paths are displayed relative to $ALGOFORGE_ROOT for documentation portability</div></div></section></div>`,
    command: `axiomforge export-graph && axiomforge report ${runId} && axiomforge analyze-run ${runId}`,
    sourceOutput: `${graphOutput}\n${reportOutput}\n${JSON.stringify(analysis)}`,
  },
];

await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({
    viewport: { width: 1800, height: 1100 },
    deviceScaleFactor: 1,
    locale: "zh-CN",
    timezoneId: "Asia/Shanghai",
    colorScheme: "dark",
  });
  const page = await context.newPage();
  for (const item of pages) {
    await page.setContent(shell(item), { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    const location = path.join(output, item.filename);
    await page.screenshot({ path: location, fullPage: true, animations: "disabled" });
    item.file = `docs/images/${item.filename}`;
    item.viewport = { width: 1800, height: 1100 };
    item.sha256 = createHash("sha256")
      .update(await fs.readFile(location))
      .digest("hex");
    item.source_output_sha256 = createHash("sha256")
      .update(item.sourceOutput)
      .digest("hex");
    delete item.body;
    delete item.sourceOutput;
  }
} finally {
  await browser.close();
}

const manifestPath = path.join(output, "capture-manifest.json");
const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
manifest.captured_at = new Date().toISOString();
manifest.source_base_commit = execFileSync("git", ["rev-parse", "HEAD"], {
  cwd: root,
  encoding: "utf8",
}).trim();
manifest.source_worktree_dirty = Boolean(
  execFileSync("git", ["status", "--porcelain"], {
    cwd: root,
    encoding: "utf8",
  }).trim(),
);
manifest.reproduction =
  "node web/node_modules/.bin/vue-tsc --noEmit && node web/node_modules/.bin/vite build && node web/scripts/capture-docs.mjs && node web/scripts/capture-cli-docs.mjs";
manifest.policy = {
  ...manifest.policy,
  cli_external_network_requests: 0,
  cli_provider_calls: 0,
  cli_live_database_writes: 0,
  cli_workspace: "disposable temporary root under /tmp",
};
manifest.captures = [
  ...manifest.captures.filter((item) => !item.file.startsWith("docs/images/cli-")),
  ...pages.map((item) => ({
    file: item.file,
    title: item.title,
    route: "cli",
    command: item.command,
    viewport: item.viewport,
    sha256: item.sha256,
    source_output_sha256: item.source_output_sha256,
    historical_run_id: item.command.includes(runId) ? runId : null,
    capture_type: "cli-offline-command",
  })),
];
await fs.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`Captured ${pages.length} CLI screenshots into docs/images/ from run ${runId}`);
