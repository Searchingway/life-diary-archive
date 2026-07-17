import * as FileSystem from "expo-file-system/legacy";
import * as ImagePicker from "expo-image-picker";

import type { ImageRef } from "@/domain/models";

export const MEDIA_ROOT = `${FileSystem.documentDirectory}LifeDiaryMedia/`;

export async function ensureMediaRoot(): Promise<void> {
  await FileSystem.makeDirectoryAsync(MEDIA_ROOT, { intermediates: true });
}

function extension(uri: string): string {
  const match = uri.match(/\.([a-zA-Z0-9]{2,5})(?:\?.*)?$/);
  return match ? `.${match[1].toLowerCase()}` : ".jpg";
}

export async function pickImages(): Promise<ImageRef[]> {
  const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (!permission.granted) throw new Error("需要允许访问照片，才能添加图片。");
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ["images"],
    allowsMultipleSelection: true,
    quality: 0.92,
  });
  if (result.canceled) return [];

  await ensureMediaRoot();
  const images: ImageRef[] = [];
  for (const asset of result.assets) {
    const fileName = `${Date.now()}-${Math.random().toString(16).slice(2)}${extension(asset.uri)}`;
    const uri = `${MEDIA_ROOT}${fileName}`;
    await FileSystem.copyAsync({ from: asset.uri, to: uri });
    images.push({ fileName, uri, label: "" });
  }
  return images;
}

export async function removeStoredImage(image: ImageRef): Promise<void> {
  if (!image.uri.startsWith(MEDIA_ROOT)) return;
  await FileSystem.deleteAsync(image.uri, { idempotent: true });
}

export async function copyImageIntoMedia(sourceUri: string, preferredName: string): Promise<string> {
  await ensureMediaRoot();
  const safeName = preferredName.replace(/[^a-zA-Z0-9._-]/g, "_") || `${Date.now()}.jpg`;
  let destination = `${MEDIA_ROOT}${safeName}`;
  const info = await FileSystem.getInfoAsync(destination);
  if (info.exists) destination = `${MEDIA_ROOT}${Date.now()}-${safeName}`;
  await FileSystem.copyAsync({ from: sourceUri, to: destination });
  return destination;
}
