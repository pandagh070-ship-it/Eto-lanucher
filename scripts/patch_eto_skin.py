from pathlib import Path

p = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/fragments/MainMenuFragment.java")
s = p.read_text(encoding="utf-8")

def add_import(line):
    global s
    if line not in s:
        anchor = "import java.io.File;"
        if anchor in s:
            s = s.replace(anchor, anchor + "\n" + line, 1)
        else:
            s = s.replace("import android.content.Intent;", "import android.content.Intent;\n" + line, 1)

for imp in ("import java.io.FileInputStream;", "import java.io.FileOutputStream;", "import java.io.InputStream;"):
    add_import(imp)

# Bind the dedicated Skin button in the main launcher menu, separate from background customization.
if 'skinButton.setOnClickListener' not in s:
    anchor = '        customizeButton.setOnClickListener(v -> showEtoCustomization());'
    if anchor not in s:
        raise SystemExit("Eto main-menu customization listener not found")
    s = s.replace(anchor, anchor + """
        android.widget.Button skinButton = view.findViewById(R.id.skin_button);
        skinButton.setOnClickListener(v -> showEtoSkinPicker());
        ImageButton etoAvatar = view.findViewById(R.id.edit_profile_button);
        updateEtoSkinAvatar(etoAvatar);
""", 1)

skin_picker_method = r"""
    private void showEtoSkinPicker() {
        android.widget.EditText username = new android.widget.EditText(requireContext());
        username.setSingleLine(true);
        username.setHint("Minecraft username (Guest name)");
        username.setText(requireContext().getSharedPreferences("eto_style", 0).getString("skin_username", ""));
        new AlertDialog.Builder(requireContext())
            .setTitle("Eto Skin Studio")
            .setMessage("Choose your Minecraft username, then select a 64x64 or 64x32 PNG skin. The skin is stored locally for your selected game profile.")
            .setView(username)
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Choose PNG", (d, w) -> {
                String name = username.getText().toString().trim();
                if (name.isEmpty() || !name.matches("[A-Za-z0-9_]{1,16}")) {
                    Toast.makeText(requireContext(), "Enter a valid Minecraft username", Toast.LENGTH_LONG).show();
                    return;
                }
                requireContext().getSharedPreferences("eto_style", 0).edit().putString("skin_username", name).apply();
                Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                pick.addCategory(Intent.CATEGORY_OPENABLE);
                pick.setType("image/png");
                startActivityForResult(pick, 8304);
            }).show();
    }

"""
if "private void showEtoSkinPicker()" not in s:
    pos = s.rfind("\n}")
    if pos < 0: raise SystemExit("MainMenuFragment closing brace missing")
    s = s[:pos] + "\n" + skin_picker_method + s[pos:]

# Extend the existing picker handler with skin import before its image/video guard.
old = '        if (data == null || data.getData() == null || (requestCode != ETO_PICK_IMAGE && requestCode != ETO_PICK_VIDEO)) return;'
new = '''        if (requestCode == 8304) {
            if (resultCode != android.app.Activity.RESULT_OK || data == null || data.getData() == null) return;
            installEtoLocalSkin(data.getData());
            return;
        }
        if (data == null || data.getData() == null || (requestCode != ETO_PICK_IMAGE && requestCode != ETO_PICK_VIDEO)) return;'''
if old in s and 'installEtoLocalSkin(data.getData())' not in s:
    s = s.replace(old, new, 1)

methods = r"""
    private void installEtoLocalSkin(Uri uri) {
        if (!isAdded()) return;
        try {
            android.content.ContentResolver resolver = requireContext().getContentResolver();
            android.graphics.BitmapFactory.Options bounds = new android.graphics.BitmapFactory.Options();
            bounds.inJustDecodeBounds = true;
            try (InputStream check = resolver.openInputStream(uri)) {
                android.graphics.BitmapFactory.decodeStream(check, null, bounds);
            }
            if (!((bounds.outWidth == 64 && bounds.outHeight == 64) ||
                  (bounds.outWidth == 64 && bounds.outHeight == 32))) {
                Toast.makeText(requireContext(), "Skin must be a 64x64 or 64x32 PNG", Toast.LENGTH_LONG).show();
                return;
            }

            Instance instance = Instances.loadSelectedInstance();
            if (instance == null) {
                Toast.makeText(requireContext(), "Select a Minecraft profile first", Toast.LENGTH_LONG).show();
                return;
            }
            File gameDir = instance.getGameDirectory();
            String username = requireContext().getSharedPreferences("eto_style", 0)
                    .getString("skin_username", "Player");
            File skinDir = new File(gameDir, "CustomSkinLoader/LocalSkin/skins");
            File modsDir = new File(gameDir, "mods");
            if (!skinDir.exists() && !skinDir.mkdirs()) throw new java.io.IOException("Cannot create skin folder");
            if (!modsDir.exists() && !modsDir.mkdirs()) throw new java.io.IOException("Cannot create mods folder");

            File skinFile = new File(skinDir, username + ".png");
            try (InputStream in = resolver.openInputStream(uri);
                 FileOutputStream out = new FileOutputStream(skinFile)) {
                if (in == null) throw new java.io.IOException("Cannot read selected PNG");
                byte[] buffer = new byte[8192];
                int count;
                while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
            }

            File modFile = new File(modsDir, "CustomSkinLoader_Universal-15.0.1.jar");
            if (!modFile.exists() || modFile.length() < 10000) {
                try (InputStream in = requireContext().getAssets().open("eto/CustomSkinLoader_Universal-15.0.1.jar");
                     FileOutputStream out = new FileOutputStream(modFile)) {
                    byte[] buffer = new byte[8192];
                    int count;
                    while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count);
                }
            }
            File configDir = new File(gameDir, "CustomSkinLoader");
            if (!configDir.exists()) configDir.mkdirs();
            File config = new File(configDir, "CustomSkinLoader.json");
            if (!config.exists()) {
                String json = "{\n  \"enable\": true,\n  \"loadlist\": [\n    { \"name\": \"LocalSkin\", \"type\": \"Legacy\", \"root\": \"LocalSkin/\" },\n    { \"name\": \"Mojang\", \"type\": \"MojangAPI\" }\n  ]\n}";
                try (FileOutputStream out = new FileOutputStream(config)) {
                    out.write(json.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                }
            }
            Toast.makeText(requireContext(), "Skin installed for " + username + ". Launch this profile with Fabric, then rejoin the world.", Toast.LENGTH_LONG).show();
            View menu = getView();
            if (menu != null) {
                ImageButton avatar = menu.findViewById(R.id.edit_profile_button);
                updateEtoSkinAvatar(avatar);
            }
        } catch (Exception ex) {
            Toast.makeText(requireContext(), "Skin install failed: " + ex.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

"""
if "private void installEtoLocalSkin(Uri uri)" not in s:
    pos = s.rfind("\n}")
    if pos < 0: raise SystemExit("MainMenuFragment closing brace missing")
    s = s[:pos] + "\n" + methods + s[pos:]

avatar_method = r"""
    private void updateEtoSkinAvatar(ImageButton avatar) {
        if (avatar == null || !isAdded()) return;
        try {
            Instance instance = Instances.loadSelectedInstance();
            if (instance == null) return;
            String username = requireContext().getSharedPreferences("eto_style", 0)
                    .getString("skin_username", "Player");
            File skin = new File(new File(instance.getGameDirectory(),
                    "CustomSkinLoader/LocalSkin/skins"), username + ".png");
            if (!skin.isFile()) return;
            Bitmap source = BitmapFactory.decodeFile(skin.getAbsolutePath());
            if (source == null || source.getWidth() < 48 || source.getHeight() < 16) return;
            Bitmap face = Bitmap.createBitmap(source, 8, 8, 8, 8).copy(Bitmap.Config.ARGB_8888, true);
            Bitmap hat = Bitmap.createBitmap(source, 40, 8, 8, 8);
            new Canvas(face).drawBitmap(hat, 0, 0, null);
            hat.recycle();
            avatar.setImageBitmap(face);
            avatar.setScaleType(ImageButton.ScaleType.CENTER_CROP);
            avatar.setPadding(8, 8, 8, 8);
            avatar.setContentDescription("Current Minecraft skin");
        } catch (Exception ignored) {
            // Keep the default profile icon if no readable local skin is available.
        }
    }
"""
if "private void updateEtoSkinAvatar(" not in s:
    pos = s.rfind("\n}")
    if pos < 0: raise SystemExit("MainMenuFragment closing brace missing for skin avatar")
    s = s[:pos] + "\n" + avatar_method + "\n" + s[pos:]

p.write_text(s, encoding="utf-8")
print("Added Eto local skin import and CustomSkinLoader integration.")
