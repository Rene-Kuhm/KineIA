"use client";

import { cn } from "@/lib/utils";
import { BookOpen, FileText, Scroll, StickyNote } from "lucide-react";

export interface SourceCardProps {
  title: string;
  source: string;
  evidence_level: string;
  score: number;
  retrieval_mode?: "dense" | "hybrid" | "dense_fallback";
  score_type?: "cosine" | "rrf";
}

const levelConfig: Record<string, { icon: React.ElementType; color: string; bg: string }> = {
  protocol: { icon: Scroll, color: "text-emerald-600", bg: "bg-emerald-50 dark:bg-emerald-900/20" },
  book: { icon: BookOpen, color: "text-blue-600", bg: "bg-blue-50 dark:bg-blue-900/20" },
  paper: { icon: FileText, color: "text-amber-600", bg: "bg-amber-50 dark:bg-amber-900/20" },
  notes: { icon: StickyNote, color: "text-slate-500", bg: "bg-slate-50 dark:bg-slate-800" },
};

export function SourceCard({ title, evidence_level, score }: SourceCardProps) {
  const config = levelConfig[evidence_level] || levelConfig.notes;
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px]",
        config.bg, config.color
      )}
    >
      <Icon className="w-3 h-3 shrink-0" />
      <span className="truncate max-w-[120px]">{title}</span>
    </span>
  );
}
