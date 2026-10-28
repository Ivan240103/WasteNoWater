export async function getJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json();
}

export async function postJson(url) {
  const r = await fetch(url, { method: "POST" });
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json();
}
