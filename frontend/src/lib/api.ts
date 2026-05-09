export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class APIError extends Error {
  status: number;
  detail: string;
  userMessage: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "APIError";
    this.status = status;
    this.detail = detail;
    this.userMessage = APIError.userFriendlyMessage(status, detail);
  }

  private static userFriendlyMessage(status: number, detail: string): string {
    if (status === 0 || status === undefined) {
      return "No puedo conectarme al servidor. ¿Está corriendo el backend? Revisá que Docker esté levantado.";
    }
    if (status === 401) {
      return "Tu sesión expiró. Por favor iniciá sesión de nuevo.";
    }
    if (status === 429) {
      return "Has hecho muchas consultas. Esperá un minuto antes de la próxima.";
    }
    if (status >= 500) {
      return "El servidor encontró un error interno. Intentá de nuevo en unos segundos.";
    }
    return detail || "Ocurrió un error. Por favor intentá de nuevo.";
  }
}

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  } catch (error) {
    throw new APIError(0, "Error de conexión");
  }

  if (!response.ok) {
    let detail = "Error del servidor";
    try {
      const errorBody = await response.json();
      detail = errorBody.detail || errorBody.message || detail;
    } catch {
      // Response body might not be JSON
    }
    throw new APIError(response.status, detail);
  }

  return response.json();
}
