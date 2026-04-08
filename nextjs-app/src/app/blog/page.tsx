import { Suspense } from "react";
import { getPosts } from "@/lib/sanity";
import { generateBlogListMetadata } from "@/lib/seo";
import BlogCard from "@/components/BlogCard";
import SearchBar from "@/components/SearchBar";
import Pagination from "@/components/Pagination";

interface BlogPageProps {
  searchParams: Promise<{ page?: string; sort?: string }>;
}

export async function generateMetadata({ searchParams }: BlogPageProps) {
  const params = await searchParams;
  return generateBlogListMetadata(Number(params?.page) || 1);
}

export default async function BlogPage({ searchParams }: BlogPageProps) {
  const params = await searchParams;
  const page = Number(params?.page) || 1;
  const pageSize = 12;

  const { posts, total } = await getPosts(page, pageSize);
  const totalPages = Math.ceil((total || 0) / pageSize);

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-12 sm:py-16">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-3xl sm:text-4xl font-bold text-[var(--color-text-primary)] mb-4">
          Latest <span className="gradient-text">Articles</span>
        </h1>
        <p className="text-[var(--color-text-secondary)] mb-8 max-w-xl mx-auto">
          Explore our collection of in-depth articles, guides, and expert analysis.
        </p>

        <Suspense fallback={null}>
          <SearchBar />
        </Suspense>
      </div>

      {/* Posts Grid */}
      {posts && posts.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {posts.map(
            (
              post: {
                _id: string;
                title: string;
                slug: string;
                metaDescription: string;
                publishedAt: string;
                seoKeywords: string[];
              },
              index: number
            ) => (
              <BlogCard
                key={post._id}
                title={post.title}
                slug={post.slug}
                metaDescription={post.metaDescription || ""}
                publishedAt={post.publishedAt}
                seoKeywords={post.seoKeywords}
                index={index}
              />
            )
          )}
        </div>
      ) : (
        <div className="text-center py-20">
          <div className="text-5xl mb-4">📝</div>
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
            No articles yet
          </h2>
          <p className="text-[var(--color-text-muted)]">
            Content is being generated. Check back soon!
          </p>
        </div>
      )}

      {/* Pagination */}
      <Pagination currentPage={page} totalPages={totalPages} />
    </div>
  );
}
