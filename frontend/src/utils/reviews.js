export function reviewKey(borrowerId, mode) {
  return `riskvision:review:v1:${mode || "unknown"}:${borrowerId}`;
}
export function loadReview(key) {
  try {
    const saved = JSON.parse(localStorage.getItem(key));
    return {
      status: saved?.status || "Not reviewed",
      note: saved?.note || "",
      savedAt: saved?.savedAt || null,
    };
  } catch {
    return { status: "Not reviewed", note: "", savedAt: null };
  }
}
