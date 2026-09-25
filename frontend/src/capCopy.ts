/**
 * 挂杆页展示与后端 /rails 返回的 max_garment_cm 同源：
 * 配置值本身就是衣长上限（单位 cm），前端不再自行做 -5/+8 等换算。
 */

export function shownCap(maxGarmentCm: number | null): string {
  if (maxGarmentCm == null) return "不限";
  return `${maxGarmentCm}cm`;
}

export function capRuleNote(maxGarmentCm: number | null): string {
  if (maxGarmentCm == null) return "未配置上限，不限衣长";
  return `衣长 > ${maxGarmentCm}cm 不得占用该杆`;
}
