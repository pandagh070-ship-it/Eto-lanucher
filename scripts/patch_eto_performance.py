from pathlib import Path

# Let the existing Pojav resolution scaler go below its upstream 25% floor.
values = Path("upstream/app_pojavlauncher/src/main/res/values/values.xml")
v = values.read_text(encoding="utf-8")
old = '<integer name="resolution_seekbar_min">25</integer>'
new = '<integer name="resolution_seekbar_min">10</integer>'
if old in v:
    v = v.replace(old, new, 1)
elif new not in v:
    raise SystemExit("Could not find resolution_seekbar_min in values.xml")
values.write_text(v, encoding="utf-8")

video = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/prefs/screens/LauncherPreferenceVideoFragment.java")
s = video.read_text(encoding="utf-8")
if "if (resolution < 25)" in s:
    s = s.replace("if (resolution < 25)", "if (resolution < 10)", 1)
elif "if (resolution < 10)" not in s:
    raise SystemExit("Could not find resolution lower-bound guard in video preferences")
video.write_text(s, encoding="utf-8")

# Add a one-tap game-side performance profile and Modrinth performance pack
# to the existing Mods manager. Files are installed per Minecraft version.
p = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/fragments/MainMenuFragment.java")
s = p.read_text(encoding="utf-8")
anchor = '        android.widget.TextView subtitle = etoModsText("Find and install compatible mods and shader packs", 10, Color.LTGRAY, false);\n        right.addView(subtitle);'
if "ETO_PERFORMANCE_PACK_ACTIONS" not in s:
    if anchor not in s:
        raise SystemExit("Could not find Eto Mods manager subtitle insertion point")
    s = s.replace(anchor, anchor + """
        // ETO_PERFORMANCE_PACK_ACTIONS
        android.widget.LinearLayout performanceActions = new android.widget.LinearLayout(requireContext());
        performanceActions.setOrientation(android.widget.LinearLayout.HORIZONTAL);
        performanceActions.setPadding(0, 6, 0, 6);
        right.addView(performanceActions);
        android.widget.Button installPerformance = etoModsButton("GET PERFORMANCE MODS");
        performanceActions.addView(installPerformance, new android.widget.LinearLayout.LayoutParams(0, 42, 1f));
        installPerformance.setOnClickListener(v -> installEtoPerformancePack());
        android.widget.Button applyLite = etoModsButton("APPLY ULTRA LITE");
        android.widget.LinearLayout.LayoutParams liteParams = new android.widget.LinearLayout.LayoutParams(0, 42, 1f);
        liteParams.setMargins(6, 0, 0, 0);
        performanceActions.addView(applyLite, liteParams);
        applyLite.setOnClickListener(v -> applyEtoUltraLiteProfile());
""", 1)

methods = r'''
    private void applyEtoUltraLiteProfile() {
        if (!isAdded()) return;
        Instance instance = Instances.loadSelectedInstance();
        if (instance == null) {
            Toast.makeText(requireContext(), "Select a Minecraft profile first", Toast.LENGTH_LONG).show();
            return;
        }
        try {
            File options = new File(instance.getGameDirectory(), "options.txt");
            File backup = new File(instance.getGameDirectory(), "options.eto-backup.txt");
            if (options.isFile() && !backup.exists()) {
                java.nio.file.Files.copy(options.toPath(), backup.toPath());
            }
            java.util.LinkedHashMap<String, String> settings = new java.util.LinkedHashMap<>();
            if (options.isFile()) {
                for (String line : java.nio.file.Files.readAllLines(options.toPath(), java.nio.charset.StandardCharsets.UTF_8)) {
                    int split = line.indexOf(':');
                    if (split > 0) settings.put(line.substring(0, split), line.substring(split + 1));
                }
            }
            String[][] lite = {
                {"renderDistance", "2"},
                {"simulationDistance", "2"},
                {"graphics", "\"fast\""},
                {"fancyGraphics", "false"},
                {"renderClouds", "\"off\""},
                {"clouds", "false"},
                {"particles", "\"minimal\""},
                {"ao", "0"},
                {"biomeBlendRadius", "0"},
                {"mipmapLevels", "0"},
                {"anisotropicFiltering", "1"},
                {"entityDistanceScaling", "0.35"},
                {"maxFps", "60"},
                {"enableVsync", "false"},
                {"entityShadows", "false"},
                {"bobView", "false"},
                {"distortionEffectScale", "0.0"},
                {"fovEffectScale", "0.0"},
                {"darknessEffectScale", "0.0"}
            };
            for (String[] entry : lite) settings.put(entry[0], entry[1]);
            StringBuilder output = new StringBuilder();
            for (java.util.Map.Entry<String, String> entry : settings.entrySet()) {
                output.append(entry.getKey()).append(':').append(entry.getValue()).append('\n');
            }
            java.nio.file.Files.write(options.toPath(), output.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
            Toast.makeText(requireContext(), "Ultra Lite settings applied. Original options backup saved.", Toast.LENGTH_LONG).show();
            if (etoModsStatus != null) etoModsStatus.setText("Ultra Lite active • 2 chunks • Fast graphics • Minimal particles");
        } catch (Exception error) {
            Toast.makeText(requireContext(), "Could not apply game settings: " + error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void installEtoPerformancePack() {
        if (!isAdded()) return;
        Instance instance = Instances.loadSelectedInstance();
        if (instance == null) {
            Toast.makeText(requireContext(), "Select a Minecraft profile first", Toast.LENGTH_LONG).show();
            return;
        }
        String profile = instance.versionId == null ? "" : instance.versionId.toLowerCase(java.util.Locale.ROOT);
        if (!profile.contains("fabric")) {
            new android.app.AlertDialog.Builder(requireContext())
                .setTitle("Fabric profile required")
                .setMessage("Select or install a Fabric profile for this Minecraft version, then open Mods again. The performance pack is installed only into that profile.")
                .setPositiveButton("OK", null).show();
            return;
        }
        final String gameVersion = etoExtractMinecraftVersion(instance.versionId);
        if (etoModsStatus != null) etoModsStatus.setText("Checking compatible performance mods for Minecraft " + gameVersion + "...");
        new Thread(() -> {
            java.util.LinkedHashMap<String, String> projects = new java.util.LinkedHashMap<>();
            projects.put("sodium", "Sodium (renderer)");
            projects.put("lithium", "Lithium");
            projects.put("ferrite-core", "FerriteCore");
            projects.put("immediatelyfast", "ImmediatelyFast");
            projects.put("entityculling", "Entity Culling");
            projects.put("modernfix", "ModernFix");
            projects.put("fabric-api", "Fabric API");
            java.util.ArrayList<String> installed = new java.util.ArrayList<>();
            java.util.ArrayList<String> skipped = new java.util.ArrayList<>();
            try {
                File folder = new File(etoModsVersionRoot(instance), "mods");
                if (!folder.exists() && !folder.mkdirs()) throw new java.io.IOException("Cannot create this profile's mods folder");
                java.util.ArrayDeque<String> pending = new java.util.ArrayDeque<>(projects.keySet());
                java.util.HashSet<String> visited = new java.util.HashSet<>();
                while (!pending.isEmpty()) {
                    String slug = pending.removeFirst();
                    if (!visited.add(slug)) continue;
                    try {
                        org.json.JSONObject project = etoModsHttpJson("https://api.modrinth.com/v2/project/" + java.net.URLEncoder.encode(slug, "UTF-8"));
                        String projectId = project.optString("id", "");
                        if (projectId.isEmpty()) { skipped.add(slug + " (missing project)"); continue; }
                        String query = "https://api.modrinth.com/v2/project/" + projectId + "/version?game_versions="
                                + java.net.URLEncoder.encode("[\"" + gameVersion + "\"]", "UTF-8")
                                + "&loaders=" + java.net.URLEncoder.encode("[\"fabric\"]", "UTF-8");
                        org.json.JSONArray versions = etoModsHttpArray(query);
                        if (versions.length() == 0) { skipped.add(slug + " (no build for this version)"); continue; }
                        org.json.JSONObject version = versions.getJSONObject(0);
                        org.json.JSONArray dependencies = version.optJSONArray("dependencies");
                        if (dependencies != null) {
                            for (int i = 0; i < dependencies.length(); i++) {
                                org.json.JSONObject dep = dependencies.getJSONObject(i);
                                if (!"required".equals(dep.optString("dependency_type"))) continue;
                                String depId = dep.optString("project_id", "");
                                if (!depId.isEmpty()) {
                                    // Modrinth project IDs are accepted directly by its project endpoint.
                                    pending.addLast(depId);
                                }
                            }
                        }
                        org.json.JSONArray files = version.optJSONArray("files");
                        if (files == null || files.length() == 0) { skipped.add(slug + " (no file)"); continue; }
                        org.json.JSONObject file = files.getJSONObject(0);
                        for (int i = 0; i < files.length(); i++) if (files.getJSONObject(i).optBoolean("primary")) { file = files.getJSONObject(i); break; }
                        String filename = file.optString("filename", "");
                        String url = file.optString("url", "");
                        if (!filename.toLowerCase(java.util.Locale.ROOT).endsWith(".jar")) { skipped.add(slug + " (not a JAR)"); continue; }
                        java.net.URL downloadUrl = new java.net.URL(url);
                        if (!"https".equalsIgnoreCase(downloadUrl.getProtocol())) throw new java.io.IOException("Modrinth returned a non-HTTPS download URL");
                        File target = new File(folder, filename.replaceAll("[^A-Za-z0-9._-]", "_"));
                        File part = new File(folder, target.getName() + ".part");
                        if (target.isFile() && target.length() > 0) { installed.add(slug + " (already present)"); continue; }
                        java.net.HttpURLConnection connection = (java.net.HttpURLConnection) downloadUrl.openConnection();
                        connection.setConnectTimeout(15000);
                        connection.setReadTimeout(30000);
                        connection.setRequestProperty("User-Agent", "EtoLauncher/1.0");
                        try {
                            if (connection.getResponseCode() != 200) throw new java.io.IOException("Download HTTP " + connection.getResponseCode());
                            long length = connection.getContentLengthLong();
                            if (length > 120L * 1024L * 1024L) throw new java.io.IOException("Mod file exceeds 120 MB");
                            try (java.io.InputStream in = connection.getInputStream(); java.io.FileOutputStream out = new java.io.FileOutputStream(part)) {
                                byte[] buffer = new byte[8192]; int n; long total = 0;
                                while ((n = in.read(buffer)) != -1) {
                                    total += n;
                                    if (total > 120L * 1024L * 1024L) throw new java.io.IOException("Mod file exceeds 120 MB");
                                    out.write(buffer, 0, n);
                                }
                            }
                        } finally { connection.disconnect(); }
                        if (target.exists() && !target.delete()) throw new java.io.IOException("Cannot replace " + target.getName());
                        if (!part.renameTo(target)) throw new java.io.IOException("Could not save " + target.getName());
                        installed.add(slug);
                    } catch (Exception modError) {
                        skipped.add(slug + " (" + modError.getMessage() + ")");
                    }
                }
                requireActivity().runOnUiThread(() -> {
                    if (!isAdded()) return;
                    refreshEtoInstalledMods();
                    String summary = "Performance pack: " + installed.size() + " installed; " + skipped.size() + " unavailable for " + gameVersion + ".";
                    if (etoModsStatus != null) etoModsStatus.setText(summary);
                    new android.app.AlertDialog.Builder(requireContext())
                        .setTitle("Eto Performance Pack")
                        .setMessage(summary + "\n\nSodium needs the LTW renderer in Video settings on Android. If the game fails to start, remove Sodium from this profile's Mods list. Missing versions are skipped, not replaced with incompatible files.")
                        .setPositiveButton("OK", null).show();
                });
            } catch (Exception error) {
                requireActivity().runOnUiThread(() -> {
                    if (isAdded()) Toast.makeText(requireContext(), "Performance pack failed: " + error.getMessage(), Toast.LENGTH_LONG).show();
                });
            }
        }, "EtoPerformancePack").start();
    }

    private org.json.JSONArray etoModsHttpArray(String address) throws Exception {
        java.net.HttpURLConnection connection = (java.net.HttpURLConnection) new java.net.URL(address).openConnection();
        connection.setConnectTimeout(12000);
        connection.setReadTimeout(18000);
        connection.setRequestProperty("User-Agent", "EtoLauncher/1.0");
        try {
            if (connection.getResponseCode() != 200) throw new java.io.IOException("HTTP " + connection.getResponseCode());
            try (java.io.InputStream in = connection.getInputStream(); java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream()) {
                byte[] buffer = new byte[8192]; int n;
                while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
                return new org.json.JSONArray(new String(out.toByteArray(), java.nio.charset.StandardCharsets.UTF_8));
            }
        } finally { connection.disconnect(); }
    }
'''
if "private void installEtoPerformancePack()" not in s:
    pos = s.rfind("\n}")
    if pos < 0: raise SystemExit("MainMenuFragment class end missing")
    s = s[:pos] + "\n" + methods + s[pos:]

# Keep Modrinth project version parsing aligned with newer four-part version IDs.
s = s.replace('Pattern.compile("\\\\d+\\\\.\\\\d+(?:\\\\.\\\\d+)?")',
              'Pattern.compile("\\\\d+(?:\\\\.\\\\d+){1,3}")')

p.write_text(s, encoding="utf-8")
print("Added Modrinth performance pack, per-profile Ultra Lite options, and 10% resolution scaling.")
