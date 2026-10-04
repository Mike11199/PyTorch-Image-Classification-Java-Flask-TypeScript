export function toggleVisibleClass(visible: string[] | null, available: string[],
  className: string, checked: boolean) {
  const selected = new Set(visible === null ? [] : visible.length ? visible : available);
  if (checked) selected.add(className);
  else selected.delete(className);
  const next = available.filter((name) => selected.has(name));
  return next.length === 0 ? null : next.length === available.length ? [] : next;
}
