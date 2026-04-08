import { NextRequest, NextResponse } from "next/server";
import { searchPostsFTS } from "@/lib/supabase";

/**
 * GET /api/search?q=query
 * Hybrid search endpoint that queries Supabase full-text search.
 * Falls back to FTS-only when embeddings aren't available.
 */
export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get("q");

  if (!query || query.trim().length < 2) {
    return NextResponse.json({ results: [], query: "" });
  }

  try {
    // Use full-text search (FTS) as primary
    const results = await searchPostsFTS(query.trim(), 10);

    return NextResponse.json({
      results: results.map(
        (r: {
          id: string;
          title: string;
          slug: string;
          meta_description: string;
          keywords: string[];
          created_at: string;
          rank: number;
        }) => ({
          id: r.id,
          title: r.title,
          slug: r.slug,
          meta_description: r.meta_description,
          keywords: r.keywords,
          created_at: r.created_at,
          score: r.rank,
        })
      ),
      query,
    });
  } catch (error) {
    console.error("Search error:", error);
    return NextResponse.json(
      { results: [], query, error: "Search failed" },
      { status: 500 }
    );
  }
}
