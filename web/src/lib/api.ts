/** Same-origin transport. Credentials and generated code execution stay on the backend. */
export class ApiError extends Error {
  readonly status?: number;
  /** A POST may have reached the server even when its response is uncertain. */
  readonly ambiguous: boolean;

  constructor(message: string, status?: number, ambiguous = false) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.ambiguous = ambiguous;
  }
}

export async function api<T = any>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const method = (init.method || "GET").toUpperCase();
  const runSubmission = method === "POST" && path.split("?", 1)[0] === "/runs";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  const abort = () => controller.abort();
  init.signal?.addEventListener("abort", abort, { once: true });
  try {
    if (init.signal?.aborted) controller.abort();
    const response = await fetch(path, {
      ...init,
      headers: {
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
      },
      signal: controller.signal,
    });
    if (!response.ok) {
      let detail = `请求失败（${response.status}）`;
      try {
        const data = await response.json();
        detail = typeof data.detail === "string" ? data.detail : detail;
      } catch {
        /* Preserve the HTTP error. */
      }
      throw new ApiError(
        detail,
        response.status,
        runSubmission && response.status >= 500,
      );
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError")
      throw new ApiError(
        "请求超时或已取消，提交结果可能仍在服务端处理。",
        undefined,
        runSubmission,
      );
    if (error instanceof TypeError)
      throw new ApiError(
        runSubmission
          ? "无法确认任务提交结果，服务可能已经接受请求。"
          : "无法连接服务，请检查 API 是否已启动。",
        undefined,
        runSubmission,
      );
    throw error;
  } finally {
    clearTimeout(timeout);
    init.signal?.removeEventListener("abort", abort);
  }
}
export async function download(path: string, filename: string): Promise<void> {
  const response = await fetch(path, { signal: AbortSignal.timeout(20000) });
  if (!response.ok)
    throw new Error(`下载失败（${response.status}），请稍后重试。`);
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
