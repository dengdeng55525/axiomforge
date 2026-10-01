<script setup lang="ts">
import { computed } from "vue";
import { ChevronDown, Cpu, Gauge, Thermometer } from "@lucide/vue";
import type { Json } from "../lib/format";

const props = defineProps<{ snapshot: Json | null }>();
const fallbackDevices = Array.from({ length: 4 }, (_, index) => ({
  index,
  label: `GPU ${index}`,
  state: "unavailable",
  enabled: false,
}));
const devices = computed<any[]>(() => {
  const value = props.snapshot?.devices;
  return Array.isArray(value) && value.length
    ? value.slice(0, 4)
    : fallbackDevices;
});
const enabledCount = computed(() =>
  Number(
    props.snapshot?.enabled_count ??
      devices.value.filter((item) => item.enabled).length,
  ),
);
const expectedCount = computed(() =>
  Number(props.snapshot?.expected_count ?? 4),
);
const status = computed(() => String(props.snapshot?.status || "unknown"));
const statusLabel = computed(() => {
  if (status.value === "ready") return "四卡已启用";
  if (status.value === "partial")
    return `${enabledCount.value}/${expectedCount.value} 卡可见`;
  if (status.value === "unavailable") return "CPU / Mock";
  if (status.value === "error") return "读取失败";
  return "等待检测";
});
const statusClass = computed(() =>
  status.value === "ready"
    ? "ready"
    : status.value === "partial"
      ? "partial"
      : status.value === "error"
        ? "error"
        : "idle",
);
function metric(value: unknown, suffix = "") {
  return value === null || value === undefined || value === ""
    ? "—"
    : `${value}${suffix}`;
}
function deviceStateLabel(device: any) {
  if (device.enabled) return "已启用";
  if (device.state === "error") return "读取失败";
  if (device.state === "unavailable") return "未检测";
  return "未启用";
}
</script>

<template>
  <details class="gpu-status" data-testid="gpu-status">
    <summary
      class="gpu-status-bar"
      :class="statusClass"
      :aria-label="`GPU 状态：${statusLabel}`"
    >
      <span class="gpu-status-icon"><Cpu :size="15" /></span>
      <span class="gpu-status-name">GPU</span>
      <strong>{{ enabledCount }}/{{ expectedCount }}</strong>
      <span class="gpu-status-label">{{ statusLabel }}</span>
      <ChevronDown :size="13" class="gpu-status-chevron" />
    </summary>
    <div class="gpu-status-popover">
      <div class="gpu-status-heading">
        <div>
          <b>计算资源状态</b>
          <small>{{ props.snapshot?.message || "等待后端健康检查" }}</small>
        </div>
        <span class="badge" :class="statusClass">{{ statusLabel }}</span>
      </div>
      <div class="gpu-device-grid">
        <div
          v-for="device in devices"
          :key="device.index"
          class="gpu-device"
          :class="device.enabled ? 'enabled' : 'disabled'"
          :data-state="device.state"
        >
          <div class="gpu-device-title">
            <span class="gpu-led"></span
            ><b>{{ device.label || `GPU ${device.index}` }}</b>
            <span class="gpu-device-state">{{ deviceStateLabel(device) }}</span>
          </div>
          <small class="gpu-device-model">{{
            device.name || "未检测到设备"
          }}</small>
          <div class="gpu-device-metrics">
            <span
              ><Gauge :size="12" />{{
                metric(device.utilization_percent, "%")
              }}</span
            >
            <span
              ><Cpu :size="12" />{{
                metric(device.memory_used_mib, " MiB")
              }}</span
            >
            <span
              ><Thermometer :size="12" />{{
                metric(device.temperature_c, "°C")
              }}</span
            >
          </div>
        </div>
      </div>
      <small class="gpu-status-note"
        >状态来自后端只读 nvidia-smi 探测；无 GPU 时自动回退到 CPU / Mock
        流程。</small
      >
    </div>
  </details>
</template>

<style scoped>
.gpu-status {
  position: relative;
  z-index: 5;
}
.gpu-status summary {
  list-style: none;
}
.gpu-status summary::-webkit-details-marker {
  display: none;
}
.gpu-status-bar {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 5px 8px;
  border: 1px solid #e4ecee;
  border-radius: 8px;
  background: #fff;
  color: #62747c;
  cursor: pointer;
  font-size: 11px;
  white-space: nowrap;
}
.gpu-status-bar:hover,
.gpu-status[open] .gpu-status-bar {
  border-color: #b8ddd5;
  background: #f8fcfb;
}
.gpu-status-icon {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: #edf3f4;
  color: #84979d;
}
.gpu-status-bar.ready .gpu-status-icon {
  color: #1f946f;
  background: #e7f7ef;
}
.gpu-status-bar.partial .gpu-status-icon {
  color: #b57d2a;
  background: #fff3df;
}
.gpu-status-bar.error .gpu-status-icon {
  color: #c5685f;
  background: #fff0ef;
}
.gpu-status-name {
  font-weight: 650;
  color: #536b71;
}
.gpu-status-bar strong {
  color: #1d554e;
  font-size: 12px;
}
.gpu-status-label {
  color: #829198;
}
.gpu-status-chevron {
  color: #9bacb1;
  transition: transform 0.16s;
}
.gpu-status[open] .gpu-status-chevron {
  transform: rotate(180deg);
}
.gpu-status-popover {
  position: absolute;
  top: calc(100% + 9px);
  right: 0;
  width: min(390px, calc(100vw - 28px));
  padding: 14px;
  border: 1px solid #e0eaeb;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 14px 35px #1b3d4d18;
}
.gpu-status-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 11px;
}
.gpu-status-heading b,
.gpu-status-heading small {
  display: block;
}
.gpu-status-heading b {
  color: #304c53;
  font-size: 12px;
}
.gpu-status-heading small {
  max-width: 245px;
  margin-top: 3px;
  color: #91a0a6;
  font-size: 10px;
  line-height: 1.5;
}
.gpu-status-heading .badge {
  font-size: 10px;
}
.gpu-status-heading .badge.ready {
  background: #e7f7ef;
  color: #218564;
}
.gpu-status-heading .badge.partial {
  background: #fff3df;
  color: #a97827;
}
.gpu-status-heading .badge.error {
  background: #fff0ef;
  color: #bf6058;
}
.gpu-device-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.gpu-device {
  min-width: 0;
  padding: 10px;
  border: 1px solid #e6edef;
  border-radius: 9px;
  background: #fbfcfc;
}
.gpu-device.enabled {
  border-color: #d4ebdf;
  background: #f7fcf9;
}
.gpu-device-title {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
}
.gpu-device-title b {
  color: #50696f;
}
.gpu-led {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #b5c2c6;
}
.gpu-device.enabled .gpu-led {
  background: #2ca877;
  box-shadow: 0 0 0 3px #dff4e9;
}
.gpu-device-state {
  margin-left: auto;
  color: #97a5aa;
  font-size: 9px;
}
.gpu-device.enabled .gpu-device-state {
  color: #399778;
}
.gpu-device-model {
  display: block;
  margin: 7px 0 8px;
  overflow: hidden;
  color: #94a1a6;
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gpu-device-metrics {
  display: flex;
  justify-content: space-between;
  gap: 4px;
  color: #788c92;
  font-size: 9px;
}
.gpu-device-metrics span {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}
.gpu-status-note {
  display: block;
  margin-top: 11px;
  color: #9aa8ad;
  font-size: 9px;
  line-height: 1.5;
}
@media (max-width: 680px) {
  .gpu-status-label {
    display: none;
  }
  .gpu-status-popover {
    right: -68px;
  }
}
</style>
