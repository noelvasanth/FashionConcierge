import { useMemo, useState } from "react";

const INSTALL_KEY = "pwa.install.prompt";

const SettingsPage = () => {
  const [installPrompt, setInstallPrompt] = useState(() => {
    const stored = localStorage.getItem(INSTALL_KEY);
    return stored ? stored === "true" : true;
  });
  const isInstallSupported = useMemo(() => "serviceWorker" in navigator, []);

  const handleToggle = (checked: boolean) => {
    setInstallPrompt(checked);
    localStorage.setItem(INSTALL_KEY, String(checked));
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage preferences and integrations.</p>
      </header>
      <div className="rounded-2xl border bg-white p-4 shadow-sm">
        <p className="text-sm text-muted-foreground">
          Configure mood themes, fit preferences, and data sources once authentication is wired up.
        </p>
      </div>
      <div className="rounded-2xl border bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold">Installable app</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The web app can be installed on supported devices. Offline mode is limited to cached
          screens and won&apos;t sync new wardrobe updates until you reconnect.
        </p>
        <label className="mt-4 flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            className="h-4 w-4"
            checked={installPrompt}
            onChange={(event) => handleToggle(event.target.checked)}
          />
          Enable install prompts {isInstallSupported ? "" : "(unsupported browser)"}
        </label>
      </div>
    </div>
  );
};

export default SettingsPage;
