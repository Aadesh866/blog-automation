import Link from "next/link";
import { format } from "date-fns";

interface BlogCardProps {
  title: string;
  slug: string;
  metaDescription: string;
  publishedAt: string;
  seoKeywords?: string[];
  index?: number;
}

export default function BlogCard({
  title,
  slug,
  metaDescription,
  publishedAt,
  seoKeywords = [],
  index = 0,
}: BlogCardProps) {
  return (
    <Link
      href={`/blog/${slug}`}
      id={`blog-card-${slug}`}
      className="glass-card block p-6 group"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* Keywords */}
      {seoKeywords.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {seoKeywords.slice(0, 3).map((kw) => (
            <span
              key={kw}
              className="text-[10px] font-medium uppercase tracking-wider px-2.5 py-1 rounded-full bg-[var(--color-accent)]/10 text-[var(--color-accent-light)] border border-[var(--color-accent)]/20"
            >
              {kw}
            </span>
          ))}
        </div>
      )}

      {/* Title */}
      <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2 group-hover:text-[var(--color-accent-light)] transition-colors line-clamp-2 leading-snug">
        {title}
      </h2>

      {/* Description */}
      <p className="text-sm text-[var(--color-text-muted)] mb-4 line-clamp-3 leading-relaxed">
        {metaDescription}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)]">
        <time dateTime={publishedAt}>
          {publishedAt ? format(new Date(publishedAt), "MMM d, yyyy") : ""}
        </time>
        <span className="text-[var(--color-accent-light)] opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
          Read more
          <svg className="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </span>
      </div>
    </Link>
  );
}
