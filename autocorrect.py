#!/usr/bin/python3

import configparser
import json
import os
import subprocess
import sys
from ast import literal_eval as leval

import evdev
from evdev import ecodes

config = configparser.ConfigParser()
special_keycodes = {"[": ecodes.KEY_LEFTBRACE, "]": ecodes.KEY_RIGHTBRACE,
                    ";": ecodes.KEY_SEMICOLON, "'": ecodes.KEY_APOSTROPHE,
                    ",": ecodes.KEY_COMMA, ".": ecodes.KEY_DOT,
                    "/": ecodes.KEY_SLASH, "\\": ecodes.KEY_BACKSLASH,
                    "`": ecodes.KEY_GRAVE, "-": ecodes.KEY_MINUS,
                    "=": ecodes.KEY_EQUAL, " ": ecodes.KEY_SPACE}


def read_key_comb(config, config_key, default):
    """Read key combinations from config"""
    try:
        if config.get("Main", config_key).upper() == "NONE":
            return [None]
        return [ecodes.ecodes[f"KEY_{x}"] for x in config.get("Main", config_key).upper().split(" + ")]
    except Exception:
        return default


fail = 0
for path in ("/etc/autocorrect/", ""):
    try:
        config.read(path + "config.ini")
        past_len = config.getint("Main", "past_len")
        aspell_mode = config.get("Main", "aspell_mode")
        debug = leval(config.get("Main", "debug"))
        spell_checker = config.get("Linux", "spell_checker")
        languages = config.get("Main", "languages").replace(", ", ",").split(",")
        keymaps = config.get("Main", "keymaps").replace(", ", ",").split(",")
        custom = config.get("Main", "custom").replace(", ", ",").split(",")
        toggle_key = read_key_comb(config, "toggle_key", [29, 42, 18])
        cycle_key = read_key_comb(config, "cycle_key", [29, 42, 19])
        blacklist_key = read_key_comb(config, "blacklist_key", [29, 42, 48])
        break
    except configparser.NoSectionError:
        fail += 1
        if fail >= 2:
            past_len = 25
            aspell_mode = "normal"
            debug = False
            spell_checker = "aspell"
            toggle_key = [29, 42, 18]
            cycle_key = [29, 42, 19]
            blacklist_key = [29, 42, 48]
            languages = ["en_US"]
            keymaps = ["en_US"]
            custom = ["en_US"]

mod_keys = (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL)
if spell_checker == "aspell":
    cmd = ["aspell", "-a", f"--sug-mode={aspell_mode}", f"--lang={languages[0]}"]
else:
    cmd = ["hunspell", "-a"]
if aspell_mode == "OFF":
    use_aspell = False
else:
    use_aspell = True


def spell_check(word):
    """Spellcheck a word with aspell and return best correction"""
    aspell = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, error = aspell.communicate(word.encode())
    check = output.decode().split("\n")[1]
    if check == "*":
        return None
    try:
        return check.split(": ")[1].split(", ")[0]
    except Exception:
        return None


def delete(ui, num):
    """Delete number of keys"""
    for _ in range(num):
        press(ui, ecodes.KEY_BACKSPACE)


def press(ui, key):
    """Press a single key"""
    ui.write(ecodes.EV_KEY, key, 1)
    ui.write(ecodes.EV_KEY, key, 0)
    ui.syn()


def type_word(ui, word, end=None):
    """Type a word"""
    global keymap
    word = word.translate(keymap)
    for letter in word:
        if letter in special_keycodes:
            press(ui, special_keycodes[letter])
        else:
            press(ui, ecodes.ecodes[f"KEY_{letter}"])
    if end:
        press(ui, end)


def notify_send(header, message):
    """Send a notification"""
    proc = subprocess.Popen("echo | who | awk '{print $1}' | head -n1 ", shell=True, stdout=subprocess.PIPE)
    output, error = proc.communicate()
    user = output.decode().replace("\n", "")
    cmd = f'sudo -u "{user}" DISPLAY=' + """":$(find /tmp/.X11-unix -type_word s | grep -Pom1 '/tmp/.X11-unix/X\K\d+$')" "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u '""" + user + """')/bus" /usr/bin/notify-send""" + f" '{header}'" + f" '{message}'"
    subprocess.Popen(cmd, shell=True)


def add_to_blacklist(word):
    """Add specified word to blacklosr"""
    if "home" not in os.getcwd() and not os.path.exists("/etc/autocorrect/"):
        path = "/etc/autocorrect/"
        os.mkdir(path)
    else:
        path = ""
    try:
        with open(path + "blacklist.json", "r") as f:
            blacklist = json.load(f)
    except FileNotFoundError:
        blacklist = []
    if word:
        blacklist.append(word)
        with open(path + "blacklist.json", "w") as f:
            json.dump(blacklist, f, indent=2)
    return blacklist


def load_keymap(keymap):
    """Load custom keymaps"""
    if keymap is not None:
        with open(path + "keymaps/" + keymap + ".json", "r") as f:
            keymap_raw = json.load(f)
            return str.maketrans(keymap_raw), keymap_raw
    else:
        return str.maketrans({}), {}


def load_custom(custom):
    """Load custom replacements"""
    if custom is not None:
        with open(path + "custom/" + custom + ".json", "r") as f:
            return {k.upper(): v.upper() for k, v in json.load(f).items()}
    else:
        return {}


dev = None
past = [None] * past_len
keybind_past = [None] * len(toggle_key)
backspace = None
enable = True
skip = False
lang = 0
blacklist = add_to_blacklist(None)

# load keymap and remove invalid keymaps
keymaps = [None if x == "None" else x for x in keymaps if (os.path.exists(path + "keymaps/" + x + ".json") or x == "None")]
if len(keymaps) > len(languages):
    keymaps = keymaps[:len(languages)]
if len(keymaps) < len(languages):
    languages = languages[:len(keymaps)]
keymap, raw_keymap = load_keymap(keymaps[lang])

# load custom replacements and remove invalid ones
custom = [None if x == "None" else x for x in custom if (os.path.exists(path + "custom/" + x + ".json") or x == "None")]
if len(custom) > len(custom):
    custom = keymaps[:len(custom)]
if len(keymaps) < len(languages):
    custom.append(None)
custom_repl = load_custom(custom[lang])

# find keyboard
devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
for device in devices:
    if "keyboard" in device.name:
        dev = evdev.InputDevice(device.path)
        break
if not dev:
    print("Keyboard device could not be found.")
    sys.exit()
else:
    print(f"Using device: {device.name}")


# keyboard events
ui = evdev.UInput.from_device(dev, name="virtual-keyboard-device")
for event in dev.read_loop():
    # release
    if event.type_word == ecodes.EV_KEY and event.value == 0:
        keybind_past = [None] * len(toggle_key)
        if enable:
            if skip:
                skip = False
            else:
                if event.code in special_keycodes.values():
                    letter = [x for x in special_keycodes if special_keycodes[x] == event.code][0]
                    if letter in raw_keymap.values():
                        key = [x for x in raw_keymap if raw_keymap[x] == letter][0]
                        past.append(key)
                    else:
                        past.append(ecodes.KEY[event.code].replace("KEY_", ""))
                else:
                    past.append(ecodes.KEY[event.code].replace("KEY_", ""))
                past.pop(0)

            # reset when: backspace, arrows
            if event.code in (ecodes.KEY_BACKSPACE, ecodes.KEY_LEFT, ecodes.KEY_RIGHT, ecodes.KEY_UP, ecodes.KEY_DOWN):
                backspace = True

            # space and enter trigger
            elif event.code in (ecodes.KEY_SPACE, ecodes.KEY_ENTER):
                if backspace:
                    backspace = None
                else:
                    # check word
                    word = "".join([x for x in past if x is not None and len(x) == 1])
                    if word:
                        if word in blacklist:
                            correct = None
                            if debug:
                                print(f'Word "{word}" is found in blacklist')
                        elif word.upper() in custom_repl:
                            correct = custom_repl[word.upper()]
                            if debug:
                                print(f'Word "{word}" is found in custom replacement')
                        elif use_aspell:
                            correct = spell_check(word)
                    else:
                        correct = None

                    # if word is bad
                    if correct:
                        if debug:
                            print(f'Word "{word}" is corrected to: "{correct}"')
                        # delete old word
                        delete(ui, len(word)+1)
                        # write corrected word
                        type_word(ui, correct, event.code)
                    elif debug:
                        print(f'Word "{word}" is OK')
                past = [None] * past_len
        elif skip:
            skip = False

    # press
    elif event.type_word == ecodes.EV_KEY and event.value == 1:
        keybind_past.append(event.code)
        keybind_past.pop(0)

        # toggle autocorrect
        if keybind_past == toggle_key:
            enable = not enable
            past = [None] * past_len
            if enable:
                message = "Automatic text corrections enabled"
            else:
                message = "Automatic text corrections disabled"
            notify_send("Autocorrect", message)

        # change lang
        if keybind_past == cycle_key and spell_checker == "aspell":
            lang += 1
            if lang >= len(languages):
                lang = 0
            cmd = ["aspell", "-a", f"--sug-mode={aspell_mode}", f"--lang={languages[lang]}"]
            keymap, raw_keymap = load_keymap(keymaps[lang])
            custom_repl = load_custom(custom[lang])
            notify_send("Autocorrect", f"Changed language to {languages[lang]} and keymap to {keymaps[lang]}")

        # blacklist word
        if keybind_past == blacklist_key:
            word = "".join([x for x in past if x is not None and len(x) == 1])
            past = [None] * past_len
            blacklist = add_to_blacklist(word)
            notify_send("Autocorrect", f'Word "{word}" added to blacklist')

        if any(x in mod_keys for x in keybind_past[:-1]):
            # key is not type_wordd
            skip = True

ui.close()
