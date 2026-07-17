import { useCallback, useState } from "react";
import { Alert, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "expo-router";

import { Panel, PrimaryButton, SecondaryButton } from "@/components/Controls";
import { Screen } from "@/components/Screen";
import { StatusBanner } from "@/components/StatusBanner";
import { useRepository } from "@/db/RepositoryContext";
import { createBackup, importLegacyArchive, legacyArchiveExists, pickAndRestoreBackup } from "@/services/backup";
import { colors, spacing } from "@/theme";

export default function DataScreen() {
  const repository = useRepository();
  const [legacyAvailable, setLegacyAvailable] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState(false);

  useFocusEffect(
    useCallback(() => {
      void legacyArchiveExists().then(setLegacyAvailable);
    }, []),
  );

  async function run(action: () => Promise<unknown>, success: (value: unknown) => string) {
    setBusy(true);
    setError(false);
    setMessage("");
    try {
      const value = await action();
      setMessage(success(value));
    } catch (reason) {
      setError(true);
      setMessage(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(false);
    }
  }

  function restore() {
    Alert.alert("恢复备份", "恢复前会先自动生成一份当前数据安全备份，然后用所选备份替换当前记录。", [
      { text: "取消", style: "cancel" },
      {
        text: "选择备份",
        onPress: () =>
          run(
            () => pickAndRestoreBackup(repository),
            (value) => (value === null ? "已取消选择" : `已恢复 ${value} 条记录`),
          ),
      },
    ]);
  }

  function importLegacy() {
    Alert.alert("导入旧版数据", "会先备份当前数据，再导入旧 Qt 应用留下的 Diary 目录。", [
      { text: "取消", style: "cancel" },
      {
        text: "开始导入",
        onPress: () => run(() => importLegacyArchive(repository), (value) => `已导入 ${value} 条旧版记录`),
      },
    ]);
  }

  return (
    <Screen subtitle="备份包包含文字、状态、足迹访问和图片" title="数据管理">
      <StatusBanner error={error} text={message} />
      <Panel>
        <View style={styles.block}>
          <Text style={styles.title}>导出完整备份</Text>
          <Text style={styles.body}>生成标准 ZIP，通过系统分享保存到文件、网盘或电脑。</Text>
          <PrimaryButton
            disabled={busy}
            label={busy ? "处理中……" : "导出 ZIP 备份"}
            onPress={() => run(() => createBackup(repository), () => "备份已生成")}
          />
        </View>
      </Panel>
      <Panel>
        <View style={styles.block}>
          <Text style={styles.title}>从 ZIP 恢复</Text>
          <Text style={styles.body}>恢复会替换当前三类记录。操作前自动保存安全备份。</Text>
          <SecondaryButton label="选择 ZIP 并恢复" onPress={restore} />
        </View>
      </Panel>
      <Panel>
        <View style={styles.block}>
          <Text style={styles.title}>旧 Qt 数据迁移</Text>
          <Text style={styles.body}>
            {legacyAvailable ? "已检测到旧版 Diary 数据目录，可直接迁移。" : "当前未检测到旧版 Diary 数据目录。"}
          </Text>
          {legacyAvailable ? <SecondaryButton label="导入旧版数据" onPress={importLegacy} /> : null}
        </View>
      </Panel>
      <Text style={styles.note}>
        应用不会上传你的记录。卸载应用前请先导出 ZIP 备份；Android 卸载会清除应用私有目录。
      </Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  block: { gap: spacing.sm },
  title: { color: colors.ink, fontSize: 17, fontWeight: "700" },
  body: { color: colors.muted, lineHeight: 21 },
  note: { color: colors.muted, fontSize: 13, lineHeight: 20 },
});
