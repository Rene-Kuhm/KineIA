"use client";

import { cn } from "@/lib/utils";
import { SourceCard, type SourceCardProps } from "./SourceCard";

interface MessageBubbleProps {
  content: string;
  role: "user" | "assistant";
  sources?: SourceCardProps[];
}

// Simple markdown-like rendering
function renderContent(text: string) {
  const lines = text.split("\n");
  
  return lines.map((line, i) => {
    // Bold: **text**
    const processed = line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    
    return (
      <p
        key={i}
        className="mb-1 last:mb-0"
        dangerouslySetInnerHTML={{ __html: processed }}
      />
    );
  });
}

export function MessageBubble({ content, role, sources }: MessageBubbleProps) {
  const isUser = role === "user";
  
  return (
    <div
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-slate-800 dark:bg-slate-700 text-white"
            : "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm border border-slate-200 dark:border-slate-700"
        )}
      >
        <div className={cn(isUser && "whitespace-pre-wrap")}>
          {isUser ? (
            <span className="whitespace-pre-wrap">{content}</span>
          ) : (
            renderContent(content)
          )}
        </div>
        
        {/* Sources - only for assistant messages */}
        {!isUser && sources && sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-2 font-medium">
              Sources
            </p>
            <div className="flex flex-wrap gap-2">
              {sources.map((source, i) => (
                <SourceCard key={i} {...source} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
