import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  Modal, Alert, RefreshControl, TextInput,
} from 'react-native';
import { useApp } from '../context/AppContext';
import * as api from '../services/api';
import {
  C, Card, SectionHeader, Badge, Input, PrimaryBtn, SmallBtn,
  Loader, EmptyState, Row, Divider,
} from '../components/UI';
import { money } from '../utils/format';
import type { Product } from '../types';

const UNITS = ['bag', 'kg', 'ton', 'piece', 'litre', 'unit', 'box', 'packet', 'cu.ft', 'sheet', 'bottle', 'quintal'];
const CATEGORIES = ['General', 'Cement', 'Steel', 'Aggregate', 'Bricks', 'Fertilizers', 'Seeds', 'Pesticides', 'Equipment', 'Staples', 'Edible Oil', 'FMCG', 'Cleaning', 'Packaged Food', 'Other'];
const GST_RATES = [0, 5, 12, 18, 28];

export default function InventoryScreen() {
  const { activeBusiness, products, loadBusinessData } = useApp();
  const [filter, setFilter] = useState<'all' | 'low'>('all');
  const [search, setSearch] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [editProduct, setEditProduct] = useState<Product | null>(null);
  const [showIntel, setShowIntel] = useState(false);
  const [intelData, setIntelData] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [busy, setBusy] = useState(false);
  // Form
  const [fName, setFName] = useState('');
  const [fCategory, setFCategory] = useState('General');
  const [fUnit, setFUnit] = useState('bag');
  const [fBuyPrice, setFBuyPrice] = useState('');
  const [fSellPrice, setFSellPrice] = useState('');
  const [fStock, setFStock] = useState('');
  const [fMinStock, setFMinStock] = useState('10');
  const [fGst, setFGst] = useState('18');
  const [fHsn, setFHsn] = useState('');

  const filtered = products.filter(p => {
    const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) || (p.category || '').toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === 'all' || (filter === 'low' && p.stock_quantity <= p.min_stock_level);
    return matchSearch && matchFilter && p.is_active;
  });

  const lowStockCount = products.filter(p => p.is_active && p.stock_quantity <= p.min_stock_level).length;

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    if (activeBusiness) await loadBusinessData(activeBusiness);
    setRefreshing(false);
  }, [activeBusiness]);

  const resetForm = () => { setFName(''); setFCategory('General'); setFUnit('bag'); setFBuyPrice(''); setFSellPrice(''); setFStock(''); setFMinStock('10'); setFGst('18'); setFHsn(''); };

  const openAdd = () => { resetForm(); setEditProduct(null); setShowAdd(true); };

  const openEdit = (p: Product) => {
    setEditProduct(p);
    setFName(p.name); setFCategory(p.category || 'General'); setFUnit(p.unit);
    setFBuyPrice(String(p.purchase_price)); setFSellPrice(String(p.selling_price));
    setFStock(String(p.stock_quantity)); setFMinStock(String(p.min_stock_level));
    setFGst(String(p.gst_rate)); setFHsn(p.hsn_code || '');
    setShowAdd(true);
  };

  const saveProduct = async () => {
    if (!fName.trim() || !fSellPrice || !fBuyPrice) return Alert.alert('Required', 'Fill name, purchase price and selling price.');
    if (!activeBusiness) return;
    setBusy(true);
    try {
      const payload = {
        name: fName.trim(), category: fCategory, unit: fUnit,
        purchase_price: parseFloat(fBuyPrice) || 0, selling_price: parseFloat(fSellPrice) || 0,
        stock_quantity: parseFloat(fStock) || 0, min_stock_level: parseFloat(fMinStock) || 5,
        gst_rate: parseFloat(fGst) || 18, hsn_code: fHsn || undefined,
      };
      if (editProduct) {
        await api.products.update(activeBusiness.id, editProduct.id, payload);
      } else {
        await api.products.create(activeBusiness.id, payload);
      }
      setShowAdd(false);
      await loadBusinessData(activeBusiness);
      Alert.alert('✅ Product Saved', `${fName.trim()} has been ${editProduct ? 'updated' : 'added'}.`);
    } catch (e: any) { Alert.alert('Error', e.message); }
    finally { setBusy(false); }
  };

  const quickSell = async (p: Product) => {
    if (!activeBusiness) return;
    if (p.stock_quantity < 1) return Alert.alert('Out of Stock', 'This product has no stock.');
    try {
      await api.orders.create(activeBusiness.id, { product_id: p.id, quantity: 1, amount_paid: p.selling_price, channel: 'app' });
      await loadBusinessData(activeBusiness);
      Alert.alert('✅ Quick Sale', `1 ${p.unit} of ${p.name} sold — ₹${p.selling_price}`);
    } catch (e: any) { Alert.alert('Error', e.message); }
  };

  const loadIntelligence = async () => {
    if (!activeBusiness) return;
    try {
      const data = await api.products.intelligence(activeBusiness.id);
      setIntelData(data);
      setShowIntel(true);
    } catch (e: any) { Alert.alert('Error', e.message); }
  };

  const stockBarWidth = (p: Product): number => {
    const pct = p.max_stock_level > 0 ? Math.min(p.stock_quantity / p.max_stock_level, 1) : 0;
    return Math.max(pct * 100, 2);
  };
  const stockColor = (p: Product) => p.stock_quantity <= p.min_stock_level ? C.red : p.stock_quantity < p.min_stock_level * 2 ? C.amber : C.green;

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      <View style={s.searchBar}>
        <Text style={s.searchIcon}>🔍</Text>
        <TextInput style={s.searchInput} placeholder="Search products..." placeholderTextColor={C.textLight} value={search} onChangeText={setSearch} />
      </View>

      <ScrollView
        contentContainerStyle={{ padding: 16, paddingBottom: 80 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.primary} />}
      >
        <SectionHeader
          title="Inventory & Stock"
          subtitle={`${products.filter(p => p.is_active).length} products`}
          right={
            <Row style={{ gap: 8 }}>
              <SmallBtn label="🧠 AI Intel" onPress={loadIntelligence} color={C.purple} />
              <TouchableOpacity style={s.addBtn} onPress={openAdd}>
                <Text style={s.addBtnText}>+ Add</Text>
              </TouchableOpacity>
            </Row>
          }
        />

        <View style={s.filterRow}>
          <TouchableOpacity style={[s.filterTab, filter === 'all' && s.filterTabActive]} onPress={() => setFilter('all')}>
            <Text style={[s.filterTabText, filter === 'all' && s.filterTabTextActive]}>All ({products.filter(p => p.is_active).length})</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[s.filterTab, filter === 'low' && s.filterTabActive]} onPress={() => setFilter('low')}>
            <Text style={[s.filterTabText, filter === 'low' && s.filterTabTextActive, lowStockCount > 0 && { color: C.red }]}>
              ⚠️ Low Stock ({lowStockCount})
            </Text>
          </TouchableOpacity>
        </View>

        {filtered.length === 0 ? (
          <EmptyState icon="📦" title={search ? 'No products found' : 'No products yet'} subtitle="Add products to start tracking inventory" />
        ) : (
          filtered.map(p => {
            const sc = stockColor(p);
            const isLow = p.stock_quantity <= p.min_stock_level;
            return (
              <Card key={p.id}>
                <Row style={{ marginBottom: 8 }}>
                  <View style={[s.prodIcon, { backgroundColor: C.primary + '15' }]}>
                    <Text style={{ fontSize: 20 }}>{p.category === 'Cement' ? '🧱' : p.category === 'Steel' ? '🔩' : p.category === 'Fertilizers' ? '🌱' : p.category?.includes('Seed') ? '🌾' : '📦'}</Text>
                  </View>
                  <View style={{ flex: 1, marginLeft: 10 }}>
                    <Text style={s.prodName}>{p.name}</Text>
                    <Text style={s.prodCategory}>{p.category} • GST {p.gst_rate}%</Text>
                  </View>
                  <View style={{ alignItems: 'flex-end' }}>
                    <Text style={s.prodPrice}>₹{p.selling_price}/{p.unit}</Text>
                    <Text style={s.prodCost}>Cost: ₹{p.purchase_price}</Text>
                  </View>
                </Row>

                {/* Stock bar */}
                <Row style={{ marginBottom: 6, gap: 8 }}>
                  <Text style={[s.stockText, { color: sc }]}>{p.stock_quantity} {p.unit}</Text>
                  <View style={s.stockBarBg}>
                    <View style={[s.stockBarFill, { width: `${stockBarWidth(p)}%` as any, backgroundColor: sc }]} />
                  </View>
                  <Text style={{ fontSize: 11, color: C.textLight }}>Min: {p.min_stock_level}</Text>
                </Row>

                {isLow && (
                  <View style={s.lowStockBanner}>
                    <Text style={s.lowStockText}>⚠️ LOW STOCK — Contact supplier to reorder</Text>
                  </View>
                )}

                <Divider />
                <Row style={{ gap: 8 }}>
                  <SmallBtn label="✏️ Edit" onPress={() => openEdit(p)} />
                  <SmallBtn label="+ Sell 1" onPress={() => quickSell(p)} color={C.green} />
                  <Text style={{ flex: 1, textAlign: 'right', fontSize: 11, color: C.textLight }}>
                    Margin: {p.selling_price > 0 ? Math.round((p.selling_price - p.purchase_price) / p.selling_price * 100) : 0}%
                  </Text>
                </Row>
              </Card>
            );
          })
        )}
      </ScrollView>

      {/* ── Add/Edit Product Modal ─────────────────────────────────────── */}
      <Modal visible={showAdd} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setShowAdd(false)}>
        <ScrollView style={s.modal} contentContainerStyle={{ padding: 20 }} keyboardShouldPersistTaps="handled">
          <Row style={{ justifyContent: 'space-between', marginBottom: 20 }}>
            <Text style={s.modalTitle}>{editProduct ? 'Edit Product' : 'Add New Product'}</Text>
            <TouchableOpacity onPress={() => setShowAdd(false)}>
              <Text style={{ color: C.red, fontWeight: '700' }}>Cancel</Text>
            </TouchableOpacity>
          </Row>
          <Input label="Product Name *" value={fName} onChangeText={setFName} placeholder="e.g. OPC 53 Grade Cement" />

          <Text style={s.fieldLabel}>CATEGORY</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 12 }}>
            <Row style={{ gap: 6 }}>
              {CATEGORIES.map(c => (
                <TouchableOpacity key={c} style={[s.chip, fCategory === c && s.chipActive]} onPress={() => setFCategory(c)}>
                  <Text style={[s.chipText, fCategory === c && { color: C.primary }]}>{c}</Text>
                </TouchableOpacity>
              ))}
            </Row>
          </ScrollView>

          <Text style={s.fieldLabel}>UNIT</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 12 }}>
            <Row style={{ gap: 6 }}>
              {UNITS.map(u => (
                <TouchableOpacity key={u} style={[s.chip, fUnit === u && s.chipActive]} onPress={() => setFUnit(u)}>
                  <Text style={[s.chipText, fUnit === u && { color: C.primary }]}>{u}</Text>
                </TouchableOpacity>
              ))}
            </Row>
          </ScrollView>

          <Row style={{ gap: 12 }}>
            <Input label="Purchase Price (₹) *" value={fBuyPrice} onChangeText={setFBuyPrice} keyboardType="numeric" placeholder="0" style={{ flex: 1 }} />
            <Input label="Selling Price (₹) *" value={fSellPrice} onChangeText={setFSellPrice} keyboardType="numeric" placeholder="0" style={{ flex: 1 }} />
          </Row>
          <Row style={{ gap: 12 }}>
            <Input label="Opening Stock" value={fStock} onChangeText={setFStock} keyboardType="numeric" placeholder="0" style={{ flex: 1 }} />
            <Input label="Min Stock Level" value={fMinStock} onChangeText={setFMinStock} keyboardType="numeric" placeholder="5" style={{ flex: 1 }} />
          </Row>

          <Text style={s.fieldLabel}>GST RATE (%)</Text>
          <Row style={{ gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
            {GST_RATES.map(r => (
              <TouchableOpacity key={r} style={[s.chip, fGst === String(r) && s.chipActive]} onPress={() => setFGst(String(r))}>
                <Text style={[s.chipText, fGst === String(r) && { color: C.primary }]}>{r}%</Text>
              </TouchableOpacity>
            ))}
          </Row>

          <Input label="HSN Code (Optional)" value={fHsn} onChangeText={setFHsn} placeholder="e.g. 2523" />

          {fSellPrice && fBuyPrice && (
            <Card style={{ backgroundColor: '#F0FDF4', marginBottom: 8 }}>
              <Row style={{ justifyContent: 'space-between' }}>
                <Text style={{ color: C.textMuted }}>Profit Margin:</Text>
                <Text style={{ fontWeight: '800', color: C.green }}>
                  {parseFloat(fSellPrice) > 0 ? Math.round((parseFloat(fSellPrice) - parseFloat(fBuyPrice)) / parseFloat(fSellPrice) * 100) : 0}%
                </Text>
              </Row>
            </Card>
          )}

          <PrimaryBtn label={editProduct ? 'Update Product' : 'Add to Inventory'} onPress={saveProduct} loading={busy} />
        </ScrollView>
      </Modal>

      {/* ── AI Intelligence Modal ─────────────────────────────────────── */}
      <Modal visible={showIntel} animationType="slide" presentationStyle="pageSheet" onRequestClose={() => setShowIntel(false)}>
        <ScrollView style={s.modal} contentContainerStyle={{ padding: 20 }}>
          <Row style={{ justifyContent: 'space-between', marginBottom: 20 }}>
            <Text style={s.modalTitle}>🧠 Inventory Intelligence</Text>
            <TouchableOpacity onPress={() => setShowIntel(false)}>
              <Text style={{ color: C.primary, fontWeight: '700' }}>Done</Text>
            </TouchableOpacity>
          </Row>
          {intelData && (
            <>
              {intelData.stockout_warnings?.length > 0 && (
                <Card style={{ borderLeftWidth: 4, borderLeftColor: C.red }}>
                  <Text style={[s.fieldLabel, { color: C.red }]}>🚨 STOCKOUT WARNINGS</Text>
                  {intelData.stockout_warnings.map((w: any, i: number) => (
                    <View key={i} style={{ marginBottom: 8 }}>
                      <Text style={{ fontWeight: '700', color: C.textMain }}>{w.product}</Text>
                      <Text style={{ color: C.red }}>~{w.days_until_stockout} days until stockout ({w.daily_velocity}/day)</Text>
                    </View>
                  ))}
                </Card>
              )}
              <Card>
                <Text style={[s.fieldLabel, { color: C.primary }]}>🚀 FAST-MOVING PRODUCTS</Text>
                {intelData.fast_moving?.map((p: any, i: number) => (
                  <Row key={i} style={{ justifyContent: 'space-between', marginBottom: 4 }}>
                    <Text style={{ color: C.textMain }}>{p.name}</Text>
                    <Text style={{ fontWeight: '700', color: C.green }}>{p.sold_this_month} {p.unit} this month</Text>
                  </Row>
                ))}
              </Card>
              {intelData.slow_moving?.length > 0 && (
                <Card>
                  <Text style={[s.fieldLabel, { color: C.amber }]}>🐢 SLOW-MOVING PRODUCTS</Text>
                  {intelData.slow_moving.map((p: any, i: number) => (
                    <Row key={i} style={{ justifyContent: 'space-between', marginBottom: 4 }}>
                      <Text style={{ color: C.textMain }}>{p.name}</Text>
                      <Text style={{ color: C.amber }}>No sales this month</Text>
                    </Row>
                  ))}
                </Card>
              )}
              <Card>
                <Text style={s.fieldLabel}>📦 TOTAL INVENTORY VALUE</Text>
                <Text style={{ fontSize: 24, fontWeight: '900', color: C.primary }}>{money(intelData.total_inventory_value)}</Text>
              </Card>
            </>
          )}
        </ScrollView>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  searchBar:   { flexDirection: 'row', alignItems: 'center', backgroundColor: C.surface, margin: 12, borderRadius: 12, paddingHorizontal: 12, borderWidth: 1, borderColor: C.border },
  searchIcon:  { fontSize: 16, marginRight: 8 },
  searchInput: { flex: 1, height: 44, fontSize: 14, color: C.textMain },
  addBtn:      { backgroundColor: C.primary, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 7 },
  addBtnText:  { color: '#fff', fontWeight: '800', fontSize: 13 },
  filterRow:   { flexDirection: 'row', backgroundColor: C.border, borderRadius: 10, padding: 3, marginBottom: 14 },
  filterTab:   { flex: 1, paddingVertical: 8, alignItems: 'center', borderRadius: 8 },
  filterTabActive:   { backgroundColor: '#fff', elevation: 1 },
  filterTabText:     { fontSize: 12, fontWeight: '600', color: C.textMuted },
  filterTabTextActive:{ color: C.textMain, fontWeight: '800' },
  prodIcon:    { width: 44, height: 44, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  prodName:    { fontSize: 14, fontWeight: '800', color: C.textMain },
  prodCategory:{ fontSize: 11, color: C.textMuted },
  prodPrice:   { fontSize: 14, fontWeight: '800', color: C.primary },
  prodCost:    { fontSize: 11, color: C.textMuted },
  stockText:   { fontSize: 13, fontWeight: '800', minWidth: 60 },
  stockBarBg:  { flex: 1, height: 6, backgroundColor: C.border, borderRadius: 3 },
  stockBarFill:{ height: 6, borderRadius: 3 },
  lowStockBanner:{ backgroundColor: C.redLight, borderRadius: 8, padding: 6, marginBottom: 4 },
  lowStockText:{ fontSize: 11, color: C.red, fontWeight: '700', textAlign: 'center' },
  modal:       { flex: 1, backgroundColor: C.bg },
  modalTitle:  { fontSize: 20, fontWeight: '900', color: C.textMain },
  fieldLabel:  { fontSize: 10, fontWeight: '800', color: C.textMuted, letterSpacing: 0.5, marginBottom: 8, textTransform: 'uppercase' },
  chip:        { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 8, borderWidth: 1.5, borderColor: C.border, backgroundColor: C.surface },
  chipActive:  { borderColor: C.primary, backgroundColor: C.greenLight },
  chipText:    { fontSize: 12, fontWeight: '700', color: C.textMuted },
});
