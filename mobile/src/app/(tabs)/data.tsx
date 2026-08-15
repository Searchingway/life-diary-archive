import { useCallback, useEffect, useRef, useState } from "react";
import { Alert, StyleSheet, Text, View } from "react-native";
import { useFocusEffect, useLocalSearchParams } from "expo-router";
import Constants from "expo-constants";

import { ButtonRow, Panel, PrimaryButton, SecondaryButton } from "@/components/Controls";
import { Screen } from "@/components/Screen";
import { StatusBanner } from "@/components/StatusBanner";
import { useRepository } from "@/db/RepositoryContext";
import { applyDesktopCanonicalImport, createBackup, createMobileSnapshot, importLegacyArchive, legacyArchiveExists, loadDesktopCanonicalImport, pickAndRestoreBackup, pickDesktopCanonicalImport, type DesktopCanonicalImport } from "@/services/backup";
import { consumeIncomingUri } from "@/compat/incomingIntent";
import { clearExternalBackupDirectory, copyZipToExternalBackupDirectory, getExternalBackupDirectory, selectExternalBackupDirectory } from "@/services/externalBackup";
import { colors, spacing } from "@/theme";

export default function DataScreen() {
  const repository = useRepository();
  const [legacyAvailable, setLegacyAvailable] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState(false);
  const [canonicalImport, setCanonicalImport] = useState<DesktopCanonicalImport | null>(null);
  const [externalBackupDirectory, setExternalBackupDirectory] = useState<string | null>(null);
  const params = useLocalSearchParams<{ incoming?: string }>();
  const lastIncoming = useRef("");

  useFocusEffect(
    useCallback(() => {
      void legacyArchiveExists().then(setLegacyAvailable);
      void getExternalBackupDirectory(repository).then(setExternalBackupDirectory);
    }, [repository]),
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

  function selectExternalBackupDirectoryAction() {
    void run(
      async () => {
        const selected = await selectExternalBackupDirectory(repository);
        if (!selected) throw new Error("未授予外置备份目录权限");
        setExternalBackupDirectory(selected);
        return selected;
      },
      () => "外置备份目录已保存",
    );
  }

  function createExternalBackup() {
    void run(
      async () => {
        const directory = externalBackupDirectory ?? await getExternalBackupDirectory(repository);
        if (!directory) throw new Error("请先选择外置备份目录");
        const localZip = await createBackup(repository, false);
        try {
          return await copyZipToExternalBackupDirectory(directory, localZip);
        } catch (reason) {
          await clearExternalBackupDirectory(repository);
          setExternalBackupDirectory(null);
          throw new Error(`写入外置目录失败，已清除该目录授权，请重新选择。${reason instanceof Error ? ` ${reason.message}` : ""}`);
        }
      },
      () => "外置 ZIP 备份已写入所选目录",
    );
  }

  async function selectDesktopCanonical() {
    setBusy(true);
    setError(false);
    setMessage("");
    try {
      setCanonicalImport(await pickDesktopCanonicalImport());
    } catch (reason) {
      setError(true);
      setMessage(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    const uri = typeof params.incoming === "string" ? params.incoming : "";
    if (!uri || uri === lastIncoming.current || !consumeIncomingUri(uri)) return;
    lastIncoming.current = uri;
    setBusy(true);
    setError(false);
    setMessage("");
    void loadDesktopCanonicalImport(uri)
      .then(setCanonicalImport)
      .catch((reason) => {
        setError(true);
        setMessage(reason instanceof Error ? reason.message : String(reason));
      })
      .finally(() => setBusy(false));
  }, [params.incoming]);

  return (
    <Screen subtitle="备份包包含日记、足迹、历史接单、计划和图片" title="数据管理">
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
          <Text style={styles.title}>外置备份目录（Android）</Text>
          <Text style={styles.body}>手机记录和 SQLite 仍保存在应用私有目录；这里只保存你授权的 ZIP 输出位置，不迁移数据库。</Text>
          <Text style={styles.path}>{externalBackupDirectory || "尚未选择"}</Text>
          <ButtonRow>
            <SecondaryButton disabled={busy} label="选择目录" onPress={selectExternalBackupDirectoryAction} />
            <PrimaryButton disabled={busy || !externalBackupDirectory} label="备份到此目录" onPress={createExternalBackup} />
          </ButtonRow>
          {externalBackupDirectory ? <SecondaryButton disabled={busy} label="清除目录授权" onPress={() => void run(async () => { await clearExternalBackupDirectory(repository); setExternalBackupDirectory(null); }, () => "已清除外置备份目录") } /> : null}
        </View>
      </Panel>
      <Panel>
        <View style={styles.block}>
          <Text style={styles.title}>电脑同步</Text>
          <Text style={styles.body}>导出到电脑会生成 Mobile Snapshot ZIP；从电脑同步只接受 Desktop Canonical ZIP，确认前不会覆盖手机数据。</Text>
          <PrimaryButton disabled={busy} label="导出到电脑（Mobile Snapshot）" onPress={() => run(() => createMobileSnapshot(repository), () => "Mobile Snapshot ZIP 已生成")} />
          <SecondaryButton label="从电脑同步" onPress={() => { if (!busy) void selectDesktopCanonical(); }} />
          {canonicalImport ? <View style={styles.preview}>
            <Text style={styles.title}>来自电脑的人生档案同步包</Text>
            <Text style={styles.body}>生成时间：{canonicalImport.manifest.created_at}</Text>
            <Text style={styles.body}>日记 {canonicalImport.preview.diary} · 足迹 {canonicalImport.preview.footprints} · 计划 {canonicalImport.preview.plans} · 接单备忘 {canonicalImport.preview.orders}</Text>
            <Text style={styles.body}>电脑是正式数据源。继续后，手机共享模块将以电脑版本为准；当前手机数据会先自动备份。</Text>
            <ButtonRow>
              <SecondaryButton label="取消" onPress={() => { if (!busy) setCanonicalImport(null); }} />
              <PrimaryButton disabled={busy} label="同步到手机" onPress={() => run(async () => {
                const result = await applyDesktopCanonicalImport(repository, canonicalImport);
                setCanonicalImport(null);
                return result;
              }, (value) => `同步完成：${(value as { count: number }).count} 条记录；同步前备份已创建`)} />
            </ButtonRow>
          </View> : null}
        </View>
      </Panel>
      <Panel>
        <View style={styles.block}>
          <Text style={styles.title}>从 ZIP 恢复</Text>
          <Text style={styles.body}>恢复会替换当前日记、足迹、接单和计划记录。操作前自动保存安全备份。</Text>
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
      <Text style={styles.note}>版本 {Constants.expoConfig?.version ?? "dev"} · 构建 {Constants.nativeBuildVersion ?? "dev"} · 提交 {process.env.EXPO_PUBLIC_GIT_COMMIT?.slice(0, 12) ?? "dev"}</Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  block: { gap: spacing.sm },
  title: { color: colors.ink, fontSize: 17, fontWeight: "700" },
  body: { color: colors.muted, lineHeight: 21 },
  path: { color: colors.muted, fontSize: 12, lineHeight: 18 },
  note: { color: colors.muted, fontSize: 13, lineHeight: 20 },
  preview: { gap: spacing.sm, paddingTop: spacing.sm, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.line },
});
