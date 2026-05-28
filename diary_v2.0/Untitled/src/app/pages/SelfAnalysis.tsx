import { User } from "lucide-react";
import { RecordModulePage } from "../components/records/RecordModulePage";

export function SelfAnalysis() {
  return (
    <RecordModulePage
      moduleKey="self_analysis"
      title="自我分析"
      icon={User}
      description="自我分析草稿、关联日记和反思内容已接入旧版数据。"
      bodyLabel="分析内容"
    />
  );
}
