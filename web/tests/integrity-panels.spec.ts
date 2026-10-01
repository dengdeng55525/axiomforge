import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";

const historical = JSON.parse(
  fs.readFileSync(
    new URL("../../examples/evidence/bank_beam/report.json", import.meta.url),
    "utf8",
  ),
);

async function mockKnowledge(page: Page) {
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await page.route("**/capabilities", (route) =>
    route.fulfill({
      json: {
        capabilities: [
          {
            capability_id: "bank-policy",
            name: "银行营销通话前预测",
            summary: "保留通话前特征，避免数据泄漏。",
            version: 1,
            status: "verified",
            task_types: ["tabular_binary_classification"],
            evidence: [{ source_id: "source:uci" }],
          },
        ],
      },
    }),
  );
  await page.route("**/graph/explore?*", (route) =>
    route.fulfill({
      json: {
        nodes: [],
        edges: [],
        focus: null,
        facets: { kinds: [], relations: [] },
        stats: {
          total_nodes: 0,
          total_edges: 0,
          returned_nodes: 0,
          returned_edges: 0,
        },
        truncated: false,
        evidence: null,
        filters: {},
      },
    }),
  );
}

test("knowledge integrity is lazy, readable and does not block graph loading", async ({
  page,
}) => {
  await mockKnowledge(page);
  let qualityRequests = 0;
  await page.route("**/knowledge/quality", (route) => {
    qualityRequests += 1;
    return route.fulfill({
      json: {
        schema_version: "knowledge-quality.v1",
        status: "passed",
        summary: {
          cards: 1,
          versions: 1,
          sources: 1,
          nodes: 3,
          edges: 2,
          checks: 3,
          checks_passed: 3,
          errors: 0,
          warnings: 0,
        },
        checks: [
          { id: "source_citations", status: "passed", message: "来源定位完整" },
          {
            id: "content_hash_integrity",
            status: "passed",
            message: "内容哈希一致",
          },
          {
            id: "graph_reference_integrity",
            status: "passed",
            message: "图关系可达",
          },
        ],
        issues: [],
        warnings: [],
      },
    });
  });
  await page.goto("#/knowledge");
  const panel = page.getByTestId("knowledge-quality-panel");
  await expect(panel).toContainText("检查按需执行");
  expect(qualityRequests).toBe(0);
  await panel.getByRole("button", { name: "检查知识完整性" }).click();
  await expect(panel).toContainText("完整性检查通过");
  await expect(panel).toContainText("来源可追溯");
  await expect(panel).toContainText("3 / 3 项检查通过");
  expect(qualityRequests).toBe(1);
  await expect(panel.locator("details.quality-details[open]")).toHaveCount(0);
});

test("knowledge quality distinguishes an empty store from failed checks", async ({
  page,
}) => {
  await mockKnowledge(page);
  let response = {
    schema_version: "knowledge-quality.v1",
    status: "empty",
    summary: {
      cards: 0,
      versions: 0,
      sources: 0,
      nodes: 0,
      edges: 0,
      checks: 11,
      checks_passed: 0,
      errors: 0,
      warnings: 0,
    },
    checks: [
      {
        id: "snapshot_populated",
        status: "not_evaluated",
        message: "暂无能力版本",
      },
      { id: "snapshot_shape", status: "not_evaluated", message: "暂无快照" },
    ],
    issues: [],
    warnings: [],
  };
  await page.route("**/knowledge/quality", (route) =>
    route.fulfill({ json: response }),
  );
  await page.goto("#/knowledge");
  const panel = page.getByTestId("knowledge-quality-panel");
  await panel.getByRole("button", { name: "检查知识完整性" }).click();
  await expect(panel).toContainText("知识库为空");
  expect(await panel.getByText("检查按需执行").count()).toBe(0);
  await panel.locator("summary").first().click();
  await expect(panel).toContainText("未评估");

  response = {
    ...response,
    status: "failed",
    summary: {
      ...response.summary,
      cards: 1,
      versions: 1,
      sources: 1,
      errors: 1,
    },
    checks: [
      {
        id: "content_hash_integrity",
        status: "failed",
        message: "内容哈希不一致",
      },
      {
        id: "verified_experience_evidence",
        status: "warning",
        message: "经验缺少成功验证证据",
      },
    ],
    issues: [
      {
        code: "content_hash_integrity",
        details: { api_key: "sk-test-secret" },
      },
    ],
  };
  await panel.getByRole("button", { name: "重新检查" }).click();
  await expect(panel).toContainText("发现需要处理的问题");
  await panel.locator("summary").first().click();
  await expect(panel).toContainText("哈希不一致");
  await panel.getByText(/错误 1 项/).click();
  await expect(panel).not.toContainText("sk-test-secret");
});

test("integrity verification is manual and a delayed old run cannot contaminate the next run", async ({
  page,
}) => {
  const run = (id: string) => ({
    ...structuredClone(historical),
    run_id: id,
    agent_trace: {
      total_event_count: 0,
      cursor_sequence: 0,
      spans: [],
      events: [],
      budget: {},
    },
  });
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await page.route(/\/runs\/(slow|next)(?:\/report)?$/, (route) => {
    const id =
      new URL(route.request().url()).pathname.split("/").pop() || "next";
    return route.fulfill({ json: run(id) });
  });
  let verificationRequests = 0;
  await page.route(/\/runs\/slow\/reproducibility$/, async (route) => {
    verificationRequests += 1;
    await new Promise((resolve) => setTimeout(resolve, 500));
    await route
      .fulfill({
        json: {
          schema_version: "1.0",
          run_id: "slow",
          status: "complete",
          artifact_count: 1,
          artifacts: [
            {
              path: "slow-only/report.json",
              kind: "report",
              size_bytes: 2,
              sha256: "a".repeat(64),
              expected_sha256: "a".repeat(64),
              integrity: "verified",
            },
          ],
          missing_expected_paths: [],
          truncated: false,
        },
      })
      .catch(() => {});
  });
  await page.route(/\/runs\/next\/reproducibility$/, (route) =>
    route.fulfill({
      json: {
        schema_version: "1.0",
        run_id: "next",
        status: "partial",
        artifact_count: 0,
        artifacts: [],
        missing_expected_paths: ["report.json"],
        truncated: false,
      },
    }),
  );
  await page.goto("#/runs/slow");
  const slowPanel = page.getByTestId("run-integrity-panel");
  await expect(slowPanel).toContainText("核验按需执行");
  expect(verificationRequests).toBe(0);
  await slowPanel.getByRole("button", { name: "核验制品完整性" }).click();
  expect(verificationRequests).toBe(1);
  await page.goto("#/runs/next");
  const nextPanel = page.getByTestId("run-integrity-panel");
  await expect(nextPanel).toContainText("核验按需执行");
  await page.waitForTimeout(650);
  await expect(nextPanel).not.toContainText("slow-only");
  await expect(nextPanel).not.toContainText("制品完整性已核验");
});

test("integrity panel marks read errors and unrecorded hashes on mobile", async ({
  page,
}) => {
  const fixture = {
    ...structuredClone(historical),
    run_id: "integrity-bad",
    agent_trace: {
      total_event_count: 0,
      cursor_sequence: 0,
      spans: [],
      events: [],
      budget: {},
    },
  };
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await page.route(/\/runs\/integrity-bad(?:\/report)?$/, (route) =>
    route.fulfill({ json: fixture }),
  );
  await page.route(/\/runs\/integrity-bad\/reproducibility$/, (route) =>
    route.fulfill({
      json: {
        schema_version: "1.0",
        run_id: "integrity-bad",
        status: "partial",
        artifact_count: 2,
        artifacts: [
          {
            path: "candidates/c1/report.json",
            kind: "report",
            size_bytes: 4,
            sha256: "b".repeat(64),
            expected_sha256: "a".repeat(64),
            integrity: "mismatch",
          },
          {
            path: "candidates/c1/model.py",
            kind: "code",
            size_bytes: 0,
            sha256: null,
            expected_sha256: null,
            integrity: "unrecorded",
            error: "read_error",
          },
        ],
        missing_expected_paths: ["report.json"],
        truncated: false,
      },
    }),
  );
  await page.setViewportSize({ width: 393, height: 844 });
  await page.goto("#/runs/integrity-bad");
  const panel = page.getByTestId("run-integrity-panel");
  await panel.getByRole("button", { name: "核验制品完整性" }).click();
  await expect(panel).toContainText("制品证据不完整");
  await expect(panel).toContainText("1 项未记录预期哈希");
  await panel.getByText("查看四类制品的核验明细").click();
  await expect(panel).toContainText("哈希不一致");
  await expect(panel).toContainText("读取失败");
  await expect(panel).toContainText("缺少预期制品 1 项");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth + 1,
    ),
  ).toBe(true);
});
