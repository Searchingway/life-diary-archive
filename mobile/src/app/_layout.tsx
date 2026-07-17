import { DefaultTheme, ThemeProvider } from "expo-router";
import { StatusBar } from "expo-status-bar";

import { RepositoryProvider } from "@/db/RepositoryContext";
import { colors } from "@/theme";

const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: colors.ink,
    background: colors.paper,
    card: colors.surface,
    text: colors.ink,
    border: colors.line,
  },
};

export default function RootLayout() {
  return (
    <ThemeProvider value={theme}>
      <RepositoryProvider />
      <StatusBar style="dark" />
    </ThemeProvider>
  );
}
