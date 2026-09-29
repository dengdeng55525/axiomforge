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
