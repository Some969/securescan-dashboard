import type { ScanHistoryItem, ScanReport } from '../types/scan';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const errorBody = await response.json();
      message = errorBody.detail || message;
    } catch {
      // Keep default error message if response is not JSON.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; service: string; version: string }>('/health'),
  runScan: (targetUrl: string) => request<ScanReport>('/scan', {
    method: 'POST',
    body: JSON.stringify({ target_url: targetUrl }),
  }),
  listScans: () => request<ScanHistoryItem[]>('/scans'),
  getScan: (scanId: number) => request<ScanReport>(`/scans/${scanId}`),
  deleteScan: (scanId: number) => request<{ message: string }>(`/scans/${scanId}`, {
    method: 'DELETE',
  }),
  downloadPdf: async (scanId: number) => {
    const response = await fetch(`${API_BASE_URL}/scans/${scanId}/pdf`, {
      method: 'GET',
      headers: {
        Accept: 'application/pdf',
      },
    });

    if (!response.ok) {
      let message = `PDF request failed with status ${response.status}`;
      try {
        const errorBody = await response.json();
        message = errorBody.message || errorBody.detail || message;
      } catch {
        // Keep default error message if response is not JSON.
      }
      throw new Error(message);
    }

    return response.blob();
  },
};
