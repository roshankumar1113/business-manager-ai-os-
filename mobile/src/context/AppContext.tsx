/**
 * Global app context — auth state, active business, shared data.
 */
import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import type { Business, Dashboard, Customer, Product, Order, ActionPlanItem } from '../types';
import * as api from '../services/api';

interface AppState {
  // Auth
  token: string;
  userId: number | null;
  userName: string;
  userEmail: string;
  plan: string;
  // Business
  businesses: Business[];
  activeBusiness: Business | null;
  // Business data
  dashboard: Dashboard | null;
  customers: Customer[];
  products: Product[];
  orders: Order[];
  actionPlan: ActionPlanItem[];
  // Loading flags
  loadingData: boolean;
  // Actions
  login: (token: string, userId: number, name: string, email: string, plan: string) => void;
  logout: () => void;
  setActiveBusiness: (b: Business) => void;
  loadBusinesses: () => Promise<void>;
  loadBusinessData: (b: Business) => Promise<void>;
  refreshDashboard: () => Promise<void>;
}

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState('');
  const [userId, setUserId] = useState<number | null>(null);
  const [userName, setUserName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [plan, setPlan] = useState('free');
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [activeBusiness, setActiveBusinessState] = useState<Business | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [actionPlan, setActionPlan] = useState<ActionPlanItem[]>([]);
  const [loadingData, setLoadingData] = useState(false);

  const login = useCallback((t: string, uid: number, name: string, email: string, p: string) => {
    api.setToken(t);
    setToken(t); setUserId(uid); setUserName(name); setUserEmail(email); setPlan(p);
  }, []);

  const logout = useCallback(() => {
    api.clearToken();
    setToken(''); setUserId(null); setUserName(''); setUserEmail(''); setPlan('free');
    setBusinesses([]); setActiveBusinessState(null);
    setDashboard(null); setCustomers([]); setProducts([]); setOrders([]);
  }, []);

  const loadBusinesses = useCallback(async () => {
    try {
      const list = await api.businesses.list();
      setBusinesses(list);
      if (list.length && !activeBusiness) setActiveBusinessState(list[0]);
    } catch (e) { console.warn('loadBusinesses:', e); }
  }, [activeBusiness]);

  const loadBusinessData = useCallback(async (b: Business) => {
    setLoadingData(true);
    try {
      const [d, c, p, o, ap] = await Promise.allSettled([
        api.dashboard.get(b.id),
        api.customers.list(b.id),
        api.products.list(b.id),
        api.orders.list(b.id),
        api.ai.actionPlan(b.id),
      ]);
      if (d.status === 'fulfilled') setDashboard(d.value);
      if (c.status === 'fulfilled') setCustomers(c.value);
      if (p.status === 'fulfilled') setProducts(p.value);
      if (o.status === 'fulfilled') setOrders(o.value);
      if (ap.status === 'fulfilled') setActionPlan(ap.value);
    } finally { setLoadingData(false); }
  }, []);

  const setActiveBusiness = useCallback((b: Business) => {
    setActiveBusinessState(b);
  }, []);

  const refreshDashboard = useCallback(async () => {
    if (!activeBusiness) return;
    try {
      const d = await api.dashboard.get(activeBusiness.id);
      setDashboard(d);
    } catch (e) { console.warn('refreshDashboard:', e); }
  }, [activeBusiness]);

  useEffect(() => {
    if (token) loadBusinesses();
  }, [token]);

  useEffect(() => {
    if (token && activeBusiness) loadBusinessData(activeBusiness);
  }, [token, activeBusiness?.id]);

  return (
    <Ctx.Provider value={{
      token, userId, userName, userEmail, plan,
      businesses, activeBusiness, dashboard, customers, products, orders, actionPlan,
      loadingData,
      login, logout, setActiveBusiness, loadBusinesses, loadBusinessData, refreshDashboard,
    }}>
      {children}
    </Ctx.Provider>
  );
}

export const useApp = (): AppState => {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useApp must be inside AppProvider');
  return ctx;
};
