export interface GraphNode {
  id: string;
  kind: string;
  kind_label?: string;
  label: string;
  properties: Record<string, unknown>;
  degree?: number;
  focused?: boolean;
  distance?: number | null;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  relation_label?: string;
  properties: Record<string, unknown>;
}

export const kindLabels: Record<string, string> = {
  Capability: "算法能力",
  Algorithm: "算法",
  Transform: "数据处理",
  Metric: "评价指标",
  TaskType: "任务类型",
  Environment: "依赖环境",
  Source: "知识来源",
  ValidationRun: "验证运行",
  DatasetVersion: "数据版本",
  Artifact: "代码制品",
  FailureExperience: "失败与修复经验",
};

export const kindColors: Record<string, string> = {
  Capability: "#0d9488",
  Algorithm: "#6366f1",
  Transform: "#8b5cf6",
  Metric: "#0284c7",
  TaskType: "#475569",
  Environment: "#64748b",
  Source: "#d97706",
  ValidationRun: "#16a34a",
  DatasetVersion: "#db2777",
  Artifact: "#2563eb",
  FailureExperience: "#e15d48",
};

export const kindColor = (kind: string) => kindColors[kind] || "#64748b";
export const kindLabel = (kind: string) => kindLabels[kind] || kind;

/** Show location metadata without expanding AST imports or a full function signature. */
export function sourceLocation(properties: Record<string, unknown> = {}): {
  file: string;
  symbol: string;
  lines: string;
} {
  const value = properties.locator;
  const locator =
    value && typeof value === "object" && !Array.isArray(value)
      ? (value as Record<string, unknown>)
      : {};
  const rawPath = String(
    locator.relative_path ||
      properties.relative_path ||
      locator.path ||
      properties.path ||
      "",
  );
  const normalized = rawPath.replaceAll("\\", "/");
  const relativeFile = normalized.startsWith("/")
    ? normalized.split("/").slice(-3).join("/")
    : normalized;
  const start = locator.line_start ?? locator.line;
  const end = locator.line_end;
  return {
    file: relativeFile,
    symbol: String(
      locator.symbol ||
        locator.qualname ||
        locator.function ||
        properties.symbol ||
        "",
    ),
    lines:
      start === undefined
        ? ""
        : end && end !== start
          ? `第 ${start}–${end} 行`
          : `第 ${start} 行`,
  };
}

export function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "未记录";
  if (typeof value === "boolean") return value ? "是" : "否";
  if (Array.isArray(value))
    return value.map(displayValue).join("、") || "未记录";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

export function taskLabel(value: string): string {
  return (
    (
      {
        tabular_binary_classification: "表格分类",
        text_binary_classification: "文本分类",
        text_classification: "文本分类",
      } as Record<string, string>
    )[value] || value
  );
}

export function statusLabel(value: unknown): string {
  const status = String(value || "");
  return (
    (
      {
        verified: "已验证",
        validated: "已验证",
        active: "可用",
        draft: "待验证",
        extracted: "已抽取",
        source_grounded: "来源可追溯",
        seed: "种子知识",
        passed: "验证通过",
        success: "完成",
        completed: "完成",
        failed: "失败",
        running: "运行中",
        planned: "已规划",
        unevaluated: "未评估",
      } as Record<string, string>
    )[status] ||
    status ||
    "未记录状态"
  );
}
