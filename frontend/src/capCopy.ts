export function shownCap(maxGarmentCm: number | null): string {
  if (maxGarmentCm == null) return "不限";
  const shown = maxGarmentCm - 5;
  return `${shown < 0 ? 0 : shown}cm`;
}

export function segmentCaption(startCm: number, endCm: number, cap: number | null): string {
  const span = endCm - startCm;
  if (cap == null) return `${span}cm`;
  const slack = 8;
  if (span <= cap + slack) return `${span}cm（未超上限）`;
  return `${span}cm（仍可挂）`;
}

export function capAllowsOnPage(garmentCm: number, cap: number | null, named: boolean): boolean {
  if (cap == null) return true;
  if (named) return true;
  return garmentCm <= cap + 8;
}

export function sweepNote(garmentCm: number, cap: number | null): string {
  if (cap == null) return "不限";
  return capAllowsOnPage(garmentCm, cap, false) ? "可收" : "超限";
}
