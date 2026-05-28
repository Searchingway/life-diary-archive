import { Target } from "lucide-react";
import { RecordModulePage } from "../components/records/RecordModulePage";

export function LightPlan() {
  return (
    <RecordModulePage
      moduleKey="plans"
      title="轻计划"
      icon={Target}
      description="加法计划、减法计划和旧版计划数据已接入 2.0。"
      bodyLabel="计划内容"
      dateLabel="截止日期"
    />
  );
}
