import { test, expect, type Page } from "@playwright/test";
const config = {
  datasets: [
    {
      id: "bank",
      available: true,
      label: "UCI Bank",
      train_rows: 24712,
      validation_rows: 8238,
      sealed_test_rows: 8238,
    },
    {
      id: "sms",
      available: true,
      label: "UCI SMS",
      train_rows: 3095,
      validation_rows: 1032,
      sealed_test_rows: 1032,
    },
  ],
  providers: {
    providers: [
      { id: "deepseek", available: true, model: "test-model" },
      {
        id: "openai",
        label: "OpenAI / Responses API",
        available: true,
        configured: true,
        requires_api_key: true,
        kind: "openai_compatible_responses",
        deployment: "openai_compatible_api",
        endpoint: "https://responses.example.test/v1",
        model: "gpt-5.5",
      },
      {
        id: "local_http",
        available: false,
        configured: true,
        endpoint_count: 4,
      },
      { id: "mock", available: true },
    ],
  },
};
async function setup(page: Page) {
  await page.route("**/health", (r) => r.fulfill({ json: { status: "ok" } }));
  await page.route("**/config", (r) => r.fulfill({ json: config }));
  await page.route("**/inference/profiles", (r) =>
    r.fulfill({ json: { profiles: [] } }),
  );
}
test("scenario examples, dataset synchronization and budget validation preserve explicit request", async ({
  page,
}) => {
  await setup(page);
  const requests: any[] = [];
  await page.route("**/runs", (r) => {
    requests.push(r.request().postDataJSON());
    return r.fulfill({
      status: 202,
      json: { run_id: "b".repeat(32), status: "queued" },
    });
  });
  await page.route("**/runs/" + "b".repeat(32), (r) =>
    r.fulfill({
      json: {
        run_id: "b".repeat(32),
        status: "queued",
        dataset_id: "sms",
        candidates: [],
        events: [],
      },
    }),
  );
  await page.goto("#/workbench");
  await page.getByRole("button", { name: "银行营销预测" }).click();
  await page.getByLabel("任务数据", { exact: true }).selectOption("sms");
  await expect(page.getByLabel("你的能力需求")).toHaveValue(/短信垃圾/);
  await page.getByLabel("Mock 演示", { exact: false }).check();
  await page.locator("summary").filter({ hasText: "高级设置" }).click();
  await page.getByLabel("总运行预算（秒）").fill("5");
  await expect(
    page.getByRole("button", { name: "开始构建与验证" }),
  ).toBeDisabled();
  await page.getByLabel("你的能力需求").press("Control+Enter");
  expect(requests).toHaveLength(0);
  await page.getByLabel("总运行预算（秒）").fill("120");
  await page.getByRole("button", { name: "开始构建与验证" }).click();
  await expect(page).toHaveURL(/#\/runs\//);
  expect(requests).toHaveLength(1);
  expect(requests[0]).toMatchObject({
    dataset_id: "sms",
    provider: "mock",
    use_graph: true,
    inject_failure: false,
    max_seconds: 120,
  });
  expect(requests[0].description).toContain("短信垃圾");
});
test("provider switch selects the local four GPU endpoint pool without CLI flags", async ({
  page,
}) => {
  await setup(page);
  const requests: any[] = [];
  await page.route("**/runs", (r) => {
    requests.push(r.request().postDataJSON());
    return r.fulfill({
      status: 202,
      json: { run_id: "l".repeat(32), status: "queued" },
    });
  });
  await page.route("**/runs/" + "l".repeat(32), (route) =>
    route.fulfill({
      json: {
        run_id: "l".repeat(32),
        status: "queued",
        provider: "local_http",
        candidates: [],
        events: [],
      },
    }),
  );
  await page.goto("#/workbench?provider=local_http");
  await page.getByRole("button", { name: "银行营销预测" }).click();
  await expect(page.getByRole("radio", { name: /本地大模型/ })).toBeChecked();
  await page.getByRole("button", { name: "开始构建与验证" }).click();
  await expect(page).toHaveURL(/#\/runs\//);
  expect(requests[0]).toMatchObject({
    provider: "local_http",
    dataset_id: "bank",
  });
});

test("Responses provider persists and submits only the configured provider identity", async ({
  page,
}) => {
  await setup(page);
  const requests: any[] = [];
  const runId = "e".repeat(32);
  await page.route("**/runs", (route) => {
    requests.push(route.request().postDataJSON());
    return route.fulfill({
      status: 202,
      json: { run_id: runId, status: "queued" },
    });
  });
  await page.route("**/runs/" + runId, (route) =>
    route.fulfill({
      json: {
        run_id: runId,
        status: "queued",
        provider: "openai",
        mode: "real",
        candidates: [],
        events: [],
      },
    }),
  );
  await page.goto("#/workbench?dataset=bank");
  await page.getByRole("radio", { name: /OpenAI \/ Responses API/ }).check();
  await expect(page.locator(".provider-option.selected")).toContainText(
    "OpenAI 兼容服务",
  );
  await page.reload();
  await expect(
    page.getByRole("radio", { name: /OpenAI \/ Responses API/ }),
  ).toBeChecked();
  await page.getByRole("button", { name: "开始构建与验证" }).click();
  await expect(page).toHaveURL(new RegExp("#/runs/" + runId));
  expect(requests).toHaveLength(1);
  expect(requests[0]).toMatchObject({
    provider: "openai",
    dataset_id: "bank",
    max_seconds: 900,
  });
  for (const field of [
    "api_key",
    "base_url",
    "endpoint",
    "model",
    "deployment",
  ])
    expect(requests[0]).not.toHaveProperty(field);
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual([
    "algoforge-provider",
  ]);
});

test("unconfigured Responses provider keeps submission disabled", async ({
  page,
}) => {
  await setup(page);
  const unavailable = structuredClone(config);
  const provider = unavailable.providers.providers.find(
    (entry) => entry.id === "openai",
  )!;
  provider.available = false;
  provider.configured = false;
  await page.route("**/config", (route) =>
    route.fulfill({ json: unavailable }),
  );
  await page.goto("#/workbench?dataset=bank&provider=openai");
  await expect(
    page.getByRole("radio", { name: /OpenAI \/ Responses API/ }),
  ).toBeChecked();
  await expect(page.locator(".provider-option.selected")).toContainText(
    "需配置 API Key",
  );
  await expect(
    page.getByRole("button", { name: "开始构建与验证" }),
  ).toBeDisabled();
  await expect(page.locator("input[type=password]")).toHaveCount(0);
});

test("retry restores Responses provider and the original run constraints", async ({
  page,
}) => {
  await setup(page);
  await page.route("**/runs/previous-responses", (route) =>
    route.fulfill({
      json: {
        run_id: "previous-responses",
        provider: "openai",
        dataset_id: "sms",
        description: "复用短信分类任务的 Responses 后端与预算配置。",
        request: {
          provider: "openai",
          max_seconds: 180,
          max_candidates: 4,
          max_repairs: 1,
          search: "beam",
        },
      },
    }),
  );
  let submitted: Record<string, unknown> | undefined;
  await page.route("**/runs/retried-responses", (route) =>
    route.fulfill({
      json: {
        run_id: "retried-responses",
        status: "queued",
        provider: "openai",
        mode: "real",
        candidates: [],
        events: [],
      },
    }),
  );
  await page.route("**/runs", (route) => {
    submitted = route.request().postDataJSON();
    return route.fulfill({
      status: 202,
      json: { run_id: "retried-responses", status: "queued" },
    });
  });
  await page.goto("#/workbench?from=previous-responses");
  await expect(
    page.getByRole("radio", { name: /OpenAI \/ Responses API/ }),
  ).toBeChecked();
  await expect(page.getByLabel("你的能力需求")).toHaveValue(/复用短信分类/);
  await page.getByRole("button", { name: "开始构建与验证" }).click();
  await expect(page).toHaveURL(new RegExp("#/runs/retried-responses"));
  expect(submitted).toMatchObject({
    provider: "openai",
    dataset_id: "sms",
    max_seconds: 180,
    max_candidates: 4,
    max_repairs: 1,
    search: "beam",
  });
});

for (const [deployment, label] of [
  ["official_api", "OpenAI 官方 API"],
  ["openai_compatible_api", "OpenAI 兼容服务"],
]) {
  test(`model settings distinguish SDK and service deployment: ${deployment}`, async ({
    page,
  }) => {
    await setup(page);
    const catalog = structuredClone(config);
    catalog.providers.providers.find(
      (entry) => entry.id === "openai",
    )!.deployment = deployment;
    await page.route("**/config", (route) => route.fulfill({ json: catalog }));
    await page.goto("#/settings");
    const card = page.locator(".backend-card").filter({
      has: page.getByRole("heading", {
        name: "OpenAI / Responses API",
        exact: true,
      }),
    });
    await expect(card).toContainText(label);
    await expect(card).toContainText("OpenAI 官方 Python SDK · Responses API");
    await expect(card).toContainText("gpt-5.5");
    await card.getByRole("link", { name: "使用此后端" }).click();
    await expect(
      page.getByRole("radio", { name: /OpenAI \/ Responses API/ }),
    ).toBeChecked();
  });
}

test("history identifies and filters Responses runs alongside local and DeepSeek", async ({
  page,
}) => {
  await setup(page);
  await page.route("**/runs/responses-history", (route) =>
    route.fulfill({
      json: {
        run_id: "responses-history",
        provider: "openai",
        dataset_id: "bank",
        description: "Responses 分类验证",
      },
    }),
  );
  await page.route("**/runs", (route) =>
    route.fulfill({
      json: {
        runs: [
          {
            run_id: "responses-history",
            provider: "openai",
            mode: "real",
            status: "failed",
            description: "Responses 分类验证",
            provider_metadata: { deployment: "openai_compatible_api" },
          },
          {
            run_id: "local-history",
            provider: "local_http",
            mode: "real",
            status: "passed",
            description: "本地分类验证",
          },
          {
            run_id: "deepseek-history",
            provider: "deepseek",
            mode: "real",
            status: "passed",
            description: "DeepSeek 分类验证",
          },
        ],
      },
    }),
  );
  await page.goto("#/history");
  await expect(page.locator("tbody")).toContainText(
    "OpenAI 兼容服务 · Responses",
  );
  await page.getByLabel("筛选执行方式").selectOption("openai");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(
    page.getByRole("link", { name: "Responses 分类验证" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "复用需求" }).click();
  await expect(page).toHaveURL(
    (url) => url.hash === "#/workbench?from=responses-history",
  );
});
test("Enter edits text and double submit cannot create duplicate task", async ({
  page,
}) => {
  await setup(page);
  let submitted = 0;
  await page.route("**/runs", async (r) => {
    submitted++;
    await new Promise((resolve) => setTimeout(resolve, 500));
    await r.fulfill({ status: 429, json: { detail: "队列已满，请稍后重试" } });
  });
  await page.goto("#/workbench?dataset=bank");
  const prompt = page.getByLabel("你的能力需求");
  await prompt.press("End");
  await prompt.press("Enter");
  await expect(prompt).toHaveValue(/\n$/);
  expect(submitted).toBe(0);
  await expect(
    page.getByRole("button", { name: "开始构建与验证" }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "开始构建与验证" }).click();
  await prompt.press("Control+Enter");
  await expect(page.getByRole("alert")).toContainText("队列已满");
  expect(submitted).toBe(1);
  await expect(
    page.getByRole("button", { name: "开始构建与验证" }),
  ).toBeEnabled();
});

test("uncertain POST response locks retry and sends user to history", async ({
  page,
}) => {
  await setup(page);
  let submitted = 0;
  await page.route("**/runs", async (r) => {
    submitted++;
    return r.fulfill({ status: 503, json: { detail: "运行服务暂不可用" } });
  });
  await page.goto("#/workbench?dataset=bank");
  await expect(page.getByLabel("你的能力需求")).toBeEnabled();
  await page.getByLabel("你的能力需求").fill("确认 5xx 提交结果的处理方式。");
  await page.getByRole("button", { name: "开始构建与验证" }).click();
  await expect(page.getByRole("alert")).toContainText("无法确认任务是否已创建");
  await expect(
    page.getByRole("link", { name: "前往历史记录核对" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "开始构建与验证" }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "开始构建与验证" })
    .click({ force: true });
  expect(submitted).toBe(1);
});

test("missing run id is treated as an uncertain submission", async ({
  page,
}) => {
  await setup(page);
  let submitted = 0;
  await page.route("**/runs", async (r) => {
    submitted++;
    return r.fulfill({ status: 202, json: { status: "queued" } });
  });
  await page.goto("#/workbench?dataset=bank");
  await page
    .getByLabel("你的能力需求")
    .fill("确认缺少运行编号时不会立即重复提交。");
  await page.getByRole("button", { name: "开始构建与验证" }).click();
  await expect(page.getByRole("alert")).toContainText("没有返回运行编号");
  await expect(
    page.getByRole("link", { name: "前往历史记录核对" }),
  ).toBeVisible();
  expect(submitted).toBe(1);
});

test("startup seeding disables controls until configuration and restored task arrive", async ({
  page,
}) => {
  await page.route("**/health", (r) => r.fulfill({ json: { status: "ok" } }));
  await page.route("**/config", async (r) => {
    await new Promise((resolve) => setTimeout(resolve, 350));
    return r.fulfill({ json: config });
  });
  await page.goto("#/workbench?dataset=sms");
  await expect(
    page.getByRole("button", { name: "短信垃圾分类" }),
  ).toBeDisabled();
  await expect(page.getByLabel("你的能力需求")).toBeDisabled();
  await expect(page.getByLabel("你的能力需求")).toBeEnabled();
});

test("knowledge capability version is preserved in the task context", async ({
  page,
}) => {
  await setup(page);
  let requested = "";
  await page.route("**/capabilities/average-precision**", async (r) => {
    requested = r.request().url();
    return r.fulfill({
      json: {
        capability: {
          capability_id: "average-precision",
          version: 3,
          name: "平均精度",
          summary: "v3 能力",
          task_types: ["tabular_binary_classification"],
        },
      },
    });
  });
  await page.goto("#/workbench?capability=average-precision&version=3");
  await expect(page.getByText("v3", { exact: true })).toBeVisible();
  expect(requested).toContain("version=3");
});

test("history distinguishes load failure and no search matches", async ({
  page,
}) => {
  await setup(page);
  await page.route("**/runs", (r) =>
    r.fulfill({ status: 503, json: { detail: "运行服务暂不可用" } }),
  );
  await page.goto("#/history");
  await expect(page.getByRole("alert")).toContainText("运行服务暂不可用");
  await expect(page.getByText("还没有运行记录")).toHaveCount(0);
  await page.route("**/runs", (r) =>
    r.fulfill({
      json: {
        runs: [
          {
            run_id: "c".repeat(32),
            description: "短信模型验证",
            dataset_id: "sms",
            status: "failed",
            mode: "mock",
          },
        ],
      },
    }),
  );
  await page.getByRole("button", { name: "刷新", exact: true }).click();
  await expect(page.getByRole("link", { name: "短信模型验证" })).toBeVisible();
  await page.getByRole("textbox", { name: "搜索运行" }).fill("不存在的任务");
  await expect(page.getByText("没有符合筛选条件的运行")).toBeVisible();
  await page.getByRole("button", { name: "清空筛选" }).click();
  await expect(page.getByRole("link", { name: "短信模型验证" })).toBeVisible();
});
test("mobile navigation and draft restoration remain usable without horizontal overflow", async ({
  page,
}) => {
  await setup(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("#/workbench");
  await page
    .getByLabel("你的能力需求")
    .fill("保留我的短信分类需求与输入约束。");
  await page.getByLabel("任务数据", { exact: true }).selectOption("sms");
  await page.reload();
  await expect(page.getByLabel("你的能力需求")).toHaveValue(
    "保留我的短信分类需求与输入约束。",
  );
  await expect(page.getByLabel("任务数据", { exact: true })).toHaveValue("sms");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "打开导航" }).click();
  await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();
  await page.getByRole("link", { name: "模型与环境", exact: true }).click();
  await expect(page).toHaveURL(/#\/settings/);
});

test("help dialog keeps keyboard focus and skip link preserves current route", async ({
  page,
}) => {
  await setup(page);
  await page.goto("#/workbench");
  await page.getByRole("button", { name: "使用指南" }).click();
  const close = page.getByRole("button", { name: "关闭指南" });
  await expect(close).toBeFocused();
  await close.press("Shift+Tab");
  await expect(
    page.getByRole("button", { name: "创建第一个任务" }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "使用指南" })).toBeFocused();
  await page.getByRole("link", { name: "跳转到主要内容" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("main")).toBeFocused();
  await expect(page).toHaveURL(/#\/workbench$/);
});
