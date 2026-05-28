import { Film } from "lucide-react";
import { RecordModulePage } from "../components/records/RecordModulePage";

export function WorksReflection() {
  return (
    <RecordModulePage
      moduleKey="works"
      title="作品感悟"
      icon={Film}
      description="书、电影、课程和其他作品感悟已迁移到 2.0。"
      bodyLabel="感悟内容"
    />
  );
}
