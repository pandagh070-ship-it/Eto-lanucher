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
        View etoSettings = view.findViewById(R.id.eto_settings_button);
        if (etoSettings != null) etoSettings.setOnClickListener(v -> { View oldSettings = requireActivity().findViewById(R.id.setting_button); if (oldSettings != null) oldSettings.performClick(); });
        View etoAccount = view.findViewById(R.id.edit_profile_button);
        if (etoAccount != null) etoAccount.setOnClickListener(v -> { View account = requireActivity().findViewById(R.id.account_spinner); if (account != null) account.performClick(); });
        applyEtoCustomization(view);
""", 1)

methods = r'''
    private static final int ETO_PICK_IMAGE = 8301;
    private static final int ETO_PICK_VIDEO = 8302;\n    private static final int ETO_PICK_MUSIC = 8303;\n    private android.media.MediaPlayer etoMusicPlayer;

    private void showEtoCustomization() {
        new AlertDialog.Builder(requireContext()).setTitle("Eto customization")
            .setItems(new String[]{"Choose image background", "Choose video background", "Choose background music", "Save current background", "Use saved background", "Text color: dark", "Text color: white", "Text color: green", "Reset customization"}, (d, which) -> {
                if (which < 3) {
                    Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType(which == 0 ? "image/*" : which == 1 ? "video/*" : "audio/*");
                    startActivityForResult(i, which == 0 ? ETO_PICK_IMAGE : which == 1 ? ETO_PICK_VIDEO : ETO_PICK_MUSIC);
                } else if (which == 3) {
                    saveEtoBackground();
                } else if (which == 4) {
                    showSavedEtoBackgrounds();
                } else if (which < 8) {
                    int[] colors = {Color.rgb(24,33,43), Color.WHITE, Color.rgb(21,148,90)};
                    requireContext().getSharedPreferences("eto_style", 0).edit().putInt("text", colors[which-5]).apply();
                    applyEtoCustomization(getView());
                } else {
                    requireContext().getSharedPreferences("eto_style", 0).edit().clear().apply();
                    applyEtoCustomization(getView());
                }
            }).show();
    }

    @Override public void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (data == null || data.getData() == null || (requestCode != ETO_PICK_IMAGE && requestCode != ETO_PICK_VIDEO && requestCode != ETO_PICK_MUSIC)) return;
        Uri uri = data.getData();
        try { requireContext().getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION); } catch (Exception ignored) {}
        android.content.SharedPreferences.Editor e = requireContext().getSharedPreferences("eto_style", 0).edit();
        if (requestCode == ETO_PICK_IMAGE) e.putString("image", uri.toString()).remove("video");
        else if (requestCode == ETO_PICK_VIDEO) e.putString("video", uri.toString()).remove("image");
        else e.putString("music", uri.toString());
        e.apply();
        applyEtoCustomization(getView());
        if (requestCode == ETO_PICK_VIDEO || requestCode == ETO_PICK_MUSIC) startEtoMusicIfAvailable();
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
        java.util.ArrayList<String> labels = new java.util.ArrayList<>();
        for (String key : p.getAll().keySet()) if (key.startsWith("saved_bg_")) {
            String value = p.getString(key, "");
            keys.add(key);
            labels.add((value.startsWith("Video|") ? "Video background " : "Image background ") + keys.size());
        }
        if (keys.isEmpty()) { Toast.makeText(requireContext(), "No saved backgrounds yet", Toast.LENGTH_SHORT).show(); return; }
        new AlertDialog.Builder(requireContext()).setTitle("Saved backgrounds").setItems(labels.toArray(new String[0]), (dialog, index) -> {
            String[] parts = p.getString(keys.get(index), "").split("\\|", 2);
            if (parts.length != 2) return;
            android.content.SharedPreferences.Editor e = p.edit().remove("image").remove("video");
            e.putString(parts[0].equals("Video") ? "video" : "image", parts[1]).apply();
            applyEtoCustomization(getView());
            if (parts[0].equals("Video")) startEtoMusicIfAvailable();
        }).show();
    }

    private void startEtoMusicIfAvailable() {
        String music = requireContext().getSharedPreferences("eto_style", 0).getString("music", null);
        if (music == null) return;
        stopEtoMusic();
        try {
            etoMusicPlayer = new android.media.MediaPlayer();
            etoMusicPlayer.setDataSource(requireContext(), Uri.parse(music));
            etoMusicPlayer.setLooping(true);
            etoMusicPlayer.setVolume(0.7f, 0.7f);
            etoMusicPlayer.setOnPreparedListener(android.media.MediaPlayer::start);
            etoMusicPlayer.prepareAsync();
        } catch (Exception ex) { stopEtoMusic(); }
    }

    private void stopEtoMusic() {
        if (etoMusicPlayer != null) {
            try { etoMusicPlayer.stop(); } catch (Exception ignored) {}
            try { etoMusicPlayer.release(); } catch (Exception ignored) {}
            etoMusicPlayer = null;
        }
    }

    @Override public void onStop() {
        stopEtoMusic();
        super.onStop();
    }

    private void applyEtoCustomization(@Nullable View root) {
        if (root == null || !isAdded()) return;
        android.content.SharedPreferences prefs = requireContext().getSharedPreferences("eto_style", 0);
        tintEtoText(root, prefs.getInt("text", Color.rgb(242,245,249)));
        try {
            String image = prefs.getString("image", null), video = prefs.getString("video", null);
            View sidebar = root.findViewById(R.id.eto_sidebar);
            if (video != null && root instanceof ViewGroup) {
                root.setBackgroundColor(Color.TRANSPARENT);
                if (sidebar != null) sidebar.setBackgroundColor(Color.TRANSPARENT);
                VideoView vv = root.findViewWithTag("eto-video");
                if (vv == null) {
                    vv = new VideoView(requireContext());
                    vv.setTag("eto-video");
                    vv.setAlpha(1.0f);
                    androidx.constraintlayout.widget.ConstraintLayout.LayoutParams lp = new androidx.constraintlayout.widget.ConstraintLayout.LayoutParams(-1, -1);
                    lp.startToStart = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
                    lp.endToEnd = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
                    lp.topToTop = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
                    lp.bottomToBottom = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
                    vv.setClickable(false);
                    vv.setFocusable(false);
                    ((ViewGroup)root).addView(vv, 0, lp);
                }
                final VideoView player = vv;
                player.setVideoURI(Uri.parse(video));
                player.setOnPreparedListener(mp -> { mp.setLooping(true); mp.setVolume(0f,0f); player.start(); });
                player.setVisibility(View.VISIBLE);
                View panel = root.findViewById(R.id.eto_news_area);
                if (panel != null) panel.setBackgroundColor(Color.TRANSPARENT);
                makeEtoPanelsTransparent(root);
            } else {
                VideoView vv = root.findViewWithTag("eto-video");
                if (vv != null) vv.setVisibility(View.GONE);
                if (image != null) {
                    Drawable d = Drawable.createFromStream(requireContext().getContentResolver().openInputStream(Uri.parse(image)), null);
                    if (d != null) {
                        d.setAlpha(255);
                        root.setBackground(d);
                        View panel = root.findViewById(R.id.eto_news_area);
                        if (panel != null) panel.setBackgroundColor(Color.TRANSPARENT);
                makeEtoPanelsTransparent(root);
                        if (sidebar != null) sidebar.setBackgroundColor(Color.TRANSPARENT);
                    }
                } else {
                    root.setBackgroundColor(Color.rgb(18,22,28));
                    View panel = root.findViewById(R.id.eto_news_area);
                    if (panel != null) panel.setBackgroundColor(Color.rgb(27,34,44));
                    if (sidebar != null) sidebar.setBackgroundColor(Color.rgb(27,34,44));
                }
            }
        } catch (Exception ex) {
            Toast.makeText(requireContext(), "Could not apply background", Toast.LENGTH_SHORT).show();
        }
    }

    private void makeEtoPanelsTransparent(View v) {
        if (v instanceof ViewGroup) {
            ViewGroup g = (ViewGroup)v;
            for (int i=0; i<g.getChildCount(); i++) {
                View child = g.getChildAt(i);
                if (child instanceof android.widget.LinearLayout) child.setBackgroundColor(Color.TRANSPARENT);
                if (child instanceof ViewGroup) makeEtoPanelsTransparent(child);
            }
        }
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


# Add a lightweight in-game FPS estimate overlay to the game activity.
game = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/game/GameActivity.java")
g = game.read_text(encoding="utf-8")
for imp in [
    "import android.view.Choreographer;",
    "import android.view.Gravity;",
    "import android.widget.FrameLayout;"
]:
    if imp not in g:
        g = g.replace("import android.view.View;", "import android.view.View;\n" + imp, 1)
if "installEtoFpsCounter();" not in g:
    anchor = "        initLayout(R.layout.activity_basemain);"
    if anchor not in g:
        raise SystemExit("GameActivity layout insertion point missing")
    g = g.replace(anchor, anchor + "\n        installEtoFpsCounter();", 1)
if "private void installEtoFpsCounter()" not in g:
    methods = r'''
    private void installEtoFpsCounter() {
        final FrameLayout overlay = (FrameLayout) getWindow().getDecorView().findViewById(android.R.id.content);
        if (overlay == null) return;
        final TextView fps = new TextView(this);
        fps.setText("FPS: --");
        fps.setTextColor(Color.WHITE);
        fps.setTextSize(12f);
        fps.setTypeface(android.graphics.Typeface.MONOSPACE, android.graphics.Typeface.BOLD);
        fps.setPadding(10, 5, 10, 5);
        android.graphics.drawable.GradientDrawable bg = new android.graphics.drawable.GradientDrawable();
        bg.setColor(0x990D1117);
        bg.setCornerRadius(10f);
        fps.setBackground(bg);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT,
            Gravity.TOP | Gravity.END);
        lp.topMargin = 12;
        lp.rightMargin = 12;
        overlay.addView(fps, lp);
        final int[] frames = {0};
        final long[] start = {System.nanoTime()};
        final Choreographer choreographer = Choreographer.getInstance();
        final Choreographer.FrameCallback[] callback = new Choreographer.FrameCallback[1];
        callback[0] = frameTimeNanos -> {
            if (isFinishing() || isDestroyed()) {
                overlay.removeView(fps);
                return;
            }
            frames[0]++;
            long now = System.nanoTime();
            long elapsed = now - start[0];
            if (elapsed >= 1_000_000_000L) {
                int rate = Math.round(frames[0] * 1_000_000_000f / elapsed);
                fps.setText("FPS: " + rate);
                frames[0] = 0;
                start[0] = now;
            }
            choreographer.postFrameCallback(callback[0]);
        };
        choreographer.postFrameCallback(callback[0]);
    }
'''
    pos = g.rfind("\n}")
    if pos < 0:
        raise SystemExit("GameActivity closing brace missing")
    g = g[:pos] + "\n" + methods + g[pos:]
game.write_text(g, encoding="utf-8")
print("Added a lightweight in-game frame-rate overlay.")
