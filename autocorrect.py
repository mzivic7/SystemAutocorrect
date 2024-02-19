#!/usr/bin/python3

import time
import sys
import subprocess
import evdev
from evdev import ecodes
import configparser
import json
import os
from ast import literal_eval as leval

config = configparser.ConfigParser()

def read_key_comb(config, config_key, default):
    try:
        if config.get("Main", config_key).upper() == "NONE":
            return [None]
        else:
            return [ecodes.ecodes[f"KEY_{x}"] for x in config.get("Main", config_key).upper().split(" + ")]
    except:
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

mod_keys = (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL)
if spell_checker == "aspell":
    cmd = ["aspell", "-a", f"--sug-mode={aspell_mode}", f"--lang={languages[0]}"]
else:
    cmd = ["hunspell", "-a"]



def spell_check(word):
    aspell = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, error = aspell.communicate(word.encode())
    check = output.decode().split("\n")[1]
    if check == "*":
        return None
    else:
        try:
            return check.split(": ")[1].split(", ")[0]
        except:
            return None

def delete(ui, num):
    for _ in range(num):
        press(ui, ecodes.KEY_BACKSPACE)

def press(ui, key):
    ui.write(ecodes.EV_KEY, key, 1)
    ui.write(ecodes.EV_KEY, key, 0)
    ui.syn()

def type(ui, word):
    for letter in word:
        if letter == " ":
            press(ui, ecodes.KEY_SPACE)
        else:
            press(ui, ecodes.ecodes[f"KEY_{letter}"])

def notify_send(header, message):
    proc = subprocess.Popen("echo | who | awk '{print $1}' | head -n1 ", shell=True, stdout=subprocess.PIPE)
    output, error = proc.communicate()
    user = output.decode().replace("\n", "")
    cmd = f'sudo -u "{user}" DISPLAY=' + """":$(find /tmp/.X11-unix -type s | grep -Pom1 '/tmp/.X11-unix/X\K\d+$')" "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u '""" + user + """')/bus" /usr/bin/notify-send""" + f" '{header}'" + f" '{message}'"
    subprocess.Popen(cmd, shell=True)

def add_to_blacklist(word):
    if not "home" in os.getcwd() and not os.path.exists("/etc/autocorrect/"):
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


dev = None
past = [None] * past_len
keybind_past = [None] * len(toggle_key)
backspace = None
enable = True
skip = False
lang = 0
blacklist = add_to_blacklist(None)

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
ui = evdev.UInput.from_device(dev, name='virtual-keyboard-device')
for event in dev.read_loop():
    # release
    if event.type == ecodes.EV_KEY and event.value == 0:
        keybind_past = [None] * len(toggle_key)
        if enable:
            if skip:
                skip = False
            else:
                past.append(ecodes.KEY[event.code].replace("KEY_", ""))
                past.pop(0)
            
            # reset when backspace
            if event.code == ecodes.KEY_BACKSPACE:
                backspace = True
            
            # space and enter trigger
            elif event.code in (ecodes.KEY_SPACE, ecodes.KEY_ENTER):
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
                            print(f'Word "{word}" is corrected to: "{correct}"')
                        # delete old word
                        delete(ui, len(word)+1)
                        # write corrected word
                        type(ui, correct + " ")
                    elif debug:
                        print(f'Word "{word}" is OK')
                past = [None] * past_len
        elif skip:
            skip = False
    
    # press
    elif event.type == ecodes.EV_KEY and event.value == 1:
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
            notify_send("Autocorrect", f"Changed language to {languages[lang]}")
        
        # blacklist word
        if keybind_past == blacklist_key:
            word = "".join([x for x in past if x is not None and len(x) == 1])
            past = [None] * past_len
            blacklist = add_to_blacklist(word)
            notify_send("Autocorrect", f'Word "{word}" added to blacklist')
        
        if any(x in mod_keys for x in keybind_past[:-1]):
            # key is not typed
            skip = True
                
ui.close()
