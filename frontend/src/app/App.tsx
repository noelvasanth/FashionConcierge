import { Route, Routes } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";
import LandingPage from "../pages/LandingPage";
import AppHomePage from "../pages/AppHomePage";
import ChatPage from "../pages/ChatPage";
import OutfitsPage from "../pages/OutfitsPage";
import WardrobePage from "../pages/WardrobePage";
import SettingsPage from "../pages/SettingsPage";

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/app" element={<AppShell />}>
        <Route index element={<AppHomePage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="outfits" element={<OutfitsPage />} />
        <Route path="wardrobe" element={<WardrobePage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
};

export default App;
