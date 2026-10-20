import React, { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { THEME } from "./theme";

export const IdleScreen: React.FC = () => {
  const [timeStr, setTimeStr] = useState("");

  useEffect(() => {
    function updateClock() {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      );
    }
    updateClock();
    const interval = setInterval(updateClock, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.clock}>{timeStr}</Text>
        <Text style={styles.deviceName}>Front Door</Text>
      </View>
      <View style={styles.footer}>
        <Text style={styles.ambientText}>
          Porchlight is watching the front door
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.colors.bgDeep,
    justifyContent: "space-between",
    paddingHorizontal: THEME.margins.safeHorizontal,
    paddingVertical: THEME.margins.safeVertical,
  },
  content: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  clock: {
    fontSize: 96,
    fontWeight: "300",
    color: THEME.colors.textPrimary,
    letterSpacing: 2,
  },
  deviceName: {
    fontSize: THEME.typography.metaSize,
    color: THEME.colors.textSecondary,
    marginTop: 16,
  },
  footer: {
    alignItems: "center",
    paddingBottom: 24,
  },
  ambientText: {
    fontSize: THEME.typography.ambientSize,
    color: THEME.colors.textMuted,
    opacity: 0.15,
  },
});
