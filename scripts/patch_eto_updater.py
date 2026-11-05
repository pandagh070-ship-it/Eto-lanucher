from pathlib import Path

p = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/fragments/MainMenuFragment.java")
s = p.read_text(encoding="utf-8")

imports = [
    "import android.app.DownloadManager;",
    "import android.net.Uri;",
    "import android.os.Build;",
    "import android.os.Environment;",
    "import android.widget.Toast;",
    "import java.net.HttpURLConnection;",
    "import java.net.URL;",
    "import org.json.JSONObject;",
    "import net.kdt.pojavlaunch.BuildConfig;"
]
for imp in imports:
    if imp not in s:
        anchor = "import android.content.Intent;"
        if anchor in s:
            s = s.replace(anchor, anchor + "\n" + imp, 1)
        else:
            raise SystemExit("Cannot add updater imports")

needle = "        mVersionSpinner = view.findViewById(R.id.mc_version_spinner);"
if "checkForEtoUpdate();" not in s:
    if needle not in s:
        raise SystemExit("Updater insertion point missing")
    s = s.replace(needle, needle + "\n        checkForEtoUpdate();", 1)

methods = r"""
    private static final String ETO_UPDATE_INFO =
            "https://github.com/pandagh070-ship-it/Eto-lanucher/releases/latest/download/update.json";
    private static final String ETO_APK_URL =
            "https://github.com/pandagh070-ship-it/Eto-lanucher/releases/latest/download/EtoLauncher.apk";

    private String readEtoUpdateJson(java.io.InputStream input) throws Exception {
        java.io.ByteArrayOutputStream output = new java.io.ByteArrayOutputStream();
        byte[] buffer = new byte[4096];
        int count;
        while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
        return new String(output.toByteArray(), "UTF-8");
    }

    private void checkForEtoUpdate() {
        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(ETO_UPDATE_INFO).openConnection();
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(10000);
                connection.setRequestProperty("Cache-Control", "no-cache");
                JSONObject data = new JSONObject(readEtoUpdateJson(connection.getInputStream()));
                int latest = data.optInt("versionCode", 0);
                if (latest <= BuildConfig.VERSION_CODE || !isAdded()) return;
                String version = data.optString("versionName", "New version");
                org.json.JSONArray changes = data.optJSONArray("changelog");
                StringBuilder notes = new StringBuilder();
                if (changes != null) {
                    for (int i = 0; i < changes.length(); i++) notes.append("• ").append(changes.optString(i)).append("\n");
                }
                String message = "Installed: " + BuildConfig.VERSION_NAME + "\nAvailable: " + version
                        + "\n\nWhat's new?\n" + (notes.length() == 0 ? "Performance and stability improvements" : notes.toString());
                requireActivity().runOnUiThread(() -> {
                    if (!isAdded()) return;
                    new AlertDialog.Builder(requireContext())
                            .setTitle("❄ Eto update available")
                            .setMessage(message)
                            .setCancelable(true)
                            .setNegativeButton("Later", null)
                            .setPositiveButton("Update now", (dialog, which) -> downloadEtoUpdate())
                            .show();
                });
            } catch (Exception ignored) {
                // Offline or no published update: keep the launcher usable.
            } finally {
                if (connection != null) connection.disconnect();
            }
        }, "EtoUpdateCheck").start();
    }

    private void downloadEtoUpdate() {
        try {
            DownloadManager manager = (DownloadManager) requireContext().getSystemService(Context.DOWNLOAD_SERVICE);
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(ETO_APK_URL));
            request.setTitle("Eto Launcher update");
            request.setDescription("Downloading the latest Eto Launcher APK");
            request.setMimeType("application/vnd.android.package-archive");
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "EtoLauncher-update.apk");
            manager.enqueue(request);
            Toast.makeText(requireContext(), "Update downloading. Open the download notification when complete to install.", Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(requireContext(), "Could not start update download: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

"""
if "private void checkForEtoUpdate()" not in s:
    pos = s.rfind("\n}")
    if pos < 0:
        raise SystemExit("MainMenuFragment class end missing")
    s = s[:pos] + "\n" + methods + s[pos:]

manifest = Path("upstream/app_pojavlauncher/src/main/AndroidManifest.xml")
manifest_text = manifest.read_text(encoding="utf-8")
permission = '<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />'
if permission not in manifest_text:
    manifest_text = manifest_text.replace("<application", permission + "\n    <application", 1)
manifest.write_text(manifest_text, encoding="utf-8")

p.write_text(s, encoding="utf-8")
print("Added Eto update check and APK download dialog.")
