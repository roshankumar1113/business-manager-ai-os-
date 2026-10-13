import React, { useState, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  TextInput, ActivityIndicator, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useApp } from '../context/AppContext';
import * as api from '../services/api';
import { C, Card, Badge, Row, Divider } from '../components/UI';
import { money } from '../utils/format';

interface Message { role: 'user' | 'ai'; text: string; time: string }

const SUGGESTIONS = [
  "What is today's profit?",
  "Who hasn't paid me?",
  "Show low-stock products",
  "Which product sold the most this month?",
  "What should I focus on today?",
  "How much did I earn from cement?",
  "Show my pending orders",
  "How much did I spend this month?",
  "Analyse my business health",
  "Show my top customers",
  "Find government tenders for me",
  "What is my cash flow situation?",
];

// Random Indian business voice command examples
const VOICE_COMMANDS = [
  "Aaj ka profit kitna hai?",
  "Kaun se customer ne payment nahi ki?",
  "Stock khatam hone wale products kaun se hain?",
  "Is mahine mein sabse zyada kya bika?",
  "Aaj kya karna chahiye?",
  "Mere top customers kaun hain?",
];

export default function AIScreen() {
  const { activeBusiness, dashboard } = useApp();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'ai',
      text: activeBusiness
        ? `Namaste! 🙏 I'm your Business AI for *${activeBusiness.name}*.\n\nI have access to your real-time business data — sales, expenses, inventory, customers, and more.\n\nAsk me anything or try a suggested query below!`
        : 'Namaste! 🙏 Please select a business to start asking questions.',
      time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<ScrollView>(null);

  const sendQuery = async (q: string = query) => {
    const text = q.trim();
    if (!text || !activeBusiness) return;
    const time = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { role: 'user', text, time }]);
    setQuery('');
    setLoading(true);
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    try {
      const res = await api.ai.query(activeBusiness.id, text);
      setMessages(prev => [...prev, { role: 'ai', text: res.answer, time }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'ai', text: `Sorry, I encountered an error: ${e.message}`, time }]);
    } finally {
      setLoading(false);
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    }
  };

  const voiceSimulate = () => {
    const cmd = VOICE_COMMANDS[Math.floor(Math.random() * VOICE_COMMANDS.length)];
    Alert.alert(
      '🎤 Voice Command',
      `Simulating voice input:\n\n"${cmd}"\n\n(Full voice recognition requires native Android SpeechRecognizer)`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Send Query', onPress: () => sendQuery(cmd) },
      ]
    );
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: C.bg }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      {/* Header stats strip */}
      {dashboard && (
        <View style={s.statsStrip}>
          <View style={s.stripItem}>
            <Text style={s.stripVal}>{money(dashboard.today_sales, true)}</Text>
            <Text style={s.stripLabel}>Today Sales</Text>
          </View>
          <View style={s.stripDivider} />
          <View style={s.stripItem}>
            <Text style={[s.stripVal, { color: C.green }]}>{money(dashboard.today_estimated_profit, true)}</Text>
            <Text style={s.stripLabel}>Today Profit</Text>
          </View>
          <View style={s.stripDivider} />
          <View style={s.stripItem}>
            <Text style={[s.stripVal, { color: C.amber }]}>{money(dashboard.receivables, true)}</Text>
            <Text style={s.stripLabel}>Receivables</Text>
          </View>
          <View style={s.stripDivider} />
          <View style={s.stripItem}>
            <Text style={[s.stripVal, { color: dashboard.low_stock_count > 0 ? C.red : C.green }]}>
              {dashboard.low_stock_count}
            </Text>
            <Text style={s.stripLabel}>Low Stock</Text>
          </View>
        </View>
      )}

      {/* Chat messages */}
      <ScrollView
        ref={scrollRef}
        style={{ flex: 1 }}
        contentContainerStyle={{ padding: 16, paddingBottom: 8 }}
        keyboardShouldPersistTaps="handled"
      >
        {messages.map((m, i) => (
          <View key={i} style={[s.msgRow, m.role === 'user' && s.msgRowUser]}>
            {m.role === 'ai' && (
              <View style={s.aiAvatar}><Text style={{ fontSize: 14 }}>🤖</Text></View>
            )}
            <View style={[s.bubble, m.role === 'user' ? s.bubbleUser : s.bubbleAi]}>
              <Text style={m.role === 'user' ? s.bubbleTextUser : s.bubbleTextAi}>{m.text}</Text>
              <Text style={s.msgTime}>{m.time}</Text>
            </View>
          </View>
        ))}
        {loading && (
          <View style={[s.msgRow]}>
            <View style={s.aiAvatar}><Text style={{ fontSize: 14 }}>🤖</Text></View>
            <View style={[s.bubble, s.bubbleAi, { paddingHorizontal: 20, paddingVertical: 14 }]}>
              <Row style={{ gap: 6 }}>
                <ActivityIndicator size="small" color={C.primary} />
                <Text style={{ color: C.textMuted, fontSize: 13 }}>Analysing your business data...</Text>
              </Row>
            </View>
          </View>
        )}

        {/* Suggestions */}
        <Text style={s.suggestLabel}>💡 SUGGESTED QUERIES</Text>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
          {SUGGESTIONS.map((s2, i) => (
            <TouchableOpacity key={i} style={s.suggChip} onPress={() => sendQuery(s2)} disabled={loading}>
              <Text style={s.suggChipText}>{s2}</Text>
            </TouchableOpacity>
          ))}
        </View>
        <View style={{ height: 16 }} />
      </ScrollView>

      {/* Input bar */}
      <View style={s.inputBar}>
        <TouchableOpacity style={s.voiceBtn} onPress={voiceSimulate}>
          <Text style={{ fontSize: 22 }}>🎤</Text>
        </TouchableOpacity>
        <TextInput
          style={s.textInput}
          placeholder="Ask your Business AI anything..."
          placeholderTextColor={C.textLight}
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={() => sendQuery()}
          returnKeyType="send"
          multiline
        />
        <TouchableOpacity
          style={[s.sendBtn, (!query.trim() || loading) && { opacity: 0.4 }]}
          onPress={() => sendQuery()}
          disabled={!query.trim() || loading}
        >
          <Text style={{ color: '#fff', fontWeight: '900', fontSize: 16 }}>→</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  statsStrip:  { flexDirection: 'row', backgroundColor: C.primaryDark, paddingVertical: 10, paddingHorizontal: 16 },
  stripItem:   { flex: 1, alignItems: 'center' },
  stripVal:    { fontSize: 14, fontWeight: '900', color: '#fff' },
  stripLabel:  { fontSize: 9, color: '#A7F3D0', marginTop: 2, textTransform: 'uppercase', letterSpacing: 0.3 },
  stripDivider:{ width: 1, backgroundColor: 'rgba(255,255,255,0.2)', marginVertical: 4 },
  msgRow:      { flexDirection: 'row', marginBottom: 12, alignItems: 'flex-end' },
  msgRowUser:  { flexDirection: 'row-reverse' },
  aiAvatar:    { width: 32, height: 32, borderRadius: 10, backgroundColor: C.greenLight, alignItems: 'center', justifyContent: 'center', marginRight: 8 },
  bubble:      { maxWidth: '80%', borderRadius: 16, padding: 12 },
  bubbleAi:    { backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderBottomLeftRadius: 4 },
  bubbleUser:  { backgroundColor: C.primary, borderBottomRightRadius: 4 },
  bubbleTextAi:  { fontSize: 14, color: C.textMain, lineHeight: 21 },
  bubbleTextUser:{ fontSize: 14, color: '#fff', lineHeight: 21 },
  msgTime:     { fontSize: 10, color: C.textLight, marginTop: 4, textAlign: 'right' },
  suggestLabel:{ fontSize: 10, fontWeight: '800', color: C.textMuted, letterSpacing: 0.5, textTransform: 'uppercase', marginTop: 8 },
  suggChip:    { backgroundColor: C.surface, borderRadius: 20, paddingHorizontal: 12, paddingVertical: 7, borderWidth: 1, borderColor: C.border },
  suggChipText:{ fontSize: 12, color: C.textMain, fontWeight: '600' },
  inputBar:    { flexDirection: 'row', alignItems: 'flex-end', padding: 12, backgroundColor: C.surface, borderTopWidth: 1, borderTopColor: C.border, gap: 8 },
  voiceBtn:    { width: 44, height: 44, borderRadius: 12, backgroundColor: C.greenLight, alignItems: 'center', justifyContent: 'center' },
  textInput:   { flex: 1, maxHeight: 100, borderWidth: 1.5, borderColor: C.border, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 10, fontSize: 14, color: C.textMain, backgroundColor: C.bg },
  sendBtn:     { width: 44, height: 44, borderRadius: 12, backgroundColor: C.primary, alignItems: 'center', justifyContent: 'center' },
});
