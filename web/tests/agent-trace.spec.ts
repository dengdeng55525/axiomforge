import { test, expect, type Page } from "@playwright/test";
import fs from "node:fs";

const historical = JSON.parse(
  fs.readFileSync(
    new URL("../../examples/evidence/bank_beam/report.json", import.meta.url),
    "utf8",
  ),
);

async function openReport(page: Page, id: string) {
  await page.goto(`#/runs/${id}`);
  await expect(
    page.getByRole("heading", { name: "验证报告", exact: true }),
  ).toBeVisible();
}

test("agent observability folds details and replays read-only state", async ({
  page,
}) => {
  const fixture = {
    ...structuredClone(historical),
    run_id: "trace",
    agent_trace: {
      schema_version: "agent-trace-v1",
      run_id: "trace",
      status: "completed",
      mode: "real",
      framework: { name: "langchain-core", version: "0.3" },
      event_count: 4,
      total_event_count: 4,
      cursor_sequence: 4,
      is_replay: false,
      spans: [
        {
          span_id: "agent-1",
          kind: "agent",
          name: "planner",
          role: "planner",
          status: "completed",
          started_at: "2026-09-30T00:00:00Z",
          finished_at: "2026-09-30T00:00:01Z",
          duration_seconds: 1,
          start_sequence: 1,
          end_sequence: 2,
          output_summary: { result_keys: ["algorithm"], returned_count: 1 },
        },
        {
          span_id: "tool-1",
          kind: "tool",
          name: "search_capabilities",
          status: "completed",
          started_at: "2026-09-30T00:00:01Z",
          finished_at: "2026-09-30T00:00:02Z",
          duration_seconds: 1,
          start_sequence: 2,
          end_sequence: 3,
          output_summary: { capability_ids: ["cap-1"], returned_count: 1 },
        },
      ],
      budget: {
        calls: 2,
        input_tokens: 100,
        output_tokens: 40,
        max_calls: 8,
        wall_seconds: 2,
        max_seconds: 60,
      },
      evidence: { capability_ids: ["cap-1"], count: 1, retrieval_count: 1 },
      events: [
        {
          sequence: 1,
          event_type: "AGENT_STARTED",
          created_at: "2026-09-30T00:00:00Z",
          role: "planner",
        },
        {
          sequence: 2,
          event_type: "AGENT_COMPLETED",
          created_at: "2026-09-30T00:00:01Z",
          role: "planner",
        },
      ],
    },
  };
  let replayRequests = 0;
  let postRequests = 0;
  await page.route(
    /\/runs\/trace\/agent-trace\?through_sequence=\d+$/,
    async (route) => {
      replayRequests += 1;
      if (route.request().method() === "POST") postRequests += 1;
      await route.fulfill({
        json: {
          ...fixture.agent_trace,
          cursor_sequence: 2,
          event_count: 2,
          total_event_count: 4,
          is_replay: true,
          spans: fixture.agent_trace.spans.slice(0, 1),
          evidence: { capability_ids: ["cap-1"], count: 1, retrieval_count: 0 },
        },
      });
    },
  );
  await page.route(/\/runs\/trace(?:\/report)?$/, (route) =>
    route.fulfill({ json: fixture }),
  );
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await openReport(page, "trace");
  const panel = page.getByTestId("agent-trace-panel");
  await expect(panel).toContainText("Agent 观测台");
  await expect(panel).toContainText("2");
  await expect(panel.locator("details[open]")).toHaveCount(0);
  await panel.getByText("展开时序与预算详情").click();
  await expect(panel).toContainText("planner");
  await expect(panel).toContainText("调用预算");
  await panel.getByLabel("回放事件游标").fill("2");
  await expect.poll(() => replayRequests).toBeGreaterThan(0);
  await expect(panel).toContainText("回放至 #2");
  expect(postRequests).toBe(0);
  await expect(panel).toContainText("回放只读取历史投影");
});

test("agent observability remains within a phone viewport", async ({
  page,
}) => {
  const fixture = {
    ...structuredClone(historical),
    run_id: "mobile-trace",
    agent_trace: {
      total_event_count: 1,
      cursor_sequence: 1,
      spans: [],
      events: [],
      budget: {},
    },
  };
  await page.route(/\/runs\/mobile-trace(?:\/report)?$/, (route) =>
    route.fulfill({ json: fixture }),
  );
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await openReport(page, "mobile-trace");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth + 1,
    ),
  ).toBe(true);
});

test("a delayed replay from an old run never crosses the route identity", async ({
  page,
}) => {
  const report = (id: string) => ({
    ...structuredClone(historical),
    run_id: id,
    agent_trace: {
      total_event_count: 2,
      cursor_sequence: 2,
      events: [
        {
          sequence: 1,
          event_type: "AGENT_STARTED",
          created_at: "2026-09-30T00:00:00Z",
          role: "planner",
        },
        {
          sequence: 2,
          event_type: "AGENT_COMPLETED",
          created_at: "2026-09-30T00:00:01Z",
          role: "planner",
        },
      ],
      spans: [],
      budget: {},
      evidence: { capability_ids: [], count: 0, retrieval_count: 0 },
    },
  });
  await page.route(
    /\/runs\/slow\/agent-trace\?through_sequence=\d+$/,
    async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route
        .fulfill({
          json: {
            ...report("slow").agent_trace,
            cursor_sequence: 1,
            is_replay: true,
            evidence: {
              capability_ids: ["slow-only-capability"],
              count: 1,
              retrieval_count: 1,
            },
          },
        })
        .catch(() => {});
    },
  );
  await page.route(/\/runs\/(slow|next)(?:\/report)?$/, (route) => {
    const id =
      new URL(route.request().url()).pathname.split("/").pop() || "next";
    return route.fulfill({ json: report(id) });
  });
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await openReport(page, "slow");
  const panel = page.getByTestId("agent-trace-panel");
  await panel.getByText("展开时序与预算详情").click();
  await panel.getByLabel("回放事件游标").fill("1");
  await page.goto("#/runs/next");
  await expect(
    page.getByRole("heading", { name: "验证报告", exact: true }),
  ).toBeVisible();
  await page.waitForTimeout(650);
  await expect(page.getByTestId("agent-trace-panel")).not.toContainText(
    "slow-only-capability",
  );
});
