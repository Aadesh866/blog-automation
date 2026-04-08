import { notFound } from "next/navigation";
import { getPostBySlug, getAllSlugs, getRelatedPosts } from "@/lib/sanity";
import { generatePostMetadata, generateBlogPostingJsonLd } from "@/lib/seo";
import { PortableText } from "@portabletext/react";
import { format } from "date-fns";
import JsonLd from "@/components/JsonLd";
import Link from "next/link";
import type { Metadata } from "next";

// ISR: revalidate every 3600 seconds (1 hour)
export const revalidate = 3600;

interface BlogPostPageProps {
  params: Promise<{ slug: string }>;
}

// Generate static paths at build time
export async function generateStaticParams() {
  try {
    const slugs = await getAllSlugs();
    return (slugs || []).map((slug: string) => ({ slug }));
  } catch {
    return [];
  }
}

// Generate per-page SEO metadata
export async function generateMetadata({
  params,
}: BlogPostPageProps): Promise<Metadata> {
  const { slug } = await params;
  try {
    const post = await getPostBySlug(slug);
    if (!post) return { title: "Post Not Found" };
    return generatePostMetadata({
      title: post.title,
      slug: post.slug,
      metaDescription: post.metaDescription || "",
      seoKeywords: post.seoKeywords,
    });
  } catch {
    return { title: "Post Not Found" };
  }
}

export default async function BlogPostPage({ params }: BlogPostPageProps) {
  const { slug } = await params;

  let post;
  try {
    post = await getPostBySlug(slug);
  } catch {
    notFound();
  }
  if (!post) notFound();

  // Get related posts
  let relatedPosts: Array<{
    _id: string;
    title: string;
    slug: string;
    metaDescription: string;
    publishedAt: string;
  }> = [];
  try {
    relatedPosts = await getRelatedPosts(slug, post.seoKeywords || []);
  } catch {
    // Non-critical, continue without related posts
  }

  // JSON-LD structured data
  const jsonLd = generateBlogPostingJsonLd({
    title: post.title,
    slug: post.slug,
    metaDescription: post.metaDescription || "",
    publishedAt: post.publishedAt,
    author: post.author || "Editorial Team",
  });

  // Estimate reading time
  const wordCount = post.body
    ? post.body
        .map((b: { children?: Array<{ text?: string }> }) =>
          b.children?.map((c: { text?: string }) => c.text || "").join(" ")
        )
        .join(" ")
        .split(/\s+/).length
    : 0;
  const readingTime = Math.max(1, Math.ceil(wordCount / 200));

  return (
    <>
      <JsonLd data={jsonLd} />

      <article className="mx-auto max-w-3xl px-4 sm:px-6 py-12 sm:py-16">
        {/* Back link */}
        <Link
          href="/blog"
          className="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-accent-light)] transition-colors mb-8"
          id="back-to-blog"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Blog
        </Link>

        {/* Header */}
        <header className="mb-10">
          {/* Keywords */}
          {post.seoKeywords && post.seoKeywords.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {post.seoKeywords.map((kw: string) => (
                <span
                  key={kw}
                  className="text-[10px] font-medium uppercase tracking-wider px-2.5 py-1 rounded-full bg-[var(--color-accent)]/10 text-[var(--color-accent-light)] border border-[var(--color-accent)]/20"
                >
                  {kw}
                </span>
              ))}
            </div>
          )}

          <h1 className="text-3xl sm:text-4xl font-bold text-[var(--color-text-primary)] leading-tight mb-4" id="post-title">
            {post.title}
          </h1>

          {post.metaDescription && (
            <p className="text-lg text-[var(--color-text-secondary)] mb-6 leading-relaxed">
              {post.metaDescription}
            </p>
          )}

          {/* Meta info bar */}
          <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)] border-t border-b border-[var(--color-border)] py-4">
            <span>{post.author || "Editorial Team"}</span>
            <span className="w-1 h-1 rounded-full bg-[var(--color-text-muted)]" />
            {post.publishedAt && (
              <time dateTime={post.publishedAt}>
                {format(new Date(post.publishedAt), "MMMM d, yyyy")}
              </time>
            )}
            <span className="w-1 h-1 rounded-full bg-[var(--color-text-muted)]" />
            <span>{readingTime} min read</span>
          </div>
        </header>

        {/* Body Content */}
        <div className="blog-content" id="post-content">
          {post.body ? (
            <PortableText value={post.body} />
          ) : (
            <p className="text-[var(--color-text-muted)]">Content not available.</p>
          )}
        </div>
      </article>

      {/* Related Posts */}
      {relatedPosts.length > 0 && (
        <section className="mx-auto max-w-6xl px-4 sm:px-6 pb-20">
          <h2 className="text-2xl font-bold text-[var(--color-text-primary)] mb-6">
            Related Articles
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {relatedPosts.map(
              (related: {
                _id: string;
                title: string;
                slug: string;
                metaDescription: string;
                publishedAt: string;
              }) => (
                <Link
                  key={related._id}
                  href={`/blog/${related.slug}`}
                  className="glass-card p-5 group"
                >
                  <h3 className="text-sm font-semibold text-[var(--color-text-primary)] group-hover:text-[var(--color-accent-light)] transition-colors line-clamp-2 mb-2">
                    {related.title}
                  </h3>
                  <p className="text-xs text-[var(--color-text-muted)] line-clamp-2">
                    {related.metaDescription}
                  </p>
                </Link>
              )
            )}
          </div>
        </section>
      )}
    </>
  );
}
