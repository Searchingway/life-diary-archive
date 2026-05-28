import { BookOpen } from "lucide-react";
import { RecordModulePage } from "../components/records/RecordModulePage";

export function Diary() {
  return (
    <RecordModulePage
      moduleKey="entries"
      title="日记"
      icon={BookOpen}
      description="从旧版日记迁移过来的本地记录，可继续编辑保存。"
      bodyLabel="日记正文"
    />
  );
}
