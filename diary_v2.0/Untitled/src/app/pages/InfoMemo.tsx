import { ReactNode, useEffect, useState } from "react";
import { Download, Eye, FileText, Plus, Save, Search } from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { RecordItem, exportNotesMarkdown, listRecords, saveRecord } from "../lib/api";

function draftNote(): RecordItem {
  return {
    id: "",
    title: "",
    subtitle: "信息备忘",
    body: "",
    date: new Date().toISOString().slice(0, 10),
    updated_at: "",
    type: "Markdown",
    status: "草稿",
    extra: { note_type: "Markdown", status: "草稿" },
  };
}

function inlineCode(text: string): ReactNode[] {
  return text.split(/(`[^`]+`)/g).map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={index} className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.9em]">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

function renderMarkdown(markdown: string): ReactNode[] {
  const lines = markdown.split(/\r?\n/);
  const blocks: ReactNode[] = [];
  let listItems: string[] = [];
  let codeLines: string[] = [];
  let inCode = false;

  function flushList() {
    if (!listItems.length) return;
    blocks.push(
      <ul key={`list-${blocks.length}`} className="list-disc space-y-1 pl-5">
        {listItems.map((item, index) => (
          <li key={`${item}-${index}`}>{inlineCode(item)}</li>
        ))}
      </ul>,
    );
    listItems = [];
  }

  function flushCode() {
    blocks.push(
      <pre key={`code-${blocks.length}`} className="overflow-x-auto rounded-md bg-muted p-3 text-sm">
        <code>{codeLines.join("\n")}</code>
      </pre>,
    );
    codeLines = [];
  }

  lines.forEach((line) => {
    if (line.trim().startsWith("```")) {
      if (inCode) {
        flushCode();
        inCode = false;
      } else {
        flushList();
        inCode = true;
      }
      return;
    }

    if (inCode) {
      codeLines.push(line);
      return;
    }

    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      return;
    }

    const heading = /^(#{1,3})\s+(.+)$/.exec(trimmed);
    if (heading) {
      flushList();
      const level = heading[1].length;
      const className = level === 1 ? "text-2xl font-semibold" : level === 2 ? "text-xl font-semibold" : "text-lg font-medium";
      blocks.push(
        <div key={`heading-${blocks.length}`} className={className}>
          {heading[2]}
        </div>,
      );
      return;
    }

    const listItem = /^[-*]\s+(.+)$/.exec(trimmed);
    if (listItem) {
      listItems.push(listItem[1]);
      return;
    }

    if (trimmed.startsWith(">")) {
      flushList();
      blocks.push(
        <blockquote key={`quote-${blocks.length}`} className="border-l-4 pl-3 text-muted-foreground">
          {inlineCode(trimmed.slice(1).trim())}
        </blockquote>,
      );
      return;
    }

    flushList();
    blocks.push(
      <p key={`paragraph-${blocks.length}`} className="leading-7">
        {inlineCode(trimmed)}
      </p>,
    );
  });

  flushList();
  if (inCode || codeLines.length) {
    flushCode();
  }
  return blocks.length ? blocks : [<p key="empty" className="text-muted-foreground">暂无内容</p>];
}

export function InfoMemo() {
  const [notes, setNotes] = useState<RecordItem[]>([]);
  const [selected, setSelected] = useState<RecordItem | null>(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("正在读取信息备忘");

  async function load(keyword = query) {
    const data = await listRecords("notes", keyword);
    setNotes(data);
    setSelected((current) => (current?.id ? data.find((item) => item.id === current.id) ?? data[0] ?? null : data[0] ?? null));
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("new")) {
      listRecords("notes")
        .then((data) => {
          setNotes(data);
          setSelected(draftNote());
          setMessage("已创建信息备忘草稿");
        })
        .catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
      return;
    }
    load("").catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
  }, []);

  async function saveSelected() {
    if (!selected) return;
    const saved = await saveRecord("notes", selected);
    setSelected(saved);
    setNotes((items) => (items.some((item) => item.id === saved.id) ? items.map((item) => (item.id === saved.id ? saved : item)) : [saved, ...items]));
    setMessage("信息备忘已保存");
  }

  async function exportMarkdown() {
    try {
      const result = await exportNotesMarkdown();
      window.alert(`信息备忘导出完成，共 ${result.count ?? ""} 条记录\n\n目录：${result.output_dir}`);
      setMessage("信息备忘已导出 Markdown");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "信息备忘导出失败");
    }
  }

  return (
    <div className="h-full flex">
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">信息备忘</h2>
            <Button size="sm" onClick={() => setSelected(draftNote())}>
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="搜索 Markdown..."
              className="pl-9"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && load(query)}
            />
          </div>
          <p className="text-xs text-muted-foreground">{message}</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {notes.map((note) => (
            <button
              key={note.id}
              onClick={() => setSelected(note)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selected?.id === note.id ? "bg-primary text-primary-foreground" : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <FileText className="size-4 mt-1 shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium truncate">{note.title || "未命名备忘"}</p>
                  <p className="text-xs opacity-80 mt-1">{note.date || note.updated_at?.slice(0, 10) || "未设置日期"}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        {selected ? (
          <div className="max-w-6xl space-y-6">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-3 flex-1">
                <Input
                  className="text-3xl font-semibold border-0 px-0 focus-visible:ring-0"
                  value={selected.title}
                  placeholder="信息标题"
                  onChange={(event) => setSelected({ ...selected, title: event.target.value })}
                />
                <div className="flex flex-wrap items-center gap-3">
                  <label className="flex items-center gap-2 text-sm text-muted-foreground">
                    日期
                    <Input
                      className="h-8 w-40"
                      type="date"
                      value={selected.date || ""}
                      onChange={(event) => setSelected({ ...selected, date: event.target.value })}
                    />
                  </label>
                  <Badge variant="secondary">Markdown</Badge>
                  <span className="text-xs text-muted-foreground">{selected.body.length} 字符</span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={exportMarkdown}>
                  <Download className="size-4" />
                  导出 MD
                </Button>
                <Button onClick={saveSelected}>
                  <Save className="size-4" />
                  保存
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <section className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <FileText className="size-4" />
                  编辑
                </div>
                <Textarea
                  className="min-h-[560px] resize-none font-mono text-sm leading-6"
                  value={selected.body || ""}
                  onChange={(event) => setSelected({ ...selected, body: event.target.value })}
                  placeholder={"# 标题\n\n- 要点\n- 链接、联系人、项目笔记\n\n> 重要提醒"}
                />
              </section>

              <section className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Eye className="size-4" />
                  预览
                </div>
                <div className="min-h-[560px] rounded-lg border bg-card p-5">
                  <div className="space-y-4 text-sm">{renderMarkdown(selected.body || "")}</div>
                </div>
              </section>
            </div>
          </div>
        ) : (
          <div className="h-full grid place-content-center text-muted-foreground">选择一条信息备忘查看详情</div>
        )}
      </div>
    </div>
  );
}
