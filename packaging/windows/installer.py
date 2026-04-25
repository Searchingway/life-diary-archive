from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import zipfile
from pathlib import Path
from tkinter import DISABLED, NORMAL, Button, Entry, Frame, Label, StringVar, Tk, filedialog, messagebox


APP_NAME = "人生档案"
APP_EXE_NAME = "人生档案.exe"


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath(*parts)


def default_install_dir() -> Path:
    root = os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(root) / "Programs" / APP_NAME


class InstallerWindow:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title(f"{APP_NAME} 安装器")
        self.root.geometry("560x260")
        self.root.resizable(False, False)

        self.install_dir = StringVar(value=str(default_install_dir()))
        self.status = StringVar(value="请选择安装位置，然后开始安装。")
        self.launch_path: Path | None = None

        self._build_ui()

    def run(self) -> None:
        self.root.mainloop()

    def _build_ui(self) -> None:
        frame = Frame(self.root, padx=24, pady=20)
        frame.pack(fill="both", expand=True)

        Label(frame, text=APP_NAME, font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w")
        Label(frame, text="选择安装路径，安装完成后可直接启动。", font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(6, 18))

        path_row = Frame(frame)
        path_row.pack(fill="x")

        self.path_entry = Entry(path_row, textvariable=self.install_dir, font=("Microsoft YaHei UI", 10))
        self.path_entry.pack(side="left", fill="x", expand=True)

        Button(path_row, text="浏览...", command=self.browse).pack(side="left", padx=(8, 0))

        self.status_label = Label(frame, textvariable=self.status, anchor="w", font=("Microsoft YaHei UI", 10))
        self.status_label.pack(fill="x", pady=(18, 12))

        action_row = Frame(frame)
        action_row.pack(fill="x", pady=(4, 0))

        self.install_button = Button(action_row, text="开始安装", width=14, command=self.install)
        self.install_button.pack(side="left")

        self.launch_button = Button(action_row, text="启动人生档案", width=16, state=DISABLED, command=self.launch)
        self.launch_button.pack(side="left", padx=(10, 0))

        Button(action_row, text="退出", width=10, command=self.root.destroy).pack(side="right")

    def browse(self) -> None:
        selected = filedialog.askdirectory(initialdir=str(Path(self.install_dir.get()).parent))
        if selected:
            self.install_dir.set(str(Path(selected)))

    def install(self) -> None:
        self.install_button.configure(state=DISABLED)
        self.launch_button.configure(state=DISABLED)
        self.status.set("正在安装，请稍等...")
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self) -> None:
        try:
            target = Path(self.install_dir.get()).expanduser().resolve()
            payload = resource_path("payload", "life_diary_payload.zip")
            if not payload.exists():
                raise FileNotFoundError(f"安装包内容缺失：{payload}")

            target.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(payload, "r") as archive:
                archive.extractall(target)

            exe_path = target / APP_EXE_NAME
            if not exe_path.exists():
                raise FileNotFoundError(f"安装完成但没有找到启动程序：{exe_path}")

            self.launch_path = exe_path
            self.root.after(0, lambda: self._install_done(target))
        except Exception as exc:
            self.root.after(0, lambda: self._install_failed(exc))

    def _install_done(self, target: Path) -> None:
        self.status.set(f"安装完成：{target}")
        self.install_button.configure(state=NORMAL)
        self.launch_button.configure(state=NORMAL)
        messagebox.showinfo(APP_NAME, "安装完成，可以点击“启动人生档案”直接运行。")

    def _install_failed(self, exc: Exception) -> None:
        self.status.set("安装失败。")
        self.install_button.configure(state=NORMAL)
        messagebox.showerror(APP_NAME, f"安装失败：\n{exc}")

    def launch(self) -> None:
        if not self.launch_path or not self.launch_path.exists():
            messagebox.showwarning(APP_NAME, "没有找到已安装的启动程序。")
            return
        subprocess.Popen([str(self.launch_path)], cwd=str(self.launch_path.parent))


def main() -> int:
    InstallerWindow().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
