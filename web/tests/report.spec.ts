import { test, expect, type Page } from "@playwright/test";
import fs from "node:fs";

// Historical, committed evidence provides the same shape as the real API. All
// API requests in these tests are intercepted: no paid provider is contacted.
const historical = JSON.parse(
  fs.readFileSync(
    new URL("../../examples/evidence/bank_beam/report.json", import.meta.url),
    "utf8",
  ),
);
const passed = { ...historical, run_id: "passed" };
const failed = {
  ...structuredClone(historical),
  run_id: "failed",
  status: "failed",
  selected_candidate_id: null,
  quality_status: "not_evaluated",
  failure_reason: "No candidate passed independent validation within budget",
  candidates: [
    {
      candidate_id: "early_fail",
      status: "failed",
      checks: [
        {
          name: "source_policy",
          passed: false,
          mandatory: true,
          detail: "bad entrypoint",
        },
      ],
      metrics: {},
      attempts: [],
      repairs: [],
      error: { type: "CodePolicyError", message: "bad entrypoint" },
    },
  ],
};
const empty = {
  run_id: "empty",
  status: "cancelled",
  mode: "mock",
  provider: "mock",
  description: "空候选终止",
  candidates: [],
  events: [],
  finished_at: "2026-09-29T00:00:00Z",
};
const low = structuredClone(passed);
low.run_id = "low";
low.quality_status = "baseline_or_worse";
low.candidates[0].quality_status = "baseline_or_worse";
low.candidates[0].metrics.average_precision = 0.08;
low.candidates[0].metrics.ap_improvement_over_dummy = -0.0307;
low.candidates[0].checks.find(
  (item: { name: string }) => item.name === "ap_above_dummy",
).passed = false;

async function intercept(page: Page) {
  const counts: Record<string, number> = {};
  let pollPhase = 0;
  let cancelled = false;
  const fixtures: Record<string, unknown> = { passed, failed, empty, low };
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await page.context().route(/\/runs\/[^/?]+(?:\/[^?]+)?$/, async (route) => {
    const [, , identity, ...tail] = new URL(
      route.request().url(),
    ).pathname.split("/");
    counts[identity] = (counts[identity] || 0) + 1;
    if (tail[0] === "artifacts")
      return route.fulfill({
        json: {
          code: "# <img src=x onerror=alert(1)>\ndef build_pipeline(task_spec):\n    pass\n",
          code_sha256: "test",
        },
      });
    if (tail[0] === "report")
      return route.fulfill({ json: fixtures[identity] || passed });
    if (tail[0] === "report.md")
      return route.fulfill({
        contentType: "text/markdown",
        body: "# Validation report\n\nHistorical evidence.",
      });
    if (tail[0] === "report.html")
      return route.fulfill({
        contentType: "text/html",
        body: "<h1>Validation report</h1>",
      });
    if (identity === "missing")
      return route.fulfill({ status: 404, json: { detail: "Unknown run" } });
    if (identity === "cancel") {
      if (tail[0] === "cancel" && route.request().method() === "POST") {
        cancelled = true;
        return route.fulfill({
          json: { run_id: identity, status: "running", cancel_requested: true },
        });
      }
      return route.fulfill({
        json: {
          ...passed,
          run_id: identity,
          selected_candidate_id: null,
          status: cancelled ? "cancelled" : "running",
        },
      });
    }
    if (identity === "poll") {
      const state = ["queued", "running", "finalizing", "passed"][
        Math.min(pollPhase++, 3)
      ];
      return route.fulfill({
        json: { ...passed, run_id: identity, status: state },
      });
    }
    if (identity === "stale") {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      return route
        .fulfill({
          json: {
            ...passed,
            run_id: "stale",
            description: "STALE_SHOULD_NOT_RENDER",
          },
        })
        .catch(() => {});
    }
    return route.fulfill({ json: fixtures[identity] || passed });
  });
  return counts;
}

async function openReport(page: Page, identity: string) {
  await page.goto(`#/runs/${identity}`);
  await expect(
    page.getByRole("heading", { name: "验证报告", exact: true }),
  ).toBeVisible();
}

for (const [deployment, label] of [
  ["official_api", "OpenAI 官方 API · Responses"],
  ["openai_compatible_api", "OpenAI 兼容服务 · Responses"],
  [undefined, "OpenAI Responses API"],
] as const) {
  test(`report preserves Responses provider identity: ${deployment || "legacy metadata"}`, async ({
    page,
  }) => {
    await intercept(page);
    const fixture = {
      ...structuredClone(passed),
      run_id: "responses-report",
      mode: "real",
      provider: "openai",
      provider_metadata: { deployment },
    };
    await page.route(
      new RegExp("/runs/responses-report(?:/report)?$"),
      (route) => route.fulfill({ json: fixture }),
    );
    await openReport(page, "responses-report");
    await expect(page.locator(".mode-badge")).toHaveText(label);
    await expect(page.locator("details[open]")).toHaveCount(0);
  });
}

test("resource tradeoffs show measured costs and keep audit details folded", async ({
  page,
}) => {
  await intercept(page);
  const fixture = structuredClone(passed);
  fixture.run_id = "pareto";
  fixture.optimization = {
    analysis_version: "pareto-observations-v1",
    frontier_candidate_ids: ["fixture_quality", "fixture_fast"],
    candidates: [
      {
        candidate_id: "fixture_quality",
        average_precision: 0.9,
        fit_seconds: 2,
        peak_rss_mib: 200,
        pareto_optimal: true,
      },
      {
        candidate_id: "fixture_fast",
        average_precision: 0.8,
        fit_seconds: 1,
        peak_rss_mib: 100,
        pareto_optimal: true,
      },
    ],
    excluded: [
      {
        candidate_id: "fixture_missing",
        reason: "missing_or_invalid_measurements",
      },
    ],
  };
  await page.route(/\/runs\/pareto(?:\/report)?$/, (route) =>
    route.fulfill({ json: fixture }),
  );
  await openReport(page, "pareto");
  const panel = page.locator("section").filter({
    has: page.getByRole("heading", { name: "质量与资源权衡", exact: true }),
  });
  await expect(panel).toContainText("200.0 MiB");
  await expect(panel).toContainText("单次测量不代表稳定加速");
  await expect(panel.locator("details[open]")).toHaveCount(0);
  await panel.locator("summary").click();
  await expect(panel.locator("pre")).toContainText("fixture_missing");
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth + 1,
    ),
  ).toBe(true);
});

test("readable report preserves real metrics, all candidates and folded evidence", async ({
  page,
}) => {
  await intercept(page);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await openReport(page, "passed");
  await expect(
    page.getByRole("heading", { name: "算法验证完成，报告已就绪" }),
  ).toBeVisible();
  await expect(page.locator("input[type=radio]")).toHaveCount(6);
  await expect(page.locator("details[open]")).toHaveCount(0);
  await expect(page.locator(".primary-metric")).toContainText("0.1829");
  await expect(page.locator(".comparison-charts")).toContainText(
    "固定范围 0–1",
  );
  await expect(page.locator(".comparison-charts")).toContainText(
    "Lift · 独立倍数刻度",
  );
  await page
    .getByRole("radio", { name: "查看候选 bank_forest_default" })
    .check();
  await expect(
    page.locator(".candidate-detail .section-heading"),
  ).toContainText("随机森林");
  await page.locator("summary").filter({ hasText: "生成代码" }).click();
  await expect(page.locator("pre.code-block")).toContainText(
    "<img src=x onerror=alert(1)>",
  );
  await expect(page.locator("pre.code-block img")).toHaveCount(0);
  await page.locator("summary").filter({ hasText: "知识依据与来源" }).click();
  await expect(
    page.locator(".evidence-card .graph-link").first(),
  ).toHaveAttribute("href", /knowledge\?focus=capability/);
  expect(errors).toEqual([]);
});

test("failed and cancelled runs do not imply missing checks or quality passed", async ({
  page,
}) => {
  await intercept(page);
  await openReport(page, "failed");
  await expect(
    page.getByRole("heading", { name: "本次运行未完成验证目标" }),
  ).toBeVisible();
  await expect(page.locator(".validation-dimension.good")).toHaveCount(0);
  await expect(page.locator("input[type=radio]")).toHaveCount(1);
  await openReport(page, "empty");
  await expect(
    page.getByRole("heading", { name: "运行已取消，已产生的证据仍可查看" }),
  ).toBeVisible();
  await expect(page.locator(".validation-dimensions")).toHaveCount(0);
  await expect(page.locator(".primary-metric")).toContainText("—");
  await expect(page.locator(".mode-badge")).toContainText("Mock");
});

test("quality advisory remains failed when mandatory checks pass", async ({
  page,
}) => {
  await intercept(page);
  await openReport(page, "low");
  await expect(
    page.getByRole("heading", { name: "算法验证完成，报告已就绪" }),
  ).toBeVisible();
  await expect(page.locator(".headline")).toContainText("AP 未超过基线");
  await expect(page.locator(".validation-dimension.bad")).toHaveCount(1);
  await expect(page.locator(".decision-note")).toContainText(
    "当前 AP 未证实超过基线",
  );
});

test("missing run shows recoverable error and late old fetch cannot replace a new run", async ({
  page,
}) => {
  await intercept(page);
  await openReport(page, "missing");
  await expect(
    page.getByRole("alert").filter({ hasText: "Unknown run" }),
  ).toBeVisible();
  await expect(page.locator(".result-hero")).toHaveCount(0);
  await openReport(page, "stale");
  await page.evaluate(() => {
    location.hash = "/runs/failed";
  });
  await expect(
    page.getByRole("heading", { name: "本次运行未完成验证目标" }),
  ).toBeVisible();
  await page.waitForTimeout(1900);
  await expect(page.locator(".report-footer")).toContainText("failed");
  await expect(page.locator(".report-footer")).not.toContainText("stale");
});

test("polls finalizing and stops after the authoritative terminal state", async ({
  page,
}) => {
  const counts = await intercept(page);
  await openReport(page, "poll");
  await expect(
    page.getByRole("heading", { name: "算法验证完成，报告已就绪" }),
  ).toBeVisible({ timeout: 15000 });
  const countAtCompletion = counts.poll;
  await page.waitForTimeout(3000);
  expect(counts.poll).toBe(countAtCompletion);
  expect(countAtCompletion).toBe(4);
});

test("cancel requests update from the server and report exports remain available", async ({
  page,
}) => {
  await intercept(page);
  await openReport(page, "cancel");
  await page.getByRole("button", { name: "取消运行", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "运行已取消，已产生的证据仍可查看" }),
  ).toBeVisible();
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "JSON", exact: true }).click();
  expect((await downloaded).suggestedFilename()).toBe("axiomforge-cancel.json");
  const popup = page.waitForEvent("popup");
  await page.getByRole("button", { name: "打开 / 打印报告" }).click();
  await expect(
    (await popup).getByRole("heading", { name: "Validation report" }),
  ).toBeVisible();
});

test("report remains usable on a narrow viewport", async ({ page }) => {
  await intercept(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await openReport(page, "passed");
  await expect(
    page.getByRole("heading", { name: "算法验证完成，报告已就绪" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    ),
  ).toBe(false);
  await expect(page.locator(".table-scroll")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "JSON", exact: true }),
  ).toBeVisible();
});
