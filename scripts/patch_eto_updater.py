from pathlib import Path

p = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/fragments/MainMenuFragment.java")
s = p.read_text(encoding="utf-8")

for imp in [
    "import org.json.JSONObject;",
    "import org.json.JSONArray;",
    "import java.net.HttpURLConnection;",
    "import java.net.URL;",
    "import java.io.ByteArrayOutputStream;",
    "import java.io.InputStream;",
    "import java.nio.charset.StandardCharsets;"
]:
    if imp not in s:
        anchor = "import android.content.Intent;"
        if anchor not in s:
            raise SystemExit("Cannot locate MainMenuFragment import anchor")
        s = s.replace(anchor, anchor + "\n" + imp, 1)

needle = "        mVersionSpinner = view.findViewById(R.id.mc_version_spinner);"
if "checkEtoContentUpdates();" not in s:
    if needle not in s:
        raise SystemExit("Content updater insertion point missing")
    s = s.replace(needle, needle + "\n        applyEtoRemoteContent(view);\n        checkEtoContentUpdates();", 1)

methods = r"""
    // Eto Content Update Engine: updates launcher content without replacing the APK.
    private static final String ETO_CONTENT_URL =
            "https://raw.githubusercontent.com/pandagh070-ship-it/Eto-lanucher/main/updates/content.json";

    private JSONObject fetchEtoContent() throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(ETO_CONTENT_URL).openConnection();
        c.setConnectTimeout(12000);
        c.setReadTimeout(12000);
        c.setUseCaches(false);
        c.setRequestProperty("Cache-Control", "no-cache");
        c.setRequestProperty("Pragma", "no-cache");
        try {
            int code = c.getResponseCode();
            if (code != 200) throw new java.io.IOException("HTTP " + code);
            InputStream in = c.getInputStream();
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buffer = new byte[4096];
            int n;
            while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
            in.close();
            return new JSONObject(new String(out.toByteArray(), StandardCharsets.UTF_8));
        } finally {
            c.disconnect();
        }
    }

    private void checkEtoContentUpdates() {
        new Thread(() -> {
            try {
                JSONObject remote = fetchEtoContent();
                int latest = remote.optInt("contentVersion", 0);
                int installed = requireContext().getSharedPreferences("eto_live_content", 0)
                        .getInt("content_version", 0);
                if (latest <= installed || !isAdded()) return;
                String version = remote.optString("versionName", "Eto content update");
                JSONArray changes = remote.optJSONArray("changelog");
                StringBuilder notes = new StringBuilder();
                if (changes != null) {
                    for (int i = 0; i < changes.length(); i++) {
                        notes.append("• ").append(changes.optString(i)).append("\n");
                    }
                }
                String message = "New launcher content is ready.\n\n"
                        + (notes.length() == 0 ? "New content and improvements." : notes.toString())
                        + "\nThis update does not download or reinstall the APK.";
                requireActivity().runOnUiThread(() -> {
                    if (!isAdded()) return;
                    new AlertDialog.Builder(requireContext())
                            .setTitle("❄ Eto content update • " + version)
                            .setMessage(message)
                            .setCancelable(true)
                            .setNegativeButton("Later", null)
                            .setPositiveButton("Update", (dialog, which) -> downloadEtoContentUpdate())
                            .show();
                });
            } catch (Exception ignored) {
                // Offline: use the last successfully installed content.
            }
        }, "EtoContentCheck").start();
    }

    private void downloadEtoContentUpdate() {
        new Thread(() -> {
            try {
                JSONObject data = fetchEtoContent();
                int version = data.optInt("contentVersion", 0);
                if (version <= 0) throw new IllegalStateException("Invalid content version");
                requireContext().getSharedPreferences("eto_live_content", 0).edit()
                        .putInt("content_version", version)
                        .putString("version_name", data.optString("versionName", "Eto content"))
                        .putString("title", data.optString("title", "Eto Launcher"))
                        .putString("message", data.optString("message", "Welcome to Eto Launcher"))
                        .putString("changelog", data.optJSONArray("changelog") == null
                                ? "" : data.optJSONArray("changelog").toString())
                        .apply();
                requireActivity().runOnUiThread(() -> {
                    if (!isAdded()) return;
                    applyEtoRemoteContent(getView());
                    android.widget.Toast.makeText(requireContext(),
                            "Eto content updated successfully • " + data.optString("versionName", ""),
                            android.widget.Toast.LENGTH_LONG).show();
                });
            } catch (Exception error) {
                requireActivity().runOnUiThread(() -> {
                    if (!isAdded()) return;
                    new AlertDialog.Builder(requireContext())
                            .setTitle("Update failed")
                            .setMessage("Could not download Eto content. Check your connection and try again.\n" + error.getMessage())
                            .setPositiveButton("Retry", (d, w) -> downloadEtoContentUpdate())
                            .setNegativeButton("Close", null)
                            .show();
                });
            }
        }, "EtoContentDownload").start();
    }

    private void applyEtoRemoteContent(@Nullable View root) {
        if (root == null || !isAdded()) return;
        android.content.SharedPreferences p = requireContext().getSharedPreferences("eto_live_content", 0);
        TextView title = root.findViewById(R.id.eto_remote_title);
        TextView message = root.findViewById(R.id.eto_remote_message);
        TextView version = root.findViewById(R.id.eto_remote_version);
        if (title != null) title.setText(p.getString("title", "Welcome to Eto"));
        if (message != null) message.setText(p.getString("message",
                "Your Eto Launcher content and news will update here without reinstalling the app."));
        if (version != null) version.setText("LIVE CONTENT • " + p.getString("version_name", "BUILT-IN"));
    }

"""
if "private void checkEtoContentUpdates()" not in s:
    pos = s.rfind("\n}")
    if pos < 0:
        raise SystemExit("MainMenuFragment class end missing")
    s = s[:pos] + "\n" + methods + s[pos:]

p.write_text(s, encoding="utf-8")
print("Installed Eto live content update engine (JSON only; no APK download).")
