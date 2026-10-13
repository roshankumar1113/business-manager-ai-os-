/**
 * Business Manager AI OS — Root App Component
 * Navigation, business switcher, tab bar, global header.
 */
import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet,
  Modal, ScrollView, Alert, ActivityIndicator,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';

import { AppProvider, useApp } from './src/context/AppContext';
import { C, Row } from './src/components/UI';
import { categoryIcon } from './src/utils/format';

import AuthScreen       from './src/screens/AuthScreen';
import HomeScreen       from './src/screens/HomeScreen';
import OrdersScreen     from './src/screens/OrdersScreen';
import CustomersScreen  from './src/screens/CustomersScreen';
import InventoryScreen  from './src/screens/InventoryScreen';
import AIScreen         from './src/screens/AIScreen';
import WhatsAppScreen   from './src/screens/WhatsAppScreen';
import IntelligenceScreen from './src/screens/IntelligenceScreen';

type Tab = 'Home' | 'Orders' | 'Customers' | 'Inventory' | 'AI' | 'WhatsApp' | 'Intelligence';

const TABS: { id: Tab; icon: string; label: string }[] = [
  { id: 'Home',          icon: '🏠', label: 'Home' },
  { id: 'Orders',        icon: '📦', label: 'Orders' },
  { id: 'Customers',     icon: '👥', label: 'Customers' },
  { id: 'Inventory',     icon: '🏭', label: 'Inventory' },
  { id: 'AI',            icon: '🤖', label: 'AI' },
  { id: 'WhatsApp',      icon: '💬', label: 'WhatsApp' },
  { id: 'Intelligence',  icon: '📈', label: 'Intel' },
];

// ── Inner app (rendered after login) ────────────────────────────────────────
function MainApp() {
  const { activeBusiness, businesses, setActiveBusiness, logout, userName, loadingData } = useApp();
  const [tab, setTab] = useState<Tab>('Home');
  const [showSwitcher, setShowSwitcher] = useState(false);

  if (!activeBusiness) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: C.bg }}>
        <ActivityIndicator size="large" color={C.primary} />
        <Text style={{ marginTop: 12, color: C.textMuted }}>Loading your businesses...</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      {/* ── Top Header ─────────────────────────────────────────────── */}
      <SafeAreaView edges={['top']} style={{ backgroundColor: C.primaryDark }}>
        <View style={s.header}>
          {/* Business selector */}
          <TouchableOpacity style={s.bizSelector} onPress={() => setShowSwitcher(true)}>
            <Text style={s.bizIcon}>{categoryIcon(activeBusiness.category)}</Text>
            <View style={{ flex: 1 }}>
              <Text style={s.bizCategory}>{activeBusiness.category.toUpperCase()} • BUSINESS MANAGER</Text>
              <Row style={{ alignItems: 'center', gap: 4 }}>
                <Text style={s.bizName} numberOfLines={1}>{activeBusiness.name}</Text>
                <Text style={{ color: '#A7F3D0', fontSize: 11 }}>▼</Text>
              </Row>
            </View>
          </TouchableOpacity>

          {/* Right: health score + avatar */}
          <Row style={{ gap: 10 }}>
            <View style={s.healthPill}>
              <Text style={s.healthPillText}>{activeBusiness.health_score}</Text>
              <Text style={s.healthPillLabel}>Health</Text>
            </View>
            <TouchableOpacity
              style={s.avatar}
              onPress={() => Alert.alert(
                `👤 ${userName}`,
                'Manage your account',
                [
                  { text: 'Cancel', style: 'cancel' },
                  { text: 'Sign Out', style: 'destructive', onPress: logout },
                ]
              )}
            >
              <Text style={s.avatarText}>{(userName || 'U')[0].toUpperCase()}</Text>
            </TouchableOpacity>
          </Row>
        </View>
      </SafeAreaView>

      {/* ── Screen Content ─────────────────────────────────────────── */}
      <View style={{ flex: 1 }}>
        {tab === 'Home'          && <HomeScreen         onTabChange={t => setTab(t as Tab)} />}
        {tab === 'Orders'        && <OrdersScreen />}
        {tab === 'Customers'     && <CustomersScreen />}
        {tab === 'Inventory'     && <InventoryScreen />}
        {tab === 'AI'            && <AIScreen />}
        {tab === 'WhatsApp'      && <WhatsAppScreen />}
        {tab === 'Intelligence'  && <IntelligenceScreen />}
      </View>

      {/* ── Bottom Tab Bar ──────────────────────────────────────────── */}
      <SafeAreaView edges={['bottom']} style={{ backgroundColor: C.surface }}>
        <View style={s.tabBar}>
          {TABS.map(t => (
            <TouchableOpacity
              key={t.id}
              style={[s.tabItem, tab === t.id && s.tabItemActive]}
              onPress={() => setTab(t.id)}
              activeOpacity={0.7}
            >
              <Text style={s.tabIcon}>{t.icon}</Text>
              <Text style={[s.tabLabel, tab === t.id && s.tabLabelActive]}>{t.label}</Text>
              {tab === t.id && <View style={s.tabActiveDot} />}
            </TouchableOpacity>
          ))}
        </View>
      </SafeAreaView>

      {/* ── Business Switcher Modal ────────────────────────────────── */}
      <Modal visible={showSwitcher} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setShowSwitcher(false)}>
        <View style={{ flex: 1, backgroundColor: C.bg }}>
          <View style={s.switcherHeader}>
            <Text style={s.switcherTitle}>Switch Business</Text>
            <TouchableOpacity onPress={() => setShowSwitcher(false)}>
              <Text style={{ color: C.primary, fontWeight: '700' }}>Done</Text>
            </TouchableOpacity>
          </View>
          <ScrollView contentContainerStyle={{ padding: 16 }}>
            {businesses.map(b => (
              <TouchableOpacity
                key={b.id}
                style={[s.switcherItem, b.id === activeBusiness.id && s.switcherItemActive]}
                onPress={() => { setActiveBusiness(b); setShowSwitcher(false); }}
              >
                <Text style={{ fontSize: 32 }}>{categoryIcon(b.category)}</Text>
                <View style={{ flex: 1, marginLeft: 14 }}>
                  <Text style={s.switcherBizName}>{b.name}</Text>
                  <Text style={s.switcherBizCat}>{b.category}</Text>
                </View>
                <View style={s.switcherHealthPill}>
                  <Text style={s.switcherHealthText}>{b.health_score}/100</Text>
                </View>
                {b.id === activeBusiness.id && <Text style={{ color: C.primary, fontWeight: '900', marginLeft: 8 }}>✓</Text>}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

// ── Root (auth gate) ─────────────────────────────────────────────────────────
function RootNavigator() {
  const { token } = useApp();
  return token ? <MainApp /> : <AuthScreen />;
}

// ── App entry ────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <SafeAreaProvider>
      <ExpoStatusBar style="light" />
      <AppProvider>
        <RootNavigator />
      </AppProvider>
    </SafeAreaProvider>
  );
}

const s = StyleSheet.create({
  header:      { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14, paddingVertical: 10, gap: 10 },
  bizSelector: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 10 },
  bizIcon:     { fontSize: 26 },
  bizCategory: { fontSize: 9, color: '#A7F3D0', fontWeight: '700', letterSpacing: 0.5 },
  bizName:     { fontSize: 16, fontWeight: '900', color: '#fff', maxWidth: 180 },
  healthPill:  { backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 10, paddingHorizontal: 10, paddingVertical: 5, alignItems: 'center' },
  healthPillText: { fontSize: 16, fontWeight: '900', color: '#fff' },
  healthPillLabel:{ fontSize: 9, color: '#A7F3D0', fontWeight: '700' },
  avatar:      { width: 36, height: 36, borderRadius: 10, backgroundColor: '#10B981', alignItems: 'center', justifyContent: 'center' },
  avatarText:  { color: '#fff', fontWeight: '900', fontSize: 16 },
  tabBar:      { flexDirection: 'row', borderTopWidth: 1, borderTopColor: C.border, backgroundColor: C.surface, paddingBottom: 2 },
  tabItem:     { flex: 1, alignItems: 'center', paddingVertical: 8, position: 'relative' },
  tabItemActive:{ backgroundColor: C.greenLight + '60' },
  tabIcon:     { fontSize: 20, marginBottom: 2 },
  tabLabel:    { fontSize: 9, color: C.textMuted, fontWeight: '600' },
  tabLabelActive: { color: C.primary, fontWeight: '800' },
  tabActiveDot:{ position: 'absolute', bottom: 0, width: 20, height: 2.5, backgroundColor: C.primary, borderRadius: 2 },
  switcherHeader:{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 20, borderBottomWidth: 1, borderBottomColor: C.border },
  switcherTitle: { fontSize: 20, fontWeight: '900', color: C.textMain },
  switcherItem:  { flexDirection: 'row', alignItems: 'center', backgroundColor: C.surface, borderRadius: 14, padding: 16, marginBottom: 10, borderWidth: 1.5, borderColor: C.border },
  switcherItemActive: { borderColor: C.primary, backgroundColor: C.greenLight + '40' },
  switcherBizName:   { fontSize: 16, fontWeight: '800', color: C.textMain },
  switcherBizCat:    { fontSize: 12, color: C.textMuted, marginTop: 2 },
  switcherHealthPill:{ backgroundColor: C.blueLight, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4 },
  switcherHealthText:{ fontSize: 12, fontWeight: '800', color: C.blue },
});
