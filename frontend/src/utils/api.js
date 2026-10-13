export const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");
export async function apiFetch(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: options.signal || controller.signal,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const detail = typeof body.detail === "string" ? body.detail
        : Array.isArray(body.detail) ? body.detail.map((item) => item.msg).join(" ") : "";
      throw new Error(detail || (response.status === 404
        ? "This record was not found."
        : "The analysis service could not complete this request. Please retry."));
    }
    return response;
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error(
        "The analysis service took too long to respond. Please retry.",
        { cause: error },
      );
    if (error instanceof TypeError)
      throw new Error(
        "Cannot connect to RiskVision. Start the analysis service and retry.",
        { cause: error },
      );
    throw error;
  } finally {
    clearTimeout(timer);
  }
}
export async function getJson(path, options) {
  return (await apiFetch(path, options)).json();
}
export const money = (value) =>
  value == null
    ? "—"
    : `₹${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 1 })}`;
export const label = (value) =>
  value
    ? value
        .toLowerCase()
        .replaceAll("_", " ")
        .replace(/^./, (c) => c.toUpperCase())
    : "Unavailable";
export function downloadFile(name, content, type = "text/plain;charset=utf-8") {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
