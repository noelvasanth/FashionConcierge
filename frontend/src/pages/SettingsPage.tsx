const SettingsPage = () => {
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
    </div>
  );
};

export default SettingsPage;
