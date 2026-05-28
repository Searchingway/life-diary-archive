import { FileText } from "lucide-react";
import { RecordModulePage } from "../components/records/RecordModulePage";

export function InfoMemo() {
  return (
    <RecordModulePage
      moduleKey="info_memos"
      title="信息备忘"
      icon={FileText}
      description="接单记录、网课资源和通用信息已从旧版迁移。"
      bodyLabel="备忘内容"
    />
  );
}
