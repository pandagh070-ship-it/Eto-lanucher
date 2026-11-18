from pathlib import Path

p = Path("upstream/app_pojavlauncher/src/main/java/net/kdt/pojavlaunch/fragments/MainMenuFragment.java")
s = p.read_text(encoding="utf-8")

needle = "        mVersionSpinner = view.findViewById(R.id.mc_version_spinner);"
if "etoEditVersionButton.setOnClickListener" not in s:
    if needle not in s:
        raise SystemExit("Version spinner binding not found")
    s = s.replace(needle, needle + """
        android.widget.ImageButton etoEditVersionButton = view.findViewById(R.id.edit_version_button);
        etoEditVersionButton.setOnClickListener(v -> mVersionSpinner.performClick());
        etoEditVersionButton.setContentDescription("Choose Minecraft version");
        view.post(() -> applyEtoResponsiveLayout(view));
""", 1)

method = r'''
    private void applyEtoResponsiveLayout(View root) {
        if (root == null || !isAdded()) return;
        View areaView = root.findViewById(R.id.eto_news_area);
        if (!(areaView instanceof android.widget.LinearLayout)) return;
        android.widget.LinearLayout area = (android.widget.LinearLayout) areaView;
        if (area.getChildCount() < 2) return;

        android.view.ViewGroup first = (android.view.ViewGroup) area.getChildAt(0);
        android.view.ViewGroup second = (android.view.ViewGroup) area.getChildAt(1);
        int widthDp = getResources().getConfiguration().screenWidthDp;

        if (widthDp < 700) {
            area.setOrientation(android.widget.LinearLayout.VERTICAL);
            area.setPadding(16, 10, 16, 10);
            android.widget.LinearLayout.LayoutParams firstParams =
                    new android.widget.LinearLayout.LayoutParams(-1, 0, 1f);
            android.widget.LinearLayout.LayoutParams secondParams =
                    new android.widget.LinearLayout.LayoutParams(-1, -2);
            secondParams.topMargin = 8;
            first.setLayoutParams(firstParams);
            second.setLayoutParams(secondParams);
            first.setPadding(0, 4, 0, 8);
            second.setPadding(0, 0, 0, 0);
            View hero = first.findViewById(R.id.eto_hero_title);
            if (hero instanceof android.widget.TextView) ((android.widget.TextView) hero).setTextSize(27);
        } else {
            area.setOrientation(android.widget.LinearLayout.HORIZONTAL);
            area.setPadding(22, 22, 22, 22);
            first.setLayoutParams(new android.widget.LinearLayout.LayoutParams(0, -1, 1f));
            second.setLayoutParams(new android.widget.LinearLayout.LayoutParams(
                    (int) (250 * getResources().getDisplayMetrics().density), -1));
            first.setPadding(0, 0, 18, 0);
        }
        area.requestLayout();
    }

'''
if "private void applyEtoResponsiveLayout(View root)" not in s:
    pos=s.rfind("\n}")
    if pos<0: raise SystemExit("MainMenuFragment closing brace missing")
    s=s[:pos]+"\n"+method+s[pos:]

p.write_text(s,encoding="utf-8")
print("Connected the version selector and added responsive launcher layout.")
