import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Modal, Alert, RefreshControl, Linking, ActivityIndicator,
} from 'react-native';
import { useApp } from '../context/AppContext';
import * as api from '../services/api';
import { C, Card, SectionHeader, Badge, Row, SmallBtn, Loader, Divider } from '../components/UI';
import type { EconomicIntelligence, Tender, GovScheme } from '../types';

type Tab = 'market' | 'tenders' | 'schemes';

export default function IntelligenceScreen() {
  const { activeBusiness } = useApp();
  const [tab, setTab] = useState<Tab>('market');
  const [data, setData] = useState<EconomicIntelligence | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTender, setSelectedTender] = useState<Tender | null>(null);
  const [marketAnalysis, setMarketAnalysis] = useState('');
  const [analysisLoading, setAnalysisLoading] = useState(false);

  const load = useCallback(async () => {
    if (!activeBusiness) return;
    try {
      const d = await api.intelligence.get(activeBusiness.id);
      setData(d);
    } catch (e: any) {
      Alert.alert('Error', e.message);
    } finally { setLoading(false); setRefreshing(false); }
  }, [activeBusiness]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = () => { setRefreshing(true); load(); };

  const getMarketAnalysis = async () => {
    if (!activeBusiness) return;
    setAnalysisLoading(true);
    try {
      const res = await api.intelligence.marketImpact(activeBusiness.id);
      setMarketAnalysis(res.analysis);
    } catch (e: any) { setMarketAnalysis(`Error: ${e.message}`); }
    finally { setAnalysisLoading(false); }
  };

  const openUrl = (url: string) => {
    Linking.openURL(url.startsWith('http') ? url : `https://${url}`).catch(() =>
      Alert.alert('Cannot open', `Please visit: ${url}`)
    );
  };

  if (loading) return <Loader text="Loading market intelligence..." />;

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      {/* Tabs */}
      <View style={s.tabBar}>
        {(['market', 'tenders', 'schemes'] as Tab[]).map(t => (
          <TouchableOpacity key={t} style={[s.tab, tab === t && s.tabActive]} onPress={() => setTab(t)}>
            <Text style={[s.tabText, tab === t && s.tabTextActive]}>
              {t === 'market' ? '📈 Market' : t === 'tenders' ? '📑 Tenders' : '🏛️ Schemes'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView
        contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />}
      >
        {/* ── Market Tab ─────────────────────────────────────────────── */}
        {tab === 'market' && data && (
          <>
            <SectionHeader title="Market Intelligence" subtitle="Live commodity & economic data" />

            {/* AI Market Impact */}
            <Card style={{ borderLeftWidth: 4, borderLeftColor: C.purple }}>
              <Row style={{ justifyContent: 'space-between', marginBottom: 8 }}>
                <Text style={s.cardTitle}>✦ AI Market Impact Analysis</Text>
                <SmallBtn label={analysisLoading ? '...' : 'Ask AI'} onPress={getMarketAnalysis} color={C.purple} />
              </Row>
              {analysisLoading ? (
                <Row style={{ gap: 8 }}>
                  <ActivityIndicator size="small" color={C.purple} />
                  <Text style={{ color: C.textMuted }}>Analysing market impact for your business...</Text>
                </Row>
              ) : marketAnalysis ? (
                <Text style={s.analysisText}>{marketAnalysis}</Text>
              ) : (
                <Text style={{ color: C.textMuted, fontSize: 13 }}>
                  Tap "Ask AI" to get a personalised analysis of how current market conditions affect your {activeBusiness?.category} business.
                </Text>
              )}
              <Text style={s.disclaimer}>⚠️ AI analysis for planning only — verify from official sources before decisions.</Text>
            </Card>

            <SectionHeader title="Commodity Prices" subtitle="Indicative benchmark rates" />
            {data.commodities.map((c, i) => (
              <Card key={i} style={{ padding: 12 }}>
                <Row style={{ justifyContent: 'space-between' }}>
                  <View style={{ flex: 1 }}>
                    <Text style={s.commName}>{c.name}</Text>
                    <Text style={s.commImpact}>{c.impact}</Text>
                  </View>
                  <View style={{ alignItems: 'flex-end' }}>
                    <Text style={s.commPrice}>{c.price}</Text>
                    <Badge
                      label={c.change}
                      color={c.trend === 'up' ? C.red : c.trend === 'down' ? C.green : C.textMuted}
                      bg={c.trend === 'up' ? C.redLight : c.trend === 'down' ? C.greenLight : C.border}
                    />
                  </View>
                </Row>
              </Card>
            ))}

            <SectionHeader title="Macro Indicators" />
            {data.macro_indicators.map((m, i) => (
              <Card key={i} style={{ padding: 12 }}>
                <Row style={{ justifyContent: 'space-between', marginBottom: 4 }}>
                  <Text style={s.macroName}>{m.name}</Text>
                  <Text style={s.macroValue}>{m.value}</Text>
                </Row>
                <Row style={{ justifyContent: 'space-between' }}>
                  <Badge label={m.status} color={C.blue} bg={C.blueLight} />
                  <Text style={s.macroImpl}>{m.implication}</Text>
                </Row>
              </Card>
            ))}

            <Text style={s.disclaimerFull}>{data.disclaimer}</Text>
          </>
        )}

        {/* ── Tenders Tab ────────────────────────────────────────────── */}
        {tab === 'tenders' && data && (
          <>
            <SectionHeader
              title="Government Tenders"
              subtitle={`${data.tenders.length} opportunities for ${activeBusiness?.category}`}
            />
            <Card style={{ backgroundColor: C.blueLight, marginBottom: 8 }}>
              <Text style={[s.cardTitle, { color: C.blue }]}>ℹ️ About Tender Intelligence</Text>
              <Text style={{ fontSize: 12, color: C.blue, lineHeight: 18 }}>
                These tenders are curated based on your business category. Always verify details from the official source URL before applying. Deadlines and values are indicative.
              </Text>
            </Card>
            {data.tenders.length === 0 ? (
              <View style={s.emptyState}>
                <Text style={{ fontSize: 40 }}>📑</Text>
                <Text style={s.emptyTitle}>No tenders for {activeBusiness?.category}</Text>
              </View>
            ) : (
              data.tenders.map(t => (
                <TouchableOpacity key={t.id} onPress={() => setSelectedTender(t)} activeOpacity={0.8}>
                  <Card>
                    <Row style={{ marginBottom: 8 }}>
                      <View style={[s.tenderValueBadge, { backgroundColor: C.blue + '18' }]}>
                        <Text style={[s.tenderValue, { color: C.blue }]}>₹{t.value_lakhs}L</Text>
                      </View>
                      <View style={{ flex: 1, marginLeft: 10 }}>
                        <Text style={s.tenderTitle} numberOfLines={2}>{t.title}</Text>
                        <Text style={s.tenderDept}>{t.department}</Text>
                      </View>
                    </Row>
                    <Row style={{ justifyContent: 'space-between' }}>
                      <Badge label={`📍 ${t.location}`} color={C.textMuted} bg={C.border} />
                      <Badge label={`⏰ ${t.deadline}`} color={C.amber} bg={C.amberLight} />
                    </Row>
                    <Divider />
                    <Text style={s.aiSummary} numberOfLines={2}>{t.ai_summary}</Text>
                    <Row style={{ justifyContent: 'flex-end', marginTop: 8 }}>
                      <SmallBtn label="View Details →" onPress={() => setSelectedTender(t)} color={C.blue} />
                    </Row>
                  </Card>
                </TouchableOpacity>
              ))
            )}
          </>
        )}

        {/* ── Schemes Tab ───────────────────────────────────────────── */}
        {tab === 'schemes' && data && (
          <>
            <SectionHeader title="Government Schemes" subtitle="MSME & sector-specific benefits" />
            {data.schemes.map(scheme => (
              <Card key={scheme.id}>
                <Row style={{ marginBottom: 8 }}>
                  <View style={s.schemeBadge}>
                    <Text style={{ fontSize: 20 }}>🏛️</Text>
                  </View>
                  <View style={{ flex: 1, marginLeft: 10 }}>
                    <Text style={s.schemeName}>{scheme.name}</Text>
                    <Text style={s.schemeTarget}>{scheme.target}</Text>
                  </View>
                </Row>
                <View style={s.benefitBox}>
                  <Text style={s.benefitLabel}>BENEFIT</Text>
                  <Text style={s.benefitText}>{scheme.benefit}</Text>
                </View>
                {scheme.ai_tip && (
                  <View style={s.aiTipBox}>
                    <Text style={s.aiTipText}>✦ {scheme.ai_tip}</Text>
                  </View>
                )}
                <Row style={{ justifyContent: 'space-between', marginTop: 10 }}>
                  <Badge label={`📅 ${scheme.deadline}`} color={C.textMuted} bg={C.border} />
                  <TouchableOpacity onPress={() => openUrl(scheme.portal)} style={s.portalBtn}>
                    <Text style={s.portalBtnText}>🌐 {scheme.portal} ↗</Text>
                  </TouchableOpacity>
                </Row>
              </Card>
            ))}
          </>
        )}
      </ScrollView>

      {/* ── Tender Detail Modal ─────────────────────────────────────── */}
      <Modal visible={!!selectedTender} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setSelectedTender(null)}>
        {selectedTender && (
          <ScrollView style={s.modal} contentContainerStyle={{ padding: 20 }}>
            <Row style={{ justifyContent: 'space-between', marginBottom: 20 }}>
              <Badge label="GOVERNMENT TENDER" color={C.blue} bg={C.blueLight} />
              <TouchableOpacity onPress={() => setSelectedTender(null)}>
                <Text style={{ color: C.primary, fontWeight: '700' }}>Close</Text>
              </TouchableOpacity>
            </Row>
            <Text style={s.tenderDetailTitle}>{selectedTender.title}</Text>
            <Text style={s.tenderDeptDetail}>{selectedTender.department}</Text>

            <View style={s.tenderMetaGrid}>
              {[
                { label: 'Value', value: `₹${selectedTender.value_lakhs} Lakhs`, color: C.blue },
                { label: 'Deadline', value: selectedTender.deadline, color: C.amber },
                { label: 'Location', value: selectedTender.location, color: C.textMain },
                { label: 'State', value: selectedTender.state, color: C.textMain },
              ].map((m, i) => (
                <View key={i} style={s.tenderMeta}>
                  <Text style={s.tenderMetaLabel}>{m.label}</Text>
                  <Text style={[s.tenderMetaValue, { color: m.color }]}>{m.value}</Text>
                </View>
              ))}
            </View>

            <Card style={{ backgroundColor: '#EFF6FF' }}>
              <Text style={[s.fieldLabel, { color: C.blue }]}>AI SUMMARY</Text>
              <Text style={{ fontSize: 14, color: C.textMain, lineHeight: 22 }}>{selectedTender.ai_summary}</Text>
            </Card>

            <Card>
              <Text style={s.fieldLabel}>ELIGIBILITY</Text>
              <Text style={{ color: C.textMain }}>{selectedTender.eligibility}</Text>
            </Card>

            {selectedTender.documents && (
              <Card>
                <Text style={s.fieldLabel}>DOCUMENTS REQUIRED</Text>
                <Text style={{ color: C.textMain }}>{selectedTender.documents}</Text>
              </Card>
            )}

            <Card style={{ backgroundColor: C.amberLight }}>
              <Text style={[s.fieldLabel, { color: C.amber }]}>⚠️ IMPORTANT NOTICE</Text>
              <Text style={{ fontSize: 12, color: C.amber, lineHeight: 18 }}>
                Always verify tender details from the official source before applying. Deadlines, values, and eligibility may have changed. Do not rely solely on this summary for application decisions.
              </Text>
            </Card>

            <TouchableOpacity style={s.officialBtn} onPress={() => openUrl(selectedTender.source_url)}>
              <Text style={s.officialBtnText}>🌐 View Official Tender Notice ↗</Text>
            </TouchableOpacity>
          </ScrollView>
        )}
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  tabBar:     { flexDirection: 'row', backgroundColor: C.surface, borderBottomWidth: 1, borderBottomColor: C.border },
  tab:        { flex: 1, paddingVertical: 12, alignItems: 'center' },
  tabActive:  { borderBottomWidth: 2.5, borderBottomColor: C.primary },
  tabText:    { fontSize: 13, fontWeight: '600', color: C.textMuted },
  tabTextActive:{ color: C.primary, fontWeight: '800' },
  cardTitle:  { fontSize: 14, fontWeight: '800', color: C.textMain, flex: 1 },
  analysisText:{ fontSize: 14, color: C.textMain, lineHeight: 22 },
  disclaimer: { fontSize: 11, color: C.amber, marginTop: 8, fontStyle: 'italic' },
  disclaimerFull: { fontSize: 11, color: C.textLight, textAlign: 'center', marginTop: 16, lineHeight: 16 },
  commName:   { fontSize: 13, fontWeight: '700', color: C.textMain, flex: 1 },
  commImpact: { fontSize: 11, color: C.textMuted, marginTop: 2 },
  commPrice:  { fontSize: 14, fontWeight: '800', color: C.textMain, marginBottom: 4 },
  macroName:  { fontSize: 13, fontWeight: '700', color: C.textMain, flex: 1 },
  macroValue: { fontSize: 14, fontWeight: '900', color: C.blue },
  macroImpl:  { fontSize: 11, color: C.textMuted, flex: 1, textAlign: 'right' },
  tenderValueBadge:{ width: 52, height: 52, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  tenderValue:{ fontSize: 13, fontWeight: '900' },
  tenderTitle:{ fontSize: 13, fontWeight: '800', color: C.textMain },
  tenderDept: { fontSize: 11, color: C.textMuted, marginTop: 2 },
  aiSummary:  { fontSize: 12, color: C.textMuted, lineHeight: 18 },
  emptyState: { alignItems: 'center', paddingVertical: 40 },
  emptyTitle: { color: C.textMuted, fontSize: 15, marginTop: 12 },
  schemeBadge:{ width: 44, height: 44, borderRadius: 12, backgroundColor: C.blueLight, alignItems: 'center', justifyContent: 'center' },
  schemeName: { fontSize: 14, fontWeight: '800', color: C.textMain },
  schemeTarget:{ fontSize: 11, color: C.textMuted, marginTop: 2 },
  benefitBox: { backgroundColor: C.greenLight, borderRadius: 8, padding: 10, marginTop: 8 },
  benefitLabel:{ fontSize: 9, fontWeight: '900', color: C.green, letterSpacing: 0.5 },
  benefitText:{ fontSize: 13, color: C.textMain, marginTop: 4, lineHeight: 19 },
  aiTipBox:   { backgroundColor: '#F5F3FF', borderRadius: 8, padding: 8, marginTop: 6 },
  aiTipText:  { fontSize: 12, color: C.purple, lineHeight: 18 },
  portalBtn:  { backgroundColor: C.blueLight, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 5 },
  portalBtnText:{ fontSize: 11, color: C.blue, fontWeight: '700' },
  modal:      { flex: 1, backgroundColor: C.bg },
  tenderDetailTitle: { fontSize: 18, fontWeight: '900', color: C.textMain, marginBottom: 6 },
  tenderDeptDetail:  { fontSize: 13, color: C.textMuted, marginBottom: 16 },
  tenderMetaGrid:    { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
  tenderMeta:        { width: '47%', backgroundColor: C.surface, borderRadius: 10, padding: 10, borderWidth: 1, borderColor: C.border },
  tenderMetaLabel:   { fontSize: 9, fontWeight: '800', color: C.textMuted, letterSpacing: 0.5 },
  tenderMetaValue:   { fontSize: 14, fontWeight: '900', marginTop: 4 },
  fieldLabel:        { fontSize: 10, fontWeight: '800', color: C.textMuted, letterSpacing: 0.5, marginBottom: 6, textTransform: 'uppercase' },
  officialBtn:       { backgroundColor: C.blue, borderRadius: 12, padding: 14, alignItems: 'center', marginTop: 8 },
  officialBtnText:   { color: '#fff', fontWeight: '900', fontSize: 14 },
});
