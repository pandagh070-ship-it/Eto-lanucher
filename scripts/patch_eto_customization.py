from pathlib import Path

p = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/fragments/MainMenuFragment.java")
s = p.read_text(encoding="utf-8")
imports = [
    ("import android.content.Intent;", "import android.content.Intent;\nimport android.net.Uri;"),
    ("import android.view.View;", "import android.view.View;\nimport android.view.ViewGroup;"),
    ("import android.widget.Toast;", "import android.widget.Toast;\nimport android.widget.TextView;\nimport android.widget.VideoView;"),
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
        applyEtoCustomization(view);
""", 1)

methods = r'''
    private static final int ETO_PICK_IMAGE = 8301;
    private static final int ETO_PICK_VIDEO = 8302;

    private void showEtoCustomization() {
        new AlertDialog.Builder(requireContext()).setTitle("Eto customization")
            .setItems(new String[]{"Choose image background", "Choose video background", "Text color: dark", "Text color: white", "Text color: green", "Reset customization"}, (d, which) -> {
                if (which < 2) {
                    Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType(which == 0 ? "image/*" : "video/*");
                    startActivityForResult(i, which == 0 ? ETO_PICK_IMAGE : ETO_PICK_VIDEO);
                } else if (which < 5) {
                    int[] colors = {Color.rgb(24,33,43), Color.WHITE, Color.rgb(21,148,90)};
                    requireContext().getSharedPreferences("eto_style", 0).edit().putInt("text", colors[which-2]).apply();
                    applyEtoCustomization(getView());
                } else {
                    requireContext().getSharedPreferences("eto_style", 0).edit().clear().apply();
                    applyEtoCustomization(getView());
                }
            }).show();
    }

    @Override public void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (data == null || data.getData() == null || (requestCode != ETO_PICK_IMAGE && requestCode != ETO_PICK_VIDEO)) return;
        Uri uri = data.getData();
        try { requireContext().getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION); } catch (Exception ignored) {}
        android.content.SharedPreferences.Editor e = requireContext().getSharedPreferences("eto_style", 0).edit();
        if (requestCode == ETO_PICK_IMAGE) e.putString("image", uri.toString()).remove("video");
        else e.putString("video", uri.toString()).remove("image");
        e.apply();
        applyEtoCustomization(getView());
    }

    private void applyEtoCustomization(@Nullable View root) {
        if (root == null || !isAdded()) return;
        android.content.SharedPreferences prefs = requireContext().getSharedPreferences("eto_style", 0);
        tintEtoText(root, prefs.getInt("text", Color.rgb(24,33,43)));
        try {
            String image = prefs.getString("image", null), video = prefs.getString("video", null);
            if (video != null && root instanceof ViewGroup) {
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
            } else {
                VideoView vv = root.findViewWithTag("eto-video");
                if (vv != null) vv.setVisibility(View.GONE);
                if (image != null) {
                    Drawable d = Drawable.createFromStream(requireContext().getContentResolver().openInputStream(Uri.parse(image)), null);
                    root.setBackground(d);
                    View panel = root.findViewById(R.id.eto_news_area);
                    if (panel != null) panel.setBackground(d);
                } else {
                    root.setBackgroundColor(Color.rgb(244,246,248));
                    View panel = root.findViewById(R.id.eto_news_area);
                    if (panel != null) panel.setBackgroundColor(Color.rgb(244,246,248));
                }
            }
        } catch (Exception ex) {
            Toast.makeText(requireContext(), "Could not apply background", Toast.LENGTH_SHORT).show();
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
