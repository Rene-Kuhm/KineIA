"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAdmin as checkIsAdmin } from "@/lib/auth";
import { fetchApi, APIError } from "@/lib/api";
import { Shield, FileText, Upload, Loader2, AlertCircle, BarChart3, BookOpen, Scroll, StickyNote, FileText as FileIcon, Users, Layers, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface AreaStat {
  area: string;
  count: number;
}

interface EvidenceLevelStat {
  level: string;
  count: number;
}

interface KnowledgeStats {
  total_documents: number;
  areas: AreaStat[];
  evidence_levels: EvidenceLevelStat[];
}

interface StatsResponse {
  data?: KnowledgeStats;
  total_documents?: number;
  areas?: AreaStat[];
  evidence_levels?: EvidenceLevelStat[];
}

const AREA_OPTIONS = [
  "Anatomía",
  "Fisiología",
  "Biomecánica",
  "Traumatología",
  "Neurología",
  "Deportología",
  "Cardiorrespiratorio",
  "Pediatría",
  "Geriatría",
  "Ortopedia",
  "Reumatología",
  "Oncología",
  "Uroginecología",
  "Ergonomía",
  "General",
];

const LEVELS = [
  { value: "protocol", label: "Protocolo", icon: Scroll, color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-50 dark:bg-emerald-900/20" },
  { value: "book", label: "Libro", icon: BookOpen, color: "text-blue-600 dark:text-blue-400", bg: "bg-blue-50 dark:bg-blue-900/20" },
  { value: "paper", label: "Paper", icon: FileText, color: "text-amber-600 dark:text-amber-400", bg: "bg-amber-50 dark:bg-amber-900/20" },
  { value: "notes", label: "Apuntes", icon: StickyNote, color: "text-orange-600 dark:text-orange-400", bg: "bg-orange-50 dark:bg-orange-900/20" },
];

export default function AdminPage() {
  const router = useRouter();
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [area, setArea] = useState("");
  const [level, setLevel] = useState("protocol");
  const [title, setTitle] = useState("");
  const [reviewer, setReviewer] = useState("");
  const [reviewDate, setReviewDate] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    if (!checkIsAdmin()) {
      router.replace("/");
      return;
    }
    setAuthChecked(true);
    loadStats();
  }, [router]);

  const loadStats = async () => {
    setStatsLoading(true);
    setStatsError(null);

    try {
      const response: StatsResponse = await fetchApi("/knowledge/stats");
      const data = response.data || response;
      setStats({
        total_documents: data.total_documents || 0,
        areas: data.areas || [],
        evidence_levels: data.evidence_levels || [],
      });
    } catch (err) {
      if (err instanceof APIError) {
        setStatsError(err.userMessage);
      } else {
        setStatsError("No se pudieron cargar las estadísticas.");
      }
    } finally {
      setStatsLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !area || !reviewer.trim() || !reviewDate) return;

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(false);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("area", area);
    formData.append("evidence_level", level);
    formData.append("reviewer", reviewer.trim());
    formData.append("review_date", reviewDate);
    if (title.trim()) {
      formData.append("title", title.trim());
    }

    try {
      await fetchApi("/knowledge/ingest", {
        method: "POST",
        body: formData,
      });

      setUploadSuccess(true);
      setFile(null);
      setTitle("");
      setArea("");
      setLevel("protocol");
      setReviewer("");
      setReviewDate("");

      // Reset file input
      const fileInput = document.getElementById("doc-upload") as HTMLInputElement;
      if (fileInput) fileInput.value = "";

      // Reload stats
      loadStats();

      setTimeout(() => setUploadSuccess(false), 5000);
    } catch (err) {
      if (err instanceof APIError) {
        setUploadError(err.userMessage);
      } else {
        setUploadError("Error al subir el documento.");
      }
    } finally {
      setUploading(false);
    }
  };

  // Don't render anything until auth check completes
  if (!authChecked) return null;

  const maxAreaCount = stats?.areas?.reduce((max, a) => Math.max(max, a.count), 0) || 1;

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 dark:bg-slate-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center">
            <Shield className="w-5 h-5 text-violet-600 dark:text-violet-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              Admin
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Gestión de conocimiento y usuarios
            </p>
          </div>
        </div>

        {/* Stats Section */}
        <section className="mb-8">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
            <BarChart3 className="w-4 h-4" />
            Estadísticas del Conocimiento
          </h2>

          {statsLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
            </div>
          )}

          {!statsLoading && statsError && (
            <div className="flex flex-col items-center py-12 text-center">
              <AlertCircle className="w-6 h-6 text-red-500 dark:text-red-400 mb-2" />
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-3">{statsError}</p>
              <button
                onClick={loadStats}
                className="px-3 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-sm hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors"
              >
                Reintentar
              </button>
            </div>
          )}

          {!statsLoading && !statsError && stats && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {/* Total documents card */}
              <div className="flex items-center gap-4 p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                <div className="w-10 h-10 rounded-lg bg-violet-50 dark:bg-violet-900/20 flex items-center justify-center">
                  <Layers className="w-5 h-5 text-violet-600 dark:text-violet-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900 dark:text-white">
                    {stats.total_documents}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Documentos</p>
                </div>
              </div>

              {/* Areas breakdown */}
              <div className="md:col-span-2 p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
                  Por Área
                </h3>
                {stats.areas.length === 0 ? (
                  <p className="text-sm text-slate-400 dark:text-slate-500 py-2">
                    Sin documentos
                  </p>
                ) : (
                  <div className="space-y-2">
                    {stats.areas.map((a) => (
                      <div key={a.area} className="flex items-center gap-2">
                        <span className="text-xs text-slate-600 dark:text-slate-400 w-28 truncate" title={a.area}>
                          {a.area}
                        </span>
                        <div className="flex-1 h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-violet-500 dark:bg-violet-400 transition-all duration-500"
                            style={{ width: `${(a.count / maxAreaCount) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400 w-6 text-right">
                          {a.count}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Evidence level breakdown */}
          {!statsLoading && !statsError && stats && stats.evidence_levels.length > 0 && (
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 mb-6">
              <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
                Por Nivel de Evidencia
              </h3>
              <div className="flex flex-wrap gap-3">
                {stats.evidence_levels.map((el) => {
                  const config = LEVELS.find((l) => l.value === el.level);
                  const IconComponent = config?.icon || FileIcon;
                  return (
                    <div
                      key={el.level}
                      className={cn(
                        "flex items-center gap-2 px-3 py-2 rounded-lg",
                        config?.bg || "bg-slate-100 dark:bg-slate-700/50"
                      )}
                    >
                      <IconComponent className={cn("w-4 h-4", config?.color || "text-slate-500")} />
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        {config?.label || el.level}
                      </span>
                      <span className="text-sm text-slate-500 dark:text-slate-400">{el.count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </section>

        {/* Document Upload Form */}
        <section className="mb-8">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
            <Upload className="w-4 h-4" />
            Subir Documento
          </h2>

          <form
            onSubmit={handleUpload}
            className="p-6 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-4"
          >
            {/* File input */}
            <div>
              <label htmlFor="doc-upload" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                Archivo
              </label>
              <input
                id="doc-upload"
                type="file"
                accept=".pdf,.txt,.md,.markdown"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-slate-500 dark:text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-slate-100 dark:file:bg-slate-700 file:text-slate-700 dark:file:text-slate-300 hover:file:bg-slate-200 dark:hover:file:bg-slate-600 file:transition-colors file:cursor-pointer cursor-pointer"
              />
              {file && (
                <p className="mt-1.5 text-xs text-slate-400 dark:text-slate-500">
                  {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </p>
              )}
            </div>

            {/* Title */}
            <div>
              <label htmlFor="doc-title" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                Título <span className="text-slate-400">(opcional)</span>
              </label>
              <input
                id="doc-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Ej: Manual de anatomía funcional"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-400 dark:focus:ring-violet-600 text-sm"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="doc-reviewer" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                  Profesional revisor/a *
                </label>
                <input
                  id="doc-reviewer"
                  type="text"
                  value={reviewer}
                  onChange={(e) => setReviewer(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-400 dark:focus:ring-violet-600 text-sm"
                />
              </div>
              <div>
                <label htmlFor="doc-review-date" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                  Fecha de revisión *
                </label>
                <input
                  id="doc-review-date"
                  type="date"
                  value={reviewDate}
                  onChange={(e) => setReviewDate(e.target.value)}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-400 dark:focus:ring-violet-600 text-sm"
                />
              </div>
            </div>

            {/* Area select */}
            <div>
              <label htmlFor="doc-area" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                Área *
              </label>
              <select
                id="doc-area"
                value={area}
                onChange={(e) => setArea(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-400 dark:focus:ring-violet-600 text-sm"
              >
                <option value="" disabled>
                  Seleccioná un área...
                </option>
                {AREA_OPTIONS.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </div>

            {/* Evidence level */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                Nivel de Evidencia
              </label>
              <div className="flex flex-wrap gap-2">
                {LEVELS.map(({ value, label, icon: IconComponent, color, bg }) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setLevel(value)}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors border",
                      level === value
                        ? cn(bg, color, "border-current/20")
                        : "border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50"
                    )}
                  >
                    <IconComponent className="w-3.5 h-3.5" />
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit */}
            <div className="flex items-center gap-3 pt-2">
              <button
                type="submit"
                disabled={!file || !area || !reviewer.trim() || !reviewDate || uploading}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                  "bg-violet-600 dark:bg-violet-500 text-white hover:bg-violet-700 dark:hover:bg-violet-600",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Subiendo...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Subir Documento
                  </>
                )}
              </button>

              {uploadError && (
                <span className="text-sm text-red-600 dark:text-red-400">{uploadError}</span>
              )}

              {uploadSuccess && (
                <span className="flex items-center gap-1 text-sm text-emerald-600 dark:text-emerald-400">
                  <CheckCircle className="w-4 h-4" />
                  Documento subido correctamente
                </span>
              )}
            </div>
          </form>
        </section>

        {/* Users Section (placeholder) */}
        <section>
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
            <Users className="w-4 h-4" />
            Usuarios
          </h2>
          <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-center">
            <div className="w-10 h-10 mx-auto mb-3 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center">
              <Users className="w-5 h-5 text-slate-400 dark:text-slate-500" />
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              La gestión de usuarios estará disponible próximamente.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
