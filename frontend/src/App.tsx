import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
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
  fetchContacts,
  fetchDatasetStatus,
  fetchFilterMetadata,
  type ContactFilters,
  type ContactSummary
} from "./api";

const PAGE_SIZE = 25;

const initialFilters: ContactFilters = {
  search: "",
  contactType: "",
  region: "",
  status: "",
  limit: PAGE_SIZE,
  offset: 0
};

export function App() {
  const [filters, setFilters] = useState<ContactFilters>(initialFilters);
  const [searchDraft, setSearchDraft] = useState("");

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

  const filterQuery = useQuery({
    queryKey: ["filter-metadata"],
    queryFn: fetchFilterMetadata
  });

  const statusQuery = useQuery({
    queryKey: ["dataset-status"],
    queryFn: fetchDatasetStatus
  });

  const contactsQuery = useQuery({
    queryKey: ["contacts", filters],
    queryFn: () => fetchContacts(filters)
  });

  const total = contactsQuery.data?.total ?? 0;
  const pageNumber = Math.floor(filters.offset / filters.limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / filters.limit));
  const hasPreviousPage = filters.offset > 0;
  const hasNextPage = filters.offset + filters.limit < total;

  const activeDataset = statusQuery.data?.active_dataset;

  const selectedFilterCount = useMemo(
    () =>
      [filters.search.trim(), filters.contactType, filters.region, filters.status].filter(Boolean)
        .length,
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
    setFilters(initialFilters);
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
          <DatasetBadge
            isLoading={statusQuery.isPending}
            isError={statusQuery.isError}
            state={activeDataset?.state}
            count={activeDataset?.normalized_contacts_count}
            finishedAt={activeDataset?.finished_at}
          />
        </header>

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

          <SelectField
            label="Тип"
            value={filters.contactType}
            onChange={(value) => updateFilter("contactType", value)}
            options={filterQuery.data?.contact_types ?? []}
            disabled={filterQuery.isPending || filterQuery.isError}
          />
          <SelectField
            label="Регион"
            value={filters.region}
            onChange={(value) => updateFilter("region", value)}
            options={filterQuery.data?.regions ?? []}
            disabled={filterQuery.isPending || filterQuery.isError}
          />
          <SelectField
            label="Статус сделки"
            value={filters.status}
            onChange={(value) => updateFilter("status", value)}
            options={filterQuery.data?.statuses ?? []}
            disabled={filterQuery.isPending || filterQuery.isError}
          />

          <button className="button button-secondary" type="button" onClick={resetFilters}>
            <Filter size={16} strokeWidth={1.5} />
            Сбросить
          </button>
        </section>

        {filterQuery.isError && (
          <InlineAlert
            title="Не удалось загрузить фильтры"
            message={filterQuery.error.message}
            onRetry={() => void filterQuery.refetch()}
          />
        )}

        <section className="table-card" aria-label="Контакты">
          <div className="table-header">
            <div>
              <h2>Список контактов</h2>
              <p>
                {contactsQuery.isPending
                  ? "Загрузка данных"
                  : `${total.toLocaleString("ru-RU")} контактов найдено`}
              </p>
            </div>
            {selectedFilterCount > 0 && (
              <span className="badge badge-primary">{selectedFilterCount} активных фильтра</span>
            )}
          </div>

          {contactsQuery.isError ? (
            <TableError message={contactsQuery.error.message} onRetry={() => void contactsQuery.refetch()} />
          ) : contactsQuery.isPending ? (
            <ContactsSkeleton />
          ) : contactsQuery.data.items.length === 0 ? (
            <EmptyState onReset={resetFilters} />
          ) : (
            <ContactsTable contacts={contactsQuery.data.items} />
          )}

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

function ContactsTable({ contacts }: { contacts: ContactSummary[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Контакт</th>
            <th>Raw type</th>
            <th>Тип</th>
            <th>Регион</th>
            <th>Всего сделок</th>
            <th>Won</th>
            <th>Open</th>
            <th>Lost</th>
            <th>Сумма original</th>
          </tr>
        </thead>
        <tbody>
          {contacts.map((contact) => (
            <tr key={contact.contact_id}>
              <td>
                <div className="contact-cell">
                  <span>{contact.contact_name}</span>
                  <small>ID {contact.contact_id}</small>
                </div>
              </td>
              <td>{contact.contact_type_raw || "—"}</td>
              <td>
                <span className="badge badge-neutral">{contact.contact_type_normalized}</span>
              </td>
              <td>{contact.region_normalized}</td>
              <td className="number-cell">{contact.total_deals_count}</td>
              <td className="number-cell">{contact.won_deals_count}</td>
              <td className="number-cell">{contact.open_deals_count}</td>
              <td className="number-cell">{contact.lost_deals_count}</td>
              <td className="number-cell">{formatMoney(contact.total_amount_original)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatMoney(value: string) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return value;
  }

  return new Intl.NumberFormat("ru-RU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(numeric);
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
