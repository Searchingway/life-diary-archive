import { ChangeEvent, ReactNode, useState } from "react";
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
  const [renaming, setRenaming] = useState<string | null>(null);

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (files.length) onUpload?.(files);
  }

  function commit(next: EntryImage[]) {
    onChange(next);
    onCommit(next);
  }

  function removeImage(index: number) {
    commit(images.filter((_image, imageIndex) => imageIndex !== index));
  }

  function renameImage(index: number, label: string) {
    onChange(images.map((image, imageIndex) => (imageIndex === index ? { ...image, label } : image)));
  }

  function finishRename() {
    setRenaming(null);
    onCommit(images);
  }

  function dropImage(index: number) {
    if (dragIndex === null || dragIndex === index) {
      setDragIndex(null);
      return;
    }
    const next = [...images];
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
          <span className="text-sm text-muted-foreground">({images.length})</span>
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
      <div className="px-6 pb-6">
        {images.length === 0 ? (
          <div className="h-28 rounded-lg border border-dashed bg-secondary/35 flex items-center justify-center text-sm text-muted-foreground">
            还没有图片
          </div>
        ) : (
          <div className="grid grid-cols-4 gap-4">
            {images.map((image, index) => (
              <div
                key={`${image.file_name}-${index}`}
                className={`group relative rounded-lg border bg-card overflow-hidden ${dragIndex === index ? "opacity-50" : ""}`}
                draggable={editing}
                onDragStart={() => setDragIndex(index)}
                onDragOver={(event) => event.preventDefault()}
                onDrop={() => dropImage(index)}
              >
                {editing && (
                  <button
                    className="absolute right-2 top-2 z-10 size-7 rounded-full bg-background/90 border flex items-center justify-center shadow"
                    onClick={() => removeImage(index)}
                    title="删除图片"
                  >
                    <X className="size-4" />
                  </button>
                )}
                <a href={image.url} target="_blank" rel="noreferrer" className="block">
                  <img src={image.url} alt={image.label || image.file_name} className="aspect-square w-full object-cover bg-secondary" />
                </a>
                <div className="p-2 border-t">
                  {renaming === image.file_name ? (
                    <Input
                      autoFocus
                      value={image.label || ""}
                      onChange={(event) => renameImage(index, event.target.value)}
                      onBlur={finishRename}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") finishRename();
                      }}
                      className="h-8 text-xs"
                    />
                  ) : (
                    <button
                      className="w-full text-left text-xs truncate"
                      onDoubleClick={() => setRenaming(image.file_name)}
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
