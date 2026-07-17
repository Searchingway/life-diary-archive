import { Image, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { ButtonRow, SecondaryButton } from "@/components/Controls";
import type { ImageRef } from "@/domain/models";
import { pickImages, removeStoredImage } from "@/services/images";
import { colors, spacing } from "@/theme";

export function ImageStrip({
  images,
  onChange,
  title = "图片记录",
}: {
  images: ImageRef[];
  onChange: (images: ImageRef[]) => void;
  title?: string;
}) {
  async function add() {
    const selected = await pickImages();
    if (selected.length) onChange([...images, ...selected]);
  }

  async function remove(index: number) {
    await removeStoredImage(images[index]);
    onChange(images.filter((_, itemIndex) => itemIndex !== index));
  }

  function move(index: number, delta: number) {
    const target = index + delta;
    if (target < 0 || target >= images.length) return;
    const next = [...images];
    [next[index], next[target]] = [next[target], next[index]];
    onChange(next);
  }

  return (
    <View style={styles.root}>
      <View style={styles.heading}>
        <Text style={styles.title}>{title}</Text>
        <SecondaryButton label="添加图片" onPress={add} />
      </View>
      {images.length ? (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.list}>
          {images.map((image, index) => (
            <View key={`${image.uri}-${index}`} style={styles.card}>
              <Image source={{ uri: image.uri }} style={styles.image} />
              <TextInput
                onChangeText={(label) =>
                  onChange(images.map((item, itemIndex) => (itemIndex === index ? { ...item, label } : item)))
                }
                placeholder="图片说明"
                placeholderTextColor="#929AA1"
                style={styles.caption}
                value={image.label}
              />
              <ButtonRow>
                <SecondaryButton label="前移" onPress={() => move(index, -1)} />
                <SecondaryButton label="后移" onPress={() => move(index, 1)} />
                <SecondaryButton danger label="删除" onPress={() => remove(index)} />
              </ButtonRow>
            </View>
          ))}
        </ScrollView>
      ) : (
        <Text style={styles.empty}>还没有图片。图片只保存在本机和你的备份包中。</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { gap: spacing.sm },
  heading: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  title: { color: colors.ink, fontSize: 17, fontWeight: "700" },
  list: { gap: spacing.sm, paddingVertical: 2 },
  card: {
    width: 244,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.line,
    padding: spacing.sm,
    gap: spacing.sm,
    backgroundColor: colors.surface,
  },
  image: { width: "100%", aspectRatio: 4 / 3, borderRadius: 5, backgroundColor: colors.paper },
  caption: {
    minHeight: 40,
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 6,
    paddingHorizontal: 10,
    color: colors.ink,
  },
  empty: { color: colors.muted, lineHeight: 20 },
});
