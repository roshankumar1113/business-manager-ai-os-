import React, { useState, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  TextInput, Alert, KeyboardAvoidingView, Platform, ActivityIndicator,
} from 'react-native';
import { useApp } from '../context/AppContext';
import * as api from '../services/api';
import { C, Card, Row, Badge, SmallBtn } from '../components/UI';
import { money } from '../utils/format';
import type { WAChatMessage } from '../types';

const PRESETS = [
  'Need 50 bags of cement 43 grade',
  'I want 2 ton TMT steel 12mm',
  'Need 100 kg DAP fertilizer',
  '20 bags of urea chahiye',
  'Rice 25kg 5 bags needed',
  'BUY',
  'No thanks, cancel',
];

export default function WhatsAppScreen() {
  const { activeBusiness, loadBusinessData } = useApp();
  const [customerName, setCustomerName] = useState('Rahul Verma');
  const [customerPhone, setCustomerPhone] = useState('+91 98765 11111');
  const [message, setMessage] = useState('');
  const [chatLog, setChatLog] = useState<WAChatMessage[]>([
    { sender: 'ai', text: `Namaste! 🙏 Welcome to *${activeBusiness?.name ?? 'Business Manager'}*.\nSend a product inquiry or type a product name and quantity for an instant quote.`, time: now() },
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<ScrollView>(null);

  function now() { return new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }); }

  const send = async (overrideText?: string) => {
    const txt = (overrideText || message).trim();
    if (!txt || !activeBusiness) return;
    const time = now();
    setChatLog(prev => [...prev, { sender: 'customer', text: txt, time }]);
    if (!overrideText) setMessage('');
    setLoading(true);
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    try {
      const res = await api.whatsapp.simulate(activeBusiness.id, customerPhone, customerName, txt);
      setChatLog(prev => [...prev, { sender: 'ai', text: res.reply, action: res.action, time: now() }]);
      if (res.action === 'order_created') {
        await loadBusinessData(activeBusiness);
        Alert.alert(
          '🎉 Order Created Automatically!',
          `WhatsApp order #${res.order_id} created.\nInvoice: ${res.invoice_no}\nTotal: ${money(res.total_amount)}`,
        );
      }
    } catch (e: any) {
      setChatLog(prev => [...prev, { sender: 'ai', text: `Error: ${e.message}`, time: now() }]);
    } finally {
      setLoading(false);
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    }
  };

  const resetChat = () => {
    setChatLog([{ sender: 'ai', text: `Chat cleared. Send a new product inquiry!`, time: now() }]);
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: '#ECE5DD' }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      {/* WhatsApp-style header */}
      <View style={s.waHeader}>
        <View style={s.waAvatar}><Text style={{ fontSize: 18 }}>👤</Text></View>
        <View style={{ flex: 1 }}>
          <Text style={s.waName}>{customerName}</Text>
          <Text style={s.waPhone}>{customerPhone}</Text>
        </View>
        <TouchableOpacity onPress={resetChat}>
          <Text style={{ color: '#A7F3D0', fontSize: 12, fontWeight: '700' }}>Clear Chat</Text>
        </TouchableOpacity>
      </View>

      {/* Customer inputs */}
      <View style={s.customerBar}>
        <TextInput
          style={s.miniInput}
          value={customerName}
          onChangeText={setCustomerName}
          placeholder="Customer Name"
          placeholderTextColor={C.textLight}
        />
        <TextInput
          style={s.miniInput}
          value={customerPhone}
          onChangeText={setCustomerPhone}
          placeholder="Phone"
          keyboardType="phone-pad"
          placeholderTextColor={C.textLight}
        />
      </View>

      {/* Chat area */}
      <ScrollView
        ref={scrollRef}
        style={{ flex: 1 }}
        contentContainerStyle={{ padding: 12, paddingBottom: 8 }}
        keyboardShouldPersistTaps="handled"
      >
        {chatLog.map((m, i) => (
          <View key={i} style={[s.msgWrapper, m.sender === 'customer' ? s.msgRight : s.msgLeft]}>
            <View style={[s.waBubble, m.sender === 'customer' ? s.bubbleCust : s.bubbleAI]}>
              {m.sender === 'ai' && (
                <Text style={s.aiLabel}>🤖 Business AI</Text>
              )}
              <Text style={[s.waText, m.sender === 'customer' && s.waTextCust]}>{m.text}</Text>
              {m.action === 'order_created' && (
                <View style={s.orderConfirmBadge}>
                  <Text style={s.orderConfirmText}>✅ Order Created & Invoice Generated!</Text>
                </View>
              )}
              <Text style={s.waTime}>{m.time}</Text>
            </View>
          </View>
        ))}
        {loading && (
          <View style={[s.msgWrapper, s.msgLeft]}>
            <View style={[s.waBubble, s.bubbleAI]}>
              <Row style={{ gap: 8 }}>
                <ActivityIndicator size="small" color={C.primary} />
                <Text style={{ color: C.textMuted, fontSize: 13 }}>AI processing...</Text>
              </Row>
            </View>
          </View>
        )}

        {/* Preset quick-send buttons */}
        <Text style={s.presetLabel}>QUICK MESSAGES</Text>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
          {PRESETS.map((p, i) => (
            <TouchableOpacity
              key={i}
              style={[s.presetBtn, p === 'BUY' && { backgroundColor: '#25D366' }]}
              onPress={() => send(p)}
              disabled={loading}
            >
              <Text style={[s.presetText, p === 'BUY' && { color: '#fff' }]}>{p}</Text>
            </TouchableOpacity>
          ))}
        </View>
        <View style={{ height: 16 }} />
      </ScrollView>

      {/* Input area */}
      <View style={s.waInputBar}>
        <TextInput
          style={s.waInput}
          placeholder="Type a message..."
          placeholderTextColor={C.textLight}
          value={message}
          onChangeText={setMessage}
          multiline
        />
        <TouchableOpacity
          style={[s.sendBtn, (!message.trim() || loading) && { opacity: 0.4 }]}
          onPress={() => send()}
          disabled={!message.trim() || loading}
        >
          <Text style={{ fontSize: 20 }}>📤</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  waHeader:    { flexDirection: 'row', alignItems: 'center', backgroundColor: '#075E54', padding: 14, paddingTop: 10, gap: 12 },
  waAvatar:    { width: 40, height: 40, borderRadius: 20, backgroundColor: '#128C7E', alignItems: 'center', justifyContent: 'center' },
  waName:      { fontSize: 16, fontWeight: '800', color: '#fff' },
  waPhone:     { fontSize: 12, color: '#A7F3D0' },
  customerBar: { flexDirection: 'row', backgroundColor: '#F0FFF4', padding: 8, gap: 8, borderBottomWidth: 1, borderBottomColor: C.border },
  miniInput:   { flex: 1, borderWidth: 1, borderColor: C.border, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6, fontSize: 12, backgroundColor: '#fff', color: C.textMain },
  msgWrapper:  { marginBottom: 8 },
  msgLeft:     { alignItems: 'flex-start' },
  msgRight:    { alignItems: 'flex-end' },
  waBubble:    { maxWidth: '80%', borderRadius: 10, padding: 10, shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 3, elevation: 1 },
  bubbleAI:    { backgroundColor: '#fff', borderTopLeftRadius: 2 },
  bubbleCust:  { backgroundColor: '#DCF8C6', borderTopRightRadius: 2 },
  aiLabel:     { fontSize: 10, fontWeight: '800', color: C.green, marginBottom: 4 },
  waText:      { fontSize: 14, color: C.textMain, lineHeight: 20 },
  waTextCust:  { color: '#111' },
  waTime:      { fontSize: 10, color: C.textLight, textAlign: 'right', marginTop: 4 },
  orderConfirmBadge: { backgroundColor: '#D1FAE5', borderRadius: 6, padding: 6, marginTop: 6 },
  orderConfirmText:  { fontSize: 12, color: C.green, fontWeight: '800' },
  presetLabel: { fontSize: 10, fontWeight: '800', color: C.textMuted, letterSpacing: 0.5, marginBottom: 8, marginTop: 8 },
  presetBtn:   { backgroundColor: '#fff', borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6, borderWidth: 1, borderColor: C.border },
  presetText:  { fontSize: 12, color: C.textMain, fontWeight: '600' },
  waInputBar:  { flexDirection: 'row', alignItems: 'flex-end', padding: 8, backgroundColor: '#F0F0F0', gap: 8 },
  waInput:     { flex: 1, maxHeight: 100, backgroundColor: '#fff', borderRadius: 24, paddingHorizontal: 16, paddingVertical: 10, fontSize: 14, color: C.textMain },
  sendBtn:     { width: 44, height: 44, borderRadius: 22, backgroundColor: '#25D366', alignItems: 'center', justifyContent: 'center' },
});
