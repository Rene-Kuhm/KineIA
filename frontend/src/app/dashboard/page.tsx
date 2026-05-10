"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { MessageSquare, Clock, BarChart3, Loader2, AlertCircle, MessagesSquare, TrendingUp, ArrowRight } from "lucide-react";
import { fetchApi, APIError } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message?: string;
}

interface DashboardStats {
  total_conversations: number;
  total_messages: number;
  most_used_areas: { area: string; count: number }[];
}

interface HistoryResponse {
  data?: {
    conversations?: Conversation[];
    stats?: DashboardStats;
  };
  conversations?: Conversation[];
  stats?: DashboardStats;
}

export default function DashboardPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);

    try {
      const response: HistoryResponse = await fetchApi("/chat/history");

      // Handle different response shapes
      const convos = response.data?.conversations || response.conversations || [];
      const s = response.data?.stats || response.stats || null;

      setConversations(convos);
      setStats(s);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.userMessage);
      } else {
        setError("No se pudo cargar el historial.");
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString("es-AR", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  const formatTime = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleTimeString("es-AR", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 dark:bg-slate-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">
            Dashboard
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Resumen de tu actividad en KineIA
          </p>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
          </div>
        )}

        {/* Error state */}
        {!loading && error && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-14 h-14 mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <AlertCircle className="w-7 h-7 text-red-500 dark:text-red-400" />
            </div>
            <p className="text-slate-600 dark:text-slate-400 mb-4">{error}</p>
            <button
              onClick={loadHistory}
              className="px-4 py-2 rounded-lg bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors text-sm font-medium"
            >
              Reintentar
            </button>
          </div>
        )}

        {/* Stats Cards */}
        {!loading && !error && stats && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <StatCard
              icon={MessageSquare}
              label="Conversaciones"
              value={stats.total_conversations}
              color="blue"
            />
            <StatCard
              icon={MessagesSquare}
              label="Mensajes"
              value={stats.total_messages}
              color="emerald"
            />
            <StatCard
              icon={BarChart3}
              label="Áreas consultadas"
              value={stats.most_used_areas?.length || 0}
              color="violet"
            />
          </div>
        )}

        {/* Most Used Areas */}
        {!loading && !error && stats && stats.most_used_areas?.length > 0 && (
          <div className="mb-8">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
              <TrendingUp className="w-4 h-4" />
              Áreas más consultadas
            </h2>
            <div className="flex flex-wrap gap-2">
              {stats.most_used_areas.map(({ area, count }) => (
                <span
                  key={area}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                >
                  {area}
                  <span className="text-slate-400 dark:text-slate-500">{count}</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Conversations List */}
        {!loading && !error && (
          <div>
            <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
              <Clock className="w-4 h-4" />
              Conversaciones recientes
            </h2>

            {conversations.length === 0 ? (
              <EmptyState />
            ) : (
              <div className="space-y-2">
                {conversations.map((conv) => (
                  <Link
                    key={conv.id}
                    href={`/?conversation=${conv.id}`}
                    className={cn(
                      "flex items-center justify-between p-4 rounded-xl transition-colors",
                      "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700",
                      "hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-sm"
                    )}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center shrink-0">
                        <MessageSquare className="w-4 h-4 text-slate-500 dark:text-slate-400" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                          {conv.title || "Conversación sin título"}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">
                          {conv.message_count || 0} mensajes
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0 ml-4">
                      <span className="text-xs text-slate-400 dark:text-slate-500">
                        {formatDate(conv.updated_at || conv.created_at)}
                        {(conv.updated_at || conv.created_at) && (
                          <span className="ml-1">{formatTime(conv.updated_at || conv.created_at)}</span>
                        )}
                      </span>
                      <ArrowRight className="w-4 h-4 text-slate-300 dark:text-slate-600" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  color: "blue" | "emerald" | "violet";
}) {
  const colors = {
    blue: {
      bg: "bg-blue-50 dark:bg-blue-900/20",
      icon: "text-blue-600 dark:text-blue-400",
      border: "border-blue-100 dark:border-blue-800/30",
    },
    emerald: {
      bg: "bg-emerald-50 dark:bg-emerald-900/20",
      icon: "text-emerald-600 dark:text-emerald-400",
      border: "border-emerald-100 dark:border-emerald-800/30",
    },
    violet: {
      bg: "bg-violet-50 dark:bg-violet-900/20",
      icon: "text-violet-600 dark:text-violet-400",
      border: "border-violet-100 dark:border-violet-800/30",
    },
  };

  const c = colors[color];

  return (
    <div
      className={cn(
        "flex items-center gap-4 p-4 rounded-xl border bg-white dark:bg-slate-800",
        c.border
      )}
    >
      <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", c.bg)}>
        <Icon className={cn("w-5 h-5", c.icon)} />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-900 dark:text-white">{value}</p>
        <p className="text-xs text-slate-500 dark:text-slate-400">{label}</p>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 mb-4 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
        <MessageSquare className="w-7 h-7 text-slate-400 dark:text-slate-500" />
      </div>
      <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-1">
        Sin conversaciones aún
      </h3>
      <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm mb-6">
        Cuando empieces a conversar con KineIA, tus conversaciones aparecerán acá. ¡Empezá ahora!
      </p>
      <Link
        href="/"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-sm font-medium hover:bg-slate-800 dark:hover:bg-slate-200 transition-colors"
      >
        Ir al Chat
        <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  );
}
