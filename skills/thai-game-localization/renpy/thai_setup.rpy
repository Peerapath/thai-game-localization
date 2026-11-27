## Thai language setup: fonts (Chakra Petch, SIL OFL 1.1) for Thai codepoints,
## original game fonts for everything else.
##
## Note: store names created here do not survive Ren'Py's "clean stores" step (return to the
## main menu, new game). So everything the "translate thai python" block needs is either built
## inline there or kept in config (which is never cleaned).

## Screens that hard-code a font (messenger: NotoSansSC; shop/quest: GradoGradoo; Ren'Py's own
## screens: DejaVuSans) get a Thai fallback. Latin text keeps the original font, so English and
## Chinese look unchanged. Groups are built before the name is mapped, so a group can still
## name the real file.
init 1 python:
    def thaimod_group(thai_font, base_font):
        return (FontGroup()
            .add(thai_font, 0x0E00, 0x0E7F)
            .add(thai_font, 0x200B, 0x200D)
            .add(thai_font, 0x00A0, 0x00A0)
            .add(base_font, None, None))

    for _f, _t in (("GradoGradooNF.ttf", "Bold"), ("NotoSansSC-Regular.ttf", "Medium"),
                   ("DejaVuSans.ttf", "Regular"), ("DejaVuSans-Bold.ttf", "Bold")):
        if not isinstance(config.font_name_map.get(_f), FontGroup):
            config.font_name_map[_f] = thaimod_group("tl/thai/fonts/ChakraPetch-%s.ttf" % _t, _f)

## "Quill" is both a character and a gift item (a quill pen). The string table keeps the item
## meaning, and the speaker's own name is switched here. The callback lives in config lists.
init 1 python:
    def thaimod_speaker_names(*args):
        renpy.store.quil.name = "ควิล" if renpy.store._preferences.language == "thai" else "Quill"

    if not any(getattr(f, "__name__", "") == "thaimod_speaker_names" for f in config.change_language_callbacks):
        config.change_language_callbacks.append(thaimod_speaker_names)
        for _l in (None, "thai", "chinese"):
            config.language_callbacks[_l].append(thaimod_speaker_names)

translate thai python:
    # Fonts for the Thai language: Thai codepoints from Chakra Petch, the rest from the game's fonts.
    gui.text_font = (FontGroup()
        .add("tl/thai/fonts/ChakraPetch-Medium.ttf", 0x0E00, 0x0E7F)
        .add("tl/thai/fonts/ChakraPetch-Medium.ttf", 0x200B, 0x200D)
        .add("tl/thai/fonts/ChakraPetch-Medium.ttf", 0x00A0, 0x00A0)
        .add("Semplicita Medium.otf", None, None))
    gui.name_text_font = config.font_name_map["GradoGradooNF.ttf"]
    gui.interface_text_font = gui.name_text_font
    gui.button_text_font = gui.interface_text_font
    gui.choice_button_text_font = gui.text_font

## Messenger: msg() builds a Message that the phone screen shows later, sometimes cut short by the
## typewriter effect or with "1. " in front of choices, so the string table can't match it.
## Translate the text and the choice names when the Message is created. This patches the class
## (shared, never saved, untouched by store cleaning) instead of rebinding a store name, which
## would be lost on return to the main menu and could end up pickled into save files.
init 1 python:
    def thaimod_patch_message(cls):
        orig = cls.__init__

        def __init__(self, what, who, choices, *args, **kwargs):
            if renpy.store._preferences.language == "thai":
                if what:
                    what = renpy.translate_string(what)
                if choices:
                    choices = dict((k, dict(v, name=renpy.translate_string(v["name"])) if isinstance(v, dict) and "name" in v else v)
                                   for k, v in choices.items())
            orig(self, what, who, choices, *args, **kwargs)

        cls.__init__ = __init__
        cls.thaimod = True

    if not getattr(Message, "thaimod", False):
        thaimod_patch_message(Message)

## The "ไทย" button in Preferences is NOT here: tl/thai is only loaded once Thai is active
## (config.defer_tl_scripts), so it lives in game/thaimod_language_button.rpy instead.
