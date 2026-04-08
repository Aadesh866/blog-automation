/**
 * sanity.ts — Sanity client and GROQ queries for fetching blog content.
 */

import { createClient } from "next-sanity";

export const sanityClient = createClient({
  projectId: process.env.NEXT_PUBLIC_SANITY_PROJECT_ID!,
  dataset: process.env.NEXT_PUBLIC_SANITY_DATASET || "production",
  apiVersion: "2024-01-01",
  useCdn: true, // CDN for fast reads on the frontend
});

// ── GROQ Queries ──

const POST_FIELDS = `
  _id,
  title,
  "slug": slug.current,
  body,
  seoKeywords,
  metaDescription,
  publishedAt,
  author
`;

/**
 * Fetch paginated posts sorted by date.
 */
export async function getPosts(page = 1, pageSize = 12) {
  const start = (page - 1) * pageSize;
  const end = start + pageSize;

  const query = `{
    "posts": *[_type == "post"] | order(publishedAt desc) [${start}...${end}] {
      ${POST_FIELDS}
    },
    "total": count(*[_type == "post"])
  }`;

  return sanityClient.fetch(query);
}

/**
 * Fetch a single post by slug.
 */
export async function getPostBySlug(slug: string) {
  const query = `*[_type == "post" && slug.current == $slug][0] {
    ${POST_FIELDS}
  }`;

  return sanityClient.fetch(query, { slug });
}

/**
 * Fetch all post slugs for static generation.
 */
export async function getAllSlugs(): Promise<string[]> {
  const query = `*[_type == "post"]{ "slug": slug.current }.slug`;
  return sanityClient.fetch(query);
}

/**
 * Fetch posts by keyword relevance.
 */
export async function getPostsByKeyword(keyword: string, limit = 10) {
  const query = `*[_type == "post" && $keyword in seoKeywords] | order(publishedAt desc) [0...${limit}] {
    ${POST_FIELDS}
  }`;

  return sanityClient.fetch(query, { keyword });
}

/**
 * Fetch related posts (same keywords, excluding current).
 */
export async function getRelatedPosts(
  currentSlug: string,
  keywords: string[],
  limit = 4
) {
  const query = `*[_type == "post" && slug.current != $currentSlug && count((seoKeywords)[@ in $keywords]) > 0] | order(publishedAt desc) [0...${limit}] {
    ${POST_FIELDS}
  }`;

  return sanityClient.fetch(query, { currentSlug, keywords });
}

/**
 * Search posts by title match (simple GROQ search).
 */
export async function searchPosts(searchTerm: string, limit = 10) {
  const query = `*[_type == "post" && (title match $searchTerm || pt::text(body) match $searchTerm)] | order(publishedAt desc) [0...${limit}] {
    ${POST_FIELDS}
  }`;

  return sanityClient.fetch(query, { searchTerm: `${searchTerm}*` });
}
