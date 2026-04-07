"use client";

import { cn } from "@/lib/utils";
import { GraduationCap, Briefcase, GraduationCap as ExamIcon } from "lucide-react";

type Mode = "student" | "professional" | "exam";

interface ModeSelectorProps {
  currentMode: Mode;
  onModeChange: (mode: Mode) => void;
}

const modes: { value: Mode; label: string; icon: React.ElementType }[] = [
  { value: "student", label: "Student", icon: GraduationCap },
  { value: "professional", label: "Professional", icon: Briefcase },
  { value: "exam", label: "Exam", icon: ExamIcon },
];

export function ModeSelector({ currentMode, onModeChange }: ModeSelectorProps) {
  return (
    <div className="inline-flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-full">
      {modes.map(({ value, label, icon: Icon }) => {
        const isActive = currentMode === value;
        
        return (
          <button
            key={value}
            onClick={() => onModeChange(value)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200",
              isActive
                ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            )}
          >
            <Icon className="w-4 h-4" />
            <span className="hidden sm:inline">{label}</span>
          </button>
        );
      })}
    </div>
  );
}
