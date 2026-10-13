/**
 * Shared UI primitives used across all screens.
 */
import React from 'react';
import {
  View, Text, TouchableOpacity, ActivityIndicator,
  StyleSheet, TextInput, TextInputProps, ViewStyle, TextStyle,
} from 'react-native';

// ── Design tokens ─────────────────────────────────────────────────────────────
export const C = {
  bg:           '#F3F4F6',
  surface:      '#FFFFFF',
  surfaceAlt:   '#F9FAFB',
  border:       '#E5E7EB',
  green:        '#059669',
  greenLight:   '#D1FAE5',
  greenDark:    '#065F46',
  amber:        '#D97706',
  amberLight:   '#FEF3C7',
  red:          '#DC2626',
  redLight:     '#FEE2E2',
  blue:         '#2563EB',
  blueLight:    '#DBEAFE',
  purple:       '#7C3AED',
  purpleLight:  '#EDE9FE',
  textMain:     '#111827',
  textMuted:    '#6B7280',
  textLight:    '#9CA3AF',
  primary:      '#059669',
  primaryDark:  '#065F46',
};

// ── Card ─────────────────────────────────────────────────────────────────────
export const Card = ({
  children, style, onPress,
}: { children: React.ReactNode; style?: ViewStyle; onPress?: () => void }) => {
  const Inner = <View style={[s.card, style]}>{children}</View>;
  if (onPress) return <TouchableOpacity onPress={onPress} activeOpacity={0.75}>{Inner}</TouchableOpacity>;
  return Inner;
};

// ── StatCard ─────────────────────────────────────────────────────────────────
export const StatCard = ({
  label, value, sub, color, onPress,
}: { label: string; value: string; sub?: string; color?: string; onPress?: () => void }) => (
  <TouchableOpacity style={s.statCard} onPress={onPress} activeOpacity={0.8}>
    <Text style={s.statLabel}>{label}</Text>
    <Text style={[s.statValue, color ? { color } : {}]}>{value}</Text>
    {sub && <Text style={s.statSub}>{sub}</Text>}
  </TouchableOpacity>
);

// ── PrimaryButton ────────────────────────────────────────────────────────────
export const PrimaryBtn = ({
  label, onPress, loading, disabled, color, style,
}: { label: string; onPress: () => void; loading?: boolean; disabled?: boolean; color?: string; style?: ViewStyle }) => (
  <TouchableOpacity
    style={[s.primaryBtn, { backgroundColor: color || C.primary }, disabled && { opacity: 0.55 }, style]}
    onPress={onPress}
    disabled={disabled || loading}
    activeOpacity={0.8}
  >
    {loading
      ? <ActivityIndicator color="#fff" size="small" />
      : <Text style={s.primaryBtnText}>{label}</Text>}
  </TouchableOpacity>
);

// ── SecondaryButton ───────────────────────────────────────────────────────────
export const SecondaryBtn = ({
  label, onPress, style,
}: { label: string; onPress: () => void; style?: ViewStyle }) => (
  <TouchableOpacity style={[s.secondaryBtn, style]} onPress={onPress} activeOpacity={0.8}>
    <Text style={s.secondaryBtnText}>{label}</Text>
  </TouchableOpacity>
);

// ── Input ────────────────────────────────────────────────────────────────────
export const Input = ({
  label, style, ...props
}: TextInputProps & { label?: string; style?: ViewStyle }) => (
  <View style={[{ marginBottom: 12 }, style]}>
    {label && <Text style={s.inputLabel}>{label}</Text>}
    <TextInput
      style={s.input}
      placeholderTextColor={C.textLight}
      {...props}
    />
  </View>
);

// ── Badge ────────────────────────────────────────────────────────────────────
export const Badge = ({
  label, color = C.green, bg,
}: { label: string; color?: string; bg?: string }) => (
  <View style={[s.badge, { backgroundColor: bg || C.greenLight }]}>
    <Text style={[s.badgeText, { color }]}>{label}</Text>
  </View>
);

// ── SectionHeader ─────────────────────────────────────────────────────────────
export const SectionHeader = ({
  title, subtitle, right,
}: { title: string; subtitle?: string; right?: React.ReactNode }) => (
  <View style={s.sectionHeader}>
    <View style={{ flex: 1 }}>
      <Text style={s.sectionTitle}>{title}</Text>
      {subtitle && <Text style={s.sectionSub}>{subtitle}</Text>}
    </View>
    {right}
  </View>
);

// ── SmallBtn ──────────────────────────────────────────────────────────────────
export const SmallBtn = ({
  label, onPress, color = C.primary,
}: { label: string; onPress: () => void; color?: string }) => (
  <TouchableOpacity
    style={[s.smallBtn, { backgroundColor: color + '18', borderColor: color + '40' }]}
    onPress={onPress}
    activeOpacity={0.75}
  >
    <Text style={[s.smallBtnText, { color }]}>{label}</Text>
  </TouchableOpacity>
);

// ── EmptyState ───────────────────────────────────────────────────────────────
export const EmptyState = ({
  icon, title, subtitle,
}: { icon: string; title: string; subtitle?: string }) => (
  <View style={s.emptyState}>
    <Text style={s.emptyIcon}>{icon}</Text>
    <Text style={s.emptyTitle}>{title}</Text>
    {subtitle && <Text style={s.emptySub}>{subtitle}</Text>}
  </View>
);

// ── Loader ────────────────────────────────────────────────────────────────────
export const Loader = ({ text }: { text?: string }) => (
  <View style={s.loader}>
    <ActivityIndicator size="large" color={C.primary} />
    {text && <Text style={s.loaderText}>{text}</Text>}
  </View>
);

// ── Divider ───────────────────────────────────────────────────────────────────
export const Divider = () => <View style={s.divider} />;

// ── Row ───────────────────────────────────────────────────────────────────────
export const Row = ({
  children, style,
}: { children: React.ReactNode; style?: ViewStyle }) => (
  <View style={[{ flexDirection: 'row', alignItems: 'center' }, style]}>{children}</View>
);

// ── Styles ────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  card: {
    backgroundColor: C.surface, borderRadius: 14, padding: 16,
    marginBottom: 12, shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.06, shadowRadius: 4,
    elevation: 2, borderWidth: 1, borderColor: C.border,
  },
  statCard: {
    flex: 1, backgroundColor: C.surface, borderRadius: 12, padding: 14,
    margin: 4, borderWidth: 1, borderColor: C.border, elevation: 1,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05, shadowRadius: 3,
  },
  statLabel: { fontSize: 10, fontWeight: '700', color: C.textMuted, letterSpacing: 0.5, textTransform: 'uppercase' },
  statValue: { fontSize: 20, fontWeight: '800', color: C.textMain, marginTop: 4 },
  statSub:   { fontSize: 11, color: C.textLight, marginTop: 2 },
  primaryBtn: {
    borderRadius: 12, paddingVertical: 14, alignItems: 'center', justifyContent: 'center',
  },
  primaryBtnText: { color: '#fff', fontWeight: '800', fontSize: 15 },
  secondaryBtn: {
    borderRadius: 12, paddingVertical: 12, alignItems: 'center',
    borderWidth: 1.5, borderColor: C.border, backgroundColor: C.surfaceAlt,
  },
  secondaryBtnText: { color: C.textMain, fontWeight: '700', fontSize: 14 },
  inputLabel: { fontSize: 12, fontWeight: '700', color: C.textMuted, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.4 },
  input: {
    borderWidth: 1.5, borderColor: C.border, borderRadius: 10, paddingHorizontal: 14,
    paddingVertical: 12, fontSize: 15, color: C.textMain, backgroundColor: C.surface,
  },
  badge: { borderRadius: 20, paddingHorizontal: 10, paddingVertical: 3, alignSelf: 'flex-start' },
  badgeText: { fontSize: 11, fontWeight: '800', letterSpacing: 0.3 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 10, marginTop: 4 },
  sectionTitle:  { fontSize: 16, fontWeight: '800', color: C.textMain },
  sectionSub:    { fontSize: 12, color: C.textMuted, marginTop: 2 },
  smallBtn: {
    borderRadius: 8, paddingHorizontal: 12, paddingVertical: 6, borderWidth: 1,
    alignSelf: 'flex-start',
  },
  smallBtnText: { fontSize: 12, fontWeight: '700' },
  emptyState: { alignItems: 'center', paddingVertical: 40 },
  emptyIcon:  { fontSize: 44, marginBottom: 12 },
  emptyTitle: { fontSize: 16, fontWeight: '700', color: C.textMuted },
  emptySub:   { fontSize: 13, color: C.textLight, marginTop: 6, textAlign: 'center' },
  loader:     { flex: 1, alignItems: 'center', justifyContent: 'center', paddingVertical: 40 },
  loaderText: { marginTop: 12, color: C.textMuted, fontSize: 14 },
  divider:    { height: 1, backgroundColor: C.border, marginVertical: 8 },
});
