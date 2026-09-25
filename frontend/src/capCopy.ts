// 与后端 app/services/length_cap.py 同一把尺：上限即配置值，严格比较，无容差、无指定杆放行。
export function shownCap(maxGarmentCm: number | null): string {
  if (maxGarmentCm == null) return "不限";
  return `${maxGarmentCm}cm`;
}

export function segmentCaption(startCm: number, endCm: number, cap: number | null): string {
  const span = endCm - startCm;
  if (cap == null) return `${span}cm`;
  return span <= cap ? `${span}cm` : `${span}cm（超上限）`;
}

export function capAllowsOnPage(garmentCm: number, cap: number | null): boolean {
  if (cap == null) return true;
  return garmentCm <= cap;
}

export function sweepNote(garmentCm: number, cap: number | null): string {
  if (cap == null) return "不限";
  return capAllowsOnPage(garmentCm, cap) ? "可收" : "超限";
}
