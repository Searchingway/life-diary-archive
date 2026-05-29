import { ChangeEvent, DragEvent, ReactNode, useEffect, useMemo, useState } from "react";
import { Image as ImageIcon, Pencil, Plus, X } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { EntryImage } from "../../lib/api";

interface ImageManagerProps {
  title?: string;
  images: EntryImage[];
  onUpload?: (files: File[]) => void;
  onChange: (images: EntryImage[]) => void;
  onCommit: (images: EntryImage[]) => void;
  extraAction?: ReactNode;
}

export function ImageManager({
  title = "图片",
  images,
  onUpload,
  onChange,
  onCommit,
  extraAction,
}: ImageManagerProps) {
  const [editing, setEditing] = useState(false);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [fileDragActive, setFileDragActive] = useState(false);
  const [renamingIndex, setRenamingIndex] = useState<number | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [localImages, setLocalImages] = useState<EntryImage[]>(images);
  const imageSignature = useMemo(
    () => images.map((image) => `${image.file_name}:${image.label || ""}:${image.url}`).join("|"),
    [images],
  );

  useEffect(() => {
    if (renamingIndex === null && dragIndex === null) {
      setLocalImages(images);
    }
  }, [imageSignature, renamingIndex, dragIndex, images]);

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    uploadFiles(files);
  }

  function uploadFiles(files: File[]) {
    const imageFiles = files.filter((file) => file.type.startsWith("image/") || /\.(png|jpe?g|gif|webp|bmp)$/i.test(file.name));
    if (imageFiles.length) onUpload?.(imageFiles);
  }

  function handleFileDrag(event: DragEvent<HTMLDivElement>) {
    if (!onUpload) return;
    if (dragIndex !== null) return;
    if (event.dataTransfer.types.includes("application/x-life-diary-image-index")) return;
    event.preventDefault();
    if (event.dataTransfer.types.includes("Files") && !fileDragActive) {
      setFileDragActive(true);
    }
  }

  function handleFileDrop(event: DragEvent<HTMLDivElement>) {
    if (!onUpload) return;
    if (dragIndex !== null) return;
    if (event.dataTransfer.types.includes("application/x-life-diary-image-index")) return;
    event.preventDefault();
    setFileDragActive(false);
    uploadFiles(Array.from(event.dataTransfer.files ?? []));
  }

  function commit(next: EntryImage[]) {
    setLocalImages(next);
    onChange(next);
    onCommit(next);
  }

  function removeImage(index: number) {
    commit(localImages.filter((_image, imageIndex) => imageIndex !== index));
  }

  function beginRename(index: number) {
    const image = localImages[index];
    if (!image) return;
    setRenamingIndex(index);
    setRenameDraft(image.label || "");
  }

  function finishRename(index: number) {
    const target = localImages[index];
    if (!target) {
      cancelRename();
      return;
    }
    const next = localImages.map((image, imageIndex) => (imageIndex === index ? { ...image, label: renameDraft.trim() } : image));
    setRenamingIndex(null);
    setRenameDraft("");
    commit(next);
  }

  function cancelRename() {
    setRenamingIndex(null);
    setRenameDraft("");
  }

  function dropImage(index: number, event: DragEvent<HTMLDivElement>) {
    if (!event.dataTransfer.types.includes("application/x-life-diary-image-index") && event.dataTransfer.files.length > 0) {
      handleFileDrop(event);
      return;
    }
    if (dragIndex === null || dragIndex === index) {
      setDragIndex(null);
      return;
    }
    const next = [...localImages];
    const [moved] = next.splice(dragIndex, 1);
    next.splice(index, 0, moved);
    setDragIndex(null);
    commit(next);
  }

  return (
    <div className="border-t">
      <div className="px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ImageIcon className="size-4" />
          <span className="font-medium">{title}</span>
          <span className="text-sm text-muted-foreground">({localImages.length})</span>
        </div>
        <div className="flex items-center gap-2">
          {extraAction}
          <Button variant={editing ? "default" : "outline"} size="sm" onClick={() => setEditing((value) => !value)}>
            <Pencil className="size-4" />
            编辑
          </Button>
          {onUpload && (
            <Button variant="outline" size="sm" asChild>
              <label>
                <Plus className="size-4" />
                插入
                <input className="hidden" type="file" accept="image/*" multiple onChange={handleFiles} />
              </label>
            </Button>
          )}
        </div>
      </div>
      <div
        className="px-6 pb-3 max-h-[196px] overflow-y-auto overscroll-contain pr-4"
        onDragEnter={handleFileDrag}
        onDragOver={handleFileDrag}
        onDragLeave={(event) => {
          if (event.currentTarget === event.target) setFileDragActive(false);
        }}
        onDrop={handleFileDrop}
      >
        {localImages.length === 0 ? (
          <div
            className={`h-28 rounded-lg border border-dashed flex items-center justify-center text-sm transition-colors ${
              fileDragActive ? "border-primary bg-primary/10 text-primary" : "bg-secondary/35 text-muted-foreground"
            }`}
          >
            {fileDragActive ? "松开即可插入图片" : "还没有图片，拖入图片即可插入"}
          </div>
        ) : (
          <div
            className={`grid grid-cols-5 gap-3 rounded-lg transition-colors ${
              fileDragActive ? "outline outline-2 outline-primary outline-offset-4 bg-primary/5" : ""
            }`}
          >
            {localImages.map((image, index) => (
              <div
                key={`${image.file_name}-${index}`}
                className={`group relative rounded-lg border bg-card overflow-hidden min-h-[0] ${dragIndex === index ? "opacity-50" : ""}`}
                draggable={editing}
                onDragStart={(event) => {
                  if (!editing) {
                    event.preventDefault();
                    return;
                  }
                  event.dataTransfer.setData("application/x-life-diary-image-index", String(index));
                  event.dataTransfer.effectAllowed = "move";
                  setDragIndex(index);
                }}
                onDragEnd={() => {
                  setDragIndex(null);
                  setFileDragActive(false);
                }}
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => dropImage(index, event)}
                onDoubleClick={(event) => {
                  event.preventDefault();
                  beginRename(index);
                }}
              >
                {editing && (
                  <button
                    type="button"
                    className="absolute right-2 top-2 z-10 size-7 rounded-full bg-background/90 border flex items-center justify-center shadow"
                    onClick={(event) => {
                      event.stopPropagation();
                      removeImage(index);
                    }}
                    title="删除图片"
                  >
                    <X className="size-4" />
                  </button>
                )}
                <button
                  type="button"
                  className="block w-full bg-secondary/35"
                  draggable={false}
                  onDoubleClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    beginRename(index);
                  }}
                  title="双击改名"
                >
                  <img
                    src={image.url}
                    alt={image.label || image.file_name}
                    className="h-28 w-full object-contain bg-secondary/35"
                    draggable={false}
                    loading="eager"
                    decoding="sync"
                  />
                </button>
                <div className="p-2 border-t">
                  {renamingIndex === index ? (
                    <Input
                      autoFocus
                      value={renameDraft}
                      onChange={(event) => setRenameDraft(event.target.value)}
                      onBlur={() => finishRename(index)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          event.currentTarget.blur();
                        }
                        if (event.key === "Escape") {
                          event.preventDefault();
                          cancelRename();
                        }
                      }}
                      className="h-8 text-xs"
                    />
                  ) : (
                    <button
                      type="button"
                      className="w-full text-left text-xs truncate"
                      onDoubleClick={(event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        beginRename(index);
                      }}
                      title="双击改名"
                    >
                      {image.label || image.file_name}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
