from pathlib import Path

p = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/fragments/MainMenuFragment.java")
s = p.read_text(encoding="utf-8")

# Mute/hide the wallpaper as soon as the intro starts, including while it buffers.
intro_anchor = "        ViewGroup group = (ViewGroup) root;"
intro_replacement = """        ViewGroup group = (ViewGroup) root;
        etoIntroAudioActive = true;
        if (etoPersistentBackgroundVideo != null) {
            try {
                etoPersistentBackgroundVideo.pause();
                etoPersistentBackgroundVideo.setVisibility(View.GONE);
            } catch (Exception ignored) {}
        }
        if (etoBackgroundMediaPlayer != null) {
            try { etoBackgroundMediaPlayer.setVolume(0f, 0f); } catch (Exception ignored) {}
        }"""
if intro_anchor in s and "etoIntroAudioActive = true;\\n        if (etoPersistentBackgroundVideo != null)" not in s:
    s = s.replace(intro_anchor, intro_replacement, 1)

# The top-right account icon must open the real account selector. The edit icon
# beside it must open the selected Minecraft instance/profile editor.
old_account = 'etoProfileAction.setOnClickListener(v -> mVersionSpinner.openProfileEditor(requireActivity()));'
new_account = '''etoProfileAction.setOnClickListener(v -> {
            com.kdt.mcgui.AccountSpinner accounts = requireActivity().findViewById(R.id.account_spinner);
            if (accounts != null) accounts.performClick();
            else Toast.makeText(requireContext(), "Account selector is unavailable", Toast.LENGTH_SHORT).show();
        });'''
if old_account in s:
    s = s.replace(old_account, new_account, 1)
elif new_account not in s:
    raise SystemExit("Could not find Eto account button action to correct")

old_version = 'etoVersionAction.setOnClickListener(v -> mVersionSpinner.performClick());'
new_version = 'etoVersionAction.setOnClickListener(v -> mVersionSpinner.openProfileEditor(requireActivity()));'
if old_version in s:
    s = s.replace(old_version, new_version, 1)
elif new_version not in s:
    raise SystemExit("Could not find Eto version button action to correct")

s = s.replace('etoProfileAction.setContentDescription("Edit Minecraft profile");',
              'etoProfileAction.setContentDescription("Accounts");')
s = s.replace('etoVersionAction.setContentDescription("Choose Minecraft version");',
              'etoVersionAction.setContentDescription("Edit Minecraft version");')

# Pre-fill Skin Studio with the active account name instead of requiring the
# player to type it again. Keep a manual editable field for guest profiles.
old_skin_prefill = 'username.setText(requireContext().getSharedPreferences("eto_style", 0).getString("skin_username", ""));'
new_skin_prefill = '''String savedSkinName = requireContext().getSharedPreferences("eto_style", 0).getString("skin_username", "");
        if (savedSkinName.isEmpty()) {
            net.kdt.pojavlaunch.authenticator.accounts.Account current = net.kdt.pojavlaunch.authenticator.accounts.Accounts.getCurrent();
            if (current != null && current.username != null) savedSkinName = current.username;
        }
        username.setText(savedSkinName);'''
if old_skin_prefill in s:
    s = s.replace(old_skin_prefill, new_skin_prefill, 1)

# Render the selected skin's face as crisp enlarged pixel art in the launcher.
old_avatar = '''avatar.setImageBitmap(face);
            avatar.setScaleType(ImageButton.ScaleType.CENTER_CROP);
            avatar.setPadding(8, 8, 8, 8);'''
new_avatar = '''Bitmap crispFace = Bitmap.createScaledBitmap(face, 128, 128, false);
            if (crispFace != face) face.recycle();
            avatar.setImageBitmap(crispFace);
            avatar.setScaleType(ImageButton.ScaleType.FIT_CENTER);
            avatar.setPadding(4, 4, 4, 4);
            avatar.setBackgroundColor(android.graphics.Color.TRANSPARENT);'''
if old_avatar in s:
    s = s.replace(old_avatar, new_avatar, 1)

# Do not allow the selected wallpaper video to render or play under the intro
# trailer. Restore it only after the intro has completed or failed.
old_intro_prepared = '''            player.start();
            player.postDelayed(() -> {'''
new_intro_prepared = '''            if (etoPersistentBackgroundVideo != null) {
                try {
                    etoPersistentBackgroundVideo.pause();
                    etoPersistentBackgroundVideo.setVisibility(View.GONE);
                } catch (Exception ignored) {}
            }
            if (etoBackgroundMediaPlayer != null) {
                try { etoBackgroundMediaPlayer.setVolume(0f, 0f); } catch (Exception ignored) {}
            }
            player.start();
            player.postDelayed(() -> {'''
if old_intro_prepared in s:
    s = s.replace(old_intro_prepared, new_intro_prepared, 1)
elif "etoPersistentBackgroundVideo.pause();" not in s:
    raise SystemExit("Could not find intro prepared callback")

old_completion = '''            player.setVisibility(View.GONE);
        });
        player.setOnErrorListener'''
new_completion = '''            player.setVisibility(View.GONE);
            restoreEtoSelectedBackgroundVideo();
        });
        player.setOnErrorListener'''
if old_completion in s:
    s = s.replace(old_completion, new_completion, 1)

old_error_end = '''            for (View child : menuViews) {
                child.setVisibility(View.VISIBLE);
                child.setAlpha(1f);
            }
            return true;
        });'''
new_error_end = '''            for (View child : menuViews) {
                child.setVisibility(View.VISIBLE);
                child.setAlpha(1f);
            }
            restoreEtoSelectedBackgroundVideo();
            return true;
        });'''
if old_error_end in s:
    s = s.replace(old_error_end, new_error_end, 1)

restore_method = r'''
    private void restoreEtoSelectedBackgroundVideo() {
        if (!isAdded() || etoPersistentBackgroundVideo == null) return;
        try {
            etoPersistentBackgroundVideo.setVisibility(View.VISIBLE);
            if (etoBackgroundMediaPlayer != null) etoBackgroundMediaPlayer.setVolume(1f, 1f);
            if (!etoPersistentBackgroundVideo.isPlaying()) etoPersistentBackgroundVideo.start();
        } catch (Exception ignored) {}
    }

'''
if "private void restoreEtoSelectedBackgroundVideo()" not in s:
    pos = s.rfind("\n}")
    if pos < 0:
        raise SystemExit("MainMenuFragment closing brace missing for media restore")
    s = s[:pos] + "\n" + restore_method + s[pos:]

# If the user changes the wallpaper while the intro is still playing, keep the
# new wallpaper hidden and muted until the intro's completion callback.
old_wallpaper_prepared = '''                        mp.setVolume(etoIntroAudioActive ? 0f : 1f, etoIntroAudioActive ? 0f : 1f);
                        persistentPlayer.start();'''
new_wallpaper_prepared = '''                        mp.setVolume(etoIntroAudioActive ? 0f : 1f, etoIntroAudioActive ? 0f : 1f);
                        if (etoIntroAudioActive) {
                            persistentPlayer.setVisibility(View.GONE);
                        } else {
                            persistentPlayer.setVisibility(View.VISIBLE);
                            persistentPlayer.start();
                        }'''
if old_wallpaper_prepared in s:
    s = s.replace(old_wallpaper_prepared, new_wallpaper_prepared, 1)
elif "if (etoIntroAudioActive) {" not in s:
    raise SystemExit("Could not find wallpaper video prepared callback")

p.write_text(s, encoding="utf-8")
print("Corrected account/version actions, improved skin avatar rendering, and serialized intro/wallpaper video playback.")
