export type ContactSummary = {
  contact_id: number;
  contact_name: string;
  contact_type_raw: string | null;
  contact_type_normalized: string;
  region_normalized: string;
  total_deals_count: number;
  won_deals_count: number;
  open_deals_count: number;
  lost_deals_count: number;
  total_amount_original: string;
};

export type ContactSummaryPage = {
  total: number;
  limit: number;
  offset: number;
  items: ContactSummary[];
};

export type FilterMetadata = {
  contact_types: string[];
  regions: string[];
  statuses: string[];
  min_created_at: string | null;
  max_created_at: string | null;
  min_closed_at: string | null;
  max_closed_at: string | null;
};

export type PipelineStatus = {
  run_id: string | null;
  dataset_name: string;
  dataset_kind: string;
  state: string;
  message: string;
  raw_contacts_count: number;
  raw_deals_count: number;
  raw_links_count: number;
  normalized_contacts_count: number;
  normalized_deals_count: number;
  started_at: string | null;
  finished_at: string | null;
  snapshot_paths: string[];
  is_active: boolean;
};

export type DatasetStorageStatus = {
  active_dataset: PipelineStatus | null;
  latest_run: PipelineStatus | null;
};

export type ContactFilters = {
  search: string;
  contactType: string;
  region: string;
  status: string;
  limit: number;
  offset: number;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

export async function fetchContacts(filters: ContactFilters): Promise<ContactSummaryPage> {
  const params = new URLSearchParams({
    limit: String(filters.limit),
    offset: String(filters.offset)
  });

  if (filters.search.trim()) {
    params.set("search", filters.search.trim());
  }
  if (filters.contactType) {
    params.set("contact_type", filters.contactType);
  }
  if (filters.region) {
    params.set("region", filters.region);
  }
  if (filters.status) {
    params.set("status", filters.status);
  }

  return request<ContactSummaryPage>(`/api/reports/contacts?${params.toString()}`);
}

export function fetchFilterMetadata(): Promise<FilterMetadata> {
  return request<FilterMetadata>("/api/meta/filters");
}

export function fetchDatasetStatus(): Promise<DatasetStorageStatus> {
  return request<DatasetStorageStatus>("/api/datasets/status");
}

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: {
      Accept: "application/json"
    }
  });

  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Request failed with HTTP ${response.status}`);
  }

  return (await response.json()) as T;
}

async function readError(response: Response): Promise<string | null> {
  try {
    const body = (await response.json()) as { detail?: unknown; message?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (typeof body.message === "string") {
      return body.message;
    }
  } catch {
    return null;
  }
  return null;
}
