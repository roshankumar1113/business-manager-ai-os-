/** Formatting utilities for the Business Manager app */

export const money = (n: number, compact = false): string => {
  if (compact) {
    if (n >= 10_00_000) return `₹${(n / 10_00_000).toFixed(1)}L`;
    if (n >= 1_000) return `₹${(n / 1_000).toFixed(0)}K`;
  }
  return '₹' + (n || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });
};

export const fmtDate = (iso: string): string => {
  try {
    return new Date(iso).toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
    });
  } catch { return iso; }
};

export const fmtTime = (iso: string): string => {
  try {
    return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  } catch { return ''; }
};

export const fmtDateTime = (iso: string): string => `${fmtDate(iso)} ${fmtTime(iso)}`;

export const initials = (name: string): string =>
  name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase();

export const statusColor = (status: string): string => ({
  paid: '#10B981',
  partially_paid: '#F59E0B',
  pending: '#EF4444',
  cancelled: '#6B7280',
  delivered: '#10B981',
  dispatched: '#3B82F6',
  'In Progress': '#3B82F6',
  Completed: '#10B981',
  Planning: '#8B5CF6',
}[status] ?? '#6B7280');

export const categoryIcon = (cat: string): string => ({
  Construction: '🏗️',
  Agriculture: '🌾',
  Retail: '🏪',
  Wholesale: '📦',
  Manufacturing: '🏭',
  Restaurant: '🍽️',
  Pharmacy: '💊',
  Transport: '🚛',
  School: '🏫',
  Other: '🏢',
}[cat] ?? '🏢');

export const channelIcon = (ch: string): string => ({
  whatsapp: '💬',
  voice: '🎤',
  app: '📱',
  walk_in: '🚶',
  phone: '📞',
}[ch] ?? '📱');

export const severityColor = (s: string) => ({
  critical: '#EF4444',
  warning: '#F59E0B',
  info: '#3B82F6',
  success: '#10B981',
}[s] ?? '#6B7280');
