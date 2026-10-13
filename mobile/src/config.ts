import { Platform } from 'react-native';

// For Physical Phone via Wi-Fi: PC IP is 192.168.1.8
// For Android Studio Emulator: 10.0.2.2 reaches the host PC
// For Web Browser: localhost:8000
export const DEFAULT_LAN_IP = '192.168.1.8';

export const getApiBaseUrl = () => {
  if (Platform.OS === 'web') {
    return 'http://127.0.0.1:8000';
  }
  // Default to LAN IP so physical devices on Wi-Fi connect seamlessly
  return `http://${DEFAULT_LAN_IP}:8000`;
};

export const API_BASE_URL = getApiBaseUrl();
