/** Provider identifiers are the API contract; credentials stay on the server. */
export type ProviderId = "deepseek" | "openai" | "local_http" | "mock";
export type ApiDeployment = "official_api" | "openai_compatible_api";

export interface ProviderEntry {
  id: ProviderId;
  label?: string;
  available?: boolean;
  configured?: boolean;
  requires_api_key?: boolean;
  kind?: string;
  deployment?: ApiDeployment;
  model?: string;
  endpoint?: string;
  endpoint_count?: number;
}

export const providerNames: Record<ProviderId, string> = {
  deepseek: "DeepSeek API",
  openai: "OpenAI / Responses API",
  local_http: "本地大模型",
  mock: "Mock 演示",
};

export function isProviderId(value: unknown): value is ProviderId {
  return typeof value === "string" && Object.hasOwn(providerNames, value);
}

/** Transport compatibility and the service operator are separate properties. */
export function apiDeploymentLabel(deployment: unknown): string {
  if (deployment === "official_api") return "OpenAI 官方 API";
  if (deployment === "openai_compatible_api") return "OpenAI 兼容服务";
  return "服务端配置的 API";
}

export function providerTip(provider: ProviderEntry): string {
  if (provider.id === "openai")
    return `${apiDeploymentLabel(provider.deployment)} · Responses`;
  if (provider.id === "deepseek") return "使用已配置的云端 LLM 接口";
  if (provider.id === "local_http") return "14B · OpenAI 兼容 HTTP 服务";
  return "固定规则生成 · 离线工程验证";
}

export function providerStatus(provider: ProviderEntry): string {
  if (provider.id === "local_http") {
    return provider.configured
      ? `本地端点池 · ${provider.endpoint_count || 0} 个`
      : "待配置本地端点";
  }
  if (provider.id === "deepseek" || provider.id === "openai")
    return provider.available ? "已配置，可调用" : "需配置 API Key";
  return "无需网络请求";
}
