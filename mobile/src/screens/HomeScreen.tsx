import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Alert, RefreshControl, Modal,
} from 'react-native';
import { useApp } from '../context/AppContext';
import * as api from '../services/api';
import {
  C, Card, StatCard, SectionHeader, Badge, SmallBtn, Loader, EmptyState, Row,
} from '../components/UI';
import { money, fmtDate, categoryIcon, statusColor } from '../utils/format';
import type { HealthScore } from '../types';

type Props = { onTabChange?: (t: string) => void };

export default function HomeScreen({ onTabChange }: Props) {
  const { activeBusiness, dashboard, actionPlan, loadingData, refreshDashboard, loadBusinessData } = useApp();
  const [healthData, setHealthData] = useState<HealthScore | null>(null);
  const [showHealth, setShowHealth] = useState(false);
  const [healthLoading, setHealthLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    if (activeBusiness) await loadBusinessData(activeBusiness);
    setRefreshing(false);
  }, [activeBusiness]);

  const loadHealthScore = async () => {
    if (!activeBusiness) return;
    setHealthLoading(true);
    try {
      const h = await api.ai.healthScore(activeBusiness.id);
      setHealthData(h);
      setShowHealth(true);
    } catch (e: any) {
      Alert.alert('AI Error', e.message);
    } finally { setHealthLoading(false); }
  };

  if (loadingData && !dashboard) return <Loader text="Loading your business..." />;

  const score = dashboard?.health_score ?? activeBusiness?.health_score ?? 85;
  const healthColor = score >= 85 ? C.green : score >= 70 ? C.amber : C.red;

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: C.bg }}
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />}
    >
      {/* ── Business Health Score ─────────────────────────────────────── */}
      <Card style={{ marginBottom: 4 }}>
        <Row style={{ justifyContent: 'space-between', marginBottom: 8 }}>
          <View>
            <Text style={s.healthLabel}>AI BUSINESS HEALTH SCORE</Text>
            <Row style={{ alignItems: 'baseline', gap: 6, marginTop: 2 }}>
              <Text style={[s.healthScore, { color: healthColor }]}>{score}</Text>
              <Text style={s.healthOutOf}>/100</Text>
              <Badge
                label={score >= 85 ? 'Excellent' : score >= 70 ? 'Good' : 'Needs Attention'}
                color={healthColor}
                bg={healthColor + '18'}
              />
            </Row>
          </View>
          <SmallBtn
            label={healthLoading ? '...' : '✦ Why?'}
            onPress={loadHealthScore}
            color={C.primary}
          />
        </Row>
        <View style={s.healthBarBg}>
          <View style={[s.healthBarFill, { width: `${score}%` as any, backgroundColor: healthColor }]} />
        </View>
        {dashboard?.unread_alerts ? (
          <TouchableOpacity onPress={() => onTabChange?.('Alerts')} style={s.alertBanner}>
            <Text style={s.alertBannerText}>🔔 {dashboard.unread_alerts} new alert{dashboard.unread_alerts > 1 ? 's' : ''} — tap to view</Text>
          </TouchableOpacity>
        ) : null}
      </Card>

      {/* ── Today's Stats ─────────────────────────────────────────────── */}
      <SectionHeader title="Today's Business" subtitle={new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })} />
      <View style={s.statsGrid}>
        <StatCard label="TODAY SALES"   value={money(dashboard?.today_sales ?? 0, true)}   color={C.green}  sub={`${dashboard?.today_orders_count ?? 0} orders`} />
        <StatCard label="TODAY PROFIT"  value={money(dashboard?.today_estimated_profit ?? 0, true)} color={C.green} sub="Estimated" />
        <StatCard label="RECEIVABLES"   value={money(dashboard?.receivables ?? 0, true)}    color={C.amber}  sub="Pending collection" />
        <StatCard label="TODAY EXPENSE" value={money(dashboard?.today_expenses ?? 0, true)} color={C.red}    sub="Transport, Labour" />
      </View>

      {/* ── Monthly Overview ──────────────────────────────────────────── */}
      <SectionHeader title="This Month" />
      <View style={s.statsGrid}>
        <StatCard label="MONTHLY SALES"  value={money(dashboard?.month_sales ?? 0, true)} color={C.blue} sub={`${dashboard?.month_orders_count ?? 0} orders`} />
        <StatCard label="MONTHLY PROFIT" value={money(dashboard?.month_estimated_profit ?? 0, true)} color={C.green} sub="After all costs" />
        <StatCard label="LOW STOCK"      value={String(dashboard?.low_stock_count ?? 0)}  color={C.red}  sub="Items to reorder" onPress={() => onTabChange?.('Inventory')} />
        <StatCard label="NEW CUSTOMERS"  value={String(dashboard?.new_customers_this_month ?? 0)} color={C.purple} sub="This month" />
      </View>

      {/* ── AI Action Plan ────────────────────────────────────────────── */}
      <SectionHeader
        title="What Should I Do Today?"
        subtitle="AI-powered action plan"
        right={<Badge label="✦ AI" color={C.purple} bg={C.purpleLight} />}
      />
      {actionPlan.length === 0 ? (
        <EmptyState icon="✦" title="Loading action plan..." subtitle="AI is analysing your business data" />
      ) : (
        actionPlan.map(item => (
          <ActionCard key={item.id} item={item} bizId={activeBusiness?.id ?? 0} onTabChange={onTabChange} />
        ))
      )}

      {/* ── Quick Shortcuts ───────────────────────────────────────────── */}
      <SectionHeader title="Quick Actions" />
      <View style={s.quickGrid}>
        {[
          { icon: '📦', label: 'New Order',      tab: 'Orders' },
          { icon: '👥', label: 'Customers',       tab: 'Customers' },
          { icon: '🏭', label: 'Inventory',       tab: 'Inventory' },
          { icon: '💬', label: 'WhatsApp',        tab: 'WhatsApp' },
          { icon: '🤖', label: 'Ask AI',          tab: 'AI' },
          { icon: '📈', label: 'Intelligence',    tab: 'Intelligence' },
        ].map(q => (
          <TouchableOpacity key={q.tab} style={s.quickTile} onPress={() => onTabChange?.(q.tab)}>
            <Text style={s.quickIcon}>{q.icon}</Text>
            <Text style={s.quickLabel}>{q.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* ── Health Score Modal ────────────────────────────────────────── */}
      <Modal visible={showHealth} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setShowHealth(false)}>
        <View style={s.modal}>
          <Row style={{ justifyContent: 'space-between', marginBottom: 20 }}>
            <Text style={s.modalTitle}>Business Health Analysis</Text>
            <TouchableOpacity onPress={() => setShowHealth(false)}>
              <Text style={{ color: C.primary, fontWeight: '700', fontSize: 16 }}>Done</Text>
            </TouchableOpacity>
          </Row>
          {healthData && (
            <>
              <Row style={{ justifyContent: 'center', marginBottom: 16 }}>
                <Text style={[s.healthScore, { color: healthColor, fontSize: 64 }]}>{healthData.score}</Text>
                <Text style={[s.healthOutOf, { fontSize: 24 }]}>/100 — {healthData.grade}</Text>
              </Row>
              <Card style={{ backgroundColor: '#F0FDF4' }}>
                <Text style={s.geminiLabel}>✦ GEMINI 2.5 FLASH DIAGNOSTIC</Text>
                <Text style={s.explanationText}>{healthData.explanation}</Text>
              </Card>
              {healthData.bonuses.length > 0 && (
                <Card>
                  <Text style={[s.geminiLabel, { color: C.green }]}>✅ STRENGTHS</Text>
                  {healthData.bonuses.map((b, i) => <Text key={i} style={s.listItem}>• {b}</Text>)}
                </Card>
              )}
              {healthData.penalties.length > 0 && (
                <Card>
                  <Text style={[s.geminiLabel, { color: C.red }]}>⚠️ RISKS TO ADDRESS</Text>
                  {healthData.penalties.map((p, i) => <Text key={i} style={s.listItem}>• {p}</Text>)}
                </Card>
              )}
            </>
          )}
        </View>
      </Modal>
    </ScrollView>
  );
}

function ActionCard({ item, bizId, onTabChange }: { item: any; bizId: number; onTabChange?: (t: string) => void }) {
  const priorityColor = { critical: C.red, high: C.amber, medium: C.blue, low: C.green }[item.priority] ?? C.blue;
  return (
    <Card style={{ borderLeftWidth: 4, borderLeftColor: priorityColor }}>
      <Row style={{ marginBottom: 8 }}>
        <Badge label={item.badge} color={priorityColor} bg={priorityColor + '18'} />
        <View style={{ flex: 1 }} />
        <Text style={{ fontSize: 10, color: C.textLight, fontWeight: '700', textTransform: 'uppercase' }}>
          #{item.id}
        </Text>
      </Row>
      <Text style={s.actionTitle}>{item.title}</Text>
      <Text style={s.actionDesc}>{item.description}</Text>
      <TouchableOpacity
        style={[s.actionBtn, { backgroundColor: priorityColor }]}
        onPress={() => {
          if (item.action_type === 'whatsapp_reminder') onTabChange?.('WhatsApp');
          else if (item.action_type === 'reorder_stock') onTabChange?.('Inventory');
          else if (item.action_type === 'view_tenders') onTabChange?.('Intelligence');
          else if (item.action_type === 'view_mandi') onTabChange?.('Intelligence');
          else if (item.action_type === 'view_expenses') onTabChange?.('Expenses');
          else onTabChange?.('AI');
        }}
      >
        <Text style={s.actionBtnText}>{item.action_text} →</Text>
      </TouchableOpacity>
    </Card>
  );
}

const s = StyleSheet.create({
  healthLabel:    { fontSize: 10, fontWeight: '800', color: C.textMuted, letterSpacing: 0.5, textTransform: 'uppercase' },
  healthScore:    { fontSize: 40, fontWeight: '900', color: C.green },
  healthOutOf:    { fontSize: 16, color: C.textMuted, fontWeight: '600', alignSelf: 'flex-end', marginBottom: 6 },
  healthBarBg:    { height: 8, backgroundColor: C.border, borderRadius: 4, marginTop: 10 },
  healthBarFill:  { height: 8, borderRadius: 4 },
  alertBanner:    { marginTop: 10, backgroundColor: C.amberLight, borderRadius: 8, padding: 8 },
  alertBannerText:{ fontSize: 12, color: C.amber, fontWeight: '700', textAlign: 'center' },
  statsGrid:      { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: -4, marginBottom: 8 },
  quickGrid:      { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 8 },
  quickTile:      { width: '30%', backgroundColor: C.surface, borderRadius: 14, padding: 14, alignItems: 'center', borderWidth: 1, borderColor: C.border, elevation: 1 },
  quickIcon:      { fontSize: 26, marginBottom: 6 },
  quickLabel:     { fontSize: 11, fontWeight: '700', color: C.textMuted },
  actionTitle:    { fontSize: 15, fontWeight: '800', color: C.textMain, marginBottom: 4 },
  actionDesc:     { fontSize: 13, color: C.textMuted, lineHeight: 18, marginBottom: 12 },
  actionBtn:      { borderRadius: 8, paddingVertical: 8, paddingHorizontal: 14, alignSelf: 'flex-start' },
  actionBtnText:  { color: '#fff', fontWeight: '800', fontSize: 12 },
  modal:          { flex: 1, padding: 20, backgroundColor: C.bg },
  modalTitle:     { fontSize: 20, fontWeight: '900', color: C.textMain },
  geminiLabel:    { fontSize: 10, fontWeight: '900', letterSpacing: 0.5, marginBottom: 8, color: C.textMuted, textTransform: 'uppercase' },
  explanationText:{ fontSize: 14, color: C.textMain, lineHeight: 22 },
  listItem:       { fontSize: 13, color: C.textMain, marginBottom: 4 },
});
