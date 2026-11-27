# Bewitching Sinners Thai mod - language button. Installed by ThaiMod/install.bat, removed by uninstall.bat.
#
# This file lives in game/ (not game/tl/thai) on purpose: the game sets config.defer_tl_scripts,
# so tl/thai is only loaded once Thai is the active language. A button defined there would never
# appear for a player who starts in English. Language("thai") loads tl/thai when clicked.

init 1 python:
    if "thai_language_button" not in config.always_shown_screens:
        config.always_shown_screens.append("thai_language_button")

screen thai_language_button():
    zorder 200
    if renpy.get_screen("preferences"):
        vbox:
            style_prefix "check"
            pos (1157, 391)
            textbutton "{font=tl/thai/fonts/ChakraPetch-Bold.ttf}ไทย{/font}" action Language("thai")
