/** Capture current UI with immutable historical evidence and no external calls.
 * From repository root: npm --prefix web run build && node web/scripts/capture-docs.mjs
 */
import { chromium, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../..",
);
const dist = path.join(root, "web/dist");
const output = path.join(root, "docs/images");
const python =
  process.env.AXIOMFORGE_DOCS_PYTHON || path.join(root, ".venv/bin/python");
const fixtures = JSON.parse(
  execFileSync(python, [path.join(root, "scripts/capture_docs_fixtures.py")], {
    cwd: root,
    encoding: "utf8",
    maxBuffer: 30 * 1024 * 1024,
  }),
);
const reportId = "660682f3cf324bf1938b78c70f2fce8c";
const report = fixtures.reports[reportId];
if (!report || report.status !== "passed")
  throw new Error("Required historical evidence is unavailable");
const files = await fs.readdir(path.join(dist, "assets"));
const buildHash = createHash("sha256");
for (const file of files.sort())
  buildHash
    .update(file)
    .update(await fs.readFile(path.join(dist, "assets", file)));

async function sourceInputs(directory) {
  const entries = await fs.readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    const location = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await sourceInputs(location)));
    else files.push(location);
  }
  return files;
}
const sourceFiles = [
  ...(await sourceInputs(path.join(root, "web/src"))),
  ...[
    "web/index.html",
    "web/vite.config.ts",
    "web/package-lock.json",
    "web/scripts/capture-docs.mjs",
    "scripts/capture_docs_fixtures.py",
  ].map((file) => path.join(root, file)),
];
const sourceHashes = await Promise.all(
  sourceFiles.map(async (file) => ({
    path: path.relative(root, file),
    sha256: createHash("sha256")
      .update(await fs.readFile(file))
      .digest("hex"),
  })),
);

const mime = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".png": "image/png",
};
const server = createServer(async (request, response) => {
  try {
    const pathname = new URL(request.url, "http://127.0.0.1").pathname.replace(
      /^\/app\//,
      "/",
    );
    const filename = path.resolve(
      dist,
      `.${pathname === "/" ? "/index.html" : pathname}`,
    );
    if (!filename.startsWith(`${dist}${path.sep}`))
      throw new Error("Invalid static path");
    const body = await fs.readFile(filename);
    response.writeHead(200, {
      "Content-Type":
        mime[path.extname(filename)] || "application/octet-stream",
    });
    response.end(body);
  } catch {
    response.writeHead(404);
    response.end("Unknown documentation asset");
  }
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const gpuEmpty = {
  schema_version: "gpu-status.v1",
  status: "unavailable",
  source: "documentation_fixture",
  expected_count: 4,
  visible_count: 0,
  enabled_count: 0,
  message: "离线文档快照 · 当前使用 CPU / Mock 配置",
  devices: Array.from({ length: 4 }, (_, index) => ({
    index,
    label: `GPU ${index}`,
    state: "unavailable",
    enabled: false,
  })),
};
const gpuExample = {
  ...gpuEmpty,
  status: "partial",
  visible_count: 2,
  enabled_count: 2,
  message: "文档交互示例 · 模拟 2/4 卡可见状态",
  devices: gpuEmpty.devices.map((device) =>
    [0, 2].includes(device.index)
      ? {
          ...device,
          state: "enabled",
          enabled: true,
          name: "NVIDIA GeForce RTX 4090 D",
          utilization_percent: device.index === 0 ? 32 : 18,
          memory_used_mib: device.index === 0 ? 16384 : 12288,
          memory_total_mib: 24564,
          temperature_c: device.index === 0 ? 54 : 47,
        }
      : device,
  ),
};
let gpu = gpuEmpty;
const errors = [];
const captures = [];
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1,
    timezoneId: "Asia/Shanghai",
    locale: "zh-CN",
    colorScheme: "light",
  });
  const page = await context.newPage();
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.origin !== origin)
      throw new Error(`External request blocked: ${url.origin}`);
    if (!["fetch", "xhr"].includes(request.resourceType()))
      return route.continue();
    if (request.method() !== "GET")
      throw new Error(
        `Mutation blocked during capture: ${request.method()} ${url.pathname}`,
      );
    let json;
    if (url.pathname === "/health") json = { status: "ok", gpu_status: gpu };
    else if (url.pathname === "/system/gpus") json = gpu;
    else if (url.pathname === "/config") json = fixtures.config;
    else if (url.pathname === "/inference/profiles") json = fixtures.profiles;
    else if (url.pathname === "/capabilities")
      json = { capabilities: fixtures.capabilities };
    else if (url.pathname.startsWith("/capabilities/"))
      json =
        fixtures.capability_details[
          decodeURIComponent(url.pathname.split("/")[2])
        ];
    else if (url.pathname === "/graph") json = fixtures.graph;
    else if (url.pathname === "/graph/explore")
      json = fixtures.graph_views[url.searchParams.get("focus") || ""];
    else if (url.pathname === "/knowledge/quality")
      json = fixtures.knowledge_quality;
    else if (url.pathname === "/runs") json = { runs: fixtures.runs };
    else if (/^\/runs\/[^/]+(?:\/report)?$/.test(url.pathname))
      json = fixtures.reports[url.pathname.split("/")[2]];
    if (json === undefined)
      return route.fulfill({
        status: 404,
        json: { detail: `No snapshot for ${url.pathname}` },
      });
    return route.fulfill({ json });
  });
  const ready = async (route, heading) => {
    await page.goto(`${origin}/app/#${route}`);
    await expect(
      page.getByRole("heading", { name: heading, exact: true }),
    ).toBeVisible();
    await expect(page.locator(".brand")).toContainText("AxiomForge");
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
  };
  const capture = async (filename, title, route, options = {}) => {
    const location = path.join(output, filename);
    await page.screenshot({
      path: location,
      animations: "disabled",
      ...options,
    });
    captures.push({
      file: `docs/images/${filename}`,
      title,
      route,
      viewport: page.viewportSize(),
      sha256: createHash("sha256")
        .update(await fs.readFile(location))
        .digest("hex"),
      historical_run_id: route.startsWith("/runs/")
        ? route.split("/")[2]
        : null,
      gpu_fixture:
        gpu === gpuExample
          ? "explicitly-labelled-2-of-4-simulation"
          : "offline-cpu-configuration",
    });
  };
  await fs.mkdir(output, { recursive: true });
  await ready("/", "把想法，变成可验证的算法能力");
  await expect(page.locator(".stat-number").first()).toHaveText(
    String(fixtures.runs.length),
  );
  await capture("workbench-overview.png", "工作台概览", "/");

  await page.setViewportSize({ width: 1440, height: 1200 });
  await ready(
    "/workbench?dataset=sms&provider=mock",
    "描述需求，其余交给能力工厂",
  );
  await page.getByLabel("你的能力需求").fill(report.description);
  await capture(
    "task-workbench.png",
    "任务配置与自然语言需求",
    "/workbench?dataset=sms&provider=mock",
  );

  await page.setViewportSize({ width: 1440, height: 1160 });
  await ready("/settings", "模型与运行环境");
  await capture("model-settings.png", "API 与本地模型配置", "/settings");

  gpu = gpuExample;
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.reload();
  await expect(page.getByTestId("gpu-status")).toContainText("2/4");
  await page.getByTestId("gpu-status").locator("summary").click();
  await capture(
    "gpu-status-bar.png",
    "GPU 状态栏（明确标注的模拟状态）",
    "/settings",
  );
  gpu = gpuEmpty;
  await page.reload();
  await expect(page.getByTestId("gpu-status")).toContainText("0/4");

  await page.setViewportSize({ width: 1440, height: 1080 });
  await ready(`/runs/${reportId}`, "验证报告");
  await expect(page.locator(".primary-metric")).toContainText("0.9598");
  await capture(
    "workbench-report.png",
    "独立验证报告与历史 API 指标",
    `/runs/${reportId}`,
  );

  const trace = page.getByTestId("agent-trace-panel");
  await trace.getByText("展开时序与预算详情").click();
  await trace.scrollIntoViewIfNeeded();
  await page.evaluate(() => {
    const node = document.querySelector('[data-testid="agent-trace-panel"]');
    window.scrollTo(0, node.getBoundingClientRect().top + window.scrollY - 20);
  });
  await capture(
    "agent-observability.png",
    "历史事件投影、Agent 时序与预算",
    `/runs/${reportId}`,
  );

  const resourceRunId = "99066c21c7f64134bcde65a0ef068473";
  await ready(`/runs/${resourceRunId}`, "验证报告");
  const resources = page.locator(".resource-analysis");
  await resources.scrollIntoViewIfNeeded();
  await page.evaluate(() => {
    const node = document.querySelector(".resource-analysis");
    window.scrollTo(0, node.getBoundingClientRect().top + window.scrollY - 20);
  });
  await page.setViewportSize({ width: 1440, height: 620 });
  await capture(
    "resource-tradeoffs.png",
    "本地模型候选质量与资源实测权衡",
    `/runs/${resourceRunId}`,
  );

  await page.setViewportSize({ width: 1680, height: 1100 });
  await ready("/knowledge", "让每一项能力，都有据可循");
  await expect(page.locator(".graph-node").first()).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 290));
  await page.waitForTimeout(900);
  await capture(
    "workbench-graph.png",
    "来源、能力与历史验证组成的知识图谱",
    "/knowledge",
  );

  if (errors.length) throw new Error(`Browser errors: ${errors.join("; ")}`);
  const manifestPath = path.join(output, "capture-manifest.json");
  let preservedCliCaptures = [];
  try {
    const previous = JSON.parse(await fs.readFile(manifestPath, "utf8"));
    preservedCliCaptures = (previous.captures || []).filter(
      (item) => item.capture_type === "cli-offline-command",
    );
  } catch {
    preservedCliCaptures = [];
  }
  await fs.writeFile(
    manifestPath,
    `${JSON.stringify(
      {
        schema_version: "documentation-capture.v1",
        brand: "AxiomForge · 知衡",
        captured_at: new Date().toISOString(),
        source_base_commit: execFileSync("git", ["rev-parse", "HEAD"], {
          cwd: root,
          encoding: "utf8",
        }).trim(),
        source_worktree_dirty: Boolean(
          execFileSync("git", ["status", "--porcelain"], {
            cwd: root,
            encoding: "utf8",
          }).trim(),
        ),
        source_inputs: sourceHashes,
        build_assets_sha256: buildHash.digest("hex"),
        reproduction:
          "npm --prefix web run build && node web/scripts/capture-docs.mjs",
        policy: {
          requests_intercepted: true,
          external_network_requests: 0,
          provider_calls: 0,
          live_database_writes: 0,
          metrics_fabricated: false,
          context:
            "Historical reports rendered by current UI. Default empty-credential configuration. GPU demonstration is visibly labelled as simulated.",
        },
        provenance: fixtures.provenance,
        captures: [...captures, ...preservedCliCaptures],
      },
      null,
      2,
    )}\n`,
  );
  console.log(
    `Captured ${captures.length} current AxiomForge screenshots into docs/images/`,
  );
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
