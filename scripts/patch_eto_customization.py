from pathlib import Path

p = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/fragments/MainMenuFragment.java")
s = p.read_text(encoding="utf-8")
imports = [
    ("import android.content.Intent;", "import android.content.Intent;\nimport android.net.Uri;\nimport android.media.AudioAttributes;"),
    ("import android.view.View;", "import android.view.View;\nimport android.view.ViewGroup;\nimport android.view.MotionEvent;"),
    ("import android.widget.Toast;", "import android.widget.Toast;\nimport android.widget.TextView;\nimport android.widget.VideoView;\nimport android.media.MediaPlayer;"),
    ("import android.os.Bundle;", "import android.os.Bundle;\nimport android.graphics.Color;\nimport android.graphics.drawable.Drawable;")
]
for old, new in imports:
    if new not in s:
        s = s.replace(old, new, 1)

needle = "        mVersionSpinner = view.findViewById(R.id.mc_version_spinner);"
if "showEtoCustomization()" not in s:
    if needle not in s:
        raise SystemExit("MainMenuFragment insertion point missing")
    s = s.replace(needle, needle + """
        Button customizeButton = view.findViewById(R.id.customize_button);
        customizeButton.setOnClickListener(v -> showEtoCustomization());
        ImageButton etoSettingsButton = view.findViewById(R.id.eto_settings_button);
        etoSettingsButton.setOnClickListener(v -> showEtoSettings());
        applyEtoLanguage(view);
        applyEtoCustomization(view);
""", 1)

methods = r'''
    private static final int ETO_PICK_IMAGE = 8301;
    private static final int ETO_PICK_VIDEO = 8302;
    private static final int ETO_PICK_MUSIC = 8303;
    private static android.media.MediaPlayer etoMusicPlayer;
    private static android.media.MediaPlayer etoBackgroundMediaPlayer;
    private static boolean etoIntroAudioActive = false;

    private void showEtoCustomization() {
        android.widget.LinearLayout panel = new android.widget.LinearLayout(requireContext());
        panel.setOrientation(android.widget.LinearLayout.VERTICAL);
        panel.setPadding(16, 8, 16, 8);
        android.widget.TextView intro = new android.widget.TextView(requireContext());
        intro.setText("HOME LOOK & BACKGROUNDS");
        intro.setTextSize(12); intro.setTextColor(Color.GRAY); intro.setPadding(4, 8, 4, 14);
        panel.addView(intro);
        android.widget.GridLayout grid = new android.widget.GridLayout(requireContext());
        grid.setColumnCount(2); panel.addView(grid);
        String[] labels = {"Image background", "Video background", "Save current", "Saved backgrounds", "Text: dark", "Text: white", "Text: green", "Reset"};
        for (int n = 0; n < labels.length; n++) {
            final int which = n;
            android.widget.Button button = new android.widget.Button(requireContext());
            button.setText(labels[n]); button.setTextSize(12);
            android.widget.GridLayout.LayoutParams lp = new android.widget.GridLayout.LayoutParams();
            lp.width = 0; lp.height = android.widget.GridLayout.LayoutParams.WRAP_CONTENT;
            lp.columnSpec = android.widget.GridLayout.spec(n % 2, 1f); lp.setMargins(4,4,4,4);
            grid.addView(button, lp);
            button.setOnClickListener(v -> {
                android.app.Dialog old = (android.app.Dialog) panel.getTag();
                if (old != null) old.dismiss();
                if (which < 2) {
                    Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE); i.setType(which == 0 ? "image/*" : "video/*");
                    startActivityForResult(i, which == 0 ? ETO_PICK_IMAGE : ETO_PICK_VIDEO);
                } else if (which == 2) saveEtoBackground();
                else if (which == 3) showSavedEtoBackgrounds();
                else if (which < 7) {
                    int[] colors = {Color.rgb(24,33,43), Color.WHITE, Color.rgb(21,148,90)};
                    requireContext().getSharedPreferences("eto_style", 0).edit().putInt("text", colors[which-4]).apply();
                    applyEtoCustomization(getView());
                } else {
                    requireContext().getSharedPreferences("eto_style", 0).edit().clear().apply();
                    applyEtoCustomization(getView());
                }
            });
        }
        AlertDialog dialog = new AlertDialog.Builder(requireContext()).setTitle("Eto Studio").setView(panel).setNegativeButton("Close", null).create();
        panel.setTag(dialog); dialog.show();
    }

    @Override public void onPause() {
        stopEtoBackgroundPlayback();
        super.onPause();
    }

    // The wallpaper belongs to the Activity window, not this fragment.
    // Do not stop or recreate it while navigating between launcher screens.
    private void stopEtoBackgroundPlayback() {
        // Intentionally persistent across fragment changes.
    }

    @Override public void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (data == null || data.getData() == null || (requestCode != ETO_PICK_IMAGE && requestCode != ETO_PICK_VIDEO)) return;
        Uri uri = data.getData();
        try { requireContext().getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION); } catch (Exception ignored) {}
        android.content.SharedPreferences.Editor e = requireContext().getSharedPreferences("eto_style", 0).edit();
        if (requestCode == ETO_PICK_IMAGE) e.putString("image", uri.toString()).remove("video");
        else if (requestCode == ETO_PICK_VIDEO) e.putString("video", uri.toString()).remove("image");

        e.apply();
        applyEtoCustomization(getView());

    }

    private void saveEtoBackground() {
        android.content.SharedPreferences p = requireContext().getSharedPreferences("eto_style", 0);
        String uri = p.getString("video", null);
        String type = "Video";
        if (uri == null) { uri = p.getString("image", null); type = "Image"; }
        if (uri == null) { Toast.makeText(requireContext(), "Choose a background first", Toast.LENGTH_SHORT).show(); return; }
        p.edit().putString("saved_bg_" + System.currentTimeMillis(), type + "|" + uri).apply();
        Toast.makeText(requireContext(), "Background saved", Toast.LENGTH_SHORT).show();
    }

    private void showSavedEtoBackgrounds() {
        android.content.SharedPreferences p = requireContext().getSharedPreferences("eto_style", 0);
        java.util.ArrayList<String> keys = new java.util.ArrayList<>();
        java.util.ArrayList<String> values = new java.util.ArrayList<>();
        for (String key : p.getAll().keySet()) if (key.startsWith("saved_bg_")) {
            String value = p.getString(key, "");
            if (value.contains("|")) { keys.add(key); values.add(value); }
        }
        if (keys.isEmpty()) { Toast.makeText(requireContext(), "No saved backgrounds yet", Toast.LENGTH_SHORT).show(); return; }
        android.widget.ScrollView scroll = new android.widget.ScrollView(requireContext());
        android.widget.LinearLayout list = new android.widget.LinearLayout(requireContext());
        list.setOrientation(android.widget.LinearLayout.VERTICAL); list.setPadding(12,8,12,8); scroll.addView(list);
        AlertDialog dialog = new AlertDialog.Builder(requireContext()).setTitle("Saved backgrounds").setView(scroll).setNegativeButton("Close", null).create();
        for (int i=0; i<keys.size(); i++) {
            final int index = i;
            String[] parts = values.get(i).split("\\|", 2);
            if (parts.length != 2) continue;
            android.widget.LinearLayout card = new android.widget.LinearLayout(requireContext());
            card.setOrientation(android.widget.LinearLayout.VERTICAL); card.setPadding(8,8,8,12); card.setBackgroundColor(Color.rgb(35,42,53));
            android.widget.ImageView preview = new android.widget.ImageView(requireContext());
            preview.setScaleType(android.widget.ImageView.ScaleType.CENTER_CROP);
            preview.setLayoutParams(new android.widget.LinearLayout.LayoutParams(-1, 150));
            try {
                if (parts[0].equals("Image")) {
                    android.graphics.Bitmap bitmap = android.graphics.BitmapFactory.decodeStream(requireContext().getContentResolver().openInputStream(Uri.parse(parts[1])));
                    if (bitmap != null) preview.setImageBitmap(bitmap);
                } else {
                    android.media.MediaMetadataRetriever retriever = new android.media.MediaMetadataRetriever();
                    retriever.setDataSource(requireContext(), Uri.parse(parts[1]));
                    android.graphics.Bitmap frame = retriever.getFrameAtTime(1000000);
                    if (frame != null) preview.setImageBitmap(frame);
                    retriever.release();
                }
            } catch (Exception ignored) {}
            card.addView(preview);
            android.widget.TextView label = new android.widget.TextView(requireContext());
            label.setText((parts[0].equals("Video") ? "Video background " : "Image background ") + (index+1));
            label.setTextColor(Color.WHITE); label.setTextSize(14); label.setPadding(8,8,8,4); card.addView(label);
            android.widget.Button use = new android.widget.Button(requireContext()); use.setText("Use this background");
            use.setOnClickListener(v -> {
                String[] selected = p.getString(keys.get(index), "").split("\\|", 2);
                if (selected.length != 2) return;
                p.edit().remove("image").remove("video").putString(selected[0].equals("Video") ? "video" : "image", selected[1]).apply();
                dialog.dismiss(); applyEtoCustomization(getView());
            });
            card.addView(use);
            android.widget.Button remove = new android.widget.Button(requireContext()); remove.setText("Remove from saved");
            remove.setOnClickListener(v -> { p.edit().remove(keys.get(index)).apply(); dialog.dismiss(); showSavedEtoBackgrounds(); });
            card.addView(remove);
            android.widget.LinearLayout.LayoutParams cp = new android.widget.LinearLayout.LayoutParams(-1,-2); cp.setMargins(0,0,0,12); list.addView(card,cp);
        }
        dialog.show();
    }

    private static VideoView etoPersistentBackgroundVideo;

    private void applyEtoCustomization(@Nullable View root) {
        if (root == null || !isAdded()) return;
        android.content.SharedPreferences prefs = requireContext().getSharedPreferences("eto_style", 0);
        tintEtoText(root, prefs.getInt("text", Color.rgb(242,245,249)));
        applyEtoLanguage(root);
        try {
            String image = prefs.getString("image", null);
            String video = prefs.getString("video", null);
            View decorView = requireActivity().getWindow().getDecorView();
            if (!(decorView instanceof ViewGroup)) return;
            ViewGroup wallpaperHost = (ViewGroup) decorView;
            View content = requireActivity().findViewById(android.R.id.content);
            if (content != null) content.setBackgroundColor(Color.TRANSPARENT);
            root.setBackgroundColor(Color.TRANSPARENT);

            if (video != null) {
                wallpaperHost.setBackgroundColor(Color.TRANSPARENT);
                VideoView player = wallpaperHost.findViewWithTag("eto-persistent-video");
                if (player == null) {
                    player = new VideoView(requireContext());
                    player.setTag("eto-persistent-video");
                    player.setClickable(false);
                    player.setFocusable(false);
                    player.setBackgroundColor(Color.TRANSPARENT);
                    android.widget.FrameLayout.LayoutParams lp =
                            new android.widget.FrameLayout.LayoutParams(-1, -1);
                    wallpaperHost.addView(player, 0, lp);
                }
                etoPersistentBackgroundVideo = player;
                final VideoView persistentPlayer = player;
                String activeUri = prefs.getString("active_video_uri", "");
                if (!video.equals(activeUri)) {
                    prefs.edit().putString("active_video_uri", video).apply();
                    persistentPlayer.setVideoURI(Uri.parse(video));
                    persistentPlayer.setOnPreparedListener(mp -> {
                        mp.setLooping(true);
                        etoBackgroundMediaPlayer = mp;
                        mp.setVolume(etoIntroAudioActive ? 0f : 1f, etoIntroAudioActive ? 0f : 1f);
                        persistentPlayer.start();
                    });
                    persistentPlayer.setOnErrorListener((mp, what, extra) -> true);
                } else if (!persistentPlayer.isPlaying()) {
                    // Resume only if Android stopped playback; do not seek to the beginning
                    // when a settings fragment is opened or closed.
                    try { persistentPlayer.start(); } catch (Exception ignored) {}
                }
                persistentPlayer.setVisibility(View.VISIBLE);
            } else {
                VideoView oldPlayer = wallpaperHost.findViewWithTag("eto-persistent-video");
                if (oldPlayer != null) {
                    try { oldPlayer.stopPlayback(); } catch (Exception ignored) {}
                    wallpaperHost.removeView(oldPlayer);
                }
                etoPersistentBackgroundVideo = null;
                etoBackgroundMediaPlayer = null;
                prefs.edit().remove("active_video_uri").apply();
                if (image != null) {
                    Drawable d = Drawable.createFromStream(
                            requireContext().getContentResolver().openInputStream(Uri.parse(image)), null);
                    if (d != null) {
                        d.setAlpha(255);
                        wallpaperHost.setBackground(d);
                    }
                } else {
                    wallpaperHost.setBackgroundColor(Color.rgb(12, 18, 27));
                }
            }
        } catch (Exception ex) {
            Toast.makeText(requireContext(), "Could not apply background", Toast.LENGTH_SHORT).show();
        }
    }

    private void showEtoSettings() {
        if (!isAdded()) return;
        android.widget.LinearLayout panel = new android.widget.LinearLayout(requireContext());
        panel.setOrientation(android.widget.LinearLayout.VERTICAL);
        panel.setPadding(22, 18, 22, 18);
        panel.setBackgroundColor(Color.rgb(17, 25, 36));

        android.widget.TextView heading = new android.widget.TextView(requireContext());
        heading.setText("INTERFACE LANGUAGE");
        heading.setTextColor(Color.rgb(143, 230, 192));
        heading.setTextSize(11);
        heading.setTypeface(null, android.graphics.Typeface.BOLD);
        heading.setLetterSpacing(0.12f);
        panel.addView(heading);

        android.widget.TextView description = new android.widget.TextView(requireContext());
        description.setText("Choose the language used by Eto Launcher menus.");
        description.setTextColor(Color.rgb(195, 207, 220));
        description.setTextSize(12);
        description.setPadding(0, 7, 0, 12);
        panel.addView(description);

        android.widget.RadioGroup languages = new android.widget.RadioGroup(requireContext());
        languages.setOrientation(android.widget.RadioGroup.VERTICAL);
        String[] names = {"English", "العربية", "Français"};
        String[] codes = {"en", "ar", "fr"};
        String selected = requireContext().getSharedPreferences("eto_style", 0).getString("language", "en");
        for (int i = 0; i < names.length; i++) {
            android.widget.RadioButton choice = new android.widget.RadioButton(requireContext());
            choice.setId(9100 + i);
            choice.setText(names[i]);
            choice.setTextColor(Color.WHITE);
            choice.setTextSize(14);
            choice.setButtonTintList(android.content.res.ColorStateList.valueOf(Color.rgb(143, 230, 192)));
            languages.addView(choice);
            if (codes[i].equals(selected)) choice.setChecked(true);
        }
        panel.addView(languages);

        android.widget.TextView section = new android.widget.TextView(requireContext());
        section.setText("PERSONALIZATION");
        section.setTextColor(Color.rgb(143, 230, 192));
        section.setTextSize(10);
        section.setTypeface(null, android.graphics.Typeface.BOLD);
        section.setPadding(0, 18, 0, 6);
        panel.addView(section);

        android.widget.Button appearance = makeEtoSettingsButton(
                selected.equals("ar") ? "تخصيص الخلفية والمظهر" :
                selected.equals("fr") ? "Personnaliser l’apparence" : "Customize appearance");
        panel.addView(appearance);

        AlertDialog dialog = new AlertDialog.Builder(requireContext())
                .setTitle(selected.equals("ar") ? "إعدادات Eto" : selected.equals("fr") ? "Paramètres Eto" : "Eto Settings")
                .setView(panel)
                .setNegativeButton(selected.equals("ar") ? "إغلاق" : selected.equals("fr") ? "Fermer" : "Close", null)
                .create();
        languages.setOnCheckedChangeListener((group, checkedId) -> {
            int index = checkedId - 9100;
            if (index < 0 || index >= codes.length) return;
            requireContext().getSharedPreferences("eto_style", 0).edit().putString("language", codes[index]).apply();
            applyEtoLanguage(getView());
            dialog.setTitle(codes[index].equals("ar") ? "إعدادات Eto" : codes[index].equals("fr") ? "Paramètres Eto" : "Eto Settings");
            description.setText(codes[index].equals("ar") ? "اختر لغة قوائم ومكونات Eto Launcher." :
                    codes[index].equals("fr") ? "Choisissez la langue de l’interface Eto Launcher." :
                    "Choose the language used by Eto Launcher menus.");
            appearance.setText(codes[index].equals("ar") ? "تخصيص الخلفية والمظهر" :
                    codes[index].equals("fr") ? "Personnaliser l’apparence" : "Customize appearance");
        });
        appearance.setOnClickListener(v -> {
            dialog.dismiss();
            showEtoCustomization();
        });
        dialog.show();
    }

    private android.widget.Button makeEtoSettingsButton(String text) {
        android.widget.Button button = new android.widget.Button(requireContext());
        button.setText(text);
        button.setTextColor(Color.WHITE);
        button.setTextSize(12);
        button.setAllCaps(false);
        button.setPadding(18, 4, 18, 4);
        android.graphics.drawable.GradientDrawable bg = new android.graphics.drawable.GradientDrawable();
        bg.setColor(Color.rgb(39, 57, 72));
        bg.setCornerRadius(18f);
        bg.setStroke(1, Color.rgb(70, 92, 110));
        button.setBackground(bg);
        return button;
    }

    private void applyEtoLanguage(@Nullable View root) {
        if (root == null || !isAdded()) return;
        String language = requireContext().getSharedPreferences("eto_style", 0).getString("language", "en");
        boolean ar = "ar".equals(language);
        boolean fr = "fr".equals(language);
        root.setLayoutDirection(ar ? View.LAYOUT_DIRECTION_RTL : View.LAYOUT_DIRECTION_LTR);
        setEtoLabel(root, R.id.eto_home_eyebrow, ar ? "مغامرتك القادمة" : fr ? "VOTRE PROCHAINE AVENTURE" : "YOUR NEXT ADVENTURE");
        setEtoLabel(root, R.id.eto_hero_title, ar ? "اجعل هذا\nالعالم عالمك." : fr ? "FAITES DE CE\nMONDE LE VÔTRE." : "MAKE THIS\nWORLD YOURS.");
        setEtoLabel(root, R.id.eto_hero_subtitle, ar ? "عوالم ماينكرافت وحساباتك وأدواتك في مكان واحد." : fr ? "Vos mondes Minecraft, profils et outils réunis au même endroit." : "Your Minecraft worlds, profiles and tools — together in one clean place.");
        setEtoLabel(root, R.id.customize_button, ar ? "المظهر" : fr ? "APPARENCE" : "APPEARANCE");
        setEtoLabel(root, R.id.skin_button, ar ? "استوديو السكن" : fr ? "SKIN STUDIO" : "SKIN STUDIO");
        setEtoLabel(root, R.id.eto_library_title, ar ? "مكتبة الألعاب" : fr ? "BIBLIOTHÈQUE" : "GAME LIBRARY");
        setEtoLabel(root, R.id.install_jar_button, ar ? "+ إضافة إصدار" : fr ? "+ AJOUTER UNE VERSION" : "+  ADD GAME VERSION");
        setEtoLabel(root, R.id.play_button, ar ? "العب الآن  ←" : fr ? "JOUER  →" : "PLAY  →");
        setEtoLabel(root, R.id.eto_live_label, ar ? "أخبار Eto" : fr ? "ETO EN DIRECT" : "ETO LIVE");
        setEtoLabel(root, R.id.eto_home_footer, ar ? "شبكة Eto  •  عالمك يبدأ هنا" : fr ? "ETO NETWORK  •  VOS MONDES" : "ETO NETWORK     •     BUILT FOR YOUR WORLDS");
        setEtoLabel(root, R.id.eto_update_button, ar ? "تحديث المحتوى" : fr ? "METTRE À JOUR" : "UPDATE CONTENT");
        ImageButton settings = root.findViewById(R.id.eto_settings_button);
        if (settings != null) settings.setContentDescription(ar ? "الإعدادات" : fr ? "Paramètres" : "Settings");
        ImageButton account = root.findViewById(R.id.edit_profile_button);
        if (account != null) account.setContentDescription(ar ? "الحساب" : fr ? "Compte" : "Account");
    }

    private void setEtoLabel(View root, int id, String value) {
        View target = root.findViewById(id);
        if (target instanceof TextView) ((TextView) target).setText(value);
    }

    private void tintEtoText(View v, int color) {
        if (v instanceof TextView) ((TextView)v).setTextColor(color);
        if (v instanceof ViewGroup) {
            ViewGroup g = (ViewGroup)v;
            for (int i=0; i<g.getChildCount(); i++) tintEtoText(g.getChildAt(i), color);
        }
    }
'''
if "ETO_PICK_IMAGE" not in s:
    pos = s.rfind("\n}")
    if pos < 0: raise SystemExit("MainMenuFragment closing brace missing")
    s = s[:pos] + "\n" + methods + s[pos:]
p.write_text(s, encoding="utf-8")
print("Eto background and text color customization patched.")


# Do not install a Choreographer-based FPS counter: it measures Android UI frames,
# not Minecraft render frames. A real game FPS meter needs renderer instrumentation.




# Keep Android system bars hidden on the launcher until the user swipes from an edge.
import re
activity = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/LauncherActivity.java")
a = activity.read_text(encoding="utf-8")
a, count = re.subn(r"(public\s+boolean\s+setFullscreen\s*\(\s*\)\s*\{)\s*return\s+false\s*;", r"\1\n        return true;", a, count=1)
if count == 0 and re.search(r"public\s+boolean\s+setFullscreen\s*\(\s*\)\s*\{\s*return\s+true\s*;", a) is None:
    raise SystemExit("Could not locate LauncherActivity.setFullscreen()")
activity.write_text(a, encoding="utf-8")
print("Enabled immersive launcher mode: status and navigation bars reveal on edge swipe.")
