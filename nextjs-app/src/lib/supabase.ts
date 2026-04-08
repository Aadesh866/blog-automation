/**
 * supabase.ts — Supabase client for the Next.js frontend.
 * Used for search queries and admin dashboard stats.
 */

import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

/**
 * Full-text search posts using PostgreSQL tsvector.
 */
export async function searchPostsFTS(query: string, limit = 10) {
  const { data, error } = await supabase.rpc("search_posts_fts", {
    query_text: query,
    match_count: limit,
  });

  if (error) {
    console.error("FTS search error:", error);
    return [];
  }
  return data || [];
}

/**
 * Hybrid search: combines full-text search + vector similarity.
 * Requires the query embedding to be generated server-side.
 */
export async function hybridSearch(
  query: string,
  queryEmbedding: number[],
  limit = 10
) {
  const { data, error } = await supabase.rpc("hybrid_search", {
    query_text: query,
    query_embedding: queryEmbedding,
    match_count: limit,
  });

  if (error) {
    console.error("Hybrid search error:", error);
    return [];
  }
  return data || [];
}

/**
 * Get post statistics for the admin dashboard.
 */
export async function getPostStats() {
  const { data, error } = await supabase
    .from("post_stats")
    .select("*")
    .single();

  if (error) {
    console.error("Stats error:", error);
    return null;
  }
  return data;
}

/**
 * Get recent posts for the admin dashboard.
 */
export async function getRecentPosts(limit = 20) {
  const { data, error } = await supabase
    .from("posts")
    .select(
      "id, title, slug, status, quality_score, word_count, keywords, created_at"
    )
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("Recent posts error:", error);
    return [];
  }
  return data || [];
}

/**
 * Get posts per day for the chart (last 30 days).
 */
export async function getPostsPerDay() {
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const { data, error } = await supabase
    .from("posts")
    .select("created_at")
    .gte("created_at", thirtyDaysAgo.toISOString())
    .order("created_at", { ascending: true });

  if (error) return [];

  // Group by day
  const dayMap: Record<string, number> = {};
  (data || []).forEach((post: { created_at: string }) => {
    const day = post.created_at.slice(0, 10);
    dayMap[day] = (dayMap[day] || 0) + 1;
  });

  return Object.entries(dayMap).map(([date, count]) => ({ date, count }));
}
