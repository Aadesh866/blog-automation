/**
 * JsonLd.tsx — Renders JSON-LD structured data in the page <head>.
 * Used for Schema.org BlogPosting structured data to improve search results.
 */

interface JsonLdProps {
  data: Record<string, unknown>;
}

export default function JsonLd({ data }: JsonLdProps) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}
