"use client";

import { cn } from "@/lib/utils";
import { BookOpen, FileText, Scroll, StickyNote } from "lucide-react";

type EvidenceLevel = "protocol" | "book" | "paper" | "notes";

interface SourceCardProps {
  title: string;
  evidence_level: EvidenceLevel;
  source_type: string;
}

const levelConfig: Record<EvidenceLevel, { icon: React.ElementType; label: string; color: string; bg: string }> = {
  protocol: {
    icon: Scroll,
    label: "Protocol",
    color: "text-emerald-700 dark:text-emerald-400",
    bg: "bg-emerald-100 dark:bg-emerald-900/30",
  },
  book: {
    icon: BookOpen,
    label: "Book",
    color: "text-blue-700 dark:text-blue-400",
    bg: "bg-blue-100 dark:bg-blue-900/30",
  },
  paper: {
    icon: FileText,
    label: "Paper",
    color: "text-amber-700 dark:text-amber-400",
    bg: "bg-amber-100 dark:bg-amber-900/30",
  },
  notes: {
    icon: StickyNote,
    label: "Notes",
    color: "text-orange-700 dark:text-orange-400",
    bg: "bg-orange-100 dark:bg-orange-900/30",
  },
};

export function SourceCard({ title, evidence_level, source_type }: SourceCardProps) {
  const config = levelConfig[evidence_level] || levelConfig.notes;
  const Icon = config.icon;
  
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs",
        config.bg,
        config.color
      )}
    >
      <Icon className="w-3.5 h-3.5" />
      <span className="font-medium">{title}</span>
      <span className="opacity-60 text-[10px]">{source_type}</span>
    </div>
  );
}
