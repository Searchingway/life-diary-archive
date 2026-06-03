import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { MainLayout } from "./components/layouts/MainLayout";
import { Dashboard } from "./pages/Dashboard";
import { Diary } from "./pages/Diary";
import { Footprints } from "./pages/Footprints";
import { LightPlan } from "./pages/LightPlan";
import { ActionPlan } from "./pages/ActionPlan";
import { LightThought } from "./pages/LightThought";
import { LightResource } from "./pages/LightResource";
import { InfoMemo } from "./pages/InfoMemo";
import { OrderMemo } from "./pages/OrderMemo";
import { SelfObservation } from "./pages/SelfObservation";
import { LessonsReflection } from "./pages/LessonsReflection";
import { SelfAnalysis } from "./pages/SelfAnalysis";
import { WorksReflection } from "./pages/WorksReflection";
import { DataManagement } from "./pages/DataManagement";
import { AISettings } from "./pages/AISettings";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="diary" element={<Diary />} />
          <Route path="footprints" element={<Footprints />} />
          <Route path="light-plan" element={<LightPlan />} />
          <Route path="action-plan" element={<ActionPlan />} />
          <Route path="light-thought" element={<LightThought />} />
          <Route path="light-resource" element={<LightResource />} />
          <Route path="order-memo" element={<OrderMemo />} />
          <Route path="info-memo" element={<InfoMemo />} />
          <Route path="self-observation" element={<SelfObservation />} />
          <Route path="lessons-reflection" element={<LessonsReflection />} />
          <Route path="self-analysis" element={<SelfAnalysis />} />
          <Route path="works-reflection" element={<WorksReflection />} />
          <Route path="data-management" element={<DataManagement />} />
          <Route path="ai-settings" element={<AISettings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
