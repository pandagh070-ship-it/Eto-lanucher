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
    "import java.io.File;",
    "import java.io.FileOutputStream;",
    "import java.nio.charset.StandardCharsets;",
    "import android.app.ProgressDialog;"
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
    // Eto content channel: downloads only explicitly listed data assets, never the game or APK.
    private static final String ETO_CONTENT_URL =
            "https://raw.githubusercontent.com/pandagh070-ship-it/Eto-lanucher/main/updates/content.json";

    private JSONObject fetchEtoContent() throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(ETO_CONTENT_URL).openConnection();
        c.setConnectTimeout(12000);
        c.setReadTimeout(12000);
        c.setUseCaches(false);
        c.setRequestProperty("Cache-Control", "no-cache");
        try {
            if (c.getResponseCode() != 200) throw new java.io.IOException("HTTP " + c.getResponseCode());
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
                if (changes != null) for (int i = 0; i < changes.length(); i++)
                    notes.append("• ").append(changes.optString(i)).append("\n");
                JSONArray assets = remote.optJSONArray("assets");
                int count = assets == null ? 0 : assets.length();
                String message = "New content is ready: " + count + " downloadable file(s).\n\n"
                        + (notes.length() == 0 ? "Content and launcher news." : notes.toString())
                        + "\nOnly listed content files will download. Minecraft and the launcher APK are not included.";
                requireActivity().runOnUiThread(() -> {
                    if (!isAdded()) return;
                    new AlertDialog.Builder(requireContext())
                            .setTitle("Eto update • " + version)
                            .setMessage(message)
                            .setCancelable(true)
                            .setNegativeButton("Later", null)
                            .setPositiveButton("Update", (dialog, which) -> downloadEtoContentUpdate())
                            .show();
                });
            } catch (Exception ignored) {
                // Offline: keep the last successfully installed content.
            }
        }, "EtoContentCheck").start();
    }

    private void downloadEtoContentUpdate() {
        final ProgressDialog progress = new ProgressDialog(requireContext());
        progress.setTitle("Updating Eto content");
        progress.setMessage("Preparing update...");
        progress.setProgressStyle(ProgressDialog.STYLE_HORIZONTAL);
        progress.setIndeterminate(false);
        progress.setMax(100);
        progress.setProgress(0);
        progress.setCancelable(false);
        progress.show();

        new Thread(() -> {
            try {
                JSONObject data = fetchEtoContent();
                int version = data.optInt("contentVersion", 0);
                if (version <= 0) throw new IllegalStateException("Invalid content version");
                JSONArray assets = data.optJSONArray("assets");
                int count = assets == null ? 0 : assets.length();
                File directory = new File(requireContext().getFilesDir(), "eto-content");
                if (!directory.exists() && !directory.mkdirs())
                    throw new java.io.IOException("Cannot create Eto content folder");

                for (int i = 0; i < count; i++) {
                    JSONObject asset = assets.getJSONObject(i);
                    String name = asset.optString("fileName", "");
                    String address = asset.optString("url", "");
                    if (!name.matches("[A-Za-z0-9._-]{1,100}") || name.equals(".") || name.equals(".."))
                        throw new IllegalArgumentException("Invalid content file name");
                    URL url = new URL(address);
                    if (!"https".equalsIgnoreCase(url.getProtocol()))
                        throw new IllegalArgumentException("Content assets must use HTTPS");
                    HttpURLConnection connection = (HttpURLConnection) url.openConnection();
                    connection.setConnectTimeout(15000);
                    connection.setReadTimeout(20000);
                    connection.setUseCaches(false);
                    try {
                        int code = connection.getResponseCode();
                        if (code != 200) throw new java.io.IOException("Asset HTTP " + code);
                        int length = connection.getContentLength();
                        File target = new File(directory, name);
                        File temporary = new File(directory, name + ".part");
                        try (InputStream in = connection.getInputStream();
                             FileOutputStream out = new FileOutputStream(temporary)) {
                            byte[] buffer = new byte[8192];
                            int read, total = 0;
                            while ((read = in.read(buffer)) != -1) {
                                out.write(buffer, 0, read);
                                total += read;
                                if (length > 0) {
                                    final int overall = Math.min(99, ((i * 100) + (total * 100 / length)) / Math.max(1, count));
                                    requireActivity().runOnUiThread(() -> {
                                        if (progress.isShowing()) {
                                            progress.setMessage("Downloading " + name);
                                            progress.setProgress(overall);
                                        }
                                    });
                                }
                            }
                            out.getFD().sync();
                        }
                        if (target.exists() && !target.delete()) throw new java.io.IOException("Cannot replace " + name);
                        if (!temporary.renameTo(target)) throw new java.io.IOException("Cannot install " + name);
                    } finally {
                        connection.disconnect();
                    }
                }

                requireContext().getSharedPreferences("eto_live_content", 0).edit()
                        .putInt("content_version", version)
                        .putString("version_name", data.optString("versionName", "Eto content"))
                        .putString("title", data.optString("title", "Eto Launcher"))
                        .putString("message", data.optString("message", "Welcome to Eto Launcher"))
                        .putString("changelog", data.optJSONArray("changelog") == null
                                ? "" : data.optJSONArray("changelog").toString())
                        .apply();
                requireActivity().runOnUiThread(() -> {
                    if (progress.isShowing()) progress.dismiss();
                    if (!isAdded()) return;
                    progress.setProgress(100);
                    applyEtoRemoteContent(getView());
                    android.widget.Toast.makeText(requireContext(),
                            "Eto content updated • " + count + " file(s)",
                            android.widget.Toast.LENGTH_LONG).show();
                });
            } catch (Exception error) {
                requireActivity().runOnUiThread(() -> {
                    if (progress.isShowing()) progress.dismiss();
                    if (!isAdded()) return;
                    new AlertDialog.Builder(requireContext())
                            .setTitle("Update failed")
                            .setMessage("Could not install Eto content.\n" + error.getMessage())
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
        if (title != null) title.setText(p.getString("title", "Welcome back."));
        if (message != null) message.setText(p.getString("message",
                "News and supported content updates appear here."));
        if (version != null) version.setText("CONTENT CHANNEL • " + p.getString("version_name", "READY"));
    }

"""
if "private void checkEtoContentUpdates()" not in s:
    pos = s.rfind("\n}")
    if pos < 0: raise SystemExit("MainMenuFragment class end missing")
    s = s[:pos] + "\n" + methods + s[pos:]
p.write_text(s, encoding="utf-8")
print("Installed content-only updater with per-file progress; no APK/game download.")
