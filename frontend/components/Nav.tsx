"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/daily",   label: "Daily",   color: "var(--daily)" },
  { href: "/weekly",  label: "Weekly",  color: "var(--weekly)" },
  { href: "/monthly", label: "Monthly", color: "var(--monthly)" },
];

export default function Nav() {
  const path = usePathname();
  return (
    <header style={{ borderBottom: "0.5px solid var(--border)", background: "var(--bg)" }}>
      <div style={{ maxWidth: 860, margin: "0 auto", padding: "0 1.25rem", display: "flex", alignItems: "center", gap: "2rem", height: 56 }}>
        <Link href="/daily" style={{ fontWeight: 600, fontSize: 16, color: "var(--text)", textDecoration: "none", whiteSpace: "nowrap" }}>
          Oncology Tracker
        </Link>
        <nav style={{ display: "flex", gap: "0.25rem" }}>
          {TABS.map(t => {
            const active = path.startsWith(t.href);
            return (
              <Link
                key={t.href}
                href={t.href}
                style={{
                  padding: "5px 14px",
                  borderRadius: 6,
                  fontSize: 13,
                  fontWeight: active ? 600 : 400,
                  color: active ? t.color : "var(--text2)",
                  background: active ? `color-mix(in srgb, ${t.color} 10%, transparent)` : "transparent",
                  textDecoration: "none",
                  transition: "all 0.15s",
                }}
              >
                {t.label}
              </Link>
            );
          })}
        </nav>
        <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--text3)" }}>
          Updated daily at 09:00 TST
        </span>
      </div>
    </header>
  );
}
