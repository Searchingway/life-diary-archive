import { MaterialCommunityIcons } from "@expo/vector-icons";
import { Tabs } from "expo-router";

import { colors } from "@/theme";

const icons: Record<string, keyof typeof MaterialCommunityIcons.glyphMap> = {
  index: "home-variant-outline",
  diary: "book-open-page-variant-outline",
  footprints: "map-marker-path",
  orders: "briefcase-check-outline",
  data: "database-cog-outline",
};

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: {
          height: 66,
          paddingTop: 5,
          paddingBottom: 7,
          borderTopColor: colors.line,
          backgroundColor: colors.surface,
        },
        tabBarIcon: ({ color, size }) => (
          <MaterialCommunityIcons color={color} name={icons[route.name] ?? "circle-outline"} size={size} />
        ),
      })}
    >
      <Tabs.Screen name="index" options={{ title: "首页" }} />
      <Tabs.Screen name="diary" options={{ title: "日记" }} />
      <Tabs.Screen name="footprints" options={{ title: "足迹" }} />
      <Tabs.Screen name="orders" options={{ title: "接单" }} />
      <Tabs.Screen name="data" options={{ title: "数据" }} />
    </Tabs>
  );
}
