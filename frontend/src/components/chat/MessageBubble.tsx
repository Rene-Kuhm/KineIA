"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { SourceCard, type SourceCardProps } from "./SourceCard";
import { safeExternalUrl, splitSafeContent } from "./safeContent";
import { ChevronDown, ChevronUp } from "lucide-react";

export interface ImageData {
  url: string;
  label: string;
  source: string;
}

interface MessageBubbleProps {
  content: string;
  role: "user" | "assistant";
  sources?: SourceCardProps[];
  images?: ImageData[];
}

export function MessageBubble({ content, role, sources, images }: MessageBubbleProps) {
  const isUser = role === "user";
  const [showSources, setShowSources] = useState(false);

  return (
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-slate-800 dark:bg-slate-700 text-white"
            : "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm border border-slate-200 dark:border-slate-700"
        )}
      >
        <div className="whitespace-pre-wrap break-words">
          {splitSafeContent(content).map((part, index) =>
            part.kind === "citation" ? (
              <span key={`${index}-${part.citationId}`} data-citation-id={part.citationId}>
                {part.value}
              </span>
            ) : (
              <span key={`${index}-text`}>{part.value}</span>
            )
          )}
        </div>

        {/* Anatomical Images — shown automatically */}
        {!isUser && images && images.length > 0 && (
          <div className="mt-3 grid grid-cols-2 gap-2">
            {images.map((img, i) => {
              const safeUrl = safeExternalUrl(img.url);
              return safeUrl ? (
                <a
                  key={`${safeUrl}-${i}`}
                  href={safeUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <img
                    src={safeUrl}
                    alt={img.label}
                    className="w-full h-28 object-cover rounded-lg border border-slate-200 dark:border-slate-600 hover:ring-2 hover:ring-blue-400 transition-all"
                    loading="lazy"
                  />
                </a>
              ) : null;
            })}
          </div>
        )}

        {/* Collapsible Sources — hidden by default */}
        {!isUser && sources && sources.length > 0 && (
          <div className="mt-2">
            <button
              onClick={() => setShowSources(!showSources)}
              className="inline-flex items-center gap-1 text-[10px] text-slate-400 hover:text-slate-500 dark:hover:text-slate-300 transition-colors"
            >
              {showSources ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {showSources ? "Ocultar fuentes" : `${sources.length} fuentes`}
            </button>
            {showSources && (
              <div className="mt-1.5 flex flex-wrap gap-1">
                {sources.map((source, i) => (
                  <SourceCard key={i} {...source} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
