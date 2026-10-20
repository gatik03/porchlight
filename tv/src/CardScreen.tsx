import React, { useEffect, useRef } from "react";
import {
  Animated,
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { THEME } from "./theme";
import { Card } from "./usePolling";

interface CardScreenProps {
  card: Card;
  onDismiss: () => void;
}

export const CardScreen: React.FC<CardScreenProps> = ({ card, onDismiss }) => {
  const flashAnim = useRef(new Animated.Value(1.0)).current;

  // Auto-dismiss after 90 seconds
  useEffect(() => {
    const timer = setTimeout(onDismiss, 90000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  // Flashing border animation: 8 seconds duration
  useEffect(() => {
    let animLoop: Animated.CompositeAnimation | null = null;
    const isAttention = card.severity === "attention";
    const duration = isAttention ? 250 : 500; // 2Hz for attention, 1Hz for calm

    if (card.severity !== "info") {
      animLoop = Animated.loop(
        Animated.sequence([
          Animated.timing(flashAnim, {
            toValue: 0.2,
            duration,
            useNativeDriver: true,
          }),
          Animated.timing(flashAnim, {
            toValue: 1.0,
            duration,
            useNativeDriver: true,
          }),
        ])
      );
      animLoop.start();

      // Stop flashing and stay solid after 8 seconds
      const stopTimer = setTimeout(() => {
        if (animLoop) animLoop.stop();
        Animated.timing(flashAnim, {
          toValue: 1.0,
          duration: 300,
          useNativeDriver: true,
        }).start();
      }, 8000);

      return () => {
        clearTimeout(stopTimer);
        if (animLoop) animLoop.stop();
      };
    }
  }, [card.severity, flashAnim]);

  const severityColor =
    card.severity === "calm"
      ? THEME.colors.calm
      : card.severity === "attention"
      ? THEME.colors.attention
      : THEME.colors.info;

  return (
    <View style={styles.container}>
      {/* 24px Visual Chime Border */}
      <Animated.View
        style={[
          styles.flashingBorder,
          { borderColor: severityColor, opacity: flashAnim },
        ]}
      />

      <View style={styles.content}>
        {/* Severity Header */}
        <View style={styles.header}>
          <View
            style={[styles.badge, { backgroundColor: severityColor + "33" }]}
          >
            <Text style={[styles.badgeText, { color: severityColor }]}>
              {card.severity.toUpperCase()}
            </Text>
          </View>
          <Text style={styles.headerTitle}>{card.headline}</Text>
        </View>

        {/* 72px Main Sentence */}
        <Text style={styles.sentence}>{card.sentence}</Text>

        {/* 48px Expected Visitor Context */}
        {card.expectedLine && (
          <Text style={styles.expectedLine}>{card.expectedLine}</Text>
        )}

        {/* Bottom Metadata & Dismiss */}
        <View style={styles.footer}>
          <Text style={styles.metadata}>
            {card.deviceName} • {card.timeLocal}
          </Text>

          {card.frameUrl && (
            <Image source={{ uri: card.frameUrl }} style={styles.frameThumbnail} />
          )}

          <TouchableOpacity
            style={styles.dismissButton}
            onPress={onDismiss}
            hasTVPreferredFocus={true}
          >
            <Text style={styles.dismissButtonText}>Dismiss (Select)</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.colors.bgDeep,
  },
  flashingBorder: {
    ...StyleSheet.absoluteFillObject,
    borderWidth: THEME.border.flashingWidth,
    zIndex: 10,
    pointerEvents: "none",
  },
  content: {
    flex: 1,
    justifyContent: "space-between",
    paddingHorizontal: THEME.margins.safeHorizontal + 24,
    paddingVertical: THEME.margins.safeVertical + 24,
    zIndex: 20,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 20,
  },
  badge: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 8,
  },
  badgeText: {
    fontSize: 24,
    fontWeight: "bold",
    letterSpacing: 1,
  },
  headerTitle: {
    fontSize: THEME.typography.metaSize,
    color: THEME.colors.textSecondary,
    fontWeight: "500",
  },
  sentence: {
    fontSize: THEME.typography.headlineSize,
    lineHeight: THEME.typography.headlineLineHeight,
    fontWeight: "bold",
    color: THEME.colors.textPrimary,
    marginVertical: 24,
  },
  expectedLine: {
    fontSize: THEME.typography.expectedSize,
    color: THEME.colors.calm,
    fontWeight: "600",
    marginBottom: 20,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  metadata: {
    fontSize: THEME.typography.metaSize,
    color: THEME.colors.textSecondary,
  },
  frameThumbnail: {
    width: 320,
    height: 180,
    borderRadius: 12,
  },
  dismissButton: {
    backgroundColor: THEME.colors.surfaceCard,
    paddingHorizontal: 36,
    paddingVertical: 18,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: "#FFFFFF",
  },
  dismissButtonText: {
    fontSize: THEME.typography.buttonSize,
    color: THEME.colors.textPrimary,
    fontWeight: "600",
  },
});
