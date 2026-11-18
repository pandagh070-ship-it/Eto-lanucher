from pathlib import Path

p = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/fragments/MainMenuFragment.java")
s = p.read_text(encoding="utf-8")

needle = "        mVersionSpinner = view.findViewById(R.id.mc_version_spinner);"
if "showEtoModsManager()" not in s:
    if needle not in s:
        raise SystemExit("Mods button insertion point missing")
    s = s.replace(needle, needle + """
        Button etoModsButton = view.findViewById(R.id.mods_button);
        etoModsButton.setOnClickListener(v -> showEtoModsManager());
""", 1)

play_needle = "        Instance instance = Instances.loadSelectedInstance();"
if "syncEtoModsForSelectedInstance();" not in s:
    if play_needle not in s:
        raise SystemExit("Play handler insertion point missing")
    s = s.replace(play_needle, play_needle + """
        if (instance != null) syncEtoModsForSelectedInstance();
""", 1)

methods = r'''
    // Eto Mods: Modrinth catalogue + per-Minecraft-version storage.
    private android.widget.LinearLayout etoModsInstalledList;
    private android.widget.LinearLayout etoModsCatalogList;
    private android.widget.EditText etoModsSearch;
    private android.widget.EditText etoModsVersion;
    private android.widget.Spinner etoModsLoader;
    private android.widget.Spinner etoModsType;
    private android.widget.TextView etoModsStatus;
    private android.app.Dialog etoModsDialog;

    private void showEtoModsManager() {
        if (!isAdded()) return;
        Instance selected = Instances.loadSelectedInstance();
        if (selected == null) {
            Toast.makeText(requireContext(), "Select a Minecraft version first", Toast.LENGTH_LONG).show();
            return;
        }

        android.widget.LinearLayout root = new android.widget.LinearLayout(requireContext());
        root.setOrientation(android.widget.LinearLayout.HORIZONTAL);
        root.setBackgroundColor(Color.rgb(12, 18, 27));

        android.widget.LinearLayout left = new android.widget.LinearLayout(requireContext());
        left.setOrientation(android.widget.LinearLayout.VERTICAL);
        left.setPadding(12, 12, 8, 12);
        left.setBackgroundColor(Color.rgb(19, 29, 41));
        root.addView(left, new android.widget.LinearLayout.LayoutParams(0, -1, 0.34f));

        android.widget.TextView installedTitle = etoModsText("INSTALLED MODS", 13, Color.rgb(143,230,192), true);
        left.addView(installedTitle);
        android.widget.TextView installedHint = etoModsText("This Minecraft version only", 10, Color.LTGRAY, false);
        left.addView(installedHint);
        android.widget.ScrollView installedScroll = new android.widget.ScrollView(requireContext());
        etoModsInstalledList = new android.widget.LinearLayout(requireContext());
        etoModsInstalledList.setOrientation(android.widget.LinearLayout.VERTICAL);
        installedScroll.addView(etoModsInstalledList);
        left.addView(installedScroll, new android.widget.LinearLayout.LayoutParams(-1, 0, 1f));

        android.widget.LinearLayout right = new android.widget.LinearLayout(requireContext());
        right.setOrientation(android.widget.LinearLayout.VERTICAL);
        right.setPadding(12, 12, 12, 12);
        root.addView(right, new android.widget.LinearLayout.LayoutParams(0, -1, 0.66f));

        android.widget.TextView title = etoModsText("MODRINTH  /  MOD LIBRARY", 16, Color.WHITE, true);
        right.addView(title);
        android.widget.TextView subtitle = etoModsText("Find and install compatible mods and shader packs", 10, Color.LTGRAY, false);
        right.addView(subtitle);

        android.widget.LinearLayout filters = new android.widget.LinearLayout(requireContext());
        filters.setOrientation(android.widget.LinearLayout.HORIZONTAL);
        filters.setGravity(android.view.Gravity.CENTER_VERTICAL);
        right.addView(filters);

        etoModsVersion = new android.widget.EditText(requireContext());
        etoModsVersion.setSingleLine(true);
        etoModsVersion.setText(etoExtractMinecraftVersion(selected.versionId));
        etoModsVersion.setHint("Minecraft version");
        etoModsVersion.setTextColor(Color.WHITE);
        etoModsVersion.setHintTextColor(Color.GRAY);
        etoModsVersion.setTextSize(11);
        etoModsVersion.setPadding(10, 4, 10, 4);
        etoModsVersion.setBackgroundColor(Color.rgb(35, 48, 63));
        filters.addView(etoModsVersion, new android.widget.LinearLayout.LayoutParams(0, 42, 1f));

        etoModsLoader = new android.widget.Spinner(requireContext());
        String[] loaders = {"Fabric", "Forge", "NeoForge", "Quilt", "Iris"};
        android.widget.ArrayAdapter<String> loaderAdapter = new android.widget.ArrayAdapter<>(requireContext(), android.R.layout.simple_spinner_dropdown_item, loaders);
        etoModsLoader.setAdapter(loaderAdapter);
        filters.addView(etoModsLoader, new android.widget.LinearLayout.LayoutParams(0, 42, 1f));

        etoModsType = new android.widget.Spinner(requireContext());
        String[] types = {"Mods", "Shaders"};
        etoModsType.setAdapter(new android.widget.ArrayAdapter<>(requireContext(), android.R.layout.simple_spinner_dropdown_item, types));
        filters.addView(etoModsType, new android.widget.LinearLayout.LayoutParams(0, 42, 0.75f));

        android.widget.LinearLayout searchRow = new android.widget.LinearLayout(requireContext());
        searchRow.setOrientation(android.widget.LinearLayout.HORIZONTAL);
        searchRow.setGravity(android.view.Gravity.CENTER_VERTICAL);
        searchRow.setPadding(0, 8, 0, 8);
        right.addView(searchRow);

        etoModsSearch = new android.widget.EditText(requireContext());
        etoModsSearch.setSingleLine(true);
        etoModsSearch.setHint("Search mods and shaders...");
        etoModsSearch.setTextColor(Color.WHITE);
        etoModsSearch.setHintTextColor(Color.GRAY);
        etoModsSearch.setTextSize(12);
        etoModsSearch.setPadding(12, 4, 12, 4);
        etoModsSearch.setBackgroundColor(Color.rgb(35, 48, 63));
        searchRow.addView(etoModsSearch, new android.widget.LinearLayout.LayoutParams(0, 44, 1f));

        android.widget.Button searchButton = etoModsButton("SEARCH");
        searchRow.addView(searchButton, new android.widget.LinearLayout.LayoutParams(-2, 44));
        searchButton.setOnClickListener(v -> searchEtoMods());

        etoModsStatus = etoModsText("Popular projects • choose a loader and Minecraft version", 10, Color.rgb(143,230,192), false);
        right.addView(etoModsStatus);

        android.widget.ScrollView catalogScroll = new android.widget.ScrollView(requireContext());
        etoModsCatalogList = new android.widget.LinearLayout(requireContext());
        etoModsCatalogList.setOrientation(android.widget.LinearLayout.VERTICAL);
        catalogScroll.addView(etoModsCatalogList);
        right.addView(catalogScroll, new android.widget.LinearLayout.LayoutParams(-1, 0, 1f));

        etoModsDialog = new android.app.Dialog(requireContext());
        etoModsDialog.setContentView(root);
        etoModsDialog.show();
        if (etoModsDialog.getWindow() != null) {
            etoModsDialog.getWindow().setBackgroundDrawableResource(android.R.color.transparent);
            etoModsDialog.getWindow().setLayout(-1, -1);
        }
        refreshEtoInstalledMods();
        searchEtoMods();
    }

    private android.widget.TextView etoModsText(String value, float size, int color, boolean bold) {
        android.widget.TextView view = new android.widget.TextView(requireContext());
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        if (bold) view.setTypeface(null, android.graphics.Typeface.BOLD);
        view.setPadding(4, 7, 4, 7);
        return view;
    }

    private android.widget.Button etoModsButton(String value) {
        android.widget.Button button = new android.widget.Button(requireContext());
        button.setText(value);
        button.setTextSize(10);
        button.setAllCaps(false);
        button.setTextColor(Color.rgb(8, 20, 16));
        button.setTypeface(null, android.graphics.Typeface.BOLD);
        android.graphics.drawable.GradientDrawable bg = new android.graphics.drawable.GradientDrawable();
        bg.setColor(Color.rgb(143, 230, 192));
        bg.setCornerRadius(12f);
        button.setBackground(bg);
        return button;
    }

    private String etoExtractMinecraftVersion(String raw) {
        if (raw == null) return "1.20.1";
        java.util.regex.Matcher matcher = java.util.regex.Pattern.compile("\\d+\\.\\d+(?:\\.\\d+)?").matcher(raw);
        return matcher.find() ? matcher.group() : "1.20.1";
    }

    private String etoSelectedLoader() {
        if (etoModsLoader == null) return "fabric";
        String value = String.valueOf(etoModsLoader.getSelectedItem()).toLowerCase(java.util.Locale.ROOT);
        if (value.equals("neoforge")) return "neoforge";
        if (value.equals("forge")) return "forge";
        if (value.equals("quilt")) return "quilt";
        return value.equals("iris") ? "iris" : "fabric";
    }

    private boolean etoIsShaderSearch() {
        return etoModsType != null && "Shaders".equals(String.valueOf(etoModsType.getSelectedItem()));
    }

    private String etoSafeFolderName(String value) {
        if (value == null) return "unknown";
        return value.replaceAll("[^A-Za-z0-9._-]", "_");
    }

    private File etoModsVersionRoot(Instance instance) {
        String version = etoSafeFolderName(etoExtractMinecraftVersion(instance.versionId));
        return new File(new File(instance.getGameDirectory(), "eto-mods"), version);
    }

    private void searchEtoMods() {
        if (!isAdded() || etoModsCatalogList == null) return;
        final String query = etoModsSearch.getText().toString().trim();
        final String gameVersion = etoModsVersion.getText().toString().trim();
        final String loader = etoSelectedLoader();
        final boolean shaders = etoIsShaderSearch();
        if (!gameVersion.matches("\\d+\\.\\d+(?:\\.\\d+)?")) {
            etoModsStatus.setText("Enter a valid Minecraft version, e.g. 1.20.1");
            return;
        }
        etoModsStatus.setText("Searching Modrinth...");
        etoModsCatalogList.removeAllViews();
        new Thread(() -> {
            try {
                String projectType = shaders ? "shader" : "mod";
                String facets = "[[\"project_type:" + projectType + "\"],[\"versions:" + gameVersion + "\"]]";
                if (!shaders && !loader.equals("iris")) facets = "[[\"project_type:mod\"],[\"versions:" + gameVersion + "\"],[\"categories:" + loader + "\"]]";
                String address = "https://api.modrinth.com/v2/search?query=" + java.net.URLEncoder.encode(query, "UTF-8")
                        + "&limit=30&index=relevance&facets=" + java.net.URLEncoder.encode(facets, "UTF-8");
                org.json.JSONObject response = etoModsHttpJson(address);
                org.json.JSONArray hits = response.optJSONArray("hits");
                java.util.ArrayList<org.json.JSONObject> projects = new java.util.ArrayList<>();
                if (hits != null) for (int i=0; i<hits.length(); i++) projects.add(hits.getJSONObject(i));
                requireActivity().runOnUiThread(() -> {
                    if (!isAdded() || etoModsCatalogList == null) return;
                    etoModsCatalogList.removeAllViews();
                    etoModsStatus.setText(projects.size() + " projects • Minecraft " + gameVersion + " • " + (shaders ? "Shaders" : loader));
                    if (projects.isEmpty()) {
                        etoModsCatalogList.addView(etoModsText("No compatible projects found. Try another version or loader.", 12, Color.LTGRAY, false));
                        return;
                    }
                    for (org.json.JSONObject project : projects) addEtoModProjectCard(project, gameVersion, loader, shaders);
                });
            } catch (Exception error) {
                requireActivity().runOnUiThread(() -> {
                    if (isAdded() && etoModsStatus != null) etoModsStatus.setText("Catalog error: " + error.getMessage());
                });
            }
        }, "EtoModSearch").start();
    }

    private org.json.JSONObject etoModsHttpJson(String address) throws Exception {
        java.net.HttpURLConnection connection = (java.net.HttpURLConnection) new java.net.URL(address).openConnection();
        connection.setConnectTimeout(12000);
        connection.setReadTimeout(18000);
        connection.setRequestProperty("User-Agent", "EtoLauncher/1.0 (https://github.com/pandagh070-ship-it/Eto-lanucher)");
        try {
            int code = connection.getResponseCode();
            if (code != 200) throw new java.io.IOException("HTTP " + code);
            java.io.InputStream in = connection.getInputStream();
            java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int n;
            while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
            in.close();
            return new org.json.JSONObject(new String(out.toByteArray(), java.nio.charset.StandardCharsets.UTF_8));
        } finally { connection.disconnect(); }
    }

    private void addEtoModProjectCard(org.json.JSONObject project, String gameVersion, String loader, boolean shaders) {
        android.widget.LinearLayout card = new android.widget.LinearLayout(requireContext());
        card.setOrientation(android.widget.LinearLayout.VERTICAL);
        card.setPadding(12, 8, 12, 8);
        card.setBackgroundColor(Color.rgb(25, 37, 51));
        android.widget.LinearLayout.LayoutParams cardParams = new android.widget.LinearLayout.LayoutParams(-1, -2);
        cardParams.setMargins(0, 5, 0, 5);
        etoModsCatalogList.addView(card, cardParams);

        String name = project.optString("title", "Untitled project");
        String description = project.optString("description", "");
        android.widget.TextView heading = etoModsText(name, 13, Color.WHITE, true);
        card.addView(heading);
        android.widget.TextView details = etoModsText(description + "\nDownloads: " + project.optLong("downloads", 0), 10, Color.LTGRAY, false);
        card.addView(details);
        android.widget.Button install = etoModsButton("INSTALL");
        card.addView(install, new android.widget.LinearLayout.LayoutParams(-2, 38));
        install.setOnClickListener(v -> downloadEtoModProject(project.optString("project_id"), name, gameVersion, loader, shaders, install));
    }

    private void downloadEtoModProject(String projectId, String projectName, String gameVersion, String loader, boolean shaders, android.widget.Button button) {
        if (projectId == null || projectId.isEmpty()) return;
        button.setEnabled(false);
        button.setText("DOWNLOADING...");
        new Thread(() -> {
            try {
                String loadersJson = "[\"" + (shaders ? (loader.equals("iris") ? "iris" : "optifine") : loader) + "\"]";
                String address = "https://api.modrinth.com/v2/project/" + java.net.URLEncoder.encode(projectId, "UTF-8")
                        + "/version?game_versions=" + java.net.URLEncoder.encode("[\"" + gameVersion + "\"]", "UTF-8")
                        + "&loaders=" + java.net.URLEncoder.encode(loadersJson, "UTF-8");
                java.net.HttpURLConnection connection = (java.net.HttpURLConnection) new java.net.URL(address).openConnection();
                connection.setConnectTimeout(12000);
                connection.setReadTimeout(18000);
                connection.setRequestProperty("User-Agent", "EtoLauncher/1.0");
                org.json.JSONArray versions;
                try {
                    if (connection.getResponseCode() != 200) throw new java.io.IOException("No compatible version");
                    java.io.InputStream in = connection.getInputStream();
                    java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
                    byte[] buf = new byte[8192]; int n;
                    while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
                    in.close();
                    versions = new org.json.JSONArray(new String(out.toByteArray(), java.nio.charset.StandardCharsets.UTF_8));
                } finally { connection.disconnect(); }
                if (versions.length() == 0) throw new java.io.IOException("No file for " + gameVersion + " / " + loader);
                org.json.JSONObject first = versions.getJSONObject(0);
                org.json.JSONArray files = first.optJSONArray("files");
                if (files == null || files.length() == 0) throw new java.io.IOException("Project has no downloadable file");
                org.json.JSONObject selectedFile = files.getJSONObject(0);
                for (int i=0; i<files.length(); i++) if (files.getJSONObject(i).optBoolean("primary")) { selectedFile = files.getJSONObject(i); break; }
                String fileName = selectedFile.optString("filename", "");
                String fileUrl = selectedFile.optString("url", "");
                String lowerName = fileName.toLowerCase(java.util.Locale.ROOT);
                if (shaders ? !lowerName.endsWith(".zip") : !lowerName.endsWith(".jar"))
                    throw new java.io.IOException(shaders ? "Shader pack is not a ZIP file" : "This project file is not a JAR mod");
                java.net.URL downloadUrl = new java.net.URL(fileUrl);
                if (!"https".equalsIgnoreCase(downloadUrl.getProtocol())) throw new java.io.IOException("Download URL must use HTTPS");

                Instance instance = Instances.loadSelectedInstance();
                if (instance == null) throw new java.io.IOException("No selected game profile");
                File folder = new File(etoModsVersionRoot(instance), shaders ? "shaderpacks" : "mods");
                if (!folder.exists() && !folder.mkdirs()) throw new java.io.IOException("Cannot create mod folder");
                String safeName = fileName.replaceAll("[^A-Za-z0-9._-]", "_");
                File target = new File(folder, safeName);
                File temporary = new File(folder, safeName + ".part");
                java.net.HttpURLConnection fileConnection = (java.net.HttpURLConnection) downloadUrl.openConnection();
                fileConnection.setConnectTimeout(15000);
                fileConnection.setReadTimeout(30000);
                fileConnection.setRequestProperty("User-Agent", "EtoLauncher/1.0");
                try {
                    if (fileConnection.getResponseCode() != 200) throw new java.io.IOException("Download failed: HTTP " + fileConnection.getResponseCode());
                    int length = fileConnection.getContentLength();
                    if (length > 200 * 1024 * 1024) throw new java.io.IOException("File is too large");
                    try (java.io.InputStream in = fileConnection.getInputStream(); java.io.FileOutputStream out = new java.io.FileOutputStream(temporary)) {
                        byte[] buffer = new byte[8192]; int n; long total = 0;
                        while ((n = in.read(buffer)) != -1) {
                            total += n;
                            if (total > 200L * 1024L * 1024L) throw new java.io.IOException("File is too large");
                            out.write(buffer, 0, n);
                        }
                    }
                } finally { fileConnection.disconnect(); }
                if (target.exists() && !target.delete()) throw new java.io.IOException("Cannot replace existing file");
                if (!temporary.renameTo(target)) throw new java.io.IOException("Could not save downloaded file");
                requireActivity().runOnUiThread(() -> {
                    if (!isAdded()) return;
                    button.setEnabled(true);
                    button.setText("INSTALLED");
                    refreshEtoInstalledMods();
                    if (etoModsStatus != null) etoModsStatus.setText("Installed " + projectName + " for Minecraft " + gameVersion);
                });
            } catch (Exception error) {
                requireActivity().runOnUiThread(() -> {
                    if (!isAdded()) return;
                    button.setEnabled(true);
                    button.setText("RETRY");
                    Toast.makeText(requireContext(), "Install failed: " + error.getMessage(), Toast.LENGTH_LONG).show();
                });
            }
        }, "EtoModDownload").start();
    }

    private void refreshEtoInstalledMods() {
        if (!isAdded() || etoModsInstalledList == null) return;
        etoModsInstalledList.removeAllViews();
        Instance instance = Instances.loadSelectedInstance();
        if (instance == null) return;
        File root = etoModsVersionRoot(instance);
        addEtoInstalledFolder(new File(root, "mods"), false);
        addEtoInstalledFolder(new File(root, "shaderpacks"), true);
    }

    private void addEtoInstalledFolder(File folder, boolean shaders) {
        if (!folder.exists()) return;
        File[] files = folder.listFiles();
        if (files == null) return;
        for (File file : files) {
            if (!file.isFile() || file.getName().endsWith(".part")) continue;
            android.widget.LinearLayout row = new android.widget.LinearLayout(requireContext());
            row.setOrientation(android.widget.LinearLayout.HORIZONTAL);
            row.setGravity(android.view.Gravity.CENTER_VERTICAL);
            android.widget.TextView label = etoModsText(file.getName(), 10, Color.WHITE, false);
            label.setMaxLines(2);
            row.addView(label, new android.widget.LinearLayout.LayoutParams(0, -2, 1f));
            android.widget.Button remove = new android.widget.Button(requireContext());
            remove.setText("X");
            remove.setTextColor(Color.WHITE);
            remove.setTextSize(11);
            remove.setPadding(0, 0, 0, 0);
            remove.setMinWidth(34);
            remove.setOnClickListener(v -> {
                new AlertDialog.Builder(requireContext())
                        .setTitle("Remove " + file.getName() + "?")
                        .setMessage("This removes the file from this Minecraft version only.")
                        .setNegativeButton("Cancel", null)
                        .setPositiveButton("Remove", (d, w) -> {
                            if (file.delete()) {
                                refreshEtoInstalledMods();
                                Toast.makeText(requireContext(), "Removed", Toast.LENGTH_SHORT).show();
                            } else Toast.makeText(requireContext(), "Could not remove file", Toast.LENGTH_SHORT).show();
                        }).show();
            });
            row.addView(remove);
            etoModsInstalledList.addView(row);
        }
    }

    // Only Eto-managed files are swapped into the active game directory at launch.
    // This keeps different Minecraft versions isolated even when Pojav uses shared_dir.
    private void syncEtoModsForSelectedInstance() {
        try {
            Instance instance = Instances.loadSelectedInstance();
            if (instance == null) return;
            File game = instance.getGameDirectory();
            syncEtoManagedFolder(game, new File(etoModsVersionRoot(instance), "mods"), "mods", ".eto-managed-mods.txt");
            syncEtoManagedFolder(game, new File(etoModsVersionRoot(instance), "shaderpacks"), "shaderpacks", ".eto-managed-shaders.txt");
        } catch (Exception error) {
            Log.e("EtoMods", "Could not activate version-specific mods", error);
            Toast.makeText(requireContext(), "Eto could not activate its mods: " + error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void syncEtoManagedFolder(File game, File source, String folderName, String manifestName) throws Exception {
        File destination = new File(game, folderName);
        if (!destination.exists() && !destination.mkdirs()) throw new java.io.IOException("Cannot create " + folderName);
        File manifest = new File(game, manifestName);
        if (manifest.exists()) {
            java.util.List<String> previous = java.nio.file.Files.readAllLines(manifest.toPath(), java.nio.charset.StandardCharsets.UTF_8);
            for (String name : previous) {
                if (name.matches("[A-Za-z0-9._-]{1,150}")) new File(destination, name).delete();
            }
        }
        java.util.ArrayList<String> current = new java.util.ArrayList<>();
        File[] files = source.listFiles();
        if (files != null) for (File file : files) {
            if (!file.isFile() || file.getName().endsWith(".part")) continue;
            String name = file.getName();
            File target = new File(destination, name);
            if (target.exists()) target = new File(destination, "eto_" + name);
            java.nio.file.Files.copy(file.toPath(), target.toPath(), java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            current.add(target.getName());
        }
        java.nio.file.Files.write(manifest.toPath(), current, java.nio.charset.StandardCharsets.UTF_8);
    }
'''
if "Eto Mods: Modrinth catalogue" not in s:
    pos = s.rfind("\n}")
    if pos < 0: raise SystemExit("MainMenuFragment class end missing")
    s = s[:pos] + "\n" + methods + s[pos:]

p.write_text(s, encoding="utf-8")
print("Added Eto Modrinth mod/shader manager with per-version activation.")
