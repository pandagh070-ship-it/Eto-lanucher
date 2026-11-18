from pathlib import Path

p = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/fragments/MainMenuFragment.java")
s = p.read_text(encoding="utf-8")

for old, new in [
    ("import android.view.View;", "import android.view.View;\nimport android.view.ViewGroup;"),
    ("import android.content.Intent;", "import android.content.Intent;\nimport android.net.Uri;"),
    ("import android.widget.VideoView;", "import android.widget.VideoView;"),
]:
    if old in s and new not in s:
        s = s.replace(old, new, 1)

needle = "        mVersionSpinner = view.findViewById(R.id.mc_version_spinner);"
if "startEtoIntroTrailer(view);" not in s:
    apply_anchor = "        applyEtoCustomization(view);"
    if apply_anchor in s:
        s = s.replace(apply_anchor, apply_anchor + "\n        startEtoIntroTrailer(view);", 1)
    elif needle in s:
        s = s.replace(needle, needle + "\n        startEtoIntroTrailer(view);", 1)
    else:
        raise SystemExit("Eto intro insertion point missing")

methods = r"""
    // Plays the bundled Eto trailer behind the launcher UI on every fresh menu creation.
    private VideoView etoIntroPlayer;
    private static boolean etoIntroPlayed = false;

    private void startEtoIntroTrailer(View root) {
        if (!(root instanceof ViewGroup) || !isAdded() || etoIntroPlayed) return;
        ViewGroup group = (ViewGroup) root;
        // Keep the root transparent so its SurfaceView can actually be seen.
        root.setBackgroundColor(android.graphics.Color.TRANSPARENT);
        View contentPanel = root.findViewById(R.id.eto_news_area);
        if (contentPanel != null) contentPanel.setBackgroundColor(0x00101820);
        if (etoIntroPlayer != null) {
            try { etoIntroPlayer.stopPlayback(); } catch (Exception ignored) {}
        }
        VideoView player = new VideoView(requireContext());
        etoIntroPlayer = player;
        player.setTag("eto-intro-trailer");
        player.setClickable(false);
        player.setFocusable(false);
        player.setBackgroundColor(android.graphics.Color.TRANSPARENT);
        androidx.constraintlayout.widget.ConstraintLayout.LayoutParams lp =
                new androidx.constraintlayout.widget.ConstraintLayout.LayoutParams(-1, -1);
        lp.startToStart = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
        lp.endToEnd = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
        lp.topToTop = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
        lp.bottomToBottom = androidx.constraintlayout.widget.ConstraintLayout.LayoutParams.PARENT_ID;
        group.addView(player, 0, lp);

        java.util.ArrayList<View> menuViews = new java.util.ArrayList<>();
        for (int i = 1; i < group.getChildCount(); i++) {
            View child = group.getChildAt(i);
            // Keep the user's selected background video visible beneath the intro.
            if ("eto-video".equals(child.getTag())) continue;
            menuViews.add(child);
            child.setAlpha(0f);
            child.setVisibility(View.INVISIBLE);
        }
        Uri trailer = Uri.parse("android.resource://" + requireContext().getPackageName() + "/" + R.raw.eto_intro);
        player.setVideoURI(trailer);
        player.setOnPreparedListener(mp -> {
            etoIntroPlayed = true;
            mp.setLooping(false);
            mp.setVolume(0.85f, 0.85f);
            if (etoBackgroundMediaPlayer != null) {
                try { etoBackgroundMediaPlayer.setVolume(0f, 0f); } catch (Exception ignored) {}
            }
            player.start();
            player.postDelayed(() -> {
                if (!isAdded() || getView() != root) return;
                for (View child : menuViews) {
                    child.setVisibility(View.VISIBLE);
                    child.animate().alpha(1f).setDuration(650).start();
                }
            }, 8000L);
        });
        player.setOnCompletionListener(mp -> {
            if (etoBackgroundMediaPlayer != null) {
                try { etoBackgroundMediaPlayer.setVolume(1f, 1f); } catch (Exception ignored) {}
            }
            player.setVisibility(View.GONE);
        });
        player.setOnErrorListener((mp, what, extra) -> {
            if (etoBackgroundMediaPlayer != null) {
                try { etoBackgroundMediaPlayer.setVolume(1f, 1f); } catch (Exception ignored) {}
            }
            for (View child : menuViews) {
                child.setVisibility(View.VISIBLE);
                child.setAlpha(1f);
            }
            return true;
        });
    }

    private void stopEtoIntroPlayback() {
        if (etoIntroPlayer != null) {
            try { etoIntroPlayer.stopPlayback(); } catch (Exception ignored) {}
            etoIntroPlayer = null;
        }
        if (etoBackgroundMediaPlayer != null) {
            try { etoBackgroundMediaPlayer.setVolume(1f, 1f); } catch (Exception ignored) {}
        }
    }

"""
if "private void startEtoIntroTrailer(View root)" not in s:
    pos = s.rfind("\n}")
    if pos < 0: raise SystemExit("MainMenuFragment closing brace missing")
    s = s[:pos] + "\n" + methods + s[pos:]

# Keep intro audio/video from continuing while the launcher is not visible.
marker = "        stopEtoBackgroundPlayback();"
if marker in s and "stopEtoIntroPlayback();" not in s:
    s = s.replace(marker, marker + "\n        stopEtoIntroPlayback();", 1)

p.write_text(s, encoding="utf-8")
print("Added Eto intro trailer with 8-second opening, isolated intro audio, and background audio restored after the intro ends.")
