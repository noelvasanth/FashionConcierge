import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";
import LandingPage from "../pages/LandingPage";
import AppHomePage from "../pages/AppHomePage";
import ChatPage from "../pages/ChatPage";
import OutfitsPage from "../pages/OutfitsPage";
import WardrobePage from "../pages/WardrobePage";
import SettingsPage from "../pages/SettingsPage";
import OnboardingPage from "../pages/OnboardingPage";
import PlannerPage from "../pages/PlannerPage";

const RequireSession = ({ children }: { children: JSX.Element }) => {
  const sessionId = localStorage.getItem("sessionId");
  if (!sessionId) {
    return <Navigate to="/onboarding" replace />;
  }
  return children;
};

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/onboarding" element={<OnboardingPage />} />
      <Route
        path="/app"
        element={
          <RequireSession>
            <AppShell />
          </RequireSession>
        }
      >
        <Route index element={<AppHomePage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="outfits" element={<OutfitsPage />} />
        <Route path="planner" element={<PlannerPage />} />
        <Route path="wardrobe" element={<WardrobePage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
};

export default App;
