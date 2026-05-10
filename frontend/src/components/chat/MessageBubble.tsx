"use client";

import { cn } from "@/lib/utils";
import { SourceCard, type SourceCardProps } from "./SourceCard";

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

function renderContent(text: string) {
  const lines = text.split("\n");
  return lines.map((line, i) => {
    const processed = line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    return (
      <p key={i} className="mb-1 last:mb-0" dangerouslySetInnerHTML={{ __html: processed }} />
    );
  });
}

export function MessageBubble({ content, role, sources, images }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-slate-800 dark:bg-slate-700 text-white"
            : "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm border border-slate-200 dark:border-slate-700"
        )}
      >
        <div className={cn(isUser && "whitespace-pre-wrap")}>
          {isUser ? <span className="whitespace-pre-wrap">{content}</span> : renderContent(content)}
        </div>

        {/* Anatomical Images */}
        {!isUser && images && images.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-2 font-medium">
              🖼️ Imágenes de referencia
            </p>
            <div className="grid grid-cols-2 gap-2">
              {images.map((img, i) => (
                <a key={i} href={img.url} target="_blank" rel="noopener noreferrer" className="block">
                  <img
                    src={img.url}
                    alt={img.label}
                    className="w-full h-32 object-cover rounded-lg border border-slate-200 dark:border-slate-600 hover:opacity-90 transition-opacity"
                    loading="lazy"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block truncate">
                    {img.label} · {img.source}
                  </span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Sources */}
        {!isUser && sources && sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-2 font-medium">Sources</p>
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
