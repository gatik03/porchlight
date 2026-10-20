import React from "react";
import { StyleSheet, View } from "react-native";
import { CardScreen } from "./CardScreen";
import { IdleScreen } from "./IdleScreen";
import { usePolling } from "./usePolling";
import { API_BASE_URL, PASSPHRASE } from "./config";

export default function App() {
  const { currentCard, dismiss } = usePolling(API_BASE_URL, PASSPHRASE);

  return (
    <View style={styles.root}>
      {currentCard && !currentCard.dismissedAt ? (
        <CardScreen card={currentCard} onDismiss={dismiss} />
      ) : (
        <IdleScreen />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#0A0A0C",
  },
});
