"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, AlertCircle, RefreshCw, Pencil } from "lucide-react";
import { fetchApi, fetchApiStream, APIError } from "@/lib/api";
import { MessageBubble } from "./MessageBubble";
import { ModeSelector } from "./ModeSelector";
import type { SourceCardProps } from "./SourceCard";

interface Message {
  id: string;
  content: string;
  role: "user" | "assistant" | "error";
  sources?: SourceCardProps[];
  retryMessage?: string;
}

type Mode = "student" | "professional" | "exam";

export function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [mode, setMode] = useState<Mode>("student");
  const [connectionError, setConnectionError] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, streaming]);

  const fallbackToNonStreaming = async (query: string) => {
    try {
      const response = await fetchApi("/chat", {
        method: "POST",
        body: JSON.stringify({
          query,
          mode,
        }),
      });

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        content: response.data?.answer || response.answer || "No recibí respuesta del agente.",
        role: "assistant",
        sources: response.data?.sources || response.sources || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chat fallback error:", error);

      if (error instanceof APIError) {
        if (error.status === 0 || error.status === undefined) {
          setConnectionError(true);
        }
        const errorMessage: Message = {
          id: crypto.randomUUID(),
          content: error.userMessage,
          role: "error",
          retryMessage: query,
        };
        setMessages((prev) => [...prev, errorMessage]);
      } else {
        const errorMessage: Message = {
          id: crypto.randomUUID(),
          content: "Ocurrió un error inesperado. Por favor intentá de nuevo.",
          role: "error",
          retryMessage: query,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    }
  };

  const handleSend = async (retryMessage?: string) => {
    const query = retryMessage || input.trim();
    if (!query || loading) return;

    if (!retryMessage) {
      const userMessage: Message = {
        id: crypto.randomUUID(),
        content: query,
        role: "user",
      };
      setMessages((prev) => [...prev, userMessage]);
      setInput("");
    }

    setLoading(true);
    setStreaming(true);
    setConnectionError(false);

    const assistantId = crypto.randomUUID();

    // Placeholder message that gets filled as tokens arrive
    const placeholder: Message = {
      id: assistantId,
      content: "",
      role: "assistant",
      sources: [],
    };
    setMessages((prev) => [...prev, placeholder]);

    try {
      const stream = await fetchApiStream("/chat/stream", {
        method: "POST",
        body: JSON.stringify({
          query,
          mode,
        }),
      });

      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;

          const dataStr = line.slice(6);

          if (dataStr === "[DONE]") {
            // Stream complete — message is already fully accumulated
            break;
          }

          try {
            const data = JSON.parse(dataStr);

            if (data.token !== undefined) {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantId
                    ? { ...msg, content: msg.content + data.token }
                    : msg
                )
              );
            }

            if (data.sources !== undefined) {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantId
                    ? { ...msg, sources: data.sources }
                    : msg
                )
              );
            }
          } catch {
            // Ignore malformed JSON lines
          }
        }
      }
    } catch (error) {
      console.warn("Streaming failed, falling back to non-streaming:", error);

      // Remove the incomplete streaming message
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantId));

      // Fall back to the non-streaming endpoint
      await fallbackToNonStreaming(query);
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleModeChange = (newMode: Mode) => {
    setMode(newMode);
  };

  return (
    <div className="flex flex-col h-full w-full max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
            KineIA
          </h2>
          {connectionError && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
              <AlertCircle className="w-3 h-3" />
              Sin conexión
            </span>
          )}
        </div>
        <ModeSelector currentMode={mode} onModeChange={handleModeChange} />
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 mb-4 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
              <span className="text-2xl">🧠</span>
            </div>
            <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-1">
              Bienvenido a KineIA
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm">
              Consultame sobre kinesiología, anatomía, fisioterapia o protocolos clínicos.
              Seleccioná el modo de aprendizaje arriba para empezar.
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id}>
              <MessageBubble
                content={msg.content}
                role={msg.role === "error" ? "assistant" : msg.role}
                sources={msg.sources}
              />
              {msg.role === "error" && msg.retryMessage && (
                <button
                  onClick={() => handleSend(msg.retryMessage)}
                  disabled={loading}
                  className="mt-2 ml-2 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                >
                  <RefreshCw className="w-3 h-3" />
                  Reintentar
                </button>
              )}
            </div>
          ))
        )}

        {/* Streaming indicator — shows while tokens are arriving */}
        {streaming && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-slate-800 rounded-2xl px-4 py-2 shadow-sm border border-slate-200 dark:border-slate-700">
              <span className="inline-flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <Pencil className="w-3.5 h-3.5 animate-pulse" />
                KineIA está escribiendo...
              </span>
            </div>
          </div>
        )}

        {/* Spinner — only shown during non-streaming fallback */}
        {loading && !streaming && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-slate-800 rounded-2xl px-4 py-3 shadow-sm border border-slate-200 dark:border-slate-700">
              <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="px-4 py-3 border-t border-slate-200 dark:border-slate-700">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribí tu consulta..."
              rows={1}
              className="w-full px-4 py-3 pr-12 bg-slate-100 dark:bg-slate-800 border-0 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-400 dark:focus:ring-slate-600 resize-none transition-all"
              style={{ minHeight: "48px", maxHeight: "120px" }}
            />
          </div>
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="flex items-center justify-center w-12 h-12 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-xl hover:bg-slate-800 dark:hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
