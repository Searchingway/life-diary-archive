import { Stack } from "expo-router";
import { createContext, useContext, useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { colors } from "@/theme";

import { getRecordRepository } from "./database";
import type { RecordRepository } from "./repository";

const RepositoryContext = createContext<RecordRepository | null>(null);

export function RepositoryProvider() {
  const [repository, setRepository] = useState<RecordRepository | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getRecordRepository().then(setRepository).catch((reason) => setError(String(reason)));
  }, []);

  if (!repository) {
    return (
      <View style={styles.loading}>
        {error ? (
          <>
            <Text style={styles.errorTitle}>本地数据库初始化失败</Text>
            <Text style={styles.errorBody}>{error}</Text>
          </>
        ) : (
          <>
            <ActivityIndicator color={colors.accent} size="large" />
            <Text style={styles.loadingText}>正在打开人生档案</Text>
          </>
        )}
      </View>
    );
  }

  return (
    <RepositoryContext.Provider value={repository}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
      </Stack>
    </RepositoryContext.Provider>
  );
}

export function useRepository(): RecordRepository {
  const repository = useContext(RepositoryContext);
  if (!repository) throw new Error("RepositoryProvider 尚未初始化");
  return repository;
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 14,
    padding: 28,
    backgroundColor: colors.paper,
  },
  loadingText: { color: colors.muted, fontSize: 15 },
  errorTitle: { color: colors.danger, fontSize: 18, fontWeight: "700" },
  errorBody: { color: colors.muted, lineHeight: 21, textAlign: "center" },
});
