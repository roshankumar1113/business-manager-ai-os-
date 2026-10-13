// ── Auth ─────────────────────────────────────────────────────────────────────
export interface AuthToken {
  access_token: string;
  token_type: string;
  user_id: number;
  user_name: string;
  user_email: string;
  plan: string;
}

// ── Business ─────────────────────────────────────────────────────────────────
export interface Business {
  id: number;
  name: string;
  category: string;
  sub_category?: string | null;
  currency: string;
  gstin?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  health_score: number;
  whatsapp_connected: boolean;
  created_at: string;
}

// ── Dashboard ────────────────────────────────────────────────────────────────
export interface Dashboard {
  today_sales: number;
  today_expenses: number;
  today_estimated_profit: number;
  today_orders_count: number;
  month_sales: number;
  month_expenses: number;
  month_estimated_profit: number;
  month_orders_count: number;
  receivables: number;
  pending_orders: number;
  low_stock_count: number;
  new_customers_this_month: number;
  active_projects: number;
  health_score: number;
  unread_alerts: number;
}

// ── Customer ─────────────────────────────────────────────────────────────────
export interface Customer {
  id: number;
  name: string;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  gstin?: string | null;
  notes?: string | null;
  credit_limit: number;
  total_purchased: number;
  total_paid: number;
  pending_amount: number;
  last_order_at?: string | null;
  is_active: boolean;
  created_at: string;
}

// ── Product ──────────────────────────────────────────────────────────────────
export interface Product {
  id: number;
  name: string;
  sku?: string | null;
  category?: string | null;
  description?: string | null;
  unit: string;
  purchase_price: number;
  selling_price: number;
  mrp: number;
  stock_quantity: number;
  min_stock_level: number;
  max_stock_level: number;
  gst_rate: number;
  hsn_code?: string | null;
  supplier_id?: number | null;
  warehouse_location?: string | null;
  is_active: boolean;
  created_at: string;
}

// ── Order ────────────────────────────────────────────────────────────────────
export interface Order {
  id: number;
  customer_id?: number | null;
  product_id: number;
  quantity: number;
  unit_price: number;
  mrp: number;
  discount: number;
  taxable_amount: number;
  cgst_amount: number;
  sgst_amount: number;
  gst_amount: number;
  total_amount: number;
  cost_amount: number;
  delivery_charge: number;
  amount_paid: number;
  status: string;
  channel: string;
  delivery_status: string;
  invoice_no?: string | null;
  notes?: string | null;
  created_at: string;
}

// ── Expense ──────────────────────────────────────────────────────────────────
export interface Expense {
  id: number;
  category: string;
  description: string;
  amount: number;
  payment_method: string;
  supplier_id?: number | null;
  notes?: string | null;
  created_at: string;
}

// ── Payment ──────────────────────────────────────────────────────────────────
export interface Payment {
  id: number;
  order_id?: number | null;
  customer_id?: number | null;
  amount: number;
  method: string;
  reference?: string | null;
  created_at: string;
}

// ── Supplier ─────────────────────────────────────────────────────────────────
export interface Supplier {
  id: number;
  name: string;
  phone?: string | null;
  email?: string | null;
  category?: string | null;
  gstin?: string | null;
  address?: string | null;
  city?: string | null;
  total_purchased: number;
  pending_payable: number;
  rating: number;
  notes?: string | null;
  is_active: boolean;
  created_at: string;
}

// ── Project ──────────────────────────────────────────────────────────────────
export interface Project {
  id: number;
  name: string;
  client_name: string;
  client_phone?: string | null;
  location?: string | null;
  contract_value: number;
  spent_amount: number;
  advance_received: number;
  status: string;
  start_date?: string | null;
  deadline?: string | null;
  completion_percentage: number;
  notes?: string | null;
  created_at: string;
}

// ── Quotation ────────────────────────────────────────────────────────────────
export interface Quotation {
  id: number;
  customer_id?: number | null;
  product_id: number;
  quotation_no: string;
  quantity: number;
  unit_price: number;
  discount: number;
  gst_amount: number;
  total_amount: number;
  validity_days: number;
  status: string;
  order_id?: number | null;
  created_at: string;
}

// ── Invoice ──────────────────────────────────────────────────────────────────
export interface Invoice {
  invoice_no: string;
  order_id: number;
  business_name: string;
  business_address?: string | null;
  business_gstin?: string | null;
  business_phone?: string | null;
  customer_name: string;
  customer_address?: string | null;
  customer_gstin?: string | null;
  customer_phone?: string | null;
  product_name: string;
  product_hsn?: string | null;
  quantity: number;
  unit: string;
  unit_price: number;
  discount: number;
  taxable_amount: number;
  gst_rate: number;
  cgst_amount: number;
  sgst_amount: number;
  gst_amount: number;
  delivery_charge: number;
  total_amount: number;
  amount_paid: number;
  balance_due: number;
  status: string;
  channel: string;
  invoice_date: string;
  payment_terms: string;
}

// ── Alert ────────────────────────────────────────────────────────────────────
export interface Alert {
  id: number;
  alert_type: string;
  title: string;
  message: string;
  severity: string;
  action_type?: string | null;
  is_read: boolean;
  created_at: string;
}

// ── AI ───────────────────────────────────────────────────────────────────────
export interface ActionPlanItem {
  id: number;
  type: string;
  priority: string;
  title: string;
  description: string;
  badge: string;
  action_text: string;
  action_type: string;
}

export interface HealthScore {
  score: number;
  grade: string;
  explanation: string;
  bonuses: string[];
  penalties: string[];
}

// ── WhatsApp ─────────────────────────────────────────────────────────────────
export interface WAChatMessage {
  sender: 'customer' | 'ai';
  text: string;
  action?: string;
  time?: string;
}

// ── Economic Intelligence ────────────────────────────────────────────────────
export interface Commodity {
  id: string;
  name: string;
  category: string;
  price: string;
  change: string;
  trend: string;
  impact: string;
}

export interface Tender {
  id: string;
  tender_ref?: string;
  title: string;
  department: string;
  location: string;
  state: string;
  value_lakhs: number;
  deadline: string;
  eligibility: string;
  documents?: string;
  ai_summary: string;
  source_url: string;
  category_fit?: string[];
}

export interface GovScheme {
  id: string;
  name: string;
  target: string;
  benefit: string;
  eligible_categories: string[];
  portal: string;
  deadline: string;
  ai_tip?: string;
}

export interface EconomicIntelligence {
  commodities: Commodity[];
  macro_indicators: { name: string; value: string; status: string; implication: string }[];
  schemes: GovScheme[];
  tenders: Tender[];
  disclaimer: string;
}

// ── Report ───────────────────────────────────────────────────────────────────
export interface BusinessReport {
  period: string;
  total_revenue: number;
  total_cost_of_goods: number;
  total_expenses: number;
  gross_profit: number;
  estimated_net_profit: number;
  profit_margin_pct: number;
  total_orders_count: number;
  average_order_value: number;
  total_receivables: number;
  top_selling_products: { name: string; qty: number; revenue: number }[];
  expense_breakdown: { category: string; amount: number }[];
  top_customers: { name: string; revenue: number }[];
}

// ── Search ───────────────────────────────────────────────────────────────────
export interface SearchResult {
  type: string;
  id: number;
  title: string;
  subtitle: string;
  extra?: string | null;
}
