import { test, expect } from "@playwright/test";

const config = {
  datasets: [{ id: "bank", available: true, label: "UCI Bank" }],
  providers: {
    providers: [
      { id: "mock", label: "Mock", available: true },
      {
        id: "local_http",
        label: "本地大模型",
        available: false,
        configured: true,
      },
    ],
  },
};

async function setup(
  page: import("@playwright/test").Page,
  gpuStatus: unknown,
) {
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok", gpu_status: gpuStatus } }),
  );
  await page.route("**/config", (route) => route.fulfill({ json: config }));
  await page.route("**/inference/profiles", (route) =>
    route.fulfill({ json: { profiles: [] } }),
  );
}

test("GPU status bar exposes enabled cards and expandable device details", async ({
  page,
}) => {
  await setup(page, {
    schema_version: "gpu-status.v1",
    status: "partial",
    expected_count: 4,
    enabled_count: 2,
    message: "已发现 2/4 张 GPU",
    devices: [
      {
        index: 0,
        label: "GPU 0",
        state: "enabled",
        enabled: true,
        name: "RTX 4090D",
        utilization_percent: 12,
        memory_used_mib: 1024,
        temperature_c: 44,
      },
      { index: 1, label: "GPU 1", state: "unavailable", enabled: false },
      {
        index: 2,
        label: "GPU 2",
        state: "enabled",
        enabled: true,
        name: "RTX 4090D",
        utilization_percent: 0,
        memory_used_mib: 2048,
        temperature_c: 39,
      },
      { index: 3, label: "GPU 3", state: "unavailable", enabled: false },
    ],
  });
  await page.goto("#/workbench");

  await expect(page.getByTestId("gpu-status")).toContainText("2/4");
  await page.getByTestId("gpu-status").locator("summary").click();
  await expect(page.locator(".gpu-device")).toHaveCount(4);
  await expect(page.locator(".gpu-device.enabled")).toHaveCount(2);
  await expect(page.locator(".gpu-device").first()).toContainText("RTX 4090D");
});

test("GPU status bar clearly falls back to CPU and Mock when no cards are visible", async ({
  page,
}) => {
  await setup(page, {
    schema_version: "gpu-status.v1",
    status: "unavailable",
    expected_count: 4,
    enabled_count: 0,
    message: "未检测到 nvidia-smi，当前按 CPU/Mock 环境运行",
    devices: Array.from({ length: 4 }, (_, index) => ({
      index,
      label: `GPU ${index}`,
      state: "unavailable",
      enabled: false,
    })),
  });
  await page.goto("#/workbench");

  await expect(page.getByTestId("gpu-status")).toContainText("CPU / Mock");
  await page.getByTestId("gpu-status").locator("summary").click();
  await expect(page.locator(".gpu-device.enabled")).toHaveCount(0);
  await expect(page.locator(".gpu-status-note")).toContainText("CPU / Mock");
});
