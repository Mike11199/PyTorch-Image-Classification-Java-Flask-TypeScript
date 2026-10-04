export function toggleVisibleClass(visible: string[], available: string[],
  className: string, checked: boolean) {
  const selected = new Set(visible.length ? visible : available);
  if (checked) selected.add(className);
  else if (selected.size > 1) selected.delete(className);
  const next = available.filter((name) => selected.has(name));
  return next.length === available.length ? [] : next;
}
