import { expect, test, type Page } from "@playwright/test";

const capability = {
  capability_id: "bank-policy",
  name: "银行营销通话前预测",
  summary: "使用通话前可获得的客户特征；禁止使用 duration，避免数据泄漏。",
  version: 2,
  status: "source_grounded",
  task_types: ["tabular_binary_classification"],
  dependencies: ["scikit-learn"],
  preconditions: ["只使用通话前特征"],
  tags: ["银行", "泄漏"],
  input_schema: { type: "table" },
  output_schema: { type: "probability" },
  evidence: [{ source_id: "source:uci" }],
};
const nodes = [
  {
    id: "capability:bank-policy:v2",
    kind: "Capability",
    kind_label: "算法能力",
    label: capability.name,
    properties: {
      capability_id: "bank-policy",
      version: 2,
      status: "source_grounded",
    },
  },
  {
    id: "source:uci",
    kind: "Source",
    kind_label: "知识来源",
    label: "UCI 银行营销字段说明",
    properties: {
      source_type: "document",
      uri: "https://archive.ics.uci.edu/dataset/222/bank+marketing",
      locator: {
        relative_path: "data/fields.txt",
        symbol: "duration",
        line_start: 10,
        line_end: 20,
        imports: ["private_verbose_import_example"],
      },
      sha256: "test-source-hash",
    },
  },
  {
    id: "artifact:candidate-1",
    kind: "Artifact",
    kind_label: "代码制品",
    label: "逻辑回归实现",
    properties: { candidate_id: "candidate-1", run_id: "run-example" },
  },
  {
    id: "run:run-example",
    kind: "ValidationRun",
    kind_label: "验证运行",
    label: "银行验证示例",
    properties: { run_id: "run-example" },
  },
];
const edges = [
  {
    id: "e1",
    source: nodes[0]!.id,
    target: nodes[1]!.id,
    relation: "DERIVED_FROM",
    relation_label: "来源于",
    properties: { locator: "duration 字段" },
  },
  {
    id: "e2",
    source: nodes[2]!.id,
    target: nodes[0]!.id,
    relation: "IMPLEMENTS",
    relation_label: "参考能力实现",
    properties: {},
  },
  {
    id: "e3",
    source: nodes[3]!.id,
    target: nodes[2]!.id,
    relation: "EVALUATES",
    relation_label: "验证制品",
    properties: {},
  },
];
const evidence = {
  sources: [
    {
      node_id: nodes[1]!.id,
      label: nodes[1]!.label,
      properties: nodes[1]!.properties,
      path: [edges[0]],
    },
  ],
  validations: [
    {
      node_id: nodes[3]!.id,
      label: "银行验证示例",
      path: [edges[1], edges[2]],
      run_id: "run-example",
      report_available: true,
      status: "completed",
      mode: "mock",
      provider: "mock",
      dataset_id: "bank",
      selected_candidate_id: "candidate-1",
      primary_metric: "average_precision",
      metrics: { average_precision: 0.32 },
      checks: { passed: 3, total: 4 },
      quality_label: "验证集 AP 高于类别占比基线",
    },
  ],
  artifacts: [],
  failure_experiences: [],
  counts: { sources: { total: 1 }, validations: { total: 1 } },
  truncated: false,
};
const facets = {
  kinds: [
    { value: "Capability", label: "算法能力", count: 1 },
    { value: "Source", label: "知识来源", count: 1 },
    { value: "Artifact", label: "代码制品", count: 1 },
    { value: "ValidationRun", label: "验证运行", count: 1 },
  ],
  relations: [
    { value: "DERIVED_FROM", label: "来源于", count: 1 },
    { value: "IMPLEMENTS", label: "参考能力实现", count: 1 },
    { value: "EVALUATES", label: "验证制品", count: 1 },
  ],
};

async function mockKnowledge(page: Page) {
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await page.route("**/capabilities", (route) =>
    route.fulfill({ json: { capabilities: [capability] } }),
  );
  await page.route("**/capabilities/bank-policy?*", (route) =>
    route.fulfill({
      json: {
        capability,
        node_id: nodes[0]!.id,
        node: nodes[0],
        evidence,
        version_count: 1,
        versions: [
          { version: 2, status: "source_grounded", node_id: nodes[0]!.id },
        ],
      },
    }),
  );
  await page.route("**/graph/explore?*", (route) => {
    const query = new URL(route.request().url()).searchParams;
    const focus = nodes.find((node) => node.id === query.get("focus")) || null;
    const visibleNodes =
      query.get("q") === "不存在的节点" ? (focus ? [focus] : []) : nodes;
    const visibleEdges = visibleNodes.length > 1 ? edges : [];
    return route.fulfill({
      json: {
        nodes: visibleNodes,
        edges: visibleEdges,
        focus,
        facets,
        evidence,
        stats: {
          total_nodes: 4,
          total_edges: 3,
          returned_nodes: visibleNodes.length,
          returned_edges: visibleEdges.length,
        },
        truncated: false,
        filters: { focus_retained_outside_filters: false },
      },
    });
  });
}

test("graph presents provenance and validation evidence separately from expandable intermediate details", async ({
  page,
}) => {
  await mockKnowledge(page);
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  await page.goto("./#/knowledge");
  await expect(page.locator(".graph-node")).toHaveCount(4);
  await expect(
    page.getByRole("heading", { name: capability.name, exact: true }),
  ).toBeVisible();
  await expect(page.locator(".inspector")).toContainText("Mock 演示");
  await expect(page.locator(".validation-metric")).toContainText("0.3200");
  await expect(page.locator(".validation-card")).toContainText(
    "检查通过 3 / 4 项",
  );
  await expect(page.locator(".source-file")).toHaveText("data/fields.txt");
  await expect(page.locator(".source-symbol")).toHaveText("duration");
  await expect(
    page.getByRole("link", { name: "查看原始来源" }),
  ).toHaveAttribute(
    "href",
    "https://archive.ics.uci.edu/dataset/222/bank+marketing",
  );
  expect(await page.locator(".inspector").innerText()).not.toContain(
    "private_verbose_import_example",
  );
  await expect(
    page.getByRole("link", { name: "查看完整验证报告" }),
  ).toHaveAttribute("href", "#/runs/run-example");
  const properties = page
    .locator("details")
    .filter({ has: page.locator("summary", { hasText: "节点属性与标识" }) });
  await expect(properties).not.toHaveAttribute("open");
  await properties.locator("summary").click();
  await expect(properties).toContainText(nodes[0]!.id);
  expect(pageErrors).toEqual([]);
});

test("keyboard selection, neighborhood exploration and visible type filters call the real API contract", async ({
  page,
}) => {
  await mockKnowledge(page);
  await page.goto("./#/knowledge");
  const sourceNode = page.getByRole("button", {
    name: `知识来源：${nodes[1]!.label}，点击查看详情`,
    exact: true,
  });
  await sourceNode.focus();
  await sourceNode.press("Enter");
  await expect(
    page.getByRole("heading", { name: nodes[1]!.label, exact: true }),
  ).toBeVisible();
  const focusRequest = page.waitForRequest(
    (request) =>
      request.url().includes("/graph/explore?") &&
      new URL(request.url()).searchParams.get("focus") === "source:uci" &&
      new URL(request.url()).searchParams.get("limit") === "80",
  );
  await page.getByRole("button", { name: "聚焦此节点" }).click();
  await focusRequest;
  await expect(sourceNode).toHaveAttribute("aria-pressed", "true");
  const hopRequest = page.waitForRequest(
    (request) =>
      request.url().includes("/graph/explore?") &&
      new URL(request.url()).searchParams.get("hops") === "2",
  );
  await page.getByRole("button", { name: "2 跳邻域" }).click();
  await hopRequest;
  const filterRequest = page.waitForRequest(
    (request) =>
      request.url().includes("/graph/explore?") &&
      new URL(request.url()).searchParams.get("kinds") === "Source",
  );
  await page.getByRole("checkbox", { name: "知识来源 1" }).check();
  await filterRequest;
});

test("capability library can search, show empty state and link a real capability to a new task", async ({
  page,
}) => {
  await mockKnowledge(page);
  await page.goto("./#/knowledge");
  await page.getByRole("tab", { name: /能力库/ }).click();
  await expect(page.locator(".capability-card")).toHaveCount(1);
  await page.locator(".capability-card").click();
  await expect(page.getByRole("link", { name: "用于新任务" })).toHaveAttribute(
    "href",
    "#/workbench?capability=bank-policy&version=2",
  );
  await page
    .getByRole("searchbox", { name: "搜索算法能力" })
    .fill("不存在的能力");
  await expect(
    page.getByRole("heading", { name: "没有匹配的能力" }),
  ).toBeVisible();
  await page.getByRole("searchbox", { name: "搜索算法能力" }).fill("银行");
  await expect(page.locator(".capability-card")).toHaveCount(1);
});

test("graph search has useful empty state and mobile layout does not overflow", async ({
  page,
}) => {
  await mockKnowledge(page);
  await page.goto("./#/knowledge");
  await page.getByRole("button", { name: "返回概览" }).click();
  await page
    .getByRole("searchbox", { name: "搜索图谱节点" })
    .fill("不存在的节点");
  await expect(
    page.getByRole("heading", { name: "没有符合条件的节点" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "清除筛选", exact: true }).click();
  await expect(page.locator(".graph-node")).toHaveCount(4);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > window.innerWidth,
    ),
  ).toBe(false);
  await page.getByRole("button", { name: "显示筛选器" }).click();
  await expect(
    page.getByRole("searchbox", { name: "搜索图谱节点" }),
  ).toBeVisible();
});

test("focused graph deep links react to same-page route query changes", async ({
  page,
}) => {
  await mockKnowledge(page);
  await page.goto("./#/knowledge?focus=source%3Auci");
  await expect(page.locator(".explorer-breadcrumb")).toContainText(
    nodes[1]!.label,
  );
  await page.evaluate(() => {
    window.location.hash = "#/knowledge?focus=artifact%3Acandidate-1";
  });
  await expect(page.locator(".explorer-breadcrumb")).toContainText(
    nodes[2]!.label,
  );
});

test("API errors show a retry action and recover without reloading the page", async ({
  page,
}) => {
  await mockKnowledge(page);
  let firstRequest = true;
  await page.route("**/capabilities", (route) => {
    if (firstRequest) {
      firstRequest = false;
      return route.fulfill({ status: 503, json: { detail: "知识库暂不可用" } });
    }
    return route.fulfill({ json: { capabilities: [capability] } });
  });
  await page.goto("./#/knowledge");
  await expect(page.getByRole("alert")).toContainText("知识库暂不可用");
  await page.getByRole("button", { name: "重新加载", exact: true }).click();
  await expect(page.locator(".graph-node")).toHaveCount(4);
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("initial graph prefers the business capability definition and keeps desktop panes bounded", async ({
  page,
}) => {
  await mockKnowledge(page);
  await page.route("**/capabilities", (route) =>
    route.fulfill({
      json: {
        capabilities: [
          capability,
          {
            ...capability,
            capability_id: "bank-precontact-policy",
            name: "银行通话前特征约束",
            version: 1,
          },
        ],
      },
    }),
  );
  const initialRequest = page.waitForRequest((request) =>
    request.url().includes("/graph/explore?"),
  );
  await page.goto("./#/knowledge");
  const query = new URL((await initialRequest).url()).searchParams;
  expect(query.get("focus")).toBe("capability:bank-precontact-policy:v1");
  expect(query.get("relations")).toBe("SOLVES,DERIVED_FROM,USES,REQUIRES");
  await expect(page.locator(".graph-node")).toHaveCount(4);
  expect(
    (await page.locator(".explorer-body").boundingBox())!.height,
  ).toBeLessThanOrEqual(620);
  expect(
    (await page.locator(".inspector").boundingBox())!.height,
  ).toBeLessThanOrEqual(682);
});
