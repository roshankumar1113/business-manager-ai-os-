/**
 * Business Manager — API Service Layer
 * Typed fetch wrapper for all backend endpoints.
 */
import { API_BASE_URL } from '../config';
import type {
  AuthToken, Business, Dashboard, Customer, Product, Order,
  Expense, Payment, Supplier, Project, Quotation, Invoice,
  Alert, ActionPlanItem, HealthScore, EconomicIntelligence,
  BusinessReport, SearchResult, WAChatMessage,
} from '../types';

// ── Core fetch wrapper ───────────────────────────────────────────────────────
let _token = '';

export const setToken = (t: string) => { _token = t; };
export const clearToken = () => { _token = ''; };

async function request<T>(
  path: string,
  method = 'GET',
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (_token) headers['Authorization'] = `Bearer ${_token}`;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = (data as any)?.detail || `Request failed (${res.status})`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data as T;
}

const get  = <T>(path: string)                  => request<T>(path, 'GET');
const post = <T>(path: string, body?: unknown)  => request<T>(path, 'POST', body);
const put  = <T>(path: string, body?: unknown)  => request<T>(path, 'PUT',  body);
const del  = <T>(path: string)                  => request<T>(path, 'DELETE');

// ── Auth ─────────────────────────────────────────────────────────────────────
export const auth = {
  register: (name: string, email: string, password: string, phone?: string) =>
    post<AuthToken>('/auth/register', { name, email, password, phone }),
  login: (email: string, password: string) =>
    post<AuthToken>('/auth/login', { email, password }),
  me: () => get<any>('/auth/me'),
  changePassword: (current_password: string, new_password: string) =>
    post<any>('/auth/change-password', { current_password, new_password }),
};

// ── Businesses ───────────────────────────────────────────────────────────────
export const businesses = {
  list: () => get<Business[]>('/businesses'),
  create: (data: Partial<Business>) => post<Business>('/businesses', data),
  get: (id: number) => get<Business>(`/businesses/${id}`),
  update: (id: number, data: Partial<Business>) => put<Business>(`/businesses/${id}`, data),
  overview: () => get<any>('/overview'),
};

// ── Dashboard ────────────────────────────────────────────────────────────────
export const dashboard = {
  get: (bizId: number) => get<Dashboard>(`/businesses/${bizId}/dashboard`),
};

// ── Customers ────────────────────────────────────────────────────────────────
export const customers = {
  list: (bizId: number, q?: string) =>
    get<Customer[]>(`/businesses/${bizId}/customers${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  create: (bizId: number, data: Partial<Customer>) =>
    post<Customer>(`/businesses/${bizId}/customers`, data),
  get: (bizId: number, id: number) =>
    get<Customer>(`/businesses/${bizId}/customers/${id}`),
  update: (bizId: number, id: number, data: Partial<Customer>) =>
    put<Customer>(`/businesses/${bizId}/customers/${id}`, data),
  delete: (bizId: number, id: number) =>
    del<any>(`/businesses/${bizId}/customers/${id}`),
  orders: (bizId: number, id: number) =>
    get<Order[]>(`/businesses/${bizId}/customers/${id}/orders`),
};

// ── Products ─────────────────────────────────────────────────────────────────
export const products = {
  list: (bizId: number, params?: { q?: string; category?: string; low_stock_only?: boolean }) => {
    const qs = new URLSearchParams();
    if (params?.q) qs.set('q', params.q);
    if (params?.category) qs.set('category', params.category);
    if (params?.low_stock_only) qs.set('low_stock_only', 'true');
    const s = qs.toString();
    return get<Product[]>(`/businesses/${bizId}/products${s ? `?${s}` : ''}`);
  },
  create: (bizId: number, data: Partial<Product>) =>
    post<Product>(`/businesses/${bizId}/products`, data),
  get: (bizId: number, id: number) =>
    get<Product>(`/businesses/${bizId}/products/${id}`),
  update: (bizId: number, id: number, data: Partial<Product>) =>
    put<Product>(`/businesses/${bizId}/products/${id}`, data),
  delete: (bizId: number, id: number) =>
    del<any>(`/businesses/${bizId}/products/${id}`),
  adjustStock: (bizId: number, id: number, quantity_change: number, reason?: string) =>
    post<any>(`/businesses/${bizId}/products/${id}/adjust-stock`, { quantity_change, reason }),
  intelligence: (bizId: number) =>
    get<any>(`/businesses/${bizId}/inventory/intelligence`),
};

// ── Orders ───────────────────────────────────────────────────────────────────
export const orders = {
  list: (bizId: number, params?: { status?: string; channel?: string }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set('status', params.status);
    if (params?.channel) qs.set('channel', params.channel);
    const s = qs.toString();
    return get<Order[]>(`/businesses/${bizId}/orders${s ? `?${s}` : ''}`);
  },
  create: (bizId: number, data: {
    product_id: number; quantity: number; customer_id?: number;
    discount?: number; delivery_charge?: number; amount_paid?: number;
    channel?: string; notes?: string;
  }) => post<Order>(`/businesses/${bizId}/orders`, data),
  get: (bizId: number, id: number) => get<Order>(`/businesses/${bizId}/orders/${id}`),
  updateStatus: (bizId: number, id: number, status: string, amount_paid?: number, delivery_status?: string) =>
    put<any>(`/businesses/${bizId}/orders/${id}/status`, { status, amount_paid, delivery_status }),
  invoice: (bizId: number, id: number) => get<Invoice>(`/businesses/${bizId}/orders/${id}/invoice`),
};

// ── Expenses ─────────────────────────────────────────────────────────────────
export const expenses = {
  list: (bizId: number, category?: string) =>
    get<Expense[]>(`/businesses/${bizId}/expenses${category ? `?category=${category}` : ''}`),
  create: (bizId: number, data: Partial<Expense>) =>
    post<Expense>(`/businesses/${bizId}/expenses`, data),
  delete: (bizId: number, id: number) =>
    del<any>(`/businesses/${bizId}/expenses/${id}`),
};

// ── Payments ─────────────────────────────────────────────────────────────────
export const payments = {
  list: (bizId: number) => get<Payment[]>(`/businesses/${bizId}/payments`),
  record: (bizId: number, data: Partial<Payment>) =>
    post<Payment>(`/businesses/${bizId}/payments`, data),
};

// ── Suppliers ────────────────────────────────────────────────────────────────
export const suppliers = {
  list: (bizId: number) => get<Supplier[]>(`/businesses/${bizId}/suppliers`),
  create: (bizId: number, data: Partial<Supplier>) =>
    post<Supplier>(`/businesses/${bizId}/suppliers`, data),
  update: (bizId: number, id: number, data: Partial<Supplier>) =>
    put<Supplier>(`/businesses/${bizId}/suppliers/${id}`, data),
  delete: (bizId: number, id: number) =>
    del<any>(`/businesses/${bizId}/suppliers/${id}`),
};

// ── Projects ─────────────────────────────────────────────────────────────────
export const projects = {
  list: (bizId: number) => get<Project[]>(`/businesses/${bizId}/projects`),
  create: (bizId: number, data: Partial<Project>) =>
    post<Project>(`/businesses/${bizId}/projects`, data),
  update: (bizId: number, id: number, data: Partial<Project>) =>
    put<Project>(`/businesses/${bizId}/projects/${id}`, data),
  delete: (bizId: number, id: number) =>
    del<any>(`/businesses/${bizId}/projects/${id}`),
};

// ── Quotations ───────────────────────────────────────────────────────────────
export const quotations = {
  list: (bizId: number) => get<Quotation[]>(`/businesses/${bizId}/quotations`),
  create: (bizId: number, data: { product_id: number; quantity: number; customer_id?: number; discount?: number; validity_days?: number }) =>
    post<Quotation>(`/businesses/${bizId}/quotations`, data),
  convert: (bizId: number, id: number) =>
    post<any>(`/businesses/${bizId}/quotations/${id}/convert`),
};

// ── Alerts ───────────────────────────────────────────────────────────────────
export const alerts = {
  list: (bizId: number, unread_only = false) =>
    get<Alert[]>(`/businesses/${bizId}/alerts${unread_only ? '?unread_only=true' : ''}`),
  markRead: (bizId: number, id: number) =>
    post<any>(`/businesses/${bizId}/alerts/${id}/read`),
  markAllRead: (bizId: number) =>
    post<any>(`/businesses/${bizId}/alerts/read-all`),
};

// ── AI ───────────────────────────────────────────────────────────────────────
export const ai = {
  query: (bizId: number, q: string) =>
    get<{ answer: string; context: any; source: string }>(`/businesses/${bizId}/ai/query?q=${encodeURIComponent(q)}`),
  actionPlan: (bizId: number) =>
    get<ActionPlanItem[]>(`/businesses/${bizId}/ai/action-plan`),
  healthScore: (bizId: number) =>
    get<HealthScore>(`/businesses/${bizId}/ai/health-score`),
  recommendations: (bizId: number) =>
    get<any[]>(`/businesses/${bizId}/ai/recommendations`),
};

// ── WhatsApp ─────────────────────────────────────────────────────────────────
export const whatsapp = {
  simulate: (bizId: number, customer_phone: string, customer_name: string, message_text: string) =>
    post<any>(`/businesses/${bizId}/whatsapp/simulate`, { customer_phone, customer_name, message_text }),
  chats: (bizId: number) => get<any[]>(`/businesses/${bizId}/whatsapp/chats`),
  reminder: (bizId: number, customer_name: string, pending_amount: number, days_overdue: number) =>
    post<any>(`/businesses/${bizId}/whatsapp/reminder`, { customer_name, pending_amount, days_overdue }),
};

// ── Economic Intelligence ────────────────────────────────────────────────────
export const intelligence = {
  get: (bizId: number) => get<EconomicIntelligence>(`/businesses/${bizId}/intelligence`),
  marketImpact: (bizId: number) => get<any>(`/businesses/${bizId}/intelligence/market-impact`),
};

// ── Reports ──────────────────────────────────────────────────────────────────
export const reports = {
  summary: (bizId: number, period: 'today' | 'week' | 'month' | 'year' = 'month') =>
    get<BusinessReport>(`/businesses/${bizId}/reports/summary?period=${period}`),
};

// ── Search ───────────────────────────────────────────────────────────────────
export const search = {
  global: (bizId: number, q: string) =>
    get<SearchResult[]>(`/businesses/${bizId}/search?q=${encodeURIComponent(q)}`),
};
