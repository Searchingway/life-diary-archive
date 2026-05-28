import { Scale } from "lucide-react";
import { RecordModulePage } from "../components/records/RecordModulePage";

export function LightResource() {
  return (
    <RecordModulePage
      moduleKey="resources"
      title="轻资源"
      icon={Scale}
      description="评估一个决定会消耗哪些资源，旧版资源项已迁移到 2.0。"
      bodyLabel="资源描述"
    />
  );
}
