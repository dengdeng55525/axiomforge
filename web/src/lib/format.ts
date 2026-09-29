export type Json = Record<string, any>;
export const statuses: Record<string, string> = {
  passed: "验证通过",
  completed: "已完成",
  failed: "未通过",
  cancelled: "已取消",
  running: "执行中",
  queued: "排队中",
  error: "执行异常",
  above_prevalence: "AP 高于基线",
  at_or_below_prevalence: "AP 未超过基线",
  baseline_or_worse: "AP 未超过基线",
  finalizing: "正在沉淀与生成报告",
  extracted: "已抽取",
  verified: "已验证",
  proposed: "待验证",
};
export const stateLabel = (value: unknown) =>
  value == null ? "未记录" : statuses[String(value)] || String(value);
export const datasetLabel = (value: unknown) =>
  ({ bank: "银行营销响应", sms: "短信垃圾分类" })[String(value)] ||
  String(value || "未记录");
export const modeLabel = (run: Json) =>
  run.mode === "mock" || run.provider === "mock"
    ? "Mock 演示"
    : run.mode === "replay"
      ? "历史回放"
      : run.provider === "local_http"
        ? "本地模型"
        : run.mode === "real" || run.mode === "deepseek"
          ? "真实 API"
          : "模式未记录";
export const metric = (value: unknown, digits = 4) =>
  typeof value === "number" && Number.isFinite(value)
    ? value.toFixed(digits)
    : "—";
export function dateTime(value: unknown) {
  if (!value) return "未记录";
  const date = new Date(String(value));
  return Number.isNaN(date.getTime())
    ? String(value)
    : new Intl.DateTimeFormat("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }).format(date);
}
export const shortId = (value: unknown) => String(value || "—").slice(0, 8);
export const errorText = (value: unknown) =>
  value instanceof Error ? value.message : "请求失败，请重试。";
