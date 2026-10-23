const API_BASE = "http://127.0.0.1:8000/api";

export async function fetchApi(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = options.headers || {};

  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

// Rules API
export const getRules = () => fetchApi("/rules");
export const createRule = (data) => fetchApi("/rules", { method: "POST", body: JSON.stringify(data) });
export const updateRule = (id, data) => fetchApi(`/rules/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const toggleRule = (id, enabled) => fetchApi(`/rules/${id}/toggle`, { method: "PATCH", body: JSON.stringify({ enabled }) });
export const reorderRules = (reorderItems) => fetchApi("/rules/reorder", { method: "POST", body: JSON.stringify(reorderItems) });
export const deleteRule = (id) => fetchApi(`/rules/${id}`, { method: "DELETE" });
export const seedDefaultRules = () => fetchApi("/rules/seed-defaults", { method: "POST" });

// Datasets API
export const downloadSampleCsvUrl = `${API_BASE}/datasets/sample-csv`;
export const uploadAndValidateDataset = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return fetchApi("/datasets/upload-and-validate", {
    method: "POST",
    body: formData,
  });
};

// Simulations API
export const runSimulation = (data) => fetchApi("/simulations", { method: "POST", body: JSON.stringify(data) });
export const getSimulations = () => fetchApi("/simulations");
export const getSimulationDetail = (id, params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") {
      query.append(k, v);
    }
  });
  const qs = query.toString() ? `?${query.toString()}` : "";
  return fetchApi(`/simulations/${id}${qs}`);
};
export const getExportSimulationCsvUrl = (id) => `${API_BASE}/simulations/${id}/export`;
export const deleteSimulation = (id) => fetchApi(`/simulations/${id}`, { method: "DELETE" });

// Dashboard API
export const getDashboardStats = () => fetchApi("/dashboard/stats");

// Policy Analysis API
export const runPolicyAnalysis = () => fetchApi("/analysis/run", { method: "POST" });
export const getLatestPolicyAnalysis = () => fetchApi("/analysis/latest");
export const getPolicyAnalyses = () => fetchApi("/analysis");
export const getPolicyAnalysisDetail = (id) => fetchApi(`/analysis/${id}`);
export const dismissFinding = (id, reason) => fetchApi(`/analysis/findings/${id}/dismiss`, {
  method: "PATCH",
  body: JSON.stringify({ reason }),
});
export const restoreFinding = (id) => fetchApi(`/analysis/findings/${id}/restore`, {
  method: "PATCH",
});

// Policy Comparisons API
export const createPolicyComparison = (data) => fetchApi("/comparisons", {
  method: "POST",
  body: JSON.stringify(data),
});
export const getPolicyComparisons = () => fetchApi("/comparisons");
export const getPolicyComparisonDetail = (id, params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") {
      query.append(k, v);
    }
  });
  const qs = query.toString() ? `?${query.toString()}` : "";
  return fetchApi(`/comparisons/${id}${qs}`);
};
export const getExportComparisonCsvUrl = (id) => `${API_BASE}/comparisons/${id}/export`;
export const deleteComparison = (id) => fetchApi(`/comparisons/${id}`, { method: "DELETE" });

// AI API
export const getAIStatus = () => fetchApi("/ai/status");

export const aiExplainFinding = (data) => fetchApi("/ai/explain-finding", {
  method: "POST",
  body: JSON.stringify(data),
});

export const aiSuggestImprovements = (data) => fetchApi("/ai/suggest-improvements", {
  method: "POST",
  body: JSON.stringify(data),
});

export const aiExplainComparison = (data) => fetchApi("/ai/explain-comparison", {
  method: "POST",
  body: JSON.stringify(data),
});

export const aiAssistant = (data) => fetchApi("/ai/assistant", {
  method: "POST",
  body: JSON.stringify(data),
});

