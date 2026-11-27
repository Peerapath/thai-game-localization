# TEMPORARY test harness for a Ren'Py translation. Copy to game/zz_thai_spike.rpy while testing,
# delete before release. Does nothing unless the THAI_SPIKE environment variable is set.
# Labels such as cewe/piko and characters quil/red are from Bewitching Sinners: replace them.
init python:
    import os
    THAI_SPIKE = os.environ.get("THAI_SPIKE")
    THAI_SPIKE_LABEL = os.environ.get("THAI_SPIKE_LABEL")
    THAI_SPIKE_N = int(os.environ.get("THAI_SPIKE_N", "6"))
    THAI_SPIKE_EVERY = float(os.environ.get("THAI_SPIKE_EVERY", "2.5"))
    _spike_state = {"t": None, "n": 0}

    def _spike_periodic():
        import time
        if not THAI_SPIKE or not THAI_SPIKE_LABEL:
            return
        now = time.time()
        if _spike_state["t"] is None:
            _spike_state["t"] = now + 4.0
            return
        if now >= _spike_state["t"]:
            _spike_state["t"] = now + THAI_SPIKE_EVERY
            _spike_state["n"] += 1
            renpy.screenshot(THAI_SPIKE.replace(".png", "_%02d.png" % _spike_state["n"]))
            if _spike_state["n"] >= THAI_SPIKE_N:
                renpy.quit()

    config.periodic_callbacks.append(_spike_periodic)
    for _o in os.environ.get("THAI_SPIKE_OVERRIDE", "").split(","):
        if ":" in _o:
            config.label_overrides[_o.split(":")[0]] = _o.split(":")[1]

label splashscreen:
    if THAI_SPIKE and THAI_SPIKE_LABEL:
        $ renpy.change_language("thai")
        $ povname = "Palmier"
        $ nickname = "Palmy"
        if THAI_SPIKE_LABEL != "start":
            $ kamu, dia, dia2, kk = "她", "她", "她的", "姐姐"
        $ _preferences.afm_enable = True
        $ _preferences.afm_time = 3
        $ _preferences.text_cps = 0
        $ renpy.jump(THAI_SPIKE_LABEL)
    return

label thai_test_names:
    $ renpy.say(red, "ทดสอบชื่อควิล", interact=False)
    $ renpy.pause(3.5, hard=True)
    $ renpy.say(quil, "ทดสอบชื่อเธน", interact=False)
    $ renpy.pause(30, hard=True)

label thai_test_renderer:
    $ renpy.show_screen("_choose_renderer")
    $ renpy.pause(30, hard=True)

label thai_test_prefs:
    $ main_menu = True
    $ renpy.run(ShowMenu("preferences"))
    $ renpy.pause(30, hard=True)

label thai_test_inventory:
    $ renpy.run(ShowMenu(os.environ.get("THAI_SPIKE_MENU", "quests")))
    $ renpy.pause(30, hard=True)

label thai_test_restart:
    $ renpy.full_restart()

label thai_test_save:
    # Use a messenger line and two choice names that exist in YOUR game's string table.
    $ messages.append(Message("<an English messenger line from the game>", 1, False, False, 0, False, 360, message_time))
    $ messages.append(Message("", 0, {0:{'jump':'a', 'name':"<choice A>"}, 1:{'jump':'b', 'name':"<choice B>"}}, False, 0, False, 360, message_time))
    python:
        _r = []
        _r.append("msg0=" + repr(messages[-2].what))
        _r.append("choice=" + repr(messages[-1].choices))
        try:
            renpy.save("thai_test_slot", "thai test")
            _r.append("save=OK exists=%s" % renpy.can_load("thai_test_slot"))
            renpy.unlink_save("thai_test_slot")
            _r.append("deleted=%s" % (not renpy.can_load("thai_test_slot")))
        except Exception as e:
            _r.append("save=FAIL " + repr(e))
        open(os.path.join(config.basedir, "thai_diag.txt"), "w", encoding="utf-8").write("\n".join(_r))
        renpy.quit()
