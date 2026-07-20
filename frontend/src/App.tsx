import { type FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  BarChart3,
  BriefcaseBusiness,
  ChevronLeft,
  ChevronRight,
  Database,
  Filter,
  Handshake,
  LockKeyhole,
  LogOut,
  PieChart,
  RefreshCcw,
  Search,
  X
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import {
  fetchAbcAnalytics,
  fetchContactAnalytics,
  fetchContactWonRevenueSeries,
  fetchAuthSession,
  fetchDatasetStatus,
  fetchDealAnalytics,
  fetchFilterMetadata,
  fetchKevConversion,
  isApiAuthError,
  login as authLogin,
  logout as authLogout,
  refreshLocalData,
  type AbcAnalytics,
  type AbcAnalyticsPage,
  type AbcFilters,
  type AbcSort,
  type ContactAnalytics,
  type ContactAnalyticsPage,
  type ContactFilters,
  type ContactSort,
  type ContactWonRevenueSeries,
  type DealAnalytics,
  type DealAnalyticsPage,
  type DealFilters,
  type DealSort,
  type FilterMetadata,
  type LocalDataRefreshResponse,
  type KevConversionReport,
  type KevFilters
} from "./api";

const PAGE_SIZE = 25;
const CONTACTS_STORAGE_KEY = "bitrix-sales.contacts.v1";
const DEALS_STORAGE_KEY = "bitrix-sales.deals.v1";
const ABC_STORAGE_KEY = "bitrix-sales.abc.v1";
const KEV_STORAGE_KEY = "bitrix-sales.kev.v1";
const FILTER_METADATA_STORAGE_KEY = "bitrix-sales.filter-metadata.v1";
const CONTACT_SORT_FIELDS: ContactSort[] = [
  "contact_id",
  "contact_name",
  "contact_type_normalized",
  "total_deals_count",
  "won_deals_count",
  "open_deals_count",
  "lost_deals_count",
  "budget_usd",
  "budget_in_work_usd",
  "lost_budget_usd",
  "revenue_usd",
  "estimated_profit_usd",
  "average_check_usd",
  "average_cycle_days",
  "last_won_date",
  "latest_deal_date"
];
const DEAL_SORT_FIELDS: DealSort[] = [
  "deal_id",
  "deal_name",
  "status_group",
  "contact_type_normalized",
  "budget_usd",
  "estimated_profit_usd",
  "created_date",
  "closed_date"
];
const ABC_SORT_FIELDS: AbcSort[] = [
  "contact_id",
  "contact_name",
  "contact_type_normalized",
  "base_revenue_usd",
  "base_revenue_share_percent",
  "base_cumulative_share_percent",
  "base_segment",
  "base_won_deals_count",
  "base_last_won_date",
  "target_revenue_usd",
  "target_segment",
  "segment_change",
  "migration_priority"
];
const ABC_SEGMENTS = ["A", "B", "C", "Нет продаж"];
const MIGRATION_PRIORITIES = [
  "срочно",
  "важно",
  "наблюдать",
  "развивать",
  "закрепить",
  "изменение",
  "без изменений"
];

const initialFilters: ContactFilters = {
  search: "",
  contactId: "",
  contactType: "",
  status: "",
  dealCreatedFrom: "",
  dealCreatedTo: "",
  categoryId: "",
  sort: "contact_id",
  order: "asc",
  limit: PAGE_SIZE,
  offset: 0
};

const initialDealFilters: DealFilters = {
  dealId: "",
  clientId: "",
  clientSearch: "",
  contactType: "",
  status: "",
  kevHeld: "",
  dealCreatedFrom: "",
  dealCreatedTo: "",
  categoryId: "",
  sort: "deal_id",
  order: "asc",
  limit: PAGE_SIZE,
  offset: 0
};

const initialKevFilters: KevFilters = {
  dateFrom: "",
  dateTo: "",
  contactType: ""
  ,dealCreatedFrom: "", dealCreatedTo: "", categoryId: ""
};

const initialAbcFilters: AbcFilters = {
  search: "",
  contactId: "",
  contactType: "",
  segment: "",
  migrationPriority: "",
  changedOnly: false,
  dateFrom: "",
  dateTo: "",
  compareDateFrom: "",
  compareDateTo: "",
  dealCreatedFrom: "",
  dealCreatedTo: "",
  categoryId: "",
  sort: "base_revenue_usd",
  order: "desc",
  limit: PAGE_SIZE,
  offset: 0
};

type ReportView = "contacts" | "deals" | "abc" | "kev";

export function App() {
  const queryClient = useQueryClient();
  const [activeReport, setActiveReport] = useState<ReportView>("contacts");
  const [filters, setFilters] = useState<ContactFilters>(() => loadStoredFilters());
  const [dealFilters, setDealFilters] = useState<DealFilters>(() => loadStoredDealFilters());
  const [abcFilters, setAbcFilters] = useState<AbcFilters>(() => loadStoredAbcFilters());
  const [kevFilters, setKevFilters] = useState<KevFilters>(() => loadStoredKevFilters());
  const [searchDraft, setSearchDraft] = useState(filters.search);
  const [contactIdDraft, setContactIdDraft] = useState(filters.contactId);
  const [dealIdDraft, setDealIdDraft] = useState(dealFilters.dealId);
  const [dealClientSearchDraft, setDealClientSearchDraft] = useState(dealFilters.clientSearch);
  const [abcSearchDraft, setAbcSearchDraft] = useState(abcFilters.search);
  const [abcContactIdDraft, setAbcContactIdDraft] = useState(abcFilters.contactId);
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [dealCreatedDrafts, setDealCreatedDrafts] = useState({
    from: filters.dealCreatedFrom,
    to: filters.dealCreatedTo
  });
  const [dealReportCreatedDrafts, setDealReportCreatedDrafts] = useState({
    from: dealFilters.dealCreatedFrom,
    to: dealFilters.dealCreatedTo
  });
  const [abcDateDrafts, setAbcDateDrafts] = useState({
    from: abcFilters.dateFrom,
    to: abcFilters.dateTo
  });
  const [abcDealCreatedDrafts, setAbcDealCreatedDrafts] = useState({ from: abcFilters.dealCreatedFrom, to: abcFilters.dealCreatedTo });
  const [abcCompareDateDrafts, setAbcCompareDateDrafts] = useState({
    from: abcFilters.compareDateFrom,
    to: abcFilters.compareDateTo
  });
  const [kevDateDrafts, setKevDateDrafts] = useState({
    from: kevFilters.dateFrom,
    to: kevFilters.dateTo
  });
  const [kevDealCreatedDrafts, setKevDealCreatedDrafts] = useState({ from: kevFilters.dealCreatedFrom, to: kevFilters.dealCreatedTo });
  const [lastFilterMetadata, setLastFilterMetadata] = useState<FilterMetadata | null>(() =>
    loadStoredFilterMetadata()
  );
  const [lastRefreshResult, setLastRefreshResult] = useState<LocalDataRefreshResponse | null>(
    null
  );
  const [revenueChartContact, setRevenueChartContact] = useState<ContactAnalytics | null>(null);
  const [isFilterDrawerOpen, setIsFilterDrawerOpen] = useState(false);
  const isDealCreatedRangeInvalid =
    Boolean(filters.dealCreatedFrom) &&
    Boolean(filters.dealCreatedTo) &&
    filters.dealCreatedFrom > filters.dealCreatedTo;
  const areDealCreatedDraftsInvalid =
    Boolean(dealCreatedDrafts.from) &&
    Boolean(dealCreatedDrafts.to) &&
    dealCreatedDrafts.from > dealCreatedDrafts.to;
  const areDealCreatedDraftsComplete =
    isEmptyOrCompleteIsoDate(dealCreatedDrafts.from) &&
    isEmptyOrCompleteIsoDate(dealCreatedDrafts.to);
  const areDealCreatedDraftsChanged =
    dealCreatedDrafts.from !== filters.dealCreatedFrom ||
    dealCreatedDrafts.to !== filters.dealCreatedTo;
  const isDealReportCreatedRangeInvalid =
    Boolean(dealFilters.dealCreatedFrom) &&
    Boolean(dealFilters.dealCreatedTo) &&
    dealFilters.dealCreatedFrom > dealFilters.dealCreatedTo;
  const areDealReportCreatedDraftsInvalid =
    Boolean(dealReportCreatedDrafts.from) &&
    Boolean(dealReportCreatedDrafts.to) &&
    dealReportCreatedDrafts.from > dealReportCreatedDrafts.to;
  const areDealReportCreatedDraftsComplete =
    isEmptyOrCompleteIsoDate(dealReportCreatedDrafts.from) &&
    isEmptyOrCompleteIsoDate(dealReportCreatedDrafts.to);
  const areDealReportCreatedDraftsChanged =
    dealReportCreatedDrafts.from !== dealFilters.dealCreatedFrom ||
    dealReportCreatedDrafts.to !== dealFilters.dealCreatedTo;
  const isAbcDateRangeInvalid =
    Boolean(abcFilters.dateFrom) &&
    Boolean(abcFilters.dateTo) &&
    abcFilters.dateFrom > abcFilters.dateTo;
  const isAbcDealCreatedRangeInvalid = Boolean(abcFilters.dealCreatedFrom) && Boolean(abcFilters.dealCreatedTo) && abcFilters.dealCreatedFrom > abcFilters.dealCreatedTo;
  const areAbcDealCreatedDraftsComplete = isEmptyOrCompleteIsoDate(abcDealCreatedDrafts.from) && isEmptyOrCompleteIsoDate(abcDealCreatedDrafts.to);
  const areAbcDealCreatedDraftsInvalid = Boolean(abcDealCreatedDrafts.from) && Boolean(abcDealCreatedDrafts.to) && abcDealCreatedDrafts.from > abcDealCreatedDrafts.to;
  const areAbcDealCreatedDraftsChanged = abcDealCreatedDrafts.from !== abcFilters.dealCreatedFrom || abcDealCreatedDrafts.to !== abcFilters.dealCreatedTo;
  const areAbcDateDraftsInvalid =
    Boolean(abcDateDrafts.from) &&
    Boolean(abcDateDrafts.to) &&
    abcDateDrafts.from > abcDateDrafts.to;
  const areAbcDateDraftsComplete =
    isEmptyOrCompleteIsoDate(abcDateDrafts.from) &&
    isEmptyOrCompleteIsoDate(abcDateDrafts.to);
  const areAbcDateDraftsChanged =
    abcDateDrafts.from !== abcFilters.dateFrom || abcDateDrafts.to !== abcFilters.dateTo;
  const isAbcCompareIncomplete =
    (Boolean(abcFilters.compareDateFrom) && !abcFilters.compareDateTo) ||
    (!abcFilters.compareDateFrom && Boolean(abcFilters.compareDateTo));
  const isAbcCompareRangeInvalid =
    Boolean(abcFilters.compareDateFrom) &&
    Boolean(abcFilters.compareDateTo) &&
    abcFilters.compareDateFrom > abcFilters.compareDateTo;
  const areAbcCompareDraftsInvalid =
    Boolean(abcCompareDateDrafts.from) &&
    Boolean(abcCompareDateDrafts.to) &&
    abcCompareDateDrafts.from > abcCompareDateDrafts.to;
  const areAbcCompareDraftsComplete =
    isEmptyOrCompleteIsoDate(abcCompareDateDrafts.from) &&
    isEmptyOrCompleteIsoDate(abcCompareDateDrafts.to);
  const areAbcCompareDraftsChanged =
    abcCompareDateDrafts.from !== abcFilters.compareDateFrom ||
    abcCompareDateDrafts.to !== abcFilters.compareDateTo;
  const isAbcCompareEnabled =
    Boolean(abcFilters.compareDateFrom) && Boolean(abcFilters.compareDateTo);
  const isKevDateRangeInvalid =
    Boolean(kevFilters.dateFrom) &&
    Boolean(kevFilters.dateTo) &&
    kevFilters.dateFrom > kevFilters.dateTo;
  const isKevDealCreatedRangeInvalid = Boolean(kevFilters.dealCreatedFrom) && Boolean(kevFilters.dealCreatedTo) && kevFilters.dealCreatedFrom > kevFilters.dealCreatedTo;
  const areKevDealCreatedDraftsComplete = isEmptyOrCompleteIsoDate(kevDealCreatedDrafts.from) && isEmptyOrCompleteIsoDate(kevDealCreatedDrafts.to);
  const areKevDealCreatedDraftsInvalid = Boolean(kevDealCreatedDrafts.from) && Boolean(kevDealCreatedDrafts.to) && kevDealCreatedDrafts.from > kevDealCreatedDrafts.to;
  const areKevDealCreatedDraftsChanged = kevDealCreatedDrafts.from !== kevFilters.dealCreatedFrom || kevDealCreatedDrafts.to !== kevFilters.dealCreatedTo;
  const areKevDateDraftsInvalid =
    Boolean(kevDateDrafts.from) &&
    Boolean(kevDateDrafts.to) &&
    kevDateDrafts.from > kevDateDrafts.to;
  const areKevDateDraftsComplete =
    isEmptyOrCompleteIsoDate(kevDateDrafts.from) && isEmptyOrCompleteIsoDate(kevDateDrafts.to);
  const areKevDateDraftsChanged =
    kevDateDrafts.from !== kevFilters.dateFrom || kevDateDrafts.to !== kevFilters.dateTo;

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setFilters((current) => ({
        ...current,
        search: searchDraft,
        offset: 0
      }));
    }, 300);

    return () => window.clearTimeout(timer);
  }, [searchDraft]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDealFilters((current) => ({
        ...current,
        clientSearch: dealClientSearchDraft,
        offset: 0
      }));
    }, 300);

    return () => window.clearTimeout(timer);
  }, [dealClientSearchDraft]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setAbcFilters((current) => ({
        ...current,
        search: abcSearchDraft,
        offset: 0
      }));
    }, 300);

    return () => window.clearTimeout(timer);
  }, [abcSearchDraft]);

  useEffect(() => {
    storeFilters(filters);
  }, [filters]);

  useEffect(() => {
    storeDealFilters(dealFilters);
  }, [dealFilters]);

  useEffect(() => {
    storeAbcFilters(abcFilters);
  }, [abcFilters]);

  useEffect(() => {
    storeKevFilters(kevFilters);
  }, [kevFilters]);

  const authQuery = useQuery({
    queryKey: ["auth-session"],
    queryFn: fetchAuthSession,
    retry: false
  });
  const canUseApi = authQuery.data?.authenticated === true;
  const isAuthEnabled = authQuery.data?.auth_enabled === true;

  const statusQuery = useQuery({
    queryKey: ["dataset-status"],
    queryFn: fetchDatasetStatus,
    enabled: canUseApi
  });

  const activeDataset = statusQuery.data?.active_dataset;
  const isDatasetReady = activeDataset?.state === "success" && activeDataset.is_active;
  const activeContactsCount = activeDataset?.normalized_contacts_count;

  const filterQuery = useQuery({
    queryKey: ["filter-metadata"],
    queryFn: fetchFilterMetadata,
    enabled: canUseApi && isDatasetReady
  });
  const isFreshFilterMetadataValid = isFilterMetadataValidForDataset(
    filterQuery.data,
    activeContactsCount
  );
  const isStoredFilterMetadataValid = isFilterMetadataValidForDataset(
    lastFilterMetadata,
    activeContactsCount
  );
  const isFreshFilterMetadataInvalid = Boolean(filterQuery.data) && !isFreshFilterMetadataValid;
  const filterMetadata = isFreshFilterMetadataValid
    ? filterQuery.data
    : isStoredFilterMetadataValid
      ? lastFilterMetadata
      : null;

  const contactsQuery = useQuery({
    queryKey: ["contacts", filters],
    queryFn: () => fetchContactAnalytics(filters),
    enabled:
      canUseApi && activeReport === "contacts" && isDatasetReady && !isDealCreatedRangeInvalid
  });

  const dealsQuery = useQuery({
    queryKey: ["deals", dealFilters],
    queryFn: () => fetchDealAnalytics(dealFilters),
    enabled:
      canUseApi && activeReport === "deals" && isDatasetReady && !isDealReportCreatedRangeInvalid
  });

  const abcQuery = useQuery({
    queryKey: ["abc", abcFilters],
    queryFn: () => fetchAbcAnalytics(abcFilters),
    enabled:
      canUseApi &&
      activeReport === "abc" &&
      isDatasetReady &&
      !isAbcDateRangeInvalid &&
      !isAbcDealCreatedRangeInvalid &&
      !isAbcCompareIncomplete &&
      !isAbcCompareRangeInvalid
  });

  const kevQuery = useQuery({
    queryKey: ["kev-conversion", kevFilters],
    queryFn: () => fetchKevConversion(kevFilters),
    enabled: canUseApi && activeReport === "kev" && isDatasetReady && !isKevDateRangeInvalid && !isKevDealCreatedRangeInvalid
  });

  const revenueSeriesQuery = useQuery({
    queryKey: [
      "contact-won-revenue-series",
      revenueChartContact?.contact_id,
      filters.dealCreatedFrom,
      filters.dealCreatedTo
    ],
    queryFn: () =>
      fetchContactWonRevenueSeries({
        contactId: revenueChartContact?.contact_id ?? 0,
        dateFrom: filters.dealCreatedFrom,
        dateTo: filters.dealCreatedTo
      }),
    enabled: canUseApi && Boolean(revenueChartContact) && isDatasetReady
  });

  const loginMutation = useMutation({
    mutationFn: authLogin,
    onSuccess: async () => {
      setLoginPassword("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["auth-session"] }),
        queryClient.invalidateQueries({ queryKey: ["dataset-status"] }),
        queryClient.invalidateQueries({ queryKey: ["filter-metadata"] })
      ]);
    }
  });

  const logoutMutation = useMutation({
    mutationFn: authLogout,
    onSuccess: async (result) => {
      setRevenueChartContact(null);
      setIsFilterDrawerOpen(false);
      queryClient.setQueryData(["auth-session"], result);
      await queryClient.invalidateQueries({ queryKey: ["auth-session"] });
    }
  });

  const refreshMutation = useMutation({
    mutationFn: refreshLocalData,
    onMutate: () => {
      setLastRefreshResult(null);
    },
    onSuccess: async (result) => {
      setLastRefreshResult(result);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["dataset-status"] }),
        queryClient.invalidateQueries({ queryKey: ["filter-metadata"] }),
        queryClient.invalidateQueries({ queryKey: ["contacts"] }),
        queryClient.invalidateQueries({ queryKey: ["deals"] }),
        queryClient.invalidateQueries({ queryKey: ["abc"] }),
        queryClient.invalidateQueries({ queryKey: ["kev-conversion"] })
      ]);
    },
    onSettled: async () => {
      await queryClient.invalidateQueries({ queryKey: ["dataset-status"] });
    }
  });

  useEffect(() => {
    if (isFreshFilterMetadataValid && filterQuery.data) {
      setLastFilterMetadata(filterQuery.data);
      storeFilterMetadata(filterQuery.data);
    }
  }, [filterQuery.data, isFreshFilterMetadataValid]);

  useEffect(() => {
    if (!revenueChartContact) {
      return;
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setRevenueChartContact(null);
      }
    }

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [revenueChartContact]);

  useEffect(() => {
    if (!isFilterDrawerOpen) {
      return;
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsFilterDrawerOpen(false);
      }
    }

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [isFilterDrawerOpen]);

  const activeQuery =
    activeReport === "contacts"
      ? contactsQuery
      : activeReport === "deals"
        ? dealsQuery
        : activeReport === "abc"
          ? abcQuery
          : kevQuery;
  const hasSessionExpired =
    isApiAuthError(statusQuery.error) ||
    isApiAuthError(filterQuery.error) ||
    isApiAuthError(contactsQuery.error) ||
    isApiAuthError(dealsQuery.error) ||
    isApiAuthError(abcQuery.error) ||
    isApiAuthError(kevQuery.error) ||
    isApiAuthError(revenueSeriesQuery.error) ||
    isApiAuthError(refreshMutation.error);
  const activeFilters =
    activeReport === "contacts" ? filters : activeReport === "deals" ? dealFilters : abcFilters;
  const activeRangeInvalid =
    activeReport === "contacts"
      ? isDealCreatedRangeInvalid
      : activeReport === "deals"
        ? isDealReportCreatedRangeInvalid
        : activeReport === "abc"
          ? isAbcDateRangeInvalid || isAbcCompareIncomplete || isAbcCompareRangeInvalid
          : isKevDateRangeInvalid;
  const activeDraftsInvalid =
    activeReport === "contacts"
      ? areDealCreatedDraftsInvalid
      : activeReport === "deals"
        ? areDealReportCreatedDraftsInvalid
        : activeReport === "abc"
          ? areAbcDateDraftsInvalid || areAbcCompareDraftsInvalid
          : areKevDateDraftsInvalid;
  const total =
    activeReport === "contacts"
      ? contactsQuery.data?.total ?? 0
      : activeReport === "deals"
        ? dealsQuery.data?.total ?? 0
        : activeReport === "abc"
          ? abcQuery.data?.total ?? 0
          : 0;
  const isRefreshing = refreshMutation.isPending;
  const pageNumber = Math.floor(activeFilters.offset / activeFilters.limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / activeFilters.limit));
  const hasPreviousPage = activeFilters.offset > 0;
  const hasNextPage = activeFilters.offset + activeFilters.limit < total;
  const showPagination =
    isDatasetReady &&
    !statusQuery.isPending &&
    !isRefreshing &&
    !activeQuery.isPending &&
    !activeQuery.isError &&
    !activeRangeInvalid &&
    activeReport !== "kev";
  const tableSubtitle = statusQuery.isPending
    ? "Проверка локального dataset"
    : !isDatasetReady
      ? "Локальная база не подготовлена"
      : activeQuery.isPending
        ? "Загрузка данных"
        : activeReport === "contacts"
          ? `${total.toLocaleString("ru-RU")} контактов найдено`
          : activeReport === "deals"
            ? `${total.toLocaleString("ru-RU")} сделок найдено`
            : activeReport === "abc"
              ? `${total.toLocaleString("ru-RU")} клиентов в ABC`
              : kevReportSubtitle(kevQuery.data);

  const selectedFilterCount = useMemo(
    () =>
      [
        filters.search.trim(),
        filters.contactId.trim(),
        filters.contactType,
        filters.status,
        filters.dealCreatedFrom,
        filters.dealCreatedTo
        ,filters.categoryId
      ].filter(Boolean).length,
    [filters]
  );
  const selectedDealFilterCount = useMemo(
    () =>
      [
        dealFilters.dealId.trim(),
        dealFilters.clientSearch.trim() || dealFilters.clientId.trim(),
        dealFilters.contactType,
        dealFilters.status,
        dealFilters.kevHeld,
        dealFilters.dealCreatedFrom,
        dealFilters.dealCreatedTo
        ,dealFilters.categoryId
      ].filter(Boolean).length,
    [dealFilters]
  );
  const selectedAbcFilterCount = useMemo(
    () =>
      [
        abcFilters.search.trim(),
        abcFilters.contactId.trim(),
        abcFilters.contactType,
        abcFilters.segment,
        abcFilters.migrationPriority,
        abcFilters.changedOnly && isAbcCompareEnabled ? "changed" : "",
        abcFilters.dateFrom,
        abcFilters.dateTo,
        abcFilters.compareDateFrom,
        abcFilters.compareDateTo
        ,abcFilters.categoryId, abcFilters.dealCreatedFrom, abcFilters.dealCreatedTo
      ].filter(Boolean).length,
    [abcFilters, isAbcCompareEnabled]
  );
  const selectedKevFilterCount = useMemo(
    () => [kevFilters.dateFrom, kevFilters.dateTo, kevFilters.contactType, kevFilters.categoryId, kevFilters.dealCreatedFrom, kevFilters.dealCreatedTo].filter(Boolean).length,
    [kevFilters]
  );
  const activeSelectedFilterCount =
    activeReport === "contacts"
      ? selectedFilterCount
      : activeReport === "deals"
        ? selectedDealFilterCount
        : activeReport === "abc"
          ? selectedAbcFilterCount
          : selectedKevFilterCount;

  useEffect(() => {
    if (!canUseApi || !hasSessionExpired) {
      return;
    }

    setRevenueChartContact(null);
    setIsFilterDrawerOpen(false);
    void authQuery.refetch();
  }, [authQuery.refetch, canUseApi, hasSessionExpired]);

  function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!loginUsername.trim() || !loginPassword) {
      return;
    }
    loginMutation.mutate({
      username: loginUsername.trim(),
      password: loginPassword
    });
  }

  function updateFilter(name: keyof ContactFilters, value: string) {
    setFilters((current) => ({
      ...current,
      [name]: value,
      offset: 0
    }));
  }

  function resetFilters() {
    setSearchDraft("");
    setContactIdDraft("");
    setDealCreatedDrafts({ from: "", to: "" });
    window.localStorage.removeItem(CONTACTS_STORAGE_KEY);
    setFilters(initialFilters);
    void queryClient.invalidateQueries({ queryKey: ["contacts"] });
  }

  function resetDealFilters() {
    setDealIdDraft("");
    setDealClientSearchDraft("");
    setDealReportCreatedDrafts({ from: "", to: "" });
    window.localStorage.removeItem(DEALS_STORAGE_KEY);
    setDealFilters(initialDealFilters);
    void queryClient.invalidateQueries({ queryKey: ["deals"] });
  }

  function resetAbcFilters() {
    setAbcSearchDraft("");
    setAbcContactIdDraft("");
    setAbcDateDrafts({ from: "", to: "" });
    setAbcCompareDateDrafts({ from: "", to: "" });
    setAbcDealCreatedDrafts({ from: "", to: "" });
    window.localStorage.removeItem(ABC_STORAGE_KEY);
    setAbcFilters(initialAbcFilters);
    void queryClient.invalidateQueries({ queryKey: ["abc"] });
  }

  function resetKevFilters() {
    setKevDateDrafts({ from: "", to: "" });
    setKevDealCreatedDrafts({ from: "", to: "" });
    window.localStorage.removeItem(KEV_STORAGE_KEY);
    setKevFilters(initialKevFilters);
    void queryClient.invalidateQueries({ queryKey: ["kev-conversion"] });
  }

  function updateKevFilter(name: keyof KevFilters, value: string) {
    setKevFilters((current) => ({ ...current, [name]: value }));
  }

  function updateContactIdFilter(value: string) {
    const numericValue = value.replace(/\D/g, "");
    setContactIdDraft(numericValue);
    updateFilter("contactId", numericValue);
  }

  function updateDealFilter(name: keyof DealFilters, value: string) {
    setDealFilters((current) => ({
      ...current,
      [name]: value,
      offset: 0
    }));
  }

  function updateAbcFilter(name: keyof AbcFilters, value: string | boolean) {
    setAbcFilters((current) => ({
      ...current,
      [name]: value,
      offset: 0
    }));
  }

  function updateAbcContactIdFilter(value: string) {
    const numericValue = value.replace(/\D/g, "");
    setAbcContactIdDraft(numericValue);
    updateAbcFilter("contactId", numericValue);
  }

  function updateDealIdFilter(value: string) {
    const numericValue = value.replace(/\D/g, "");
    setDealIdDraft(numericValue);
    updateDealFilter("dealId", numericValue);
  }

  function updateDealClientSearch(value: string) {
    setDealClientSearchDraft(value);
    setDealFilters((current) =>
      current.clientId
        ? {
            ...current,
            clientId: "",
            offset: 0
          }
        : current
    );
  }

  function openDealsForContact(contact: ContactAnalytics, status?: string) {
    const nextFilters: DealFilters = {
      ...initialDealFilters,
      clientId: String(contact.contact_id),
      clientSearch: contact.contact_name,
      status: status ?? "",
      categoryId: filters.categoryId,
      dealCreatedFrom: filters.dealCreatedFrom,
      dealCreatedTo: filters.dealCreatedTo
    };
    setDealIdDraft("");
    setDealClientSearchDraft(contact.contact_name);
    setDealReportCreatedDrafts({ from: filters.dealCreatedFrom, to: filters.dealCreatedTo });
    setDealFilters(nextFilters);
    setActiveReport("deals");
    void queryClient.invalidateQueries({ queryKey: ["deals"] });
  }

  function updateSort(sort: ContactSort) {
    setFilters((current) => ({
      ...current,
      sort,
      order: current.sort === sort ? (current.order === "desc" ? "asc" : "desc") : "desc",
      offset: 0
    }));
  }

  function updateDealSort(sort: DealSort) {
    setDealFilters((current) => ({
      ...current,
      sort,
      order: current.sort === sort ? (current.order === "desc" ? "asc" : "desc") : "desc",
      offset: 0
    }));
  }

  function updateAbcSort(sort: AbcSort) {
    setAbcFilters((current) => ({
      ...current,
      sort,
      order: current.sort === sort ? (current.order === "desc" ? "asc" : "desc") : "desc",
      offset: 0
    }));
  }

  function updateDealCreatedDraft(name: "from" | "to", value: string) {
    setDealCreatedDrafts((current) => ({
      ...current,
      [name]: value
    }));
  }

  function applyDealCreatedDrafts() {
    if (!areDealCreatedDraftsComplete || areDealCreatedDraftsInvalid) {
      return;
    }
    setFilters((current) => ({
      ...current,
      dealCreatedFrom: dealCreatedDrafts.from,
      dealCreatedTo: dealCreatedDrafts.to,
      offset: 0
    }));
  }

  function updateDealReportCreatedDraft(name: "from" | "to", value: string) {
    setDealReportCreatedDrafts((current) => ({
      ...current,
      [name]: value
    }));
  }

  function applyDealReportCreatedDrafts() {
    if (!areDealReportCreatedDraftsComplete || areDealReportCreatedDraftsInvalid) {
      return;
    }
    setDealFilters((current) => ({
      ...current,
      dealCreatedFrom: dealReportCreatedDrafts.from,
      dealCreatedTo: dealReportCreatedDrafts.to,
      offset: 0
    }));
  }

  function updateAbcDateDraft(name: "from" | "to", value: string) {
    setAbcDateDrafts((current) => ({
      ...current,
      [name]: value
    }));
  }

  function applyAbcDateDrafts() {
    if (!areAbcDateDraftsComplete || areAbcDateDraftsInvalid) {
      return;
    }
    setAbcFilters((current) => ({
      ...current,
      dateFrom: abcDateDrafts.from,
      dateTo: abcDateDrafts.to,
      offset: 0
    }));
  }

  function updateAbcDealCreatedDraft(name: "from" | "to", value: string) {
    setAbcDealCreatedDrafts((current) => ({ ...current, [name]: value }));
  }

  function applyAbcDealCreatedDrafts() {
    if (!areAbcDealCreatedDraftsComplete || areAbcDealCreatedDraftsInvalid) return;
    setAbcFilters((current) => ({ ...current, dealCreatedFrom: abcDealCreatedDrafts.from, dealCreatedTo: abcDealCreatedDrafts.to, offset: 0 }));
  }

  function updateAbcCompareDateDraft(name: "from" | "to", value: string) {
    setAbcCompareDateDrafts((current) => ({
      ...current,
      [name]: value
    }));
  }

  function applyAbcCompareDateDrafts() {
    if (!areAbcCompareDraftsComplete || areAbcCompareDraftsInvalid) {
      return;
    }
    const hasOneCompareDate = Boolean(abcCompareDateDrafts.from) !== Boolean(abcCompareDateDrafts.to);
    if (hasOneCompareDate) {
      return;
    }
    setAbcFilters((current) => ({
      ...current,
      compareDateFrom: abcCompareDateDrafts.from,
      compareDateTo: abcCompareDateDrafts.to,
      offset: 0
    }));
  }

  function updateKevDateDraft(name: "from" | "to", value: string) {
    setKevDateDrafts((current) => ({ ...current, [name]: value }));
  }

  function applyKevDateDrafts() {
    if (!areKevDateDraftsComplete || areKevDateDraftsInvalid) {
      return;
    }
    setKevFilters((current) => ({
      ...current,
      dateFrom: kevDateDrafts.from,
      dateTo: kevDateDrafts.to
    }));
  }

  function updateKevDealCreatedDraft(name: "from" | "to", value: string) {
    setKevDealCreatedDrafts((current) => ({ ...current, [name]: value }));
  }

  function applyKevDealCreatedDrafts() {
    if (!areKevDealCreatedDraftsComplete || areKevDealCreatedDraftsInvalid) return;
    setKevFilters((current) => ({ ...current, dealCreatedFrom: kevDealCreatedDrafts.from, dealCreatedTo: kevDealCreatedDrafts.to }));
  }

  function changePage(direction: "previous" | "next") {
    if (activeReport === "contacts") {
      setFilters((current) => ({
        ...current,
        offset:
          direction === "previous"
            ? Math.max(0, current.offset - current.limit)
            : current.offset + current.limit
      }));
      return;
    }
    if (activeReport === "deals") {
      setDealFilters((current) => ({
        ...current,
        offset:
          direction === "previous"
            ? Math.max(0, current.offset - current.limit)
            : current.offset + current.limit
      }));
      return;
    }
    setAbcFilters((current) => ({
      ...current,
      offset:
        direction === "previous"
          ? Math.max(0, current.offset - current.limit)
          : current.offset + current.limit
    }));
  }

  if (authQuery.isPending) {
    return <AuthLoadingScreen />;
  }

  if (authQuery.isError) {
    return (
      <AuthMessageScreen
        title="Не удалось проверить сессию"
        message={authQuery.error.message}
        onRetry={() => void authQuery.refetch()}
      />
    );
  }

  if (isAuthEnabled && !canUseApi) {
    return (
      <LoginScreen
        username={loginUsername}
        password={loginPassword}
        isSubmitting={loginMutation.isPending}
        errorMessage={loginMutation.isError ? "Неверный логин или пароль." : null}
        onUsernameChange={setLoginUsername}
        onPasswordChange={setLoginPassword}
        onSubmit={submitLogin}
      />
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Основная навигация">
        <div className="brand">
          <span className="brand-mark">BS</span>
          <span>Bitrix Sales</span>
        </div>
        <nav className="nav-list">
          <button
            className={activeReport === "contacts" ? "nav-item nav-item-active" : "nav-item"}
            type="button"
            onClick={() => setActiveReport("contacts")}
            aria-current={activeReport === "contacts" ? "page" : undefined}
          >
            <BarChart3 size={18} strokeWidth={1.5} />
            Contacts
          </button>
          <button
            className={activeReport === "deals" ? "nav-item nav-item-active" : "nav-item"}
            type="button"
            onClick={() => setActiveReport("deals")}
            aria-current={activeReport === "deals" ? "page" : undefined}
          >
            <BriefcaseBusiness size={18} strokeWidth={1.5} />
            Deals
          </button>
          <button
            className={activeReport === "abc" ? "nav-item nav-item-active" : "nav-item"}
            type="button"
            onClick={() => setActiveReport("abc")}
            aria-current={activeReport === "abc" ? "page" : undefined}
          >
            <PieChart size={18} strokeWidth={1.5} />
            ABC
          </button>
          <button
            className={activeReport === "kev" ? "nav-item nav-item-active" : "nav-item"}
            type="button"
            onClick={() => setActiveReport("kev")}
            aria-current={activeReport === "kev" ? "page" : undefined}
          >
            <Handshake size={18} strokeWidth={1.5} />
            КЭВ
          </button>
        </nav>
      </aside>

      <main className="main-panel" id={activeReport}>
        <header className="workspace-header">
          <div className="workspace-title">
            <span className="badge badge-neutral">Reports</span>
            <strong>{reportTitle(activeReport)}</strong>
            {activeSelectedFilterCount > 0 && (
              <span className="badge badge-primary">{activeSelectedFilterCount} фильтра</span>
            )}
          </div>
          <div className="header-actions">
            {isDatasetReady && (
              <button
                className="button button-secondary"
                type="button"
                onClick={() => setIsFilterDrawerOpen(true)}
              >
                <Filter size={16} strokeWidth={1.5} />
                Фильтры
              </button>
            )}
            <DatasetBadge
              isLoading={statusQuery.isPending}
              isError={statusQuery.isError}
              state={activeDataset?.state}
              count={activeDataset?.normalized_contacts_count}
              finishedAt={activeDataset?.finished_at}
            />
            {isDatasetReady && (
              <button
                className="button button-primary"
                type="button"
                disabled={isRefreshing}
                onClick={() => refreshMutation.mutate()}
              >
                <RefreshCcw size={16} strokeWidth={1.5} />
                {isRefreshing ? "Обновление..." : "Обновить из Bitrix"}
              </button>
            )}
            {isAuthEnabled && (
              <button
                className="button button-secondary"
                type="button"
                disabled={logoutMutation.isPending}
                onClick={() => logoutMutation.mutate()}
              >
                <LogOut size={16} strokeWidth={1.5} />
                {logoutMutation.isPending ? "Выход..." : "Выйти"}
              </button>
            )}
          </div>
        </header>

        {isDatasetReady &&
          (filterQuery.isError || (isFreshFilterMetadataInvalid && !filterMetadata)) && (
            <InlineAlert
              title={
                filterMetadata
                  ? "Фильтры показаны из кэша"
                  : "Не удалось загрузить фильтры"
              }
              message={
                filterQuery.isError
                  ? filterQuery.error.message
                  : "Backend вернул пустые фильтры для активной базы. Повторите загрузку фильтров."
              }
              onRetry={() => void filterQuery.refetch()}
            />
          )}

        {isDatasetReady && refreshMutation.isError && !isRefreshing && (
          <InlineAlert
            title="Не удалось обновить данные"
            message={refreshMutation.error.message}
            onRetry={() => refreshMutation.mutate()}
          />
        )}

        {lastRefreshResult && !isRefreshing && (
          <InlineSuccess message={formatRefreshSuccess(lastRefreshResult)} />
        )}

        {isDatasetReady && activeRangeInvalid && (
          <InlineValidation message={rangeValidationMessage(activeReport, isAbcCompareIncomplete)} />
        )}

        {isDatasetReady && activeDraftsInvalid && (
          <InlineValidation message={draftRangeValidationMessage(activeReport)} />
        )}

        <section className="table-card" aria-label={reportTitle(activeReport)}>
          <div className="table-header">
            <div>
              <h2>{tableTitle(activeReport)}</h2>
              <p>{tableSubtitle}</p>
            </div>
            {activeSelectedFilterCount > 0 && (
              <span className="badge badge-primary">{activeSelectedFilterCount} активных фильтра</span>
            )}
          </div>

          {statusQuery.isError ? (
            <TableError
              entityLabel={entityLabel(activeReport)}
              message={statusQuery.error.message}
              onRetry={() => void statusQuery.refetch()}
            />
          ) : statusQuery.isPending ? (
            <ContactsSkeleton />
          ) : isRefreshing ? (
            <RefreshProgressState />
          ) : !isDatasetReady ? (
            <DatabaseNotReadyState
              errorMessage={refreshMutation.isError ? refreshMutation.error.message : null}
              isRefreshing={isRefreshing}
              onRefresh={() => refreshMutation.mutate()}
            />
          ) : activeQuery.isError ? (
            <TableError
              entityLabel={entityLabel(activeReport)}
              message={activeQuery.error.message}
              onRetry={() => void activeQuery.refetch()}
            />
          ) : activeRangeInvalid ? (
            <EmptyState
              entityLabel={reportTitle(activeReport)}
              onReset={
                activeReport === "contacts"
                  ? resetFilters
                  : activeReport === "deals"
                    ? resetDealFilters
                    : activeReport === "abc"
                      ? resetAbcFilters
                      : resetKevFilters
              }
            />
          ) : activeQuery.isPending ? (
            <ContactsSkeleton />
          ) : activeReport === "contacts" && (contactsQuery.data?.items.length ?? 0) === 0 ? (
            <EmptyState entityLabel="Контакты" onReset={resetFilters} />
          ) : activeReport === "deals" && (dealsQuery.data?.items.length ?? 0) === 0 ? (
            <EmptyState entityLabel="Сделки" onReset={resetDealFilters} />
          ) : activeReport === "abc" && (abcQuery.data?.items.length ?? 0) === 0 ? (
            <EmptyState entityLabel="ABC" onReset={resetAbcFilters} />
          ) : activeReport === "kev" &&
            kevQuery.data &&
            kevQuery.data.with_kev.closed_deals_count +
              kevQuery.data.without_kev.closed_deals_count ===
              0 ? (
            <KevNoDataState onReset={resetKevFilters} />
          ) : activeReport === "contacts" ? (
            <ContactsTable
              contacts={contactsQuery.data?.items ?? []}
              page={contactsQuery.data}
              sort={filters.sort}
              order={filters.order}
              onSort={updateSort}
              onOpenDeals={openDealsForContact}
              onOpenRevenueChart={setRevenueChartContact}
            />
          ) : activeReport === "deals" ? (
            <>
              <DealsTable
                deals={dealsQuery.data?.items ?? []}
                page={dealsQuery.data}
                sort={dealFilters.sort}
                order={dealFilters.order}
                onSort={updateDealSort}
              />
            </>
          ) : activeReport === "abc" ? (
            <>
              {abcQuery.data && (
                <AbcSummaryBar page={abcQuery.data} isCompareEnabled={isAbcCompareEnabled} />
              )}
              <AbcTable
                rows={abcQuery.data?.items ?? []}
                sort={abcFilters.sort}
                order={abcFilters.order}
                isCompareEnabled={isAbcCompareEnabled}
                onSort={updateAbcSort}
              />
              {abcQuery.data && (
                <AbcSummaryBar page={abcQuery.data} isCompareEnabled={isAbcCompareEnabled} />
              )}
            </>
          ) : (
            <KevConversionComparison report={kevQuery.data!} />
          )}

          {showPagination && (
            <div className="pagination">
              <span>
                Страница {pageNumber.toLocaleString("ru-RU")} из {totalPages.toLocaleString("ru-RU")}
              </span>
              <div className="pagination-actions">
                <button
                  className="icon-button"
                  type="button"
                  disabled={!hasPreviousPage}
                  onClick={() => changePage("previous")}
                  aria-label="Предыдущая страница"
                >
                  <ChevronLeft size={16} strokeWidth={1.5} />
                </button>
                <button
                  className="icon-button"
                  type="button"
                  disabled={!hasNextPage}
                  onClick={() => changePage("next")}
                  aria-label="Следующая страница"
                >
                  <ChevronRight size={16} strokeWidth={1.5} />
                </button>
              </div>
            </div>
          )}
        </section>
      </main>
      {isDatasetReady && isFilterDrawerOpen && (
        <div
          className="drawer-backdrop"
          role="presentation"
          onMouseDown={() => setIsFilterDrawerOpen(false)}
        >
          <aside
            className="filter-drawer"
            role="dialog"
            aria-modal="true"
            aria-labelledby="filter-drawer-title"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <header className="drawer-header">
              <div>
                <p className="eyebrow">Filters</p>
                <h2 id="filter-drawer-title">Фильтры: {reportTitle(activeReport)}</h2>
              </div>
              <button
                className="icon-button"
                type="button"
                onClick={() => setIsFilterDrawerOpen(false)}
                aria-label="Закрыть фильтры"
              >
                <X size={16} strokeWidth={1.5} />
              </button>
            </header>

            <div className="drawer-body">
              {activeReport === "contacts" && (
                <div className="drawer-form">
                  <label className="field">
                    <span>Поиск</span>
                    <div className="input-shell">
                      <Search size={16} strokeWidth={1.5} />
                      <input
                        value={searchDraft}
                        onChange={(event) => setSearchDraft(event.target.value)}
                        placeholder="Название контакта"
                        type="search"
                      />
                    </div>
                  </label>

                  <label className="field">
                    <span>ID контакта</span>
                    <div className="input-shell">
                      <Search size={16} strokeWidth={1.5} />
                      <input
                        value={contactIdDraft}
                        onChange={(event) => updateContactIdFilter(event.target.value)}
                        placeholder="661"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        type="search"
                      />
                    </div>
                  </label>

                  <SelectField
                    label="Тип"
                    value={filters.contactType}
                    onChange={(value) => updateFilter("contactType", value)}
                    options={filterMetadata?.contact_types ?? []}
                    disabled={!filterMetadata}
                  />
                  <SelectField
                    label="Статус сделки"
                    value={filters.status}
                    onChange={(value) => updateFilter("status", value)}
                    options={filterMetadata?.statuses ?? []}
                    disabled={!filterMetadata}
                  />
                  <CategorySelectField value={filters.categoryId} onChange={(value) => updateFilter("categoryId", value)} categories={filterMetadata?.categories ?? []} disabled={!filterMetadata} />

                  <label className="field">
                    <span>Создана с</span>
                    <input
                      className="date-input"
                      value={dealCreatedDrafts.from}
                      onChange={(event) => updateDealCreatedDraft("from", event.target.value)}
                      min={dateOnly(filterMetadata?.min_created_at)}
                      max={dateOnly(filterMetadata?.max_created_at)}
                      type="date"
                    />
                  </label>

                  <label className="field">
                    <span>Создана по</span>
                    <input
                      className="date-input"
                      value={dealCreatedDrafts.to}
                      onChange={(event) => updateDealCreatedDraft("to", event.target.value)}
                      min={dateOnly(filterMetadata?.min_created_at)}
                      max={dateOnly(filterMetadata?.max_created_at)}
                      type="date"
                    />
                  </label>

                  <button
                    className="button button-secondary"
                    type="button"
                    disabled={
                      !areDealCreatedDraftsChanged ||
                      !areDealCreatedDraftsComplete ||
                      areDealCreatedDraftsInvalid
                    }
                    onClick={applyDealCreatedDrafts}
                  >
                    <Filter size={16} strokeWidth={1.5} />
                    Применить даты
                  </button>
                </div>
              )}

              {activeReport === "deals" && (
                <div className="drawer-form">
                  <label className="field">
                    <span>Клиент</span>
                    <div className="input-shell">
                      <Search size={16} strokeWidth={1.5} />
                      <input
                        value={dealClientSearchDraft}
                        onChange={(event) => updateDealClientSearch(event.target.value)}
                        placeholder="Название клиента"
                        type="search"
                      />
                    </div>
                  </label>

                  <label className="field">
                    <span>ID сделки</span>
                    <div className="input-shell">
                      <Search size={16} strokeWidth={1.5} />
                      <input
                        value={dealIdDraft}
                        onChange={(event) => updateDealIdFilter(event.target.value)}
                        placeholder="1024"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        type="search"
                      />
                    </div>
                  </label>

                  <SelectField
                    label="Статус сделки"
                    value={dealFilters.status}
                    onChange={(value) => updateDealFilter("status", value)}
                    options={filterMetadata?.statuses ?? []}
                    disabled={!filterMetadata}
                  />
                  <KevSelectField
                    value={dealFilters.kevHeld}
                    onChange={(value) => updateDealFilter("kevHeld", value)}
                  />
                  <CategorySelectField value={dealFilters.categoryId} onChange={(value) => updateDealFilter("categoryId", value)} categories={filterMetadata?.categories ?? []} disabled={!filterMetadata} />
                  <SelectField
                    label="Тип"
                    value={dealFilters.contactType}
                    onChange={(value) => updateDealFilter("contactType", value)}
                    options={filterMetadata?.contact_types ?? []}
                    disabled={!filterMetadata}
                  />

                  <label className="field">
                    <span>Создана с</span>
                    <input
                      className="date-input"
                      value={dealReportCreatedDrafts.from}
                      onChange={(event) => updateDealReportCreatedDraft("from", event.target.value)}
                      min={dateOnly(filterMetadata?.min_created_at)}
                      max={dateOnly(filterMetadata?.max_created_at)}
                      type="date"
                    />
                  </label>

                  <label className="field">
                    <span>Создана по</span>
                    <input
                      className="date-input"
                      value={dealReportCreatedDrafts.to}
                      onChange={(event) => updateDealReportCreatedDraft("to", event.target.value)}
                      min={dateOnly(filterMetadata?.min_created_at)}
                      max={dateOnly(filterMetadata?.max_created_at)}
                      type="date"
                    />
                  </label>

                  <button
                    className="button button-secondary"
                    type="button"
                    disabled={
                      !areDealReportCreatedDraftsChanged ||
                      !areDealReportCreatedDraftsComplete ||
                      areDealReportCreatedDraftsInvalid
                    }
                    onClick={applyDealReportCreatedDrafts}
                  >
                    <Filter size={16} strokeWidth={1.5} />
                    Применить даты
                  </button>
                </div>
              )}

              {activeReport === "abc" && (
                <div className="drawer-form">
                  <label className="field">
                    <span>Клиент</span>
                    <div className="input-shell">
                      <Search size={16} strokeWidth={1.5} />
                      <input
                        value={abcSearchDraft}
                        onChange={(event) => setAbcSearchDraft(event.target.value)}
                        placeholder="Название клиента"
                        type="search"
                      />
                    </div>
                  </label>

                  <label className="field">
                    <span>ID клиента</span>
                    <div className="input-shell">
                      <Search size={16} strokeWidth={1.5} />
                      <input
                        value={abcContactIdDraft}
                        onChange={(event) => updateAbcContactIdFilter(event.target.value)}
                        placeholder="661"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        type="search"
                      />
                    </div>
                  </label>

                  <SelectField
                    label="Тип"
                    value={abcFilters.contactType}
                    onChange={(value) => updateAbcFilter("contactType", value)}
                    options={filterMetadata?.contact_types ?? []}
                    disabled={!filterMetadata}
                  />
                  <SelectField
                    label="ABC"
                    value={abcFilters.segment}
                    onChange={(value) => updateAbcFilter("segment", value)}
                    options={ABC_SEGMENTS}
                  />
                  <SelectField
                    label="Приоритет"
                    value={abcFilters.migrationPriority}
                    onChange={(value) => updateAbcFilter("migrationPriority", value)}
                    options={MIGRATION_PRIORITIES}
                  />
                  <CategorySelectField value={abcFilters.categoryId} onChange={(value) => updateAbcFilter("categoryId", value)} categories={filterMetadata?.categories ?? []} disabled={!filterMetadata} />
                  <label className="field"><span>Сделка создана с</span><input className="date-input" type="date" value={abcDealCreatedDrafts.from} min={dateOnly(filterMetadata?.min_created_at)} max={dateOnly(filterMetadata?.max_created_at)} onChange={(event) => updateAbcDealCreatedDraft("from", event.target.value)} /></label>
                  <label className="field"><span>Сделка создана по</span><input className="date-input" type="date" value={abcDealCreatedDrafts.to} min={dateOnly(filterMetadata?.min_created_at)} max={dateOnly(filterMetadata?.max_created_at)} onChange={(event) => updateAbcDealCreatedDraft("to", event.target.value)} /></label>
                  <button className="button button-secondary" type="button" disabled={!areAbcDealCreatedDraftsChanged || !areAbcDealCreatedDraftsComplete || areAbcDealCreatedDraftsInvalid} onClick={applyAbcDealCreatedDrafts}>Применить даты создания</button>

                  <label className="field checkbox-field">
                    <span>Изменения</span>
                    <label className="check-shell">
                      <input
                        checked={isAbcCompareEnabled && abcFilters.changedOnly}
                        disabled={!isAbcCompareEnabled}
                        onChange={(event) => updateAbcFilter("changedOnly", event.target.checked)}
                        type="checkbox"
                      />
                      Только изменившие ABC
                    </label>
                  </label>

                  <label className="field">
                    <span>Было с</span>
                    <input
                      className="date-input"
                      value={abcDateDrafts.from}
                      onChange={(event) => updateAbcDateDraft("from", event.target.value)}
                      min={dateOnly(filterMetadata?.min_closed_at)}
                      max={dateOnly(filterMetadata?.max_closed_at)}
                      type="date"
                    />
                  </label>
                  <label className="field">
                    <span>Было по</span>
                    <input
                      className="date-input"
                      value={abcDateDrafts.to}
                      onChange={(event) => updateAbcDateDraft("to", event.target.value)}
                      min={dateOnly(filterMetadata?.min_closed_at)}
                      max={dateOnly(filterMetadata?.max_closed_at)}
                      type="date"
                    />
                  </label>
                  <button
                    className="button button-secondary"
                    type="button"
                    disabled={
                      !areAbcDateDraftsChanged ||
                      !areAbcDateDraftsComplete ||
                      areAbcDateDraftsInvalid
                    }
                    onClick={applyAbcDateDrafts}
                  >
                    <Filter size={16} strokeWidth={1.5} />
                    Применить было
                  </button>

                  <label className="field">
                    <span>Стало с</span>
                    <input
                      className="date-input"
                      value={abcCompareDateDrafts.from}
                      onChange={(event) => updateAbcCompareDateDraft("from", event.target.value)}
                      min={dateOnly(filterMetadata?.min_closed_at)}
                      max={dateOnly(filterMetadata?.max_closed_at)}
                      type="date"
                    />
                  </label>
                  <label className="field">
                    <span>Стало по</span>
                    <input
                      className="date-input"
                      value={abcCompareDateDrafts.to}
                      onChange={(event) => updateAbcCompareDateDraft("to", event.target.value)}
                      min={dateOnly(filterMetadata?.min_closed_at)}
                      max={dateOnly(filterMetadata?.max_closed_at)}
                      type="date"
                    />
                  </label>
                  <button
                    className="button button-secondary"
                    type="button"
                    disabled={
                      !areAbcCompareDraftsChanged ||
                      !areAbcCompareDraftsComplete ||
                      areAbcCompareDraftsInvalid ||
                      Boolean(abcCompareDateDrafts.from) !== Boolean(abcCompareDateDrafts.to)
                    }
                    onClick={applyAbcCompareDateDrafts}
                  >
                    <Filter size={16} strokeWidth={1.5} />
                    Применить стало
                  </button>
                </div>
              )}

              {activeReport === "kev" && (
                <div className="drawer-form">
                  <SelectField
                    label="Тип"
                    value={kevFilters.contactType}
                    onChange={(value) => updateKevFilter("contactType", value)}
                    options={filterMetadata?.contact_types ?? []}
                    disabled={!filterMetadata}
                  />
                  <CategorySelectField value={kevFilters.categoryId} onChange={(value) => updateKevFilter("categoryId", value)} categories={filterMetadata?.categories ?? []} disabled={!filterMetadata} />
                  <label className="field"><span>Сделка создана с</span><input className="date-input" type="date" value={kevDealCreatedDrafts.from} min={dateOnly(filterMetadata?.min_created_at)} max={dateOnly(filterMetadata?.max_created_at)} onChange={(event) => updateKevDealCreatedDraft("from", event.target.value)} /></label>
                  <label className="field"><span>Сделка создана по</span><input className="date-input" type="date" value={kevDealCreatedDrafts.to} min={dateOnly(filterMetadata?.min_created_at)} max={dateOnly(filterMetadata?.max_created_at)} onChange={(event) => updateKevDealCreatedDraft("to", event.target.value)} /></label>
                  <button className="button button-secondary" type="button" disabled={!areKevDealCreatedDraftsChanged || !areKevDealCreatedDraftsComplete || areKevDealCreatedDraftsInvalid} onClick={applyKevDealCreatedDrafts}>Применить даты создания</button>
                  <label className="field">
                    <span>Закрыта с</span>
                    <input
                      className="date-input"
                      value={kevDateDrafts.from}
                      onChange={(event) => updateKevDateDraft("from", event.target.value)}
                      min={dateOnly(filterMetadata?.min_closed_at)}
                      max={dateOnly(filterMetadata?.max_closed_at)}
                      type="date"
                    />
                  </label>
                  <label className="field">
                    <span>Закрыта по</span>
                    <input
                      className="date-input"
                      value={kevDateDrafts.to}
                      onChange={(event) => updateKevDateDraft("to", event.target.value)}
                      min={dateOnly(filterMetadata?.min_closed_at)}
                      max={dateOnly(filterMetadata?.max_closed_at)}
                      type="date"
                    />
                  </label>
                  <button
                    className="button button-secondary"
                    type="button"
                    disabled={
                      !areKevDateDraftsChanged ||
                      !areKevDateDraftsComplete ||
                      areKevDateDraftsInvalid
                    }
                    onClick={applyKevDateDrafts}
                  >
                    <Filter size={16} strokeWidth={1.5} />
                    Применить даты
                  </button>
                </div>
              )}
            </div>

            <footer className="drawer-footer">
              <button
                className="button button-secondary"
                type="button"
                onClick={
                  activeReport === "contacts"
                    ? resetFilters
                    : activeReport === "deals"
                      ? resetDealFilters
                      : activeReport === "abc"
                        ? resetAbcFilters
                        : resetKevFilters
                }
              >
                <Filter size={16} strokeWidth={1.5} />
                Сбросить фильтры
              </button>
              <button
                className="button button-primary"
                type="button"
                onClick={() => setIsFilterDrawerOpen(false)}
              >
                Готово
              </button>
            </footer>
          </aside>
        </div>
      )}
      {revenueChartContact && (
        <ContactRevenueModal
          contact={revenueChartContact}
          periodFrom={filters.dealCreatedFrom}
          periodTo={filters.dealCreatedTo}
          series={revenueSeriesQuery.data ?? null}
          isLoading={revenueSeriesQuery.isPending}
          errorMessage={revenueSeriesQuery.isError ? revenueSeriesQuery.error.message : null}
          onRetry={() => void revenueSeriesQuery.refetch()}
          onClose={() => setRevenueChartContact(null)}
        />
      )}
    </div>
  );
}

function AuthLoadingScreen() {
  return (
    <div className="auth-shell">
      <section className="auth-card" aria-live="polite">
        <div className="auth-mark">
          <LockKeyhole size={22} strokeWidth={1.5} />
        </div>
        <h1>Bitrix Sales</h1>
        <p>Проверка сессии...</p>
      </section>
    </div>
  );
}

function AuthMessageScreen({
  title,
  message,
  onRetry
}: {
  title: string;
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="auth-shell">
      <section className="auth-card" role="alert">
        <div className="auth-mark auth-mark-danger">
          <AlertCircle size={22} strokeWidth={1.5} />
        </div>
        <h1>{title}</h1>
        <p>{message}</p>
        <button className="button button-primary" type="button" onClick={onRetry}>
          <RefreshCcw size={16} strokeWidth={1.5} />
          Повторить
        </button>
      </section>
    </div>
  );
}

function LoginScreen({
  username,
  password,
  isSubmitting,
  errorMessage,
  onUsernameChange,
  onPasswordChange,
  onSubmit
}: {
  username: string;
  password: string;
  isSubmitting: boolean;
  errorMessage: string | null;
  onUsernameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <div className="auth-shell">
      <form className="auth-card" onSubmit={onSubmit}>
        <div className="auth-mark">
          <LockKeyhole size={22} strokeWidth={1.5} />
        </div>
        <h1>Bitrix Sales</h1>
        <p>Вход во внутреннюю аналитику</p>

        <label className="field">
          <span>Логин</span>
          <input
            className="auth-input"
            value={username}
            onChange={(event) => onUsernameChange(event.target.value)}
            autoComplete="username"
            autoFocus
            type="text"
          />
        </label>

        <label className="field">
          <span>Пароль</span>
          <input
            className="auth-input"
            value={password}
            onChange={(event) => onPasswordChange(event.target.value)}
            autoComplete="current-password"
            type="password"
          />
        </label>

        {errorMessage && (
          <p className="auth-error" role="alert">
            {errorMessage}
          </p>
        )}

        <button
          className="button button-primary"
          type="submit"
          disabled={isSubmitting || !username.trim() || !password}
        >
          <LockKeyhole size={16} strokeWidth={1.5} />
          {isSubmitting ? "Проверка..." : "Войти"}
        </button>
      </form>
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
  disabled
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
  disabled?: boolean;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} disabled={disabled}>
        <option value="">Все</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function CategorySelectField({ value, onChange, categories, disabled }: { value: string; onChange: (value: string) => void; categories: { category_id: number; category_name: string }[]; disabled?: boolean }) {
  return <label className="field"><span>Воронка</span><select value={value} onChange={(event) => onChange(event.target.value)} disabled={disabled}><option value="">Все воронки</option>{categories.map((category) => <option key={category.category_id} value={String(category.category_id)}>{category.category_name}</option>)}</select></label>;
}

function KevSelectField({
  value,
  onChange
}: {
  value: "" | "true" | "false";
  onChange: (value: "" | "true" | "false") => void;
}) {
  return (
    <label className="field">
      <span>КЭВ</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as "" | "true" | "false")}
      >
        <option value="">Все</option>
        <option value="true">Был</option>
        <option value="false">Не был</option>
      </select>
    </label>
  );
}

function DatasetBadge({
  isLoading,
  isError,
  state,
  count,
  finishedAt
}: {
  isLoading: boolean;
  isError: boolean;
  state?: string;
  count?: number;
  finishedAt?: string | null;
}) {
  if (isLoading) {
    return <span className="status-badge">Проверка dataset</span>;
  }

  if (isError) {
    return <span className="status-badge status-badge-error">Dataset недоступен</span>;
  }

  const label = state === "success" ? "Dataset активен" : "Dataset не готов";

  return (
    <span className={state === "success" ? "status-badge status-badge-success" : "status-badge"}>
      <Database size={16} strokeWidth={1.5} />
      <span>{label}</span>
      {count !== undefined && <strong>{count.toLocaleString("ru-RU")}</strong>}
      {finishedAt && <time dateTime={finishedAt}>{formatDateTime(finishedAt)}</time>}
    </span>
  );
}

function InlineAlert({
  title,
  message,
  onRetry
}: {
  title: string;
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="alert" role="alert">
      <AlertCircle size={18} strokeWidth={1.5} />
      <div>
        <strong>{title}</strong>
        <p>{message}</p>
      </div>
      <button className="button button-ghost" type="button" onClick={onRetry}>
        <RefreshCcw size={15} strokeWidth={1.5} />
        Повторить
      </button>
    </div>
  );
}

function InlineSuccess({ message }: { message: string }) {
  return (
    <div className="alert alert-success" role="status">
      <Database size={18} strokeWidth={1.5} />
      <div>
        <strong>Обновление завершено</strong>
        <p>{message}</p>
      </div>
    </div>
  );
}

function InlineValidation({ message }: { message: string }) {
  return (
    <div className="alert" role="alert">
      <AlertCircle size={18} strokeWidth={1.5} />
      <div>
        <strong>Проверьте диапазон дат</strong>
        <p>{message}</p>
      </div>
    </div>
  );
}

function TableError({
  entityLabel,
  message,
  onRetry
}: {
  entityLabel: string;
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="state-panel" role="alert">
      <AlertCircle size={24} strokeWidth={1.5} />
      <h3>Не удалось загрузить {entityLabel}</h3>
      <p>{message}</p>
      <button className="button button-primary" type="button" onClick={onRetry}>
        <RefreshCcw size={16} strokeWidth={1.5} />
        Повторить
      </button>
    </div>
  );
}

function EmptyState({ entityLabel, onReset }: { entityLabel: string; onReset: () => void }) {
  return (
    <div className="state-panel">
      <Search size={24} strokeWidth={1.5} />
      <h3>{entityLabel} не найдены</h3>
      <p>Измените поисковый запрос или сбросьте фильтры.</p>
      <button className="button button-secondary" type="button" onClick={onReset}>
        Сбросить фильтры
      </button>
    </div>
  );
}

function DatabaseNotReadyState({
  errorMessage,
  isRefreshing,
  onRefresh
}: {
  errorMessage: string | null;
  isRefreshing: boolean;
  onRefresh: () => void;
}) {
  return (
    <div className="state-panel state-panel-wide">
      <Database size={26} strokeWidth={1.5} />
      <h3>Локальная база не подготовлена.</h3>
      <p>Нажмите «Обновить из Bitrix», чтобы загрузить данные.</p>
      <p>Ручное read-only обновление может занять несколько минут.</p>
      {errorMessage && (
        <p className="state-error" role="alert">
          {errorMessage}
        </p>
      )}
      <button
        className="button button-primary"
        type="button"
        disabled={isRefreshing}
        onClick={onRefresh}
      >
        <RefreshCcw size={16} strokeWidth={1.5} />
        {isRefreshing ? "Загрузка данных из Bitrix..." : "Обновить из Bitrix"}
      </button>
      {isRefreshing && <p className="state-note">Это может занять несколько минут.</p>}
    </div>
  );
}

function RefreshProgressState() {
  return (
    <div className="state-panel state-panel-wide" role="status" aria-live="polite">
      <RefreshCcw className="spin-icon" size={26} strokeWidth={1.5} />
      <h3>Загрузка данных из Bitrix...</h3>
      <p>Это может занять несколько минут.</p>
    </div>
  );
}

function ContactsSkeleton() {
  return (
    <div className="skeleton-table" aria-label="Загрузка контактов">
      {Array.from({ length: 8 }).map((_, index) => (
        <div className="skeleton-row" key={index}>
          <span />
          <span />
          <span />
          <span />
        </div>
      ))}
    </div>
  );
}

type SortField = ContactSort | DealSort | AbcSort;

function ContactsTable({
  contacts,
  page,
  sort,
  order,
  onSort,
  onOpenDeals,
  onOpenRevenueChart
}: {
  contacts: ContactAnalytics[];
  page?: ContactAnalyticsPage;
  sort: ContactSort;
  order: "asc" | "desc";
  onSort: (sort: ContactSort) => void;
  onOpenDeals: (contact: ContactAnalytics, status?: string) => void;
  onOpenRevenueChart: (contact: ContactAnalytics) => void;
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <SortableHeader label="ID" field="contact_id" sort={sort} order={order} onSort={onSort} />
            <SortableHeader
              label="Контакт"
              field="contact_name"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              label="Тип"
              field="contact_type_normalized"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              label="Всего сделок"
              field="total_deals_count"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Успешные"
              field="won_deals_count"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Открытые"
              field="open_deals_count"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Проигранные"
              field="lost_deals_count"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Бюджет"
              field="budget_usd"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Бюджет в работе"
              field="budget_in_work_usd"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Бюджет проигранных"
              field="lost_budget_usd"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Выручка"
              field="revenue_usd"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Прибыль"
              field="estimated_profit_usd"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader label="Средний чек" field="average_check_usd" sort={sort} order={order} onSort={onSort} />
            <SortableHeader label="Средний цикл, дн." field="average_cycle_days" sort={sort} order={order} onSort={onSort} />
            <SortableHeader
              label="Дата закрытия"
              field="last_won_date"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              label="Последняя сделка"
              field="latest_deal_date"
              sort={sort}
              order={order}
              onSort={onSort}
            />
          </tr>
        </thead>
        <tbody>
          {contacts.map((contact) => (
            <tr key={contact.contact_id}>
              <td>
                <div className="id-cell">
                  <span>{contact.contact_id}</span>
                  <a
                    href={`https://dialar.bitrix24.by/crm/contact/details/${contact.contact_id}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Посмотреть
                  </a>
                </div>
              </td>
              <td>
                <div className="contact-cell">
                  <button
                    className="contact-name-button"
                    type="button"
                    onClick={() => onOpenRevenueChart(contact)}
                    aria-label={`Показать график выручки клиента ${contact.contact_name}`}
                  >
                    {contact.contact_name}
                  </button>
                </div>
              </td>
              <td>
                <span className="badge badge-neutral">{contact.contact_type_normalized}</span>
              </td>
              <td className="number-cell">
                <DealCountButton
                  count={contact.total_deals_count}
                  label={`Открыть все сделки клиента ${contact.contact_name}`}
                  onClick={() => onOpenDeals(contact)}
                />
              </td>
              <td className="number-cell">
                <DealCountButton
                  count={contact.won_deals_count}
                  label={`Открыть успешные сделки клиента ${contact.contact_name}`}
                  onClick={() => onOpenDeals(contact, "won")}
                />
              </td>
              <td className="number-cell">
                <DealCountButton
                  count={contact.open_deals_count}
                  label={`Открыть открытые сделки клиента ${contact.contact_name}`}
                  onClick={() => onOpenDeals(contact, "open")}
                />
              </td>
              <td className="number-cell">
                <DealCountButton
                  count={contact.lost_deals_count}
                  label={`Открыть проигранные сделки клиента ${contact.contact_name}`}
                  onClick={() => onOpenDeals(contact, "lost")}
                />
              </td>
              <td className="number-cell money-cell">{formatUsd(contact.budget_usd)}</td>
              <td className="number-cell money-cell">{formatUsd(contact.budget_in_work_usd)}</td>
              <td className="number-cell money-cell">{formatUsd(contact.lost_budget_usd)}</td>
              <td className="number-cell money-cell">{formatUsd(contact.revenue_usd)}</td>
              <td className="number-cell money-cell">
                {formatUsd(contact.estimated_profit_usd)}
              </td>
              <td className="number-cell money-cell">{contact.average_check_usd ? formatUsd(contact.average_check_usd) : "—"}</td>
              <td className="number-cell">{contact.average_cycle_days ?? "—"}</td>
              <td>{formatDate(contact.last_won_date)}</td>
              <td>{formatDate(contact.latest_deal_date)}</td>
            </tr>
          ))}
        </tbody>
        {page && <tfoot><tr><th colSpan={3}>Итого по выборке</th><th>{page.filtered_total_deals_count}</th><th>{page.filtered_won_deals_count}</th><th>{page.filtered_open_deals_count}</th><th>{page.filtered_lost_deals_count}</th><th>{formatUsd(page.filtered_budget_usd)}</th><th>{formatUsd(page.filtered_budget_in_work_usd)}</th><th>{formatUsd(page.filtered_lost_budget_usd)}</th><th>{formatUsd(page.filtered_revenue_usd)}</th><th>{formatUsd(page.filtered_estimated_profit_usd)}</th><th>{page.filtered_average_check_usd ? formatUsd(page.filtered_average_check_usd) : "—"}</th><th>{page.filtered_average_cycle_days ?? "—"}</th><th>—</th><th>—</th></tr></tfoot>}
      </table>
    </div>
  );
}

function DealsTable({
  deals,
  page,
  sort,
  order,
  onSort
}: {
  deals: DealAnalytics[];
  page?: DealAnalyticsPage;
  sort: DealSort;
  order: "asc" | "desc";
  onSort: (sort: DealSort) => void;
}) {
  return (
    <div className="table-scroll">
      <table className="deals-table">
        <thead>
          <tr>
            <SortableHeader label="ID" field="deal_id" sort={sort} order={order} onSort={onSort} />
            <SortableHeader
              label="Название сделки"
              field="deal_name"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              label="Статус сделки"
              field="status_group"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <th>КЭВ</th>
            <th>Воронка</th>
            <th>Цикл, дн.</th>
            <SortableHeader
              label="Тип"
              field="contact_type_normalized"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              label="Бюджет"
              field="budget_usd"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Прибыль"
              field="estimated_profit_usd"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Дата создания"
              field="created_date"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              label="Дата закрытия"
              field="closed_date"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <th>Средний чек</th>
          </tr>
        </thead>
        <tbody>
          {deals.map((deal) => (
            <tr key={deal.deal_id}>
              <td>
                <div className="id-cell">
                  <span>{deal.deal_id}</span>
                  <a
                    href={`https://dialar.bitrix24.by/crm/deal/details/${deal.deal_id}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Посмотреть
                  </a>
                </div>
              </td>
              <td>
                <div className="contact-cell deal-name-cell">
                  <span>{deal.deal_name}</span>
                </div>
              </td>
              <td>
                <span className={`badge ${statusBadgeClass(deal.status_group)}`}>
                  {formatDealStatus(deal.status_group)}
                </span>
              </td>
              <td>{deal.category_name ?? "—"}</td>
              <td className="number-cell">{deal.cycle_days ?? "—"}</td>
              <td>
                <span className={`badge ${deal.kev_held ? "badge-success" : "badge-neutral"}`}>
                  {deal.kev_held ? "Был" : "Не был"}
                </span>
              </td>
              <td>
                <span className="badge badge-neutral">{deal.contact_type_normalized}</span>
              </td>
              <td className="number-cell money-cell">{formatUsd(deal.budget_usd)}</td>
              <td className="number-cell money-cell">{formatUsd(deal.estimated_profit_usd)}</td>
              <td>{formatDate(deal.created_date)}</td>
              <td>{formatDate(deal.closed_date)}</td>
              <td className="number-cell">—</td>
            </tr>
          ))}
        </tbody>
        {page && <tfoot><tr><th colSpan={3}>Итого по выборке</th><th>—</th><th>—</th><th>{page.filtered_average_cycle_days ?? "—"}</th><th>—</th><th>{formatUsd(page.filtered_budget_usd)}</th><th>{formatUsd(page.filtered_estimated_profit_usd)}</th><th>—</th><th>—</th><th>{page.filtered_average_check_usd ? formatUsd(page.filtered_average_check_usd) : "—"}</th></tr></tfoot>}
      </table>
    </div>
  );
}

function KevConversionComparison({ report }: { report: KevConversionReport }) {
  const rows = [
    { label: "КЭВ был", value: report.with_kev, accent: true },
    { label: "КЭВ не был", value: report.without_kev, accent: false }
  ];
  return (
    <div className="kev-report">
      <div className="kev-difference" aria-label="Разница конверсии">
        <span>Разница конверсии</span>
        <strong>{formatPercentagePoints(report.conversion_difference_percentage_points)}</strong>
        <small>КЭВ был минус КЭВ не был</small>
      </div>
      <div className="table-scroll kev-table-scroll">
        <table className="kev-table">
          <thead>
            <tr>
              <th>Группа</th>
              <th className="number-cell">Закрытые</th>
              <th className="number-cell">Успешные</th>
              <th className="number-cell">Проигранные</th>
              <th className="number-cell">Конверсия</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <td>
                  <span className={`badge ${row.accent ? "badge-success" : "badge-neutral"}`}>
                    {row.label}
                  </span>
                </td>
                <td className="number-cell">{row.value.closed_deals_count.toLocaleString("ru-RU")}</td>
                <td className="number-cell">{row.value.won_deals_count.toLocaleString("ru-RU")}</td>
                <td className="number-cell">{row.value.lost_deals_count.toLocaleString("ru-RU")}</td>
                <td className="number-cell money-cell">
                  {formatNullablePercent(row.value.conversion_percent)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {(report.with_kev.conversion_percent === null ||
        report.without_kev.conversion_percent === null) && (
        <p className="kev-note">Для группы без закрытых сделок конверсия и разница показаны как «—».</p>
      )}
    </div>
  );
}

function KevNoDataState({ onReset }: { onReset: () => void }) {
  return (
    <div className="state-panel">
      <Handshake size={28} strokeWidth={1.5} />
      <h3>Нет закрытых сделок</h3>
      <p>В выбранных фильтрах нет выигранных или проигранных сделок с датой закрытия.</p>
      <button className="button button-secondary" type="button" onClick={onReset}>
        <Filter size={16} strokeWidth={1.5} />
        Сбросить фильтры
      </button>
    </div>
  );
}

function AbcTable({
  rows,
  sort,
  order,
  isCompareEnabled,
  onSort
}: {
  rows: AbcAnalytics[];
  sort: AbcSort;
  order: "asc" | "desc";
  isCompareEnabled: boolean;
  onSort: (sort: AbcSort) => void;
}) {
  return (
    <div className="table-scroll">
      <table className={isCompareEnabled ? "abc-table abc-table-compare" : "abc-table"}>
        <thead>
          <tr>
            <SortableHeader label="ID" field="contact_id" sort={sort} order={order} onSort={onSort} />
            <SortableHeader
              label="Клиент"
              field="contact_name"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              label="Тип"
              field="contact_type_normalized"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              label="Выручка было"
              field="base_revenue_usd"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Доля"
              field="base_revenue_share_percent"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Накопленная доля"
              field="base_cumulative_share_percent"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="ABC было"
              field="base_segment"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            <SortableHeader
              label="Успешные сделки"
              field="base_won_deals_count"
              sort={sort}
              order={order}
              onSort={onSort}
              align="right"
            />
            <SortableHeader
              label="Последняя успешная сделка"
              field="base_last_won_date"
              sort={sort}
              order={order}
              onSort={onSort}
            />
            {isCompareEnabled && (
              <>
                <SortableHeader
                  label="Выручка стало"
                  field="target_revenue_usd"
                  sort={sort}
                  order={order}
                  onSort={onSort}
                  align="right"
                />
                <SortableHeader
                  label="ABC стало"
                  field="target_segment"
                  sort={sort}
                  order={order}
                  onSort={onSort}
                />
                <SortableHeader
                  label="Переход"
                  field="segment_change"
                  sort={sort}
                  order={order}
                  onSort={onSort}
                />
                <SortableHeader
                  label="Приоритет"
                  field="migration_priority"
                  sort={sort}
                  order={order}
                  onSort={onSort}
                />
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr className={row.segment_changed ? "abc-row-changed" : undefined} key={row.contact_id}>
              <td>
                <div className="id-cell">
                  <span>{row.contact_id}</span>
                  <a
                    href={`https://dialar.bitrix24.by/crm/contact/details/${row.contact_id}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Посмотреть
                  </a>
                </div>
              </td>
              <td>
                <div className="contact-cell">
                  <span>{row.contact_name}</span>
                  {row.segment_changed && <small>Сегмент изменился</small>}
                </div>
              </td>
              <td>
                <span className="badge badge-neutral">{row.contact_type_normalized}</span>
              </td>
              <td className="number-cell money-cell">{formatUsd(row.base_revenue_usd)}</td>
              <td className="number-cell">{formatPercent(row.base_revenue_share_percent)}</td>
              <td className="number-cell">
                {formatPercent(row.base_cumulative_share_percent)}
              </td>
              <td>
                <span className={`badge ${abcSegmentBadgeClass(row.base_segment)}`}>
                  {row.base_segment}
                </span>
              </td>
              <td className="number-cell">{row.base_won_deals_count}</td>
              <td>{formatDate(row.base_last_won_date)}</td>
              {isCompareEnabled && (
                <>
                  <td className="number-cell money-cell">{formatUsd(row.target_revenue_usd)}</td>
                  <td>
                    <span className={`badge ${abcSegmentBadgeClass(row.target_segment)}`}>
                      {row.target_segment}
                    </span>
                  </td>
                  <td>
                    <span className={row.segment_changed ? "badge badge-warning" : "badge badge-neutral"}>
                      {row.segment_change}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${priorityBadgeClass(row.migration_priority)}`}>
                      {row.migration_priority}
                    </span>
                  </td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

type RevenueChartPoint = {
  closedDate: string;
  revenueUsd: number;
  wonDealsCount: number;
};

function ContactRevenueModal({
  contact,
  periodFrom,
  periodTo,
  series,
  isLoading,
  errorMessage,
  onRetry,
  onClose
}: {
  contact: ContactAnalytics;
  periodFrom: string;
  periodTo: string;
  series: ContactWonRevenueSeries | null;
  isLoading: boolean;
  errorMessage: string | null;
  onRetry: () => void;
  onClose: () => void;
}) {
  const chartData: RevenueChartPoint[] =
    series?.points.map((point) => ({
      closedDate: point.closed_date,
      revenueUsd: Number(point.revenue_usd),
      wonDealsCount: point.won_deals_count
    })) ?? [];
  const periodLabel = formatChartPeriod(periodFrom, periodTo);

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="contact-revenue-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-header">
          <div>
            <p className="eyebrow">Won revenue</p>
            <h2 id="contact-revenue-title">{contact.contact_name}</h2>
            <p className="modal-subtitle">
              ID {contact.contact_id} · закрытые успешные сделки · период: {periodLabel}
            </p>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="Закрыть">
            <X size={16} strokeWidth={1.5} />
          </button>
        </header>

        {isLoading ? (
          <div className="modal-state">
            <RefreshCcw className="spin-icon" size={22} strokeWidth={1.5} />
            <p>Загружаем выручку клиента...</p>
          </div>
        ) : errorMessage ? (
          <div className="modal-state">
            <AlertCircle size={24} strokeWidth={1.5} />
            <h3>Не удалось загрузить график</h3>
            <p>{errorMessage}</p>
            <button className="button button-secondary" type="button" onClick={onRetry}>
              Повторить
            </button>
          </div>
        ) : !series || chartData.length === 0 ? (
          <div className="modal-state">
            <BarChart3 size={24} strokeWidth={1.5} />
            <h3>Нет закрытых успешных сделок</h3>
            <p>В выбранном периоде у клиента нет won revenue по датам закрытия.</p>
          </div>
        ) : (
          <>
            <div className="chart-summary">
              <div>
                <span>Выручка</span>
                <strong>{formatUsd(series.total_revenue_usd)}</strong>
              </div>
              <div>
                <span>Успешные сделки</span>
                <strong>{series.won_deals_count.toLocaleString("ru-RU")}</strong>
              </div>
            </div>
            <div className="revenue-chart" aria-label="График won revenue по датам закрытия">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 16, left: 8, bottom: 8 }}>
                  <CartesianGrid stroke="#e5e7eb" strokeDasharray="4 4" />
                  <XAxis dataKey="closedDate" tickFormatter={formatShortDateTick} minTickGap={20} />
                  <YAxis
                    tickFormatter={formatCompactUsd}
                    width={76}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    labelFormatter={(label: unknown) =>
                      typeof label === "string" ? formatDate(label) : ""
                    }
                    formatter={(value: unknown, name: unknown) => {
                      if (name === "revenueUsd") {
                        return [formatUsd(String(value)), "Выручка"];
                      }
                      return [String(value), String(name)];
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="revenueUsd"
                    name="Выручка"
                    stroke="#2563eb"
                    strokeWidth={2.5}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function DealCountButton({
  count,
  label,
  onClick
}: {
  count: number;
  label: string;
  onClick: () => void;
}) {
  if (count <= 0) {
    return <span className="count-value count-value-muted">{count}</span>;
  }

  return (
    <button className="count-link" type="button" onClick={onClick} aria-label={label}>
      {count}
    </button>
  );
}

function DealTotalsBar({ page }: { page: DealAnalyticsPage }) {
  return (
    <div className="totals-bar">
      <div>
        <span>Бюджет</span>
        <strong>{formatUsd(page.filtered_budget_usd)}</strong>
      </div>
      <div>
        <span>Выручка</span>
        <strong>{formatUsd(page.filtered_revenue_usd)}</strong>
      </div>
      <div>
        <span>Прибыль</span>
        <strong>{formatUsd(page.filtered_estimated_profit_usd)}</strong>
      </div>
    </div>
  );
}

function AbcSummaryBar({
  page,
  isCompareEnabled
}: {
  page: AbcAnalyticsPage;
  isCompareEnabled: boolean;
}) {
  const changedCount = page.migration_priority_counts["без изменений"] === undefined
    ? page.total
    : page.total - page.migration_priority_counts["без изменений"];

  return (
    <div className="totals-bar abc-summary-bar">
      <div>
        <span>Выручка было</span>
        <strong>{formatUsd(page.base_total_revenue_usd)}</strong>
      </div>
      {isCompareEnabled && (
        <div>
          <span>Выручка стало</span>
          <strong>{formatUsd(page.target_total_revenue_usd)}</strong>
        </div>
      )}
      <div>
        <span>ABC было</span>
        <strong>{formatCounts(page.base_segment_counts)}</strong>
      </div>
      {isCompareEnabled && (
        <div>
          <span>Изменений</span>
          <strong>{changedCount.toLocaleString("ru-RU")}</strong>
        </div>
      )}
    </div>
  );
}

function SortableHeader<TSort extends SortField>({
  label,
  field,
  sort,
  order,
  onSort,
  align = "left"
}: {
  label: string;
  field: TSort;
  sort: TSort;
  order: "asc" | "desc";
  onSort: (sort: TSort) => void;
  align?: "left" | "right";
}) {
  const active = sort === field;
  const indicator = active ? (order === "asc" ? "↑" : "↓") : "↕";

  return (
    <th className={align === "right" ? "number-cell" : undefined} aria-sort={active ? (order === "asc" ? "ascending" : "descending") : "none"}>
      <button className="sort-button" type="button" onClick={() => onSort(field)}>
        <span>{label}</span>
        <span aria-hidden="true">{indicator}</span>
      </button>
    </th>
  );
}

function formatDealStatus(status: string) {
  if (status === "won") {
    return "Успешная";
  }
  if (status === "open") {
    return "Открытая";
  }
  if (status === "lost") {
    return "Проигранная";
  }
  return status;
}

function statusBadgeClass(status: string) {
  if (status === "won") {
    return "badge-success";
  }
  if (status === "lost") {
    return "badge-danger";
  }
  return "badge-neutral";
}

function abcSegmentBadgeClass(segment: string) {
  if (segment === "A") {
    return "badge-success";
  }
  if (segment === "B") {
    return "badge-primary";
  }
  if (segment === "C") {
    return "badge-warning";
  }
  return "badge-neutral";
}

function priorityBadgeClass(priority: string) {
  if (priority === "срочно") {
    return "badge-danger";
  }
  if (priority === "важно") {
    return "badge-warning";
  }
  if (priority === "развивать" || priority === "закрепить") {
    return "badge-success";
  }
  return "badge-neutral";
}

function reportTitle(report: ReportView) {
  if (report === "contacts") {
    return "Contacts";
  }
  if (report === "deals") {
    return "Deals";
  }
  return report === "abc" ? "ABC" : "КЭВ";
}

function reportSubtitle(report: ReportView) {
  if (report === "contacts") {
    return "Таблица контактов с поиском и фильтрами по локальным данным.";
  }
  if (report === "deals") {
    return "Таблица сделок с фильтрами по локальным данным.";
  }
  return report === "abc"
    ? "ABC-анализ клиентов по won-only USD выручке из локальной базы."
    : "Сравнение конверсии закрытых сделок с КЭВ и без КЭВ.";
}

function tableTitle(report: ReportView) {
  if (report === "contacts") {
    return "Список контактов";
  }
  if (report === "deals") {
    return "Список сделок";
  }
  return report === "abc" ? "ABC клиентов" : "Конверсия по КЭВ";
}

function entityLabel(report: ReportView) {
  if (report === "contacts") {
    return "контакты";
  }
  if (report === "deals") {
    return "сделки";
  }
  return report === "abc" ? "ABC" : "отчёт КЭВ";
}

function rangeValidationMessage(report: ReportView, isCompareIncomplete: boolean) {
  if (report === "abc" && isCompareIncomplete) {
    return "Для периода «Стало» заполните обе даты или очистите обе даты.";
  }
  if (report === "abc") {
    return "Дата начала периода должна быть не позже даты окончания периода.";
  }
  if (report === "kev") {
    return "Дата «Закрыта с» должна быть не позже даты «Закрыта по».";
  }
  return "Дата «Создана с» должна быть не позже даты «Создана по».";
}

function draftRangeValidationMessage(report: ReportView) {
  if (report === "abc") {
    return "В черновике дат «Было» или «Стало» начало должно быть не позже окончания.";
  }
  if (report === "kev") {
    return "В черновике дат значение «Закрыта с» должно быть не позже «Закрыта по».";
  }
  return "В черновике дат значение «Создана с» должно быть не позже «Создана по».";
}

function formatUsd(value: string) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return value;
  }

  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(numeric);
}

function formatCompactUsd(value: number) {
  if (!Number.isFinite(value)) {
    return "";
  }
  return new Intl.NumberFormat("ru-RU", {
    notation: "compact",
    maximumFractionDigits: 1
  }).format(value);
}

function formatShortDateTick(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit"
  }).format(new Date(value));
}

function formatChartPeriod(dateFrom: string, dateTo: string) {
  if (dateFrom && dateTo) {
    return `${formatDate(dateFrom)} - ${formatDate(dateTo)}`;
  }
  if (dateFrom) {
    return `с ${formatDate(dateFrom)}`;
  }
  if (dateTo) {
    return `по ${formatDate(dateTo)}`;
  }
  return "все даты закрытия";
}

function formatPercent(value: string) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return value;
  }
  return `${new Intl.NumberFormat("ru-RU", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(numeric)}%`;
}

function formatNullablePercent(value: string | null) {
  return value === null ? "—" : formatPercent(value);
}

function formatPercentagePoints(value: string | null) {
  if (value === null) {
    return "—";
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return `${value} п.п.`;
  }
  const formatted = new Intl.NumberFormat("ru-RU", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
    signDisplay: "exceptZero"
  }).format(numeric);
  return `${formatted} п.п.`;
}

function kevReportSubtitle(report: KevConversionReport | undefined) {
  if (!report) {
    return "Сравнение закрытых сделок";
  }
  const total = report.with_kev.closed_deals_count + report.without_kev.closed_deals_count;
  return `${total.toLocaleString("ru-RU")} закрытых сделок в сравнении`;
}

function formatCounts(counts: Record<string, number>) {
  const labels = ["A", "B", "C", "Нет продаж"];
  return labels
    .filter((label) => counts[label])
    .map((label) => `${label}: ${counts[label].toLocaleString("ru-RU")}`)
    .join(" / ") || "—";
}

function formatDate(value: string | null) {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit"
  }).format(new Date(value));
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function formatRefreshSuccess(result: LocalDataRefreshResponse) {
  const status = result.status;
  const contacts = status.normalized_contacts_count.toLocaleString("ru-RU");
  const deals = status.normalized_deals_count.toLocaleString("ru-RU");
  const rates = result.currency_rate_rows_loaded.toLocaleString("ru-RU");
  return `Обновление завершено: ${contacts} контактов, ${deals} сделок, ${rates} курсов загружено.`;
}

function loadStoredFilters(): ContactFilters {
  try {
    const stored = window.localStorage.getItem(CONTACTS_STORAGE_KEY);
    if (!stored) {
      return initialFilters;
    }
    const parsed = JSON.parse(stored) as Partial<Record<keyof ContactFilters, unknown>>;
    return {
      search: stringValue(parsed.search),
      contactId: stringValue(parsed.contactId).replace(/\D/g, ""),
      contactType: stringValue(parsed.contactType),
      status: stringValue(parsed.status),
      dealCreatedFrom: dateValue(parsed.dealCreatedFrom),
      dealCreatedTo: dateValue(parsed.dealCreatedTo),
      categoryId: stringValue(parsed.categoryId).replace(/\D/g, ""),
      sort: sortValue(parsed.sort),
      order: parsed.order === "desc" ? "desc" : "asc",
      limit: positiveNumberValue(parsed.limit, PAGE_SIZE),
      offset: nonNegativeNumberValue(parsed.offset)
    };
  } catch {
    return initialFilters;
  }
}

function loadStoredDealFilters(): DealFilters {
  try {
    const stored = window.localStorage.getItem(DEALS_STORAGE_KEY);
    if (!stored) {
      return initialDealFilters;
    }
    const parsed = JSON.parse(stored) as Partial<Record<keyof DealFilters, unknown>>;
    return {
      dealId: stringValue(parsed.dealId).replace(/\D/g, ""),
      clientId: stringValue(parsed.clientId).replace(/\D/g, ""),
      clientSearch: stringValue(parsed.clientSearch),
      contactType: stringValue(parsed.contactType),
      status: stringValue(parsed.status),
      kevHeld: ["true", "false"].includes(stringValue(parsed.kevHeld))
        ? (stringValue(parsed.kevHeld) as "true" | "false")
        : "",
      dealCreatedFrom: dateValue(parsed.dealCreatedFrom),
      dealCreatedTo: dateValue(parsed.dealCreatedTo),
      categoryId: stringValue(parsed.categoryId).replace(/\D/g, ""),
      sort: dealSortValue(parsed.sort),
      order: parsed.order === "desc" ? "desc" : "asc",
      limit: positiveNumberValue(parsed.limit, PAGE_SIZE),
      offset: nonNegativeNumberValue(parsed.offset)
    };
  } catch {
    return initialDealFilters;
  }
}

function loadStoredAbcFilters(): AbcFilters {
  try {
    const stored = window.localStorage.getItem(ABC_STORAGE_KEY);
    if (!stored) {
      return initialAbcFilters;
    }
    const parsed = JSON.parse(stored) as Partial<Record<keyof AbcFilters, unknown>>;
    return {
      search: stringValue(parsed.search),
      contactId: stringValue(parsed.contactId).replace(/\D/g, ""),
      contactType: stringValue(parsed.contactType),
      segment: ABC_SEGMENTS.includes(stringValue(parsed.segment))
        ? stringValue(parsed.segment)
        : "",
      migrationPriority: MIGRATION_PRIORITIES.includes(stringValue(parsed.migrationPriority))
        ? stringValue(parsed.migrationPriority)
        : "",
      changedOnly: parsed.changedOnly === true,
      dateFrom: dateValue(parsed.dateFrom),
      dateTo: dateValue(parsed.dateTo),
      compareDateFrom: dateValue(parsed.compareDateFrom),
      compareDateTo: dateValue(parsed.compareDateTo),
      dealCreatedFrom: dateValue(parsed.dealCreatedFrom),
      dealCreatedTo: dateValue(parsed.dealCreatedTo),
      categoryId: stringValue(parsed.categoryId).replace(/\D/g, ""),
      sort: abcSortValue(parsed.sort),
      order: parsed.order === "asc" ? "asc" : "desc",
      limit: positiveNumberValue(parsed.limit, PAGE_SIZE),
      offset: nonNegativeNumberValue(parsed.offset)
    };
  } catch {
    return initialAbcFilters;
  }
}

function loadStoredKevFilters(): KevFilters {
  try {
    const stored = window.localStorage.getItem(KEV_STORAGE_KEY);
    if (!stored) {
      return initialKevFilters;
    }
    const parsed = JSON.parse(stored) as Partial<Record<keyof KevFilters, unknown>>;
    return {
      dateFrom: dateValue(parsed.dateFrom),
      dateTo: dateValue(parsed.dateTo),
      contactType: stringValue(parsed.contactType)
      ,dealCreatedFrom: dateValue(parsed.dealCreatedFrom),
      dealCreatedTo: dateValue(parsed.dealCreatedTo),
      categoryId: stringValue(parsed.categoryId).replace(/\D/g, "")
    };
  } catch {
    return initialKevFilters;
  }
}

function loadStoredFilterMetadata(): FilterMetadata | null {
  try {
    const stored = window.localStorage.getItem(FILTER_METADATA_STORAGE_KEY);
    if (!stored) {
      return null;
    }
    const parsed = JSON.parse(stored) as Partial<Record<keyof FilterMetadata, unknown>>;
    return {
      contact_types: stringArrayValue(parsed.contact_types),
      regions: stringArrayValue(parsed.regions),
      statuses: stringArrayValue(parsed.statuses),
      min_created_at: nullableStringValue(parsed.min_created_at),
      max_created_at: nullableStringValue(parsed.max_created_at),
      min_closed_at: nullableStringValue(parsed.min_closed_at),
      max_closed_at: nullableStringValue(parsed.max_closed_at),
      categories: validCategoryOptions(parsed.categories)
    };
  } catch {
    return null;
  }
}

function validCategoryOptions(value: unknown): { category_id: number; category_name: string }[] {
  if (!Array.isArray(value)) return [];
  const categories = value.map((item) => {
    if (!item || typeof item !== "object") return null;
    const category = item as { category_id?: unknown; category_name?: unknown };
    if (!Number.isInteger(category.category_id) || (category.category_id as number) < 0 || typeof category.category_name !== "string") return null;
    const category_name = category.category_name.trim();
    return category_name ? { category_id: category.category_id as number, category_name } : null;
  });
  return categories.every(Boolean) ? categories as { category_id: number; category_name: string }[] : [];
}

function storeFilters(filters: ContactFilters) {
  if (areDefaultFilters(filters)) {
    window.localStorage.removeItem(CONTACTS_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(CONTACTS_STORAGE_KEY, JSON.stringify(filters));
}

function storeDealFilters(filters: DealFilters) {
  if (areDefaultDealFilters(filters)) {
    window.localStorage.removeItem(DEALS_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(DEALS_STORAGE_KEY, JSON.stringify(filters));
}

function storeAbcFilters(filters: AbcFilters) {
  if (areDefaultAbcFilters(filters)) {
    window.localStorage.removeItem(ABC_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(ABC_STORAGE_KEY, JSON.stringify(filters));
}

function storeKevFilters(filters: KevFilters) {
  if (JSON.stringify(filters) === JSON.stringify(initialKevFilters)) {
    window.localStorage.removeItem(KEV_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(KEV_STORAGE_KEY, JSON.stringify(filters));
}

function storeFilterMetadata(metadata: FilterMetadata) {
  window.localStorage.setItem(FILTER_METADATA_STORAGE_KEY, JSON.stringify(metadata));
}

function areDefaultFilters(filters: ContactFilters) {
  return JSON.stringify(filters) === JSON.stringify(initialFilters);
}

function areDefaultDealFilters(filters: DealFilters) {
  return JSON.stringify(filters) === JSON.stringify(initialDealFilters);
}

function areDefaultAbcFilters(filters: AbcFilters) {
  return JSON.stringify(filters) === JSON.stringify(initialAbcFilters);
}

function stringValue(value: unknown) {
  return typeof value === "string" ? value : "";
}

function nullableStringValue(value: unknown) {
  return typeof value === "string" ? value : null;
}

function stringArrayValue(value: unknown) {
  if (!Array.isArray(value)) {
    return [];
  }
  return Array.from(
    new Set(value.filter((item): item is string => typeof item === "string" && item.trim() !== ""))
  );
}

function dateValue(value: unknown) {
  const string = stringValue(value);
  return /^\d{4}-\d{2}-\d{2}$/.test(string) ? string : "";
}

function isFilterMetadataValidForDataset(
  metadata: FilterMetadata | null | undefined,
  normalizedContactsCount: number | undefined
) {
  if (!metadata) {
    return false;
  }
  if (!isStringArray(metadata.contact_types) || !isStringArray(metadata.regions) || !isStringArray(metadata.statuses)) {
    return false;
  }
  if ((normalizedContactsCount ?? 0) > 0 && metadata.contact_types.length === 0) {
    return false;
  }
  return true;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isEmptyOrCompleteIsoDate(value: string) {
  return value === "" || /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function sortValue(value: unknown): ContactSort {
  return typeof value === "string" && CONTACT_SORT_FIELDS.includes(value as ContactSort)
    ? (value as ContactSort)
    : initialFilters.sort;
}

function dealSortValue(value: unknown): DealSort {
  return typeof value === "string" && DEAL_SORT_FIELDS.includes(value as DealSort)
    ? (value as DealSort)
    : initialDealFilters.sort;
}

function abcSortValue(value: unknown): AbcSort {
  return typeof value === "string" && ABC_SORT_FIELDS.includes(value as AbcSort)
    ? (value as AbcSort)
    : initialAbcFilters.sort;
}

function positiveNumberValue(value: unknown, fallback: number) {
  return typeof value === "number" && Number.isInteger(value) && value > 0 ? value : fallback;
}

function nonNegativeNumberValue(value: unknown) {
  return typeof value === "number" && Number.isInteger(value) && value >= 0 ? value : 0;
}

function dateOnly(value: string | null | undefined) {
  return value ? value.slice(0, 10) : undefined;
}
