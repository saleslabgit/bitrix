import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Database,
  Filter,
  RefreshCcw,
  Search
} from "lucide-react";
import {
  fetchContactAnalytics,
  fetchDatasetStatus,
  fetchFilterMetadata,
  refreshLocalData,
  type ContactAnalytics,
  type ContactFilters,
  type ContactSort,
  type FilterMetadata,
  type LocalDataRefreshResponse
} from "./api";

const PAGE_SIZE = 25;
const CONTACTS_STORAGE_KEY = "bitrix-sales.contacts.v1";
const FILTER_METADATA_STORAGE_KEY = "bitrix-sales.filter-metadata.v1";
const CONTACT_SORT_FIELDS: ContactSort[] = [
  "contact_id",
  "contact_name",
  "contact_type_normalized",
  "region_normalized",
  "total_deals_count",
  "won_deals_count",
  "open_deals_count",
  "lost_deals_count",
  "budget_usd",
  "budget_in_work_usd",
  "lost_budget_usd",
  "revenue_usd",
  "estimated_profit_usd",
  "last_won_date",
  "latest_deal_date"
];

const initialFilters: ContactFilters = {
  search: "",
  contactId: "",
  contactType: "",
  region: "",
  status: "",
  dealCreatedFrom: "",
  dealCreatedTo: "",
  sort: "contact_id",
  order: "asc",
  limit: PAGE_SIZE,
  offset: 0
};

export function App() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<ContactFilters>(() => loadStoredFilters());
  const [searchDraft, setSearchDraft] = useState(filters.search);
  const [contactIdDraft, setContactIdDraft] = useState(filters.contactId);
  const [dealCreatedDrafts, setDealCreatedDrafts] = useState({
    from: filters.dealCreatedFrom,
    to: filters.dealCreatedTo
  });
  const [lastFilterMetadata, setLastFilterMetadata] = useState<FilterMetadata | null>(() =>
    loadStoredFilterMetadata()
  );
  const [lastRefreshResult, setLastRefreshResult] = useState<LocalDataRefreshResponse | null>(
    null
  );
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
    storeFilters(filters);
  }, [filters]);

  const statusQuery = useQuery({
    queryKey: ["dataset-status"],
    queryFn: fetchDatasetStatus
  });

  const activeDataset = statusQuery.data?.active_dataset;
  const isDatasetReady = activeDataset?.state === "success" && activeDataset.is_active;
  const activeContactsCount = activeDataset?.normalized_contacts_count;

  const filterQuery = useQuery({
    queryKey: ["filter-metadata"],
    queryFn: fetchFilterMetadata,
    enabled: isDatasetReady
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
    enabled: isDatasetReady && !isDealCreatedRangeInvalid
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
        queryClient.invalidateQueries({ queryKey: ["contacts"] })
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

  const total = contactsQuery.data?.total ?? 0;
  const isRefreshing = refreshMutation.isPending;
  const pageNumber = Math.floor(filters.offset / filters.limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / filters.limit));
  const hasPreviousPage = filters.offset > 0;
  const hasNextPage = filters.offset + filters.limit < total;
  const tableSubtitle = statusQuery.isPending
    ? "Проверка локального dataset"
    : !isDatasetReady
      ? "Локальная база не подготовлена"
      : contactsQuery.isPending
        ? "Загрузка данных"
        : `${total.toLocaleString("ru-RU")} контактов найдено`;

  const selectedFilterCount = useMemo(
    () =>
      [
        filters.search.trim(),
        filters.contactId.trim(),
        filters.contactType,
        filters.region,
        filters.status,
        filters.dealCreatedFrom,
        filters.dealCreatedTo
      ].filter(Boolean).length,
    [filters]
  );

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

  function updateContactIdFilter(value: string) {
    const numericValue = value.replace(/\D/g, "");
    setContactIdDraft(numericValue);
    updateFilter("contactId", numericValue);
  }

  function updateSort(sort: ContactSort) {
    setFilters((current) => ({
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

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Основная навигация">
        <div className="brand">
          <span className="brand-mark">BS</span>
          <span>Bitrix Sales</span>
        </div>
        <nav className="nav-list">
          <a className="nav-item nav-item-active" href="#contacts" aria-current="page">
            <BarChart3 size={18} strokeWidth={1.5} />
            Contacts
          </a>
        </nav>
      </aside>

      <main className="main-panel" id="contacts">
        <header className="page-header">
          <div>
            <p className="eyebrow">Reports</p>
            <h1>Contacts</h1>
            <p className="page-subtitle">Таблица контактов с поиском и фильтрами по локальным данным.</p>
          </div>
          <div className="header-actions">
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
          </div>
        </header>

        {isDatasetReady && (
          <section className="toolbar" aria-label="Фильтры контактов">
            <label className="field search-field">
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
              label="Регион"
              value={filters.region}
              onChange={(value) => updateFilter("region", value)}
              options={filterMetadata?.regions ?? []}
              disabled={!filterMetadata}
            />
            <SelectField
              label="Статус сделки"
              value={filters.status}
              onChange={(value) => updateFilter("status", value)}
              options={filterMetadata?.statuses ?? []}
              disabled={!filterMetadata}
            />

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
              className="button button-secondary date-apply-button"
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

            <button className="button button-secondary" type="button" onClick={resetFilters}>
              <Filter size={16} strokeWidth={1.5} />
              Сбросить
            </button>
          </section>
        )}

        {isDatasetReady && (filterQuery.isError || isFreshFilterMetadataInvalid) && (
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

        {isDatasetReady && isDealCreatedRangeInvalid && (
          <InlineValidation message="Дата «Создана с» должна быть не позже даты «Создана по»." />
        )}

        {isDatasetReady && areDealCreatedDraftsInvalid && (
          <InlineValidation message="В черновике дат значение «Создана с» должно быть не позже «Создана по»." />
        )}

        <section className="table-card" aria-label="Контакты">
          <div className="table-header">
            <div>
              <h2>Список контактов</h2>
              <p>{tableSubtitle}</p>
            </div>
            {selectedFilterCount > 0 && (
              <span className="badge badge-primary">{selectedFilterCount} активных фильтра</span>
            )}
          </div>

          {statusQuery.isError ? (
            <TableError message={statusQuery.error.message} onRetry={() => void statusQuery.refetch()} />
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
          ) : contactsQuery.isError ? (
            <TableError message={contactsQuery.error.message} onRetry={() => void contactsQuery.refetch()} />
          ) : isDealCreatedRangeInvalid ? (
            <EmptyState onReset={resetFilters} />
          ) : contactsQuery.isPending ? (
            <ContactsSkeleton />
          ) : contactsQuery.data.items.length === 0 ? (
            <EmptyState onReset={resetFilters} />
          ) : (
            <ContactsTable
              contacts={contactsQuery.data.items}
              sort={filters.sort}
              order={filters.order}
              onSort={updateSort}
            />
          )}

          {isDatasetReady && (
            <div className="pagination">
              <span>
                Страница {pageNumber.toLocaleString("ru-RU")} из {totalPages.toLocaleString("ru-RU")}
              </span>
              <div className="pagination-actions">
                <button
                  className="icon-button"
                  type="button"
                  disabled={!hasPreviousPage}
                  onClick={() =>
                    setFilters((current) => ({
                      ...current,
                      offset: Math.max(0, current.offset - current.limit)
                    }))
                  }
                  aria-label="Предыдущая страница"
                >
                  <ChevronLeft size={16} strokeWidth={1.5} />
                </button>
                <button
                  className="icon-button"
                  type="button"
                  disabled={!hasNextPage}
                  onClick={() =>
                    setFilters((current) => ({
                      ...current,
                      offset: current.offset + current.limit
                    }))
                  }
                  aria-label="Следующая страница"
                >
                  <ChevronRight size={16} strokeWidth={1.5} />
                </button>
              </div>
            </div>
          )}
        </section>
      </main>
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

function TableError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="state-panel" role="alert">
      <AlertCircle size={24} strokeWidth={1.5} />
      <h3>Не удалось загрузить контакты</h3>
      <p>{message}</p>
      <button className="button button-primary" type="button" onClick={onRetry}>
        <RefreshCcw size={16} strokeWidth={1.5} />
        Повторить
      </button>
    </div>
  );
}

function EmptyState({ onReset }: { onReset: () => void }) {
  return (
    <div className="state-panel">
      <Search size={24} strokeWidth={1.5} />
      <h3>Контакты не найдены</h3>
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

function ContactsTable({
  contacts,
  sort,
  order,
  onSort
}: {
  contacts: ContactAnalytics[];
  sort: ContactSort;
  order: "asc" | "desc";
  onSort: (sort: ContactSort) => void;
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
              label="Регион"
              field="region_normalized"
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
                  <span>{contact.contact_name}</span>
                </div>
              </td>
              <td>
                <span className="badge badge-neutral">{contact.contact_type_normalized}</span>
              </td>
              <td>{contact.region_normalized}</td>
              <td className="number-cell">{contact.total_deals_count}</td>
              <td className="number-cell">{contact.won_deals_count}</td>
              <td className="number-cell">{contact.open_deals_count}</td>
              <td className="number-cell">{contact.lost_deals_count}</td>
              <td className="number-cell money-cell">{formatUsd(contact.budget_usd)}</td>
              <td className="number-cell money-cell">{formatUsd(contact.budget_in_work_usd)}</td>
              <td className="number-cell money-cell">{formatUsd(contact.lost_budget_usd)}</td>
              <td className="number-cell money-cell">{formatUsd(contact.revenue_usd)}</td>
              <td className="number-cell money-cell">
                {formatUsd(contact.estimated_profit_usd)}
              </td>
              <td>{formatDate(contact.last_won_date)}</td>
              <td>{formatDate(contact.latest_deal_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SortableHeader({
  label,
  field,
  sort,
  order,
  onSort,
  align = "left"
}: {
  label: string;
  field: ContactSort;
  sort: ContactSort;
  order: "asc" | "desc";
  onSort: (sort: ContactSort) => void;
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
      region: stringValue(parsed.region),
      status: stringValue(parsed.status),
      dealCreatedFrom: dateValue(parsed.dealCreatedFrom),
      dealCreatedTo: dateValue(parsed.dealCreatedTo),
      sort: sortValue(parsed.sort),
      order: parsed.order === "desc" ? "desc" : "asc",
      limit: positiveNumberValue(parsed.limit, PAGE_SIZE),
      offset: nonNegativeNumberValue(parsed.offset)
    };
  } catch {
    return initialFilters;
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
      max_closed_at: nullableStringValue(parsed.max_closed_at)
    };
  } catch {
    return null;
  }
}

function storeFilters(filters: ContactFilters) {
  if (areDefaultFilters(filters)) {
    window.localStorage.removeItem(CONTACTS_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(CONTACTS_STORAGE_KEY, JSON.stringify(filters));
}

function storeFilterMetadata(metadata: FilterMetadata) {
  window.localStorage.setItem(FILTER_METADATA_STORAGE_KEY, JSON.stringify(metadata));
}

function areDefaultFilters(filters: ContactFilters) {
  return JSON.stringify(filters) === JSON.stringify(initialFilters);
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

function positiveNumberValue(value: unknown, fallback: number) {
  return typeof value === "number" && Number.isInteger(value) && value > 0 ? value : fallback;
}

function nonNegativeNumberValue(value: unknown) {
  return typeof value === "number" && Number.isInteger(value) && value >= 0 ? value : 0;
}

function dateOnly(value: string | null | undefined) {
  return value ? value.slice(0, 10) : undefined;
}
