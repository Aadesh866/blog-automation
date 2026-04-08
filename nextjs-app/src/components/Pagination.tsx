import Link from "next/link";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  basePath?: string;
}

export default function Pagination({
  currentPage,
  totalPages,
  basePath = "/blog",
}: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages = [];
  const maxVisible = 5;
  let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  const end = Math.min(totalPages, start + maxVisible - 1);
  start = Math.max(1, end - maxVisible + 1);

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  const buildHref = (page: number) =>
    page === 1 ? basePath : `${basePath}?page=${page}`;

  return (
    <nav aria-label="Pagination" className="flex items-center justify-center gap-2 mt-12" id="pagination">
      {/* Previous */}
      {currentPage > 1 ? (
        <Link
          href={buildHref(currentPage - 1)}
          className="px-3 py-2 rounded-lg text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-card)] border border-[var(--color-border)] transition-all"
          id="pagination-prev"
        >
          ← Prev
        </Link>
      ) : (
        <span className="px-3 py-2 rounded-lg text-sm text-[var(--color-text-muted)] border border-[var(--color-border)]/50 cursor-not-allowed">
          ← Prev
        </span>
      )}

      {/* First page + ellipsis */}
      {start > 1 && (
        <>
          <Link href={buildHref(1)} className="px-3 py-2 rounded-lg text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-card)] transition-colors">
            1
          </Link>
          {start > 2 && <span className="text-[var(--color-text-muted)] text-sm">...</span>}
        </>
      )}

      {/* Page numbers */}
      {pages.map((page) => (
        <Link
          key={page}
          href={buildHref(page)}
          id={`pagination-page-${page}`}
          className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
            page === currentPage
              ? "bg-[var(--color-accent)] text-white shadow-lg shadow-[var(--color-accent)]/25"
              : "text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-card)]"
          }`}
        >
          {page}
        </Link>
      ))}

      {/* Last page + ellipsis */}
      {end < totalPages && (
        <>
          {end < totalPages - 1 && <span className="text-[var(--color-text-muted)] text-sm">...</span>}
          <Link href={buildHref(totalPages)} className="px-3 py-2 rounded-lg text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-card)] transition-colors">
            {totalPages}
          </Link>
        </>
      )}

      {/* Next */}
      {currentPage < totalPages ? (
        <Link
          href={buildHref(currentPage + 1)}
          className="px-3 py-2 rounded-lg text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-bg-card)] border border-[var(--color-border)] transition-all"
          id="pagination-next"
        >
          Next →
        </Link>
      ) : (
        <span className="px-3 py-2 rounded-lg text-sm text-[var(--color-text-muted)] border border-[var(--color-border)]/50 cursor-not-allowed">
          Next →
        </span>
      )}
    </nav>
  );
}
