import time
import keyboard
import pynput
import sys
import os
import subprocess
import configparser
import json
from ast import literal_eval as leval
from pynput.keyboard import Key

config = configparser.ConfigParser()
keycode = {"LEFTCTRL": Key.ctrl_l, "RIGHTCTRL": Key.ctrl_r, "LEFTSHIFT": Key.shift_l, "RIGHTSHIFT": Key.shift_r, "LEFTALT": Key.alt_l, "RIGHTALT": Key.alt_r}
ctrl_keycode = ["\x01", "\x02", "\x03", "\x04", "\x05", "\x06", "\x07", "\x08", "\t", "\n", "\x0b", "\x0c", "\r", "\x0e", "\x0f", "\x10", "\x11", "\x12", "\x13", "\x14", "\x15", "\x16", "\x17", "\x18", "\x19", "\x1a"]

def read_key_comb(config, config_key, default):
    try:
        if config.get("Main", config_key).upper() == "NONE":
            return [None]
        else:
            key_comb = config.get("Main", config_key).upper().split(" + ")
            ctrl = "LEFTCTRL" in key_comb or "RIGHTCTRL" in key_comb
            return [keycode[x] if len(x)>1 else (ctrl_keycode[ord(x.lower())-97] if ctrl else x.lower()) for x in key_comb]
             
    except:
        return default

config.read("config.ini")
past_len = config.getint("Main", "past_len")
aspell_mode = config.get("Main", "aspell_mode")
debug = leval(config.get("Main", "debug"))
aspell_path = config.get("Windows", "aspell_path")
toast = config.get("Windows", "toast")
languages = config.get("Main", "languages").replace(", ", ",").split(",")
keymaps = config.get("Main", "keymaps").replace(", ", ",").split(",")
toggle_key = read_key_comb(config, "toggle_key", [Key.ctrl_l, Key.shift_l, "\x05"])
cycle_key = read_key_comb(config, "cycle_key", [Key.ctrl_l, Key.shift_l, "\x12"])
blacklist_key = read_key_comb(config, "blacklist_key", [Key.ctrl_l, Key.shift_l, "\x02"])

if toast == "win10":
    from win10toast import ToastNotifier
    toast = ToastNotifier()
elif toast == "win11":
    import win11toast

mod_keys = (pynput.keyboard.Key.ctrl_l, pynput.keyboard.Key.ctrl_r)
cmd = [aspell_path, "-a", f"--sug-mode={aspell_mode}", f"--lang={languages[0]}"]
def spell_check(word):
    aspell = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, error = aspell.communicate(word.encode())
    try:
        check = output.decode().split("\n")[1]
    except Exception:
        check = str(output).split("\\r\\n")[1]
    if check == "*":
        return None
    else:
        try:
            return check.split(": ")[1].split(", ")[0]
        except Exception:
            return None

def delete(num):
    for _ in range(num):
        keyboard.press("backspace")
        keyboard.release("backspace")

def press(key):
    keyboard.press(key)
    keyboard.release(key)

def type(word, end=None):
    global keymap
    word = word.translate(keymap)
    for letter in word:
        press(letter)
    if end:
        press(end)

def notify_send(header, message):
    if toast == "win10":
        toast.show_toast(header, message, duration=5, threaded=True)
    elif toast == "win11":
        win11toast.toast(header, message)

def add_to_blacklist(word):
    try:
        with open("blacklist.json", "r") as f:
            blacklist = json.load(f)
    except FileNotFoundError:
        blacklist = []
    if word:
        blacklist.append(word)
        with open("blacklist.json", "w") as f:
            json.dump(blacklist, f, indent=2)
    return blacklist

def load_keymap(keymap):
    if keymap is not None:
        with open("keymaps/" + keymap + ".json", "r") as f:
            return str.maketrans(json.load(f))
    else:
        return str.maketrans({})


dev = None
past = [None] * past_len
keybind_past = [None] * len(toggle_key)
backspace = None
enable = True
skip = False
lang = 0
blacklist = add_to_blacklist(None)

# load keymap and remove invalid keymaps
keymaps = [None if x == "None" else x for x in keymaps if (os.path.exists("keymaps/" + x + ".json") or x == "None")]
if len(keymaps) > len(languages):
    keymaps = keymaps[:len(languages)]
if len(keymaps) < len(languages):
    languages = languages[:len(keymaps)]
keymap = load_keymap(keymaps[lang])


# keyboard events
def on_release(key):
    global enable, past, backspace, skip, keybind_past, cmd, blacklist
    keybind_past = [None] * len(toggle_key)
    if enable:
        try:
            if skip:
                skip = False
            else:
                past.append(key.char)
                past.pop(0)
        except AttributeError:
            pass
        
        # reset when backspace
        if key == pynput.keyboard.Key.backspace:
            backspace = True
        
        # space and enter trigger
        elif key in (pynput.keyboard.Key.space, pynput.keyboard.Key.enter):
            if backspace:
                backspace = None
            else:
                # check word
                word = "".join([x for x in past if x is not None and len(x) == 1])
                if word:
                    if word not in blacklist:
                        correct = spell_check(word)
                    elif debug:
                        correct = None
                        print(f'Word "{word}" is found in blacklist')
                else:
                    correct = None
                
                # if word is bad
                if correct:
                    if debug:
                        print(f"Word {word} corrected to: {correct}")
                    # delete old word
                    delete(len(word)+1)
                    # write corrected word
                    if key == pynput.keyboard.Key.space:
                        type(correct, "space")
                    elif key == pynput.keyboard.Key.enter:
                        type(correct, "enter")
                elif debug:
                    print(f"Word {word} is OK")
            past = [None] * past_len
    elif skip:
        skip = False

def on_press(key):
    global enable, past, keybind_past, skip, cmd, lang, blacklist, keymap
    try:
        key = key.char.lower()
    except AttributeError:
        pass
    if keybind_past[-1] != key:
        keybind_past.append(key)
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
        
        # change language
        if keybind_past == cycle_key:
            lang += 1
            if lang >= len(languages):
                lang = 0
            cmd = [aspell_path, "-a", f"--sug-mode={aspell_mode}", f"--lang={languages[lang]}"]
            keymap = load_keymap(keymaps[lang])
            notify_send("Autocorrect", f"Changed language to {languages[lang]} and keymap to {keymaps[lang]}")
        
        # blacklist word
        if keybind_past == blacklist_key:
            word = "".join([x for x in past if x is not None and len(x) == 1])
            past = [None] * past_len
            blacklist = add_to_blacklist(word)
            notify_send("Autocorrect", f'Word "{word}" added to blacklist')
        
        if any(x in mod_keys for x in keybind_past[:-1]):
            # key is not typed
            skip = True

with pynput.keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
