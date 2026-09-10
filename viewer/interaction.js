export function canPlaceEndpoint(mode) {
  return mode === 'start' || mode === 'goal';
}

export function isBaselineQuery(query, baseline) {
  const flatten = q => [q?.radius, ...(q?.start ?? []), ...(q?.goal ?? [])];
  const a = flatten(query), b = flatten(baseline);
  return a.length === 5 && b.length === 5 &&
    a.every((value, i) => Number.isFinite(value) && Number.isFinite(b[i]) && Math.abs(value - b[i]) < 1e-6);
}
