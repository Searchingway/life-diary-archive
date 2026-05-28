import { MapPin } from "lucide-react";
import { RecordModulePage } from "../components/records/RecordModulePage";

export function Footprints() {
  return (
    <RecordModulePage
      moduleKey="footprints"
      title="足迹"
      icon={MapPin}
      description="地点档案和访问记录已从旧版数据目录迁移。"
      bodyLabel="地点摘要 / 访问感想"
    />
  );
}
