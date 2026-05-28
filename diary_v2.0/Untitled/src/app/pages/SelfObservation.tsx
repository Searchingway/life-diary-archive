import { Eye } from "lucide-react";
import { RecordModulePage } from "../components/records/RecordModulePage";

export function SelfObservation() {
  return (
    <RecordModulePage
      moduleKey="observations"
      title="自我观察"
      icon={Eye}
      description="情绪、触发原因和观察记录已读取旧版本地数据。"
      bodyLabel="观察内容"
    />
  );
}
