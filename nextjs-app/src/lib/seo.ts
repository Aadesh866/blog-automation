/**
 * seo.ts — SEO utilities for generating structured data, meta tags, and internal links.
 */

import type { Metadata } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://example.com";
const SITE_NAME = process.env.NEXT_PUBLIC_SITE_NAME || "Blog";

/**
 * Generate JSON-LD structured data for a BlogPosting (Schema.org).
 */
export function generateBlogPostingJsonLd(post: {
  title: string;
  slug: string;
  metaDescription: string;
  publishedAt: string;
  author: string;
  content?: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: post.title,
    description: post.metaDescription,
    url: `${SITE_URL}/blog/${post.slug}`,
    datePublished: post.publishedAt,
    dateModified: post.publishedAt,
    author: {
      "@type": "Person",
      name: post.author || "Editorial Team",
    },
    publisher: {
      "@type": "Organization",
      name: SITE_NAME,
      url: SITE_URL,
    },
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": `${SITE_URL}/blog/${post.slug}`,
    },
    ...(post.content && {
      wordCount: post.content.split(/\s+/).length,
    }),
  };
}

/**
 * Generate Next.js Metadata for a blog post page.
 */
export function generatePostMetadata(post: {
  title: string;
  slug: string;
  metaDescription: string;
  seoKeywords?: string[];
}): Metadata {
  const url = `${SITE_URL}/blog/${post.slug}`;

  return {
    title: `${post.title} | ${SITE_NAME}`,
    description: post.metaDescription,
    keywords: post.seoKeywords?.join(", "),
    alternates: { canonical: url },
    openGraph: {
      title: post.title,
      description: post.metaDescription,
      url,
      siteName: SITE_NAME,
      type: "article",
      locale: "en_US",
    },
    twitter: {
      card: "summary_large_image",
      title: post.title,
      description: post.metaDescription,
    },
  };
}

/**
 * Generate the blog listing page metadata.
 */
export function generateBlogListMetadata(page = 1): Metadata {
  const title = page === 1 ? `Blog | ${SITE_NAME}` : `Blog — Page ${page} | ${SITE_NAME}`;
  return {
    title,
    description: `Read the latest articles and insights on ${SITE_NAME}. Expert guides, tutorials, and industry analysis.`,
    alternates: {
      canonical: page === 1 ? `${SITE_URL}/blog` : `${SITE_URL}/blog?page=${page}`,
    },
    openGraph: {
      title,
      description: `Latest articles from ${SITE_NAME}`,
      url: `${SITE_URL}/blog`,
      siteName: SITE_NAME,
      type: "website",
    },
  };
}
