import { NextRequest, NextResponse } from "next/server";
import { revalidatePath } from "next/cache";

/**
 * POST /api/revalidate
 * On-demand ISR revalidation triggered by Sanity webhook.
 * When a post is created/updated in Sanity, this endpoint revalidates the blog pages.
 */
export async function POST(request: NextRequest) {
  try {
    // Verify webhook secret
    const secret = request.nextUrl.searchParams.get("secret");
    if (secret !== process.env.REVALIDATION_SECRET) {
      return NextResponse.json({ message: "Invalid secret" }, { status: 401 });
    }

    const body = await request.json();
    const slug = body?.slug?.current || body?.slug;

    // Revalidate the blog listing page
    revalidatePath("/blog");

    // Revalidate the specific post page if slug is provided
    if (slug) {
      revalidatePath(`/blog/${slug}`);
    }

    // Revalidate cached data

    return NextResponse.json({
      revalidated: true,
      slug: slug || null,
      timestamp: Date.now(),
    });
  } catch (error) {
    console.error("Revalidation error:", error);
    return NextResponse.json(
      { message: "Error revalidating", error: String(error) },
      { status: 500 }
    );
  }
}
