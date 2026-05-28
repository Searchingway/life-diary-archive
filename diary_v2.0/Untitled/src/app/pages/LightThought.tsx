import { Lightbulb } from "lucide-react";
import { RecordModulePage } from "../components/records/RecordModulePage";

export function LightThought() {
  return (
    <RecordModulePage
      moduleKey="thoughts"
      title="轻思考"
      icon={Lightbulb}
      description="碎片想法、初步结论和状态整理已接入旧版数据。"
      bodyLabel="思考内容"
    />
  );
}
