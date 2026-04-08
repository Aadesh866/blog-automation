/**
 * types.ts — Shared TypeScript types for the blog automation system.
 */

export interface BlogPost {
  id: string;
  title: string;
  slug: string;
  content: string;
  keywords: string[];
  meta_description: string;
  status: "draft" | "published" | "archived";
  quality_score: number;
  word_count: number;
  reading_time: number;
  author: string;
  created_at: string;
  updated_at: string;
}

export interface SanityPost {
  _id: string;
  _type: "post";
  title: string;
  slug: { current: string };
  body: SanityBlock[];
  seoKeywords: string[];
  metaDescription: string;
  publishedAt: string;
  author: string;
}

export interface SanityBlock {
  _type: "block";
  style: "normal" | "h2" | "h3" | "h4" | "blockquote";
  children: SanitySpan[];
}

export interface SanitySpan {
  _type: "span";
  text: string;
  marks?: string[];
}

export interface SearchResult {
  id: string;
  title: string;
  slug: string;
  meta_description: string;
  keywords: string[];
  created_at: string;
  score: number;
}

export interface PostStats {
  total_posts: number;
  published_posts: number;
  draft_posts: number;
  posts_today: number;
  posts_this_week: number;
  avg_quality_score: number;
  avg_word_count: number;
}

export interface PaginationInfo {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}
