import Link from "next/link";

export default function HomePage() {
  return (
    <div className="relative">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Glow orbs */}
        <div className="absolute top-20 left-1/4 w-72 h-72 bg-[var(--color-accent)]/10 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute top-40 right-1/4 w-96 h-96 bg-[var(--color-gradient-end)]/8 rounded-full blur-[150px] pointer-events-none" />

        <div className="relative mx-auto max-w-6xl px-4 sm:px-6 pt-24 pb-20 sm:pt-32 sm:pb-28">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-[var(--color-accent)]/20 bg-[var(--color-accent)]/5 text-[var(--color-accent-light)] text-xs font-medium mb-8 fade-in-up">
              <span className="w-2 h-2 rounded-full bg-[var(--color-success)] animate-pulse" />
              Generating fresh content daily
            </div>

            <h1 className="text-4xl sm:text-6xl font-bold tracking-tight mb-6 fade-in-up" style={{ animationDelay: "100ms" }}>
              <span className="text-[var(--color-text-primary)]">Expert insights,</span>
              <br />
              <span className="gradient-text">powered by AI</span>
            </h1>

            <p className="text-lg sm:text-xl text-[var(--color-text-secondary)] mb-10 leading-relaxed fade-in-up" style={{ animationDelay: "200ms" }}>
              Discover high-quality articles on technology, development, and industry trends.
              Fresh content delivered daily, optimised for the topics that matter.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 fade-in-up" style={{ animationDelay: "300ms" }}>
              <Link
                href="/blog"
                id="hero-cta-blog"
                className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-[var(--color-gradient-start)] to-[var(--color-gradient-mid)] text-white font-semibold text-sm hover:opacity-90 transition-opacity shadow-lg shadow-[var(--color-accent)]/25"
              >
                Browse Articles
              </Link>
              <Link
                href="/admin"
                id="hero-cta-admin"
                className="px-8 py-3.5 rounded-xl border border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-sm hover:border-[var(--color-accent)]/40 hover:text-[var(--color-text-primary)] transition-all"
              >
                View Dashboard
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="mx-auto max-w-6xl px-4 sm:px-6 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {[
            {
              icon: "⚡",
              title: "AI Generation",
              desc: "10-30 high-quality articles per day, each ~1200 words with natural language flow.",
            },
            {
              icon: "🎯",
              title: "SEO Optimised",
              desc: "Strategic keyword integration, meta tags, structured data, and internal linking built-in.",
            },
            {
              icon: "🔍",
              title: "Smart Search",
              desc: "Hybrid full-text + semantic search powered by PostgreSQL and pgvector embeddings.",
            },
          ].map((feature, i) => (
            <div
              key={feature.title}
              className="glass-card p-8 fade-in-up"
              style={{ animationDelay: `${400 + i * 100}ms` }}
            >
              <span className="text-3xl mb-4 block">{feature.icon}</span>
              <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
