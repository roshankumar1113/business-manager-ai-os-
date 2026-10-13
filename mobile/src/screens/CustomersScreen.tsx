import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Modal, Alert, RefreshControl, TextInput,
} from 'react-native';
import { useApp } from '../context/AppContext';
import * as api from '../services/api';
import {
  C, Card, SectionHeader, Badge, Input, PrimaryBtn, SecondaryBtn,
  SmallBtn, Loader, EmptyState, Row, Divider,
} from '../components/UI';
import { money, fmtDate, fmtDateTime, initials, statusColor } from '../utils/format';
import type { Customer, Order } from '../types';

export default function CustomersScreen() {
  const { activeBusiness, customers, products, loadBusinessData } = useApp();
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Customer | null>(null);
  const [custOrders, setCustOrders] = useState<Order[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  // Form
  const [fName, setFName] = useState('');
  const [fPhone, setFPhone] = useState('');
  const [fCity, setFCity] = useState('');
  const [fGstin, setFGstin] = useState('');
  const [fNotes, setFNotes] = useState('');
  const [busy, setBusy] = useState(false);

  const filtered = customers.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    (c.phone || '').includes(search)
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    if (activeBusiness) await loadBusinessData(activeBusiness);
    setRefreshing(false);
  }, [activeBusiness]);

  const openCustomer = async (c: Customer) => {
    setSelected(c);
    if (!activeBusiness) return;
    try {
      const os = await api.customers.orders(activeBusiness.id, c.id);
      setCustOrders(os);
    } catch { setCustOrders([]); }
  };

  const addCustomer = async () => {
    if (!fName.trim()) return Alert.alert('Required', 'Customer name is required.');
    if (!activeBusiness) return;
    setBusy(true);
    try {
      await api.customers.create(activeBusiness.id, { name: fName.trim(), phone: fPhone || undefined, city: fCity || undefined, gstin: fGstin || undefined, notes: fNotes || undefined });
      setShowAdd(false);
      setFName(''); setFPhone(''); setFCity(''); setFGstin(''); setFNotes('');
      await loadBusinessData(activeBusiness);
      Alert.alert('✅ Customer Added', `${fName.trim()} has been added to your customer list.`);
    } catch (e: any) { Alert.alert('Error', e.message); }
    finally { setBusy(false); }
  };

  const sendReminder = async (c: Customer) => {
    if (!activeBusiness || c.pending_amount <= 0) return Alert.alert('No Pending', 'This customer has no pending dues.');
    try {
      const res = await api.whatsapp.reminder(activeBusiness.id, c.name, c.pending_amount, 7);
      Alert.alert('WhatsApp Reminder Ready 📱', res.message, [
        { text: 'OK', style: 'default' },
      ]);
    } catch (e: any) { Alert.alert('Error', e.message); }
  };

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      {/* Search bar */}
      <View style={s.searchBar}>
        <Text style={s.searchIcon}>🔍</Text>
        <TextInput
          style={s.searchInput}
          placeholder="Search customers by name or phone..."
          placeholderTextColor={C.textLight}
          value={search}
          onChangeText={setSearch}
        />
        {search ? (
          <TouchableOpacity onPress={() => setSearch('')}>
            <Text style={{ color: C.textMuted, paddingHorizontal: 8, fontSize: 16 }}>×</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      <ScrollView
        contentContainerStyle={{ padding: 16, paddingBottom: 80 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />}
      >
        <SectionHeader
          title="Customer Khata"
          subtitle={`${filtered.length} of ${customers.length} customers`}
          right={
            <TouchableOpacity style={s.addBtn} onPress={() => setShowAdd(true)}>
              <Text style={s.addBtnText}>+ Add</Text>
            </TouchableOpacity>
          }
        />

        {filtered.length === 0 ? (
          <EmptyState icon="👥" title={search ? 'No customers found' : 'No customers yet'} subtitle={search ? 'Try a different name or phone' : 'Add your first customer to start tracking sales'} />
        ) : (
          filtered.map(c => (
            <TouchableOpacity key={c.id} onPress={() => openCustomer(c)} activeOpacity={0.8}>
              <Card>
                <Row>
                  <View style={s.avatar}>
                    <Text style={s.avatarText}>{initials(c.name)}</Text>
                  </View>
                  <View style={{ flex: 1, marginLeft: 12 }}>
                    <Text style={s.custName}>{c.name}</Text>
                    <Text style={s.custPhone}>{c.phone || 'No phone'} {c.city ? `• ${c.city}` : ''}</Text>
                    <Row style={{ marginTop: 4, gap: 8 }}>
                      <Text style={s.statLabel}>Purchased: <Text style={{ color: C.textMain, fontWeight: '700' }}>{money(c.total_purchased, true)}</Text></Text>
                      {c.pending_amount > 0 && (
                        <Text style={[s.statLabel, { color: C.red }]}>Due: <Text style={{ fontWeight: '800' }}>{money(c.pending_amount, true)}</Text></Text>
                      )}
                    </Row>
                  </View>
                  {c.pending_amount > 0 && (
                    <View style={s.dueBadge}>
                      <Text style={s.dueBadgeText}>DUE</Text>
                    </View>
                  )}
                </Row>
              </Card>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>

      {/* ── Customer Profile Modal ──────────────────────────────────────── */}
      <Modal visible={!!selected} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setSelected(null)}>
        {selected && (
          <ScrollView style={s.modal} contentContainerStyle={{ padding: 20 }}>
            <Row style={{ justifyContent: 'space-between', marginBottom: 20 }}>
              <Text style={s.modalTitle}>Customer Profile</Text>
              <TouchableOpacity onPress={() => setSelected(null)}>
                <Text style={{ color: C.primary, fontWeight: '700' }}>Done</Text>
              </TouchableOpacity>
            </Row>

            <Card style={{ backgroundColor: '#F0FDF4' }}>
              <Row>
                <View style={[s.avatar, { width: 56, height: 56, borderRadius: 16 }]}>
                  <Text style={[s.avatarText, { fontSize: 20 }]}>{initials(selected.name)}</Text>
                </View>
                <View style={{ flex: 1, marginLeft: 14 }}>
                  <Text style={{ fontSize: 20, fontWeight: '900', color: C.textMain }}>{selected.name}</Text>
                  <Text style={{ color: C.textMuted }}>{selected.phone || 'No phone'}</Text>
                  {selected.city && <Text style={{ color: C.textMuted, fontSize: 12 }}>{selected.city}</Text>}
                </View>
              </Row>
            </Card>

            <View style={s.statsRow}>
              <View style={s.miniStat}>
                <Text style={s.miniStatValue}>{money(selected.total_purchased, true)}</Text>
                <Text style={s.miniStatLabel}>Total Purchased</Text>
              </View>
              <View style={s.miniStat}>
                <Text style={[s.miniStatValue, { color: C.green }]}>{money(selected.total_paid, true)}</Text>
                <Text style={s.miniStatLabel}>Total Paid</Text>
              </View>
              <View style={s.miniStat}>
                <Text style={[s.miniStatValue, { color: selected.pending_amount > 0 ? C.red : C.green }]}>
                  {money(selected.pending_amount, true)}
                </Text>
                <Text style={s.miniStatLabel}>Pending Due</Text>
              </View>
            </View>

            {selected.pending_amount > 0 && (
              <PrimaryBtn
                label={`💬 Send WhatsApp Reminder (₹${money(selected.pending_amount)})`}
                onPress={() => sendReminder(selected)}
                color={C.green}
                style={{ marginBottom: 12 }}
              />
            )}

            {selected.gstin && (
              <Card>
                <Text style={s.invLabel}>GSTIN</Text>
                <Text style={{ fontWeight: '700', color: C.textMain }}>{selected.gstin}</Text>
              </Card>
            )}

            {selected.notes && (
              <Card>
                <Text style={s.invLabel}>NOTES</Text>
                <Text style={{ color: C.textMain }}>{selected.notes}</Text>
              </Card>
            )}

            <SectionHeader title="Purchase History" subtitle={`${custOrders.length} orders`} />
            {custOrders.length === 0 ? (
              <EmptyState icon="📦" title="No orders yet" />
            ) : (
              custOrders.slice(0, 10).map(o => {
                const prod = useApp().products.find(p => p.id === o.product_id);
                const sc = statusColor(o.status);
                return (
                  <Card key={o.id} style={{ padding: 12 }}>
                    <Row style={{ justifyContent: 'space-between' }}>
                      <View style={{ flex: 1 }}>
                        <Text style={{ fontWeight: '700', color: C.textMain }}>{prod?.name || 'Product'}</Text>
                        <Text style={{ fontSize: 12, color: C.textMuted }}>{fmtDate(o.created_at)} • Qty {o.quantity}</Text>
                      </View>
                      <View style={{ alignItems: 'flex-end' }}>
                        <Text style={{ fontWeight: '800', color: C.textMain }}>{money(o.total_amount)}</Text>
                        <Badge label={o.status} color={sc} bg={sc + '18'} />
                      </View>
                    </Row>
                  </Card>
                );
              })
            )}
          </ScrollView>
        )}
      </Modal>

      {/* ── Add Customer Modal ──────────────────────────────────────────── */}
      <Modal visible={showAdd} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setShowAdd(false)}>
        <ScrollView style={s.modal} contentContainerStyle={{ padding: 20 }} keyboardShouldPersistTaps="handled">
          <Row style={{ justifyContent: 'space-between', marginBottom: 20 }}>
            <Text style={s.modalTitle}>Add New Customer</Text>
            <TouchableOpacity onPress={() => setShowAdd(false)}>
              <Text style={{ color: C.red, fontWeight: '700' }}>Cancel</Text>
            </TouchableOpacity>
          </Row>
          <Input label="Customer Name *" value={fName} onChangeText={setFName} placeholder="Rajesh Kumar" />
          <Input label="Phone Number" value={fPhone} onChangeText={setFPhone} placeholder="+91 98765 43210" keyboardType="phone-pad" />
          <Input label="City" value={fCity} onChangeText={setFCity} placeholder="Bhubaneswar" />
          <Input label="GSTIN (Optional)" value={fGstin} onChangeText={setFGstin} placeholder="22AAAAA0000A1Z5" autoCapitalize="characters" />
          <Input label="Notes" value={fNotes} onChangeText={setFNotes} placeholder="Any notes about this customer..." multiline numberOfLines={3} />
          <PrimaryBtn label="Add Customer" onPress={addCustomer} loading={busy} />
        </ScrollView>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  searchBar:    { flexDirection: 'row', alignItems: 'center', backgroundColor: C.surface, margin: 12, borderRadius: 12, paddingHorizontal: 12, borderWidth: 1, borderColor: C.border },
  searchIcon:   { fontSize: 16, marginRight: 8 },
  searchInput:  { flex: 1, height: 44, fontSize: 14, color: C.textMain },
  addBtn:       { backgroundColor: C.primary, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 7 },
  addBtnText:   { color: '#fff', fontWeight: '800', fontSize: 13 },
  avatar:       { width: 44, height: 44, borderRadius: 12, backgroundColor: C.primary, alignItems: 'center', justifyContent: 'center' },
  avatarText:   { color: '#fff', fontWeight: '800', fontSize: 16 },
  custName:     { fontSize: 15, fontWeight: '800', color: C.textMain },
  custPhone:    { fontSize: 12, color: C.textMuted, marginTop: 2 },
  statLabel:    { fontSize: 11, color: C.textMuted },
  dueBadge:     { backgroundColor: C.redLight, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  dueBadgeText: { color: C.red, fontSize: 10, fontWeight: '900' },
  modal:        { flex: 1, backgroundColor: C.bg },
  modalTitle:   { fontSize: 20, fontWeight: '900', color: C.textMain },
  statsRow:     { flexDirection: 'row', gap: 8, marginBottom: 14 },
  miniStat:     { flex: 1, backgroundColor: C.surface, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  miniStatValue:{ fontSize: 16, fontWeight: '900', color: C.textMain },
  miniStatLabel:{ fontSize: 10, color: C.textMuted, marginTop: 3, textAlign: 'center' },
  invLabel:     { fontSize: 10, fontWeight: '800', color: C.textMuted, letterSpacing: 0.5, marginBottom: 6, textTransform: 'uppercase' },
});
