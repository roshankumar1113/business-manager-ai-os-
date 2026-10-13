import React, { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity,
  StyleSheet, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useApp } from '../context/AppContext';
import * as api from '../services/api';
import { C, Input, PrimaryBtn } from '../components/UI';

const CATEGORIES = [
  { id: 'Construction', icon: '🏗️', label: 'Construction' },
  { id: 'Agriculture',  icon: '🌾', label: 'Agriculture' },
  { id: 'Retail',       icon: '🏪', label: 'Retail Shop' },
  { id: 'Wholesale',    icon: '📦', label: 'Wholesale' },
  { id: 'Manufacturing',icon: '🏭', label: 'Manufacturing' },
  { id: 'Restaurant',   icon: '🍽️', label: 'Restaurant' },
  { id: 'Pharmacy',     icon: '💊', label: 'Pharmacy' },
  { id: 'Transport',    icon: '🚛', label: 'Transport' },
  { id: 'Other',        icon: '🏢', label: 'Other Business' },
];

type Step = 'welcome' | 'login' | 'register' | 'setup';

export default function AuthScreen() {
  const { login } = useApp();
  const [step, setStep] = useState<Step>('welcome');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('demo@businessmanager.local');
  const [password, setPassword] = useState('DemoPass123!');
  const [phone, setPhone] = useState('');
  const [bizName, setBizName] = useState('');
  const [bizCategory, setBizCategory] = useState('');
  const [busy, setBusy] = useState(false);
  const [registeredToken, setRegisteredToken] = useState<any>(null);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) return Alert.alert('Required', 'Enter email and password.');
    setBusy(true);
    try {
      const res = await api.auth.login(email.trim().toLowerCase(), password);
      login(res.access_token, res.user_id, res.user_name, res.user_email, res.plan);
    } catch (e: any) {
      Alert.alert('Login Failed', e.message || 'Check your credentials.');
    } finally { setBusy(false); }
  };

  const handleRegister = async () => {
    if (!name.trim() || !email.trim() || !password.trim()) return Alert.alert('Required', 'Fill all fields.');
    setBusy(true);
    try {
      const res = await api.auth.register(name.trim(), email.trim().toLowerCase(), password, phone || undefined);
      setRegisteredToken(res);
      setStep('setup');
    } catch (e: any) {
      Alert.alert('Registration Failed', e.message);
    } finally { setBusy(false); }
  };

  const handleSetupBusiness = async () => {
    if (!bizName.trim() || !bizCategory) return Alert.alert('Required', 'Enter business name and select a category.');
    setBusy(true);
    try {
      api.setToken(registeredToken.access_token);
      await api.businesses.create({ name: bizName.trim(), category: bizCategory });
      login(registeredToken.access_token, registeredToken.user_id, registeredToken.user_name, registeredToken.user_email, registeredToken.plan);
    } catch (e: any) {
      Alert.alert('Setup Failed', e.message);
    } finally { setBusy(false); }
  };

  // ── Welcome ──────────────────────────────────────────────────────────────
  if (step === 'welcome') return (
    <SafeAreaView style={s.safeArea}>
      <ExpoStatusBar style="light" />
      <View style={s.welcomeBg}>
        <View style={s.welcomeContent}>
          <View style={s.logoBadge}><Text style={s.logoText}>BM</Text></View>
          <Text style={s.appTitle}>Business Manager</Text>
          <Text style={s.appTagline}>Run your business.{'\n'}Let AI manage the complexity.</Text>
          <View style={s.featureRow}>
            {['🤖 AI Assistant', '💬 WhatsApp Orders', '🧾 GST Invoices', '📊 Analytics'].map(f => (
              <View key={f} style={s.featurePill}><Text style={s.featurePillText}>{f}</Text></View>
            ))}
          </View>
          <PrimaryBtn label="Create Account →" onPress={() => setStep('register')} style={{ marginBottom: 12, marginTop: 24 }} />
          <TouchableOpacity style={s.loginLink} onPress={() => setStep('login')}>
            <Text style={s.loginLinkText}>Already have an account? Sign In</Text>
          </TouchableOpacity>
          <View style={s.demoBox}>
            <Text style={s.demoTitle}>🚀 Try Demo Account</Text>
            <Text style={s.demoText}>Email: demo@businessmanager.local</Text>
            <Text style={s.demoText}>Pass: DemoPass123!</Text>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );

  // ── Business Setup ───────────────────────────────────────────────────────
  if (step === 'setup') return (
    <SafeAreaView style={s.safeArea2}>
      <ExpoStatusBar style="dark" />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={s.formContainer}>
          <Text style={s.stepTitle}>🏢 Setup Your Business</Text>
          <Text style={s.stepSub}>Tell us about your business to personalise your AI assistant.</Text>
          <Input label="Business Name" value={bizName} onChangeText={setBizName} placeholder="e.g. Sharma Traders" />
          <Text style={s.catLabel}>SELECT YOUR BUSINESS TYPE</Text>
          <View style={s.catGrid}>
            {CATEGORIES.map(c => (
              <TouchableOpacity
                key={c.id}
                style={[s.catTile, bizCategory === c.id && s.catTileActive]}
                onPress={() => setBizCategory(c.id)}
              >
                <Text style={s.catIcon}>{c.icon}</Text>
                <Text style={[s.catLabel2, bizCategory === c.id && { color: C.primary }]}>{c.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <PrimaryBtn label="Start Managing My Business →" onPress={handleSetupBusiness} loading={busy} style={{ marginTop: 8 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );

  // ── Login / Register ──────────────────────────────────────────────────────
  const isLogin = step === 'login';
  return (
    <SafeAreaView style={s.safeArea2}>
      <ExpoStatusBar style="dark" />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={s.formContainer} keyboardShouldPersistTaps="handled">
          <TouchableOpacity onPress={() => setStep('welcome')} style={{ marginBottom: 16 }}>
            <Text style={{ color: C.primary, fontWeight: '700' }}>← Back</Text>
          </TouchableOpacity>

          <View style={s.logoBadgeSmall}><Text style={s.logoTextSmall}>BM</Text></View>
          <Text style={s.formTitle}>{isLogin ? 'Welcome Back!' : 'Create Account'}</Text>
          <Text style={s.formSub}>{isLogin ? 'Sign in to your Business Manager account.' : 'Join 10,000+ Indian business owners.'}</Text>

          <View style={s.tabRow}>
            <TouchableOpacity style={[s.tab, isLogin && s.tabActive]} onPress={() => setStep('login')}>
              <Text style={[s.tabText, isLogin && s.tabTextActive]}>Sign In</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[s.tab, !isLogin && s.tabActive]} onPress={() => setStep('register')}>
              <Text style={[s.tabText, !isLogin && s.tabTextActive]}>Register</Text>
            </TouchableOpacity>
          </View>

          {!isLogin && <Input label="Full Name" value={name} onChangeText={setName} placeholder="Rajesh Kumar Sharma" />}
          {!isLogin && <Input label="Phone (Optional)" value={phone} onChangeText={setPhone} placeholder="+91 98765 43210" keyboardType="phone-pad" />}
          <Input label="Email Address" value={email} onChangeText={setEmail} placeholder="you@example.com" autoCapitalize="none" keyboardType="email-address" />
          <Input label="Password" value={password} onChangeText={setPassword} placeholder="••••••••" secureTextEntry />

          <PrimaryBtn
            label={isLogin ? 'Sign In →' : 'Create Account →'}
            onPress={isLogin ? handleLogin : handleRegister}
            loading={busy}
            style={{ marginTop: 8 }}
          />

          {isLogin && (
            <View style={s.demoBox}>
              <Text style={s.demoTitle}>🚀 Demo Credentials (Pre-filled)</Text>
              <Text style={s.demoText}>Email: demo@businessmanager.local</Text>
              <Text style={s.demoText}>Pass: DemoPass123!</Text>
              <Text style={{ color: C.textLight, fontSize: 11, marginTop: 4 }}>Construction • Agriculture • Retail</Text>
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safeArea:  { flex: 1, backgroundColor: C.primaryDark },
  safeArea2: { flex: 1, backgroundColor: C.bg },
  welcomeBg: { flex: 1, backgroundColor: C.primaryDark },
  welcomeContent: { flex: 1, padding: 28, justifyContent: 'center' },
  logoBadge: { width: 72, height: 72, borderRadius: 20, backgroundColor: '#10B981', alignItems: 'center', justifyContent: 'center', marginBottom: 20 },
  logoText:  { color: '#fff', fontSize: 28, fontWeight: '900' },
  appTitle:  { fontSize: 34, fontWeight: '900', color: '#fff', marginBottom: 8 },
  appTagline:{ fontSize: 17, color: '#A7F3D0', lineHeight: 26, marginBottom: 20 },
  featureRow:{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
  featurePill:{ backgroundColor: 'rgba(255,255,255,0.12)', borderRadius: 20, paddingHorizontal: 12, paddingVertical: 5 },
  featurePillText: { color: '#D1FAE5', fontSize: 12, fontWeight: '600' },
  loginLink: { alignItems: 'center', marginBottom: 16 },
  loginLinkText: { color: '#A7F3D0', fontSize: 14, fontWeight: '600' },
  demoBox:   { backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 12, padding: 14, borderWidth: 1, borderColor: 'rgba(255,255,255,0.15)' },
  demoTitle: { color: '#A7F3D0', fontWeight: '800', marginBottom: 6, fontSize: 13 },
  demoText:  { color: '#D1FAE5', fontSize: 12, marginBottom: 2 },
  formContainer: { padding: 24, paddingTop: 16 },
  logoBadgeSmall: { width: 52, height: 52, borderRadius: 14, backgroundColor: C.primary, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  logoTextSmall: { color: '#fff', fontSize: 20, fontWeight: '900' },
  formTitle: { fontSize: 26, fontWeight: '900', color: C.textMain, marginBottom: 4 },
  formSub:   { fontSize: 14, color: C.textMuted, marginBottom: 20 },
  tabRow:    { flexDirection: 'row', backgroundColor: C.border, borderRadius: 12, padding: 3, marginBottom: 20 },
  tab:       { flex: 1, paddingVertical: 10, alignItems: 'center', borderRadius: 10 },
  tabActive: { backgroundColor: '#fff', shadowColor: '#000', shadowOpacity: 0.08, shadowRadius: 4, elevation: 2 },
  tabText:   { fontWeight: '600', color: C.textMuted },
  tabTextActive: { color: C.textMain, fontWeight: '800' },
  stepTitle: { fontSize: 24, fontWeight: '900', color: C.textMain, marginBottom: 6 },
  stepSub:   { fontSize: 14, color: C.textMuted, marginBottom: 24 },
  catLabel:  { fontSize: 11, fontWeight: '800', color: C.textMuted, letterSpacing: 0.5, marginBottom: 10, textTransform: 'uppercase' },
  catGrid:   { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 },
  catTile:   { width: '30%', borderRadius: 12, padding: 12, backgroundColor: C.surface, borderWidth: 1.5, borderColor: C.border, alignItems: 'center' },
  catTileActive: { borderColor: C.primary, backgroundColor: C.greenLight },
  catIcon:   { fontSize: 24, marginBottom: 4 },
  catLabel2: { fontSize: 11, fontWeight: '700', color: C.textMuted, textAlign: 'center' },
});
