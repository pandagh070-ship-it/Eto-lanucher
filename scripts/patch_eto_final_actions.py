from pathlib import Path

p = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/fragments/MainMenuFragment.java")
s = p.read_text(encoding="utf-8")

# Re-apply the visible launcher actions after Pojav's original listeners have
# been installed. This prevents an upstream/default listener from replacing
# an Eto action and keeps each visible control mapped to one purpose.
marker = "        mOpenDirectoryButton.setOnClickListener((v)-> openGameDirectory(v.getContext()));"
if "ETO_FINAL_VISIBLE_ACTION_MAP" not in s:
    if marker not in s:
        raise SystemExit("Could not find the end of the upstream launcher action bindings")
    block = marker + """
        // ETO_FINAL_VISIBLE_ACTION_MAP
        ImageButton etoVersionAction = view.findViewById(R.id.edit_version_button);
        ImageButton etoProfileAction = view.findViewById(R.id.edit_profile_button);
        ImageButton etoSettingsAction = view.findViewById(R.id.eto_settings_button);
        Button etoAppearanceAction = view.findViewById(R.id.customize_button);
        Button etoSkinAction = view.findViewById(R.id.skin_button);
        Button etoModsAction = view.findViewById(R.id.mods_button);

        etoVersionAction.setOnClickListener(v -> mVersionSpinner.performClick());
        etoVersionAction.setContentDescription("Choose Minecraft version");
        etoProfileAction.setOnClickListener(v -> mVersionSpinner.openProfileEditor(requireActivity()));
        etoProfileAction.setContentDescription("Edit Minecraft profile");
        etoSettingsAction.setOnClickListener(v -> showEtoSettings());
        etoSettingsAction.setContentDescription("Eto settings");
        etoAppearanceAction.setOnClickListener(v -> showEtoCustomization());
        etoAppearanceAction.setContentDescription("Appearance and backgrounds");
        etoSkinAction.setOnClickListener(v -> showEtoSkinPicker());
        etoSkinAction.setContentDescription("Skin studio");
        etoModsAction.setOnClickListener(v -> showEtoModsManager());
        etoModsAction.setContentDescription("Mods and shaders");
"""
    s = s.replace(marker, block, 1)

p.write_text(s, encoding="utf-8")
print("Rebound each visible Eto launcher control after upstream listeners, with one explicit action per button.")
