export type ContactAnalytics = {
  contact_id: number;
  contact_name: string;
  contact_type_normalized: string;
  region_normalized: string;
  total_deals_count: number;
  won_deals_count: number;
  open_deals_count: number;
  lost_deals_count: number;
  budget_usd: string;
  budget_in_work_usd: string;
  lost_budget_usd: string;
  revenue_usd: string;
  estimated_profit_usd: string;
  first_won_date: string | null;
  last_won_date: string | null;
  latest_deal_date: string | null;
  has_sales: boolean;
};

export type ContactAnalyticsPage = {
  total: number;
  limit: number;
  offset: number;
  items: ContactAnalytics[];
};

export type DealAnalytics = {
  deal_id: number;
  deal_name: string;
  status_group: string;
  contact_type_normalized: string;
  region_normalized: string;
  budget_usd: string;
  estimated_profit_usd: string;
  created_date: string;
  closed_date: string | null;
};

export type DealAnalyticsPage = {
  total: number;
  limit: number;
  offset: number;
  items: DealAnalytics[];
};

export type ContactSort =
  | "contact_id"
  | "contact_name"
  | "contact_type_normalized"
  | "region_normalized"
  | "total_deals_count"
  | "won_deals_count"
  | "open_deals_count"
  | "lost_deals_count"
  | "budget_usd"
  | "budget_in_work_usd"
  | "lost_budget_usd"
  | "revenue_usd"
  | "estimated_profit_usd"
  | "last_won_date"
  | "latest_deal_date";

export type SortOrder = "asc" | "desc";

export type DealSort =
  | "deal_id"
  | "deal_name"
  | "status_group"
  | "contact_type_normalized"
  | "region_normalized"
  | "budget_usd"
  | "estimated_profit_usd"
  | "created_date"
  | "closed_date";

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

export type LocalDataRefreshResponse = {
  status: PipelineStatus;
  message: string;
  contact_type_rules_count: number;
  active_contact_type_rules_count: number;
  currency_rate_rows_loaded: number;
  currency_rate_currencies: string[];
};

export type ContactFilters = {
  search: string;
  contactId: string;
  contactType: string;
  region: string;
  status: string;
  dealCreatedFrom: string;
  dealCreatedTo: string;
  sort: ContactSort;
  order: SortOrder;
  limit: number;
  offset: number;
};

export type DealFilters = {
  dealId: string;
  contactType: string;
  region: string;
  status: string;
  dealCreatedFrom: string;
  dealCreatedTo: string;
  sort: DealSort;
  order: SortOrder;
  limit: number;
  offset: number;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

export async function fetchContactAnalytics(
  filters: ContactFilters
): Promise<ContactAnalyticsPage> {
  const params = new URLSearchParams({
    limit: String(filters.limit),
    offset: String(filters.offset)
  });

  if (filters.search.trim()) {
    params.set("search", filters.search.trim());
  }
  if (filters.contactId.trim()) {
    params.set("contact_id", filters.contactId.trim());
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
  if (filters.dealCreatedFrom) {
    params.set("deal_created_from", filters.dealCreatedFrom);
  }
  if (filters.dealCreatedTo) {
    params.set("deal_created_to", filters.dealCreatedTo);
  }
  params.set("sort", filters.sort);
  params.set("order", filters.order);

  return request<ContactAnalyticsPage>(`/api/reports/contacts/analytics?${params.toString()}`);
}

export async function fetchDealAnalytics(filters: DealFilters): Promise<DealAnalyticsPage> {
  const params = new URLSearchParams({
    limit: String(filters.limit),
    offset: String(filters.offset)
  });

  if (filters.dealId.trim()) {
    params.set("deal_id", filters.dealId.trim());
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
  if (filters.dealCreatedFrom) {
    params.set("deal_created_from", filters.dealCreatedFrom);
  }
  if (filters.dealCreatedTo) {
    params.set("deal_created_to", filters.dealCreatedTo);
  }
  params.set("sort", filters.sort);
  params.set("order", filters.order);

  return request<DealAnalyticsPage>(`/api/reports/deals/analytics?${params.toString()}`);
}

export function fetchFilterMetadata(): Promise<FilterMetadata> {
  return request<FilterMetadata>("/api/meta/filters");
}

export function fetchDatasetStatus(): Promise<DatasetStorageStatus> {
  return request<DatasetStorageStatus>("/api/datasets/status");
}

export async function refreshLocalData(): Promise<LocalDataRefreshResponse> {
  const result = await request<LocalDataRefreshResponse>("/api/local/refresh-data", {
    method: "POST"
  });

  if (result.status.state !== "success") {
    throw new Error(result.message || result.status.message || "Не удалось обновить данные.");
  }

  return result;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...init?.headers
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
