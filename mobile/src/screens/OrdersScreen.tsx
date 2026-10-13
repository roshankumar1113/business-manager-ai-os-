import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Modal, Alert, RefreshControl, FlatList,
} from 'react-native';
import { useApp } from '../context/AppContext';
import * as api from '../services/api';
import {
  C, Card, SectionHeader, Badge, Input, PrimaryBtn, SecondaryBtn,
  SmallBtn, Loader, EmptyState, Row, Divider,
} from '../components/UI';
import { money, fmtDate, fmtDateTime, channelIcon, statusColor } from '../utils/format';
import type { Order, Invoice } from '../types';

export default function OrdersScreen() {
  const { activeBusiness, products, customers, orders, loadBusinessData } = useApp();
  const [filter, setFilter] = useState<'all' | 'pending' | 'paid'>('all');
  const [showCreate, setShowCreate] = useState(false);
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  // Create order form
  const [selProduct, setSelProduct] = useState('');
  const [selCustomer, setSelCustomer] = useState('');
  const [qty, setQty] = useState('1');
  const [discount, setDiscount] = useState('0');
  const [amtPaid, setAmtPaid] = useState('');
  const [channel, setChannel] = useState('app');
  const [busy, setBusy] = useState(false);

  const filtered = orders.filter(o =>
    filter === 'all' ? true : filter === 'pending' ? o.status === 'pending' || o.status === 'partially_paid' : o.status === 'paid'
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    if (activeBusiness) await loadBusinessData(activeBusiness);
    setRefreshing(false);
  }, [activeBusiness]);

  const openInvoice = async (orderId: number) => {
    if (!activeBusiness) return;
    try {
      const inv = await api.orders.invoice(activeBusiness.id, orderId);
      setInvoice(inv);
    } catch (e: any) { Alert.alert('Error', e.message); }
  };

  const createOrder = async () => {
    if (!activeBusiness || !selProduct || !qty) return Alert.alert('Required', 'Select product and enter quantity.');
    const prod = products.find(p => String(p.id) === selProduct);
    if (!prod) return;
    setBusy(true);
    try {
      await api.orders.create(activeBusiness.id, {
        product_id: prod.id,
        quantity: parseFloat(qty) || 1,
        customer_id: selCustomer ? parseInt(selCustomer) : undefined,
        discount: parseFloat(discount) || 0,
        amount_paid: amtPaid ? parseFloat(amtPaid) : 0,
        channel,
      });
      setShowCreate(false);
      setSelProduct(''); setSelCustomer(''); setQty('1'); setDiscount('0'); setAmtPaid('');
      await loadBusinessData(activeBusiness);
      Alert.alert('✅ Order Created', 'Invoice has been generated.');
    } catch (e: any) { Alert.alert('Error', e.message); }
    finally { setBusy(false); }
  };

  const markPaid = async (order: Order) => {
    if (!activeBusiness) return;
    Alert.alert('Mark as Paid?', `Mark Order #${order.id} (${money(order.total_amount)}) as fully paid?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Mark Paid', onPress: async () => {
        try {
          await api.orders.updateStatus(activeBusiness.id, order.id, 'paid', order.total_amount);
          await loadBusinessData(activeBusiness);
        } catch (e: any) { Alert.alert('Error', e.message); }
      }},
    ]);
  };

  const previewProduct = products.find(p => String(p.id) === selProduct);
  const previewSubtotal = previewProduct ? previewProduct.selling_price * (parseFloat(qty) || 0) : 0;
  const previewGst = previewSubtotal * (previewProduct?.gst_rate ?? 18) / 100;
  const previewTotal = previewSubtotal + previewGst - (parseFloat(discount) || 0);

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      <ScrollView
        contentContainerStyle={{ padding: 16, paddingBottom: 80 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />}
      >
        <SectionHeader
          title="Orders & GST Invoices"
          subtitle={`${orders.length} orders recorded`}
          right={
            <TouchableOpacity style={s.addBtn} onPress={() => setShowCreate(true)}>
              <Text style={s.addBtnText}>+ New Order</Text>
            </TouchableOpacity>
          }
        />

        {/* Filter tabs */}
        <View style={s.filterRow}>
          {(['all', 'pending', 'paid'] as const).map(f => (
            <TouchableOpacity key={f} style={[s.filterTab, filter === f && s.filterTabActive]} onPress={() => setFilter(f)}>
              <Text style={[s.filterTabText, filter === f && s.filterTabTextActive]}>
                {f === 'all' ? `All (${orders.length})` : f === 'pending' ? `Pending (${orders.filter(o => o.status === 'pending' || o.status === 'partially_paid').length})` : `Paid (${orders.filter(o => o.status === 'paid').length})`}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {filtered.length === 0 ? (
          <EmptyState icon="📦" title="No orders yet" subtitle="Tap + New Order to create your first order" />
        ) : (
          filtered.map(order => {
            const prod = products.find(p => p.id === order.product_id);
            const cust = customers.find(c => c.id === order.customer_id);
            const sc = statusColor(order.status);
            return (
              <Card key={order.id}>
                <Row style={{ marginBottom: 8 }}>
                  <View style={[s.orderIdBadge, { backgroundColor: C.primary + '15' }]}>
                    <Text style={[s.orderIdText, { color: C.primary }]}>#{order.id}</Text>
                  </View>
                  <View style={{ flex: 1, marginLeft: 10 }}>
                    <Text style={s.prodName}>{prod?.name ?? 'Product'}</Text>
                    <Text style={s.custName}>{cust?.name ?? 'Walk-in Customer'}</Text>
                  </View>
                  <Text style={s.totalAmt}>{money(order.total_amount)}</Text>
                </Row>
                <Row style={{ justifyContent: 'space-between' }}>
                  <Row style={{ gap: 6 }}>
                    <Badge label={channelIcon(order.channel) + ' ' + order.channel} color={C.textMuted} bg={C.border} />
                    <Badge label={order.status.toUpperCase()} color={sc} bg={sc + '18'} />
                  </Row>
                  <Text style={s.dateText}>{fmtDate(order.created_at)}</Text>
                </Row>
                <Divider />
                <Row style={{ gap: 8 }}>
                  <SmallBtn label="🧾 Invoice" onPress={() => openInvoice(order.id)} color={C.blue} />
                  {order.status !== 'paid' && (
                    <SmallBtn label="✅ Mark Paid" onPress={() => markPaid(order)} color={C.green} />
                  )}
                  <Text style={{ flex: 1, textAlign: 'right', fontSize: 11, color: C.textLight }}>
                    Qty: {order.quantity} • Paid: {money(order.amount_paid)}
                  </Text>
                </Row>
              </Card>
            );
          })
        )}
      </ScrollView>

      {/* ── Create Order Modal ──────────────────────────────────────────── */}
      <Modal visible={showCreate} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setShowCreate(false)}>
        <ScrollView style={s.modal} contentContainerStyle={{ padding: 20 }} keyboardShouldPersistTaps="handled">
          <Row style={{ justifyContent: 'space-between', marginBottom: 20 }}>
            <Text style={s.modalTitle}>Create New Order</Text>
            <TouchableOpacity onPress={() => setShowCreate(false)}>
              <Text style={{ color: C.red, fontWeight: '700' }}>Cancel</Text>
            </TouchableOpacity>
          </Row>

          <Text style={s.fieldLabel}>SELECT PRODUCT *</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 12 }}>
            <Row style={{ gap: 8, paddingVertical: 4 }}>
              {products.filter(p => p.is_active).map(p => (
                <TouchableOpacity
                  key={p.id}
                  style={[s.prodChip, String(p.id) === selProduct && s.prodChipActive]}
                  onPress={() => setSelProduct(String(p.id))}
                >
                  <Text style={[s.prodChipText, String(p.id) === selProduct && { color: C.primary }]}>{p.name}</Text>
                  <Text style={s.prodChipPrice}>₹{p.selling_price}/{p.unit}</Text>
                </TouchableOpacity>
              ))}
            </Row>
          </ScrollView>

          <Text style={s.fieldLabel}>SELECT CUSTOMER (Optional)</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 12 }}>
            <Row style={{ gap: 8, paddingVertical: 4 }}>
              <TouchableOpacity style={[s.custChip, !selCustomer && s.prodChipActive]} onPress={() => setSelCustomer('')}>
                <Text style={s.prodChipText}>Walk-in</Text>
              </TouchableOpacity>
              {customers.filter(c => c.is_active).map(c => (
                <TouchableOpacity
                  key={c.id}
                  style={[s.custChip, String(c.id) === selCustomer && s.prodChipActive]}
                  onPress={() => setSelCustomer(String(c.id))}
                >
                  <Text style={s.prodChipText}>{c.name}</Text>
                </TouchableOpacity>
              ))}
            </Row>
          </ScrollView>

          <Row style={{ gap: 12 }}>
            <Input label="Quantity *" value={qty} onChangeText={setQty} keyboardType="numeric" style={{ flex: 1 }} />
            <Input label="Discount (₹)" value={discount} onChangeText={setDiscount} keyboardType="numeric" style={{ flex: 1 }} />
          </Row>
          <Input label="Amount Paid (₹)" value={amtPaid} onChangeText={setAmtPaid} keyboardType="numeric" placeholder="0 for pending" />

          <Text style={s.fieldLabel}>CHANNEL</Text>
          <View style={s.channelRow}>
            {['app', 'whatsapp', 'voice', 'walk_in'].map(ch => (
              <TouchableOpacity key={ch} style={[s.channelBtn, channel === ch && s.channelBtnActive]} onPress={() => setChannel(ch)}>
                <Text style={[s.channelBtnText, channel === ch && { color: C.primary }]}>
                  {ch === 'whatsapp' ? '💬' : ch === 'voice' ? '🎤' : ch === 'walk_in' ? '🚶' : '📱'} {ch}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {previewProduct && (
            <Card style={{ backgroundColor: '#F0FDF4', marginTop: 8 }}>
              <Text style={[s.fieldLabel, { color: C.green }]}>ORDER PREVIEW</Text>
              <Row style={{ justifyContent: 'space-between' }}>
                <Text style={{ color: C.textMuted }}>Subtotal:</Text>
                <Text style={{ fontWeight: '700' }}>{money(previewSubtotal)}</Text>
              </Row>
              <Row style={{ justifyContent: 'space-between' }}>
                <Text style={{ color: C.textMuted }}>GST ({previewProduct.gst_rate}%):</Text>
                <Text style={{ fontWeight: '700' }}>{money(previewGst)}</Text>
              </Row>
              <Row style={{ justifyContent: 'space-between' }}>
                <Text style={{ color: C.textMuted }}>Discount:</Text>
                <Text style={{ fontWeight: '700', color: C.red }}>-{money(parseFloat(discount) || 0)}</Text>
              </Row>
              <Divider />
              <Row style={{ justifyContent: 'space-between' }}>
                <Text style={{ fontWeight: '800', fontSize: 16 }}>Total:</Text>
                <Text style={{ fontWeight: '900', fontSize: 18, color: C.primary }}>{money(previewTotal)}</Text>
              </Row>
            </Card>
          )}
          <PrimaryBtn label="Create Order & Generate Invoice" onPress={createOrder} loading={busy} style={{ marginTop: 16 }} />
        </ScrollView>
      </Modal>

      {/* ── Invoice Modal ───────────────────────────────────────────────── */}
      <Modal visible={!!invoice} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setInvoice(null)}>
        {invoice && (
          <ScrollView style={s.modal} contentContainerStyle={{ padding: 20 }}>
            <Row style={{ justifyContent: 'space-between', marginBottom: 20 }}>
              <Text style={s.modalTitle}>GST Invoice</Text>
              <TouchableOpacity onPress={() => setInvoice(null)}>
                <Text style={{ color: C.primary, fontWeight: '700' }}>Close</Text>
              </TouchableOpacity>
            </Row>
            <Card style={{ backgroundColor: '#F0FDF4' }}>
              <Row style={{ justifyContent: 'space-between', marginBottom: 4 }}>
                <Text style={s.invBizName}>{invoice.business_name}</Text>
                <Badge label="TAX INVOICE" color={C.green} bg={C.greenLight} />
              </Row>
              {invoice.business_address && <Text style={s.invDetail}>{invoice.business_address}</Text>}
              {invoice.business_gstin && <Text style={s.invDetail}>GSTIN: {invoice.business_gstin}</Text>}
            </Card>
            <Card>
              <Text style={s.invLabel}>INVOICE DETAILS</Text>
              <Row style={{ justifyContent: 'space-between', marginBottom: 4 }}>
                <Text style={{ color: C.textMuted }}>Invoice No:</Text>
                <Text style={s.invNo}>{invoice.invoice_no}</Text>
              </Row>
              <Row style={{ justifyContent: 'space-between', marginBottom: 4 }}>
                <Text style={{ color: C.textMuted }}>Date:</Text>
                <Text style={{ fontWeight: '700' }}>{invoice.invoice_date}</Text>
              </Row>
              <Divider />
              <Text style={s.invLabel}>BILL TO</Text>
              <Text style={s.invBuyer}>{invoice.customer_name}</Text>
              {invoice.customer_phone && <Text style={s.invDetail}>{invoice.customer_phone}</Text>}
              {invoice.customer_gstin && <Text style={s.invDetail}>GSTIN: {invoice.customer_gstin}</Text>}
            </Card>
            <Card>
              <Text style={s.invLabel}>ITEM DETAILS</Text>
              <View style={s.invTableHead}>
                {['Item', 'Qty', 'Rate', 'Amount'].map(h => (
                  <Text key={h} style={[s.invCol, { flex: h === 'Item' ? 2 : 1 }]}>{h}</Text>
                ))}
              </View>
              <View style={s.invTableRow}>
                <Text style={[s.invCell, { flex: 2 }]}>{invoice.product_name}</Text>
                <Text style={[s.invCell, { flex: 1 }]}>{invoice.quantity} {invoice.unit}</Text>
                <Text style={[s.invCell, { flex: 1 }]}>{money(invoice.unit_price)}</Text>
                <Text style={[s.invCell, { flex: 1, fontWeight: '700' }]}>{money(invoice.taxable_amount)}</Text>
              </View>
              {invoice.discount > 0 && (
                <Row style={{ justifyContent: 'space-between', paddingVertical: 4 }}>
                  <Text style={{ color: C.textMuted }}>Discount:</Text>
                  <Text style={{ color: C.red, fontWeight: '700' }}>-{money(invoice.discount)}</Text>
                </Row>
              )}
              <Row style={{ justifyContent: 'space-between', paddingVertical: 4 }}>
                <Text style={{ color: C.textMuted }}>CGST ({invoice.gst_rate / 2}%):</Text>
                <Text style={{ fontWeight: '700' }}>{money(invoice.cgst_amount)}</Text>
              </Row>
              <Row style={{ justifyContent: 'space-between', paddingVertical: 4 }}>
                <Text style={{ color: C.textMuted }}>SGST ({invoice.gst_rate / 2}%):</Text>
                <Text style={{ fontWeight: '700' }}>{money(invoice.sgst_amount)}</Text>
              </Row>
              <Divider />
              <Row style={{ justifyContent: 'space-between' }}>
                <Text style={{ fontSize: 16, fontWeight: '800' }}>TOTAL:</Text>
                <Text style={{ fontSize: 20, fontWeight: '900', color: C.primary }}>{money(invoice.total_amount)}</Text>
              </Row>
              <Row style={{ justifyContent: 'space-between', marginTop: 4 }}>
                <Text style={{ color: C.textMuted }}>Amount Paid:</Text>
                <Text style={{ fontWeight: '700', color: C.green }}>{money(invoice.amount_paid)}</Text>
              </Row>
              {invoice.balance_due > 0 && (
                <Row style={{ justifyContent: 'space-between' }}>
                  <Text style={{ color: C.red, fontWeight: '700' }}>Balance Due:</Text>
                  <Text style={{ fontWeight: '900', color: C.red }}>{money(invoice.balance_due)}</Text>
                </Row>
              )}
            </Card>
          </ScrollView>
        )}
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  addBtn:         { backgroundColor: C.primary, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 7 },
  addBtnText:     { color: '#fff', fontWeight: '800', fontSize: 13 },
  filterRow:      { flexDirection: 'row', backgroundColor: C.border, borderRadius: 10, padding: 3, marginBottom: 14 },
  filterTab:      { flex: 1, paddingVertical: 8, alignItems: 'center', borderRadius: 8 },
  filterTabActive:{ backgroundColor: '#fff', elevation: 1 },
  filterTabText:  { fontSize: 12, fontWeight: '600', color: C.textMuted },
  filterTabTextActive: { color: C.textMain, fontWeight: '800' },
  orderIdBadge:   { width: 40, height: 40, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  orderIdText:    { fontSize: 12, fontWeight: '900' },
  prodName:       { fontSize: 14, fontWeight: '800', color: C.textMain },
  custName:       { fontSize: 12, color: C.textMuted },
  totalAmt:       { fontSize: 16, fontWeight: '900', color: C.textMain },
  dateText:       { fontSize: 11, color: C.textLight },
  modal:          { flex: 1, backgroundColor: C.bg },
  modalTitle:     { fontSize: 20, fontWeight: '900', color: C.textMain },
  fieldLabel:     { fontSize: 10, fontWeight: '800', color: C.textMuted, letterSpacing: 0.5, marginBottom: 8, textTransform: 'uppercase' },
  prodChip:       { borderRadius: 10, padding: 10, backgroundColor: C.surface, borderWidth: 1.5, borderColor: C.border, minWidth: 100 },
  prodChipActive: { borderColor: C.primary, backgroundColor: C.greenLight },
  prodChipText:   { fontSize: 13, fontWeight: '700', color: C.textMain },
  prodChipPrice:  { fontSize: 11, color: C.textMuted, marginTop: 2 },
  custChip:       { borderRadius: 10, padding: 10, backgroundColor: C.surface, borderWidth: 1.5, borderColor: C.border, minWidth: 80 },
  channelRow:     { flexDirection: 'row', gap: 8, marginBottom: 16, flexWrap: 'wrap' },
  channelBtn:     { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 8, borderWidth: 1.5, borderColor: C.border, backgroundColor: C.surface },
  channelBtnActive:{ borderColor: C.primary, backgroundColor: C.greenLight },
  channelBtnText: { fontSize: 12, fontWeight: '700', color: C.textMuted },
  invBizName:     { fontSize: 16, fontWeight: '900', color: C.textMain, flex: 1 },
  invDetail:      { fontSize: 12, color: C.textMuted, marginTop: 2 },
  invLabel:       { fontSize: 9, fontWeight: '900', color: C.textMuted, letterSpacing: 0.8, marginBottom: 8, textTransform: 'uppercase' },
  invBuyer:       { fontSize: 14, fontWeight: '800', color: C.textMain },
  invNo:          { fontSize: 14, fontWeight: '900', color: C.primary },
  invTableHead:   { flexDirection: 'row', backgroundColor: C.bg, padding: 8, borderRadius: 6, marginBottom: 4 },
  invCol:         { fontSize: 11, fontWeight: '800', color: C.textMuted },
  invTableRow:    { flexDirection: 'row', paddingVertical: 6 },
  invCell:        { fontSize: 13, color: C.textMain },
});
