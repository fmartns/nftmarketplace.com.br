const envBase = (import.meta as any).env?.VITE_API_BASE_URL as string | undefined;
export const API_BASE: string = envBase || 'https://api.nftmarketplace.com.br';

export type HttpParams = Record<string, string | number | boolean | undefined | null>;

export function buildQuery(params?: HttpParams): string {
  if (!params) return '';
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '');
  if (entries.length === 0) return '';
  const qp = new URLSearchParams();
  for (const [k, v] of entries) {
    qp.append(k, String(v));
  }
  return `?${qp.toString()}`;
}

export async function getJson<T>(path: string, params?: HttpParams, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}${buildQuery(params)}`;
  const defaultHeaders: HeadersInit = {
    'Accept': 'application/json',
  };
  const mergedHeaders: HeadersInit = {
    ...defaultHeaders,
    ...(init?.headers || {}),
  };
  const res = await fetch(url, {
    ...init,
    method: 'GET',
    headers: mergedHeaders,
  });
  if (!res.ok) {
    const text = await res.text();
    let errorData: any = null;
    try {
      errorData = JSON.parse(text);
    } catch {
      // Se não for JSON, usa o texto como está
    }
    const error = new Error(`GET ${path} failed: ${res.status} ${text}`);
    (error as any).status = res.status;
    (error as any).response = errorData || text;
    throw error;
  }
  return res.json() as Promise<T>;
}

export async function postJson<T>(path: string, body: any, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const mergedHeaders: HeadersInit = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    ...(init?.headers || {}),
  };
  const res = await fetch(url, {
    ...init,
    method: 'POST',
    headers: mergedHeaders,
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    let errorMessage = `POST ${path} failed: ${res.status}`;
    let errorData: any = null;
    try {
      const text = await res.text();
      try {
        errorData = JSON.parse(text);
      } catch {
        errorMessage = text || errorMessage;
        const error = new Error(errorMessage);
        (error as any).status = res.status;
        throw error;
      }
      
      // Handle validation errors (e.g., {"nick_habbo": ["message"]})
      if (typeof errorData === 'object' && errorData !== null) {
        const errors: string[] = [];
        for (const [key, value] of Object.entries(errorData)) {
          if (Array.isArray(value)) {
            errors.push(...value.map(v => String(v)));
          } else if (typeof value === 'string') {
            errors.push(value);
          } else if (key === 'detail') {
            errors.push(String(value));
          }
        }
        if (errors.length > 0) {
          errorMessage = errors.join(' ');
        } else {
          errorMessage = text;
        }
      } else {
        errorMessage = String(errorData);
      }
    } catch (e: any) {
      if (e.message && !e.message.includes('failed:')) {
        throw e;
      }
    }
    const error = new Error(errorMessage);
    (error as any).status = res.status;
    (error as any).response = errorData;
    throw error;
  }
  return res.json() as Promise<T>;
}

export async function putJson<T>(path: string, body: any, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const mergedHeaders: HeadersInit = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    ...(init?.headers || {}),
  };
  const res = await fetch(url, {
    ...init,
    method: 'PUT',
    headers: mergedHeaders,
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    let errorMessage = `PUT ${path} failed: ${res.status}`;
    let errorData: any = null;
    try {
      const text = await res.text();
      try {
        errorData = JSON.parse(text);
      } catch {
        errorMessage = text || errorMessage;
        const error = new Error(errorMessage);
        (error as any).status = res.status;
        throw error;
      }
      
      if (typeof errorData === 'object' && errorData !== null) {
        const errors: string[] = [];
        for (const [key, value] of Object.entries(errorData)) {
          if (Array.isArray(value)) {
            errors.push(...value.map(v => String(v)));
          } else if (typeof value === 'string') {
            errors.push(value);
          } else if (key === 'detail') {
            errors.push(String(value));
          }
        }
        if (errors.length > 0) {
          errorMessage = errors.join(' ');
        } else {
          errorMessage = text;
        }
      } else {
        errorMessage = String(errorData);
      }
    } catch (e: any) {
      if (e.message && !e.message.includes('failed:')) {
        throw e;
      }
    }
    const error = new Error(errorMessage);
    (error as any).status = res.status;
    (error as any).response = errorData;
    throw error;
  }
  return res.json() as Promise<T>;
}

export async function patchJson<T>(path: string, body: any, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const mergedHeaders: HeadersInit = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    ...(init?.headers || {}),
  };
  const res = await fetch(url, {
    ...init,
    method: 'PATCH',
    headers: mergedHeaders,
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    let errorMessage = `PATCH ${path} failed: ${res.status}`;
    let errorData: any = null;
    try {
      const text = await res.text();
      try {
        errorData = JSON.parse(text);
      } catch {
        errorMessage = text || errorMessage;
        const error = new Error(errorMessage);
        (error as any).status = res.status;
        throw error;
      }
      
      if (typeof errorData === 'object' && errorData !== null) {
        const errors: string[] = [];
        for (const [key, value] of Object.entries(errorData)) {
          if (Array.isArray(value)) {
            errors.push(...value.map(v => String(v)));
          } else if (typeof value === 'string') {
            errors.push(value);
          } else if (key === 'detail') {
            errors.push(String(value));
          }
        }
        if (errors.length > 0) {
          errorMessage = errors.join(' ');
        } else {
          errorMessage = text;
        }
      } else {
        errorMessage = String(errorData);
      }
    } catch (e: any) {
      if (e.message && !e.message.includes('failed:')) {
        throw e;
      }
    }
    const error = new Error(errorMessage);
    (error as any).status = res.status;
    (error as any).response = errorData;
    throw error;
  }
  return res.json() as Promise<T>;
}
