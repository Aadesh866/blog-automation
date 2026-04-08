"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Stats {
  total_posts: number;
  published_posts: number;
  draft_posts: number;
  posts_today: number;
  posts_this_week: number;
  avg_quality_score: number;
  avg_word_count: number;
}

interface RecentPost {
  id: string;
  title: string;
  slug: string;
  status: string;
  quality_score: number;
  word_count: number;
  created_at: string;
}

interface DayCount {
  date: string;
  count: number;
}

export default function AdminPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentPosts, setRecentPosts] = useState<RecentPost[]>([]);
  const [chartData, setChartData] = useState<DayCount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        // Dynamic imports to avoid SSR issues with Supabase client
        const { getPostStats, getRecentPosts, getPostsPerDay } = await import(
          "@/lib/supabase"
        );
        const [s, r, c] = await Promise.all([
          getPostStats(),
          getRecentPosts(20),
          getPostsPerDay(),
        ]);
        setStats(s);
        setRecentPosts(r);
        setChartData(c);
      } catch (err) {
        console.error("Failed to load admin data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-16">
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-3 border-[var(--color-accent)]/30 border-t-[var(--color-accent)] rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 py-12 sm:py-16">
      <h1 className="text-3xl font-bold text-[var(--color-text-primary)] mb-2" id="admin-title">
        Content <span className="gradient-text">Dashboard</span>
      </h1>
      <p className="text-[var(--color-text-muted)] mb-8">
        Monitor your automated blog generation pipeline.
      </p>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
        {[
          {
            label: "Total Posts",
            value: stats?.total_posts ?? 0,
            icon: "📄",
          },
          {
            label: "Today",
            value: stats?.posts_today ?? 0,
            icon: "📅",
            accent: true,
          },
          {
            label: "This Week",
            value: stats?.posts_this_week ?? 0,
            icon: "📊",
          },
          {
            label: "Avg Quality",
            value: `${stats?.avg_quality_score ?? 0}/100`,
            icon: "⭐",
          },
        ].map((card) => (
          <div
            key={card.label}
            className={`glass-card p-5 ${card.accent ? "gradient-border" : ""}`}
            id={`stat-${card.label.toLowerCase().replace(/\s/g, "-")}`}
          >
            <span className="text-2xl mb-2 block">{card.icon}</span>
            <p className="text-2xl font-bold text-[var(--color-text-primary)]">
              {card.value}
            </p>
            <p className="text-xs text-[var(--color-text-muted)] mt-1">
              {card.label}
            </p>
          </div>
        ))}
      </div>

      {/* Chart + Summary row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
        {/* Chart */}
        <div className="lg:col-span-2 glass-card p-6" id="posts-chart">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
            Posts Generated (Last 30 Days)
          </h2>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(120,120,160,0.1)" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#6a6a80", fontSize: 11 }}
                  tickFormatter={(v: string) => v.slice(5)}
                />
                <YAxis tick={{ fill: "#6a6a80", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: "#1a1a2e",
                    border: "1px solid rgba(120,120,160,0.2)",
                    borderRadius: "8px",
                    color: "#e8e8f0",
                  }}
                />
                <Bar dataKey="count" fill="#7c3aed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-[var(--color-text-muted)]">
              No data yet — posts will appear once generation starts.
            </div>
          )}
        </div>

        {/* Summary */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
            Summary
          </h2>
          <div className="space-y-4">
            <div className="flex justify-between text-sm">
              <span className="text-[var(--color-text-muted)]">Published</span>
              <span className="text-[var(--color-success)] font-medium">
                {stats?.published_posts ?? 0}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[var(--color-text-muted)]">Drafts</span>
              <span className="text-[var(--color-warning)] font-medium">
                {stats?.draft_posts ?? 0}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[var(--color-text-muted)]">Avg Words</span>
              <span className="text-[var(--color-text-primary)] font-medium">
                {stats?.avg_word_count ?? 0}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-[var(--color-text-muted)]">Avg Quality</span>
              <span className="text-[var(--color-text-primary)] font-medium">
                {stats?.avg_quality_score ?? 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Posts Table */}
      <div className="glass-card overflow-hidden" id="recent-posts-table">
        <div className="p-6 border-b border-[var(--color-border)]">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Recent Posts
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="text-left py-3 px-6 text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                  Title
                </th>
                <th className="text-left py-3 px-4 text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                  Status
                </th>
                <th className="text-left py-3 px-4 text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                  Words
                </th>
                <th className="text-left py-3 px-4 text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                  Quality
                </th>
                <th className="text-left py-3 px-4 text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                  Created
                </th>
              </tr>
            </thead>
            <tbody>
              {recentPosts.length > 0 ? (
                recentPosts.map((post) => (
                  <tr
                    key={post.id}
                    className="border-b border-[var(--color-border)]/50 hover:bg-[var(--color-bg-card-hover)] transition-colors"
                  >
                    <td className="py-3 px-6 text-[var(--color-text-primary)] font-medium max-w-xs truncate">
                      {post.title}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          post.status === "published"
                            ? "bg-[var(--color-success)]/10 text-[var(--color-success)]"
                            : "bg-[var(--color-warning)]/10 text-[var(--color-warning)]"
                        }`}
                      >
                        {post.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[var(--color-text-muted)]">
                      {post.word_count}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-[var(--color-bg-primary)] rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-[var(--color-gradient-start)] to-[var(--color-gradient-end)]"
                            style={{
                              width: `${Math.min(100, post.quality_score)}%`,
                            }}
                          />
                        </div>
                        <span className="text-xs text-[var(--color-text-muted)]">
                          {post.quality_score}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-[var(--color-text-muted)] text-xs">
                      {new Date(post.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-[var(--color-text-muted)]">
                    No posts generated yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
