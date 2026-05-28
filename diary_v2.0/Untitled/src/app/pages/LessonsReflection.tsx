import { AlertTriangle } from "lucide-react";
import { RecordModulePage } from "../components/records/RecordModulePage";

export function LessonsReflection() {
  return (
    <RecordModulePage
      moduleKey="lessons"
      title="教训与反思"
      icon={AlertTriangle}
      description="事件、代价、反思和关联线索已迁移到 2.0。"
      bodyLabel="反思内容"
    />
  );
}
