import { Brain } from "lucide-react";
import { RecordModulePage } from "../components/records/RecordModulePage";

export function ActionPlan() {
  return (
    <RecordModulePage
      moduleKey="action_plans"
      title="行动计划"
      icon={Brain}
      description="行动计划、任务进度和时间安排已读取旧版本地数据。"
      bodyLabel="计划说明"
      dateLabel="开始日期"
    />
  );
}
