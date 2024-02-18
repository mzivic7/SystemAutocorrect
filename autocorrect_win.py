import time
import keyboard
import pynput
import sys
import subprocess
import configparser
from ast import literal_eval as leval
from pynput.keyboard import Key

config = configparser.ConfigParser()
config.read("config.ini")

past_len = config.getint("Main", "past_len")
aspell_mode = config.get("Main", "aspell_mode")
debug = leval(config.get("Main", "debug"))
aspell_path = config.get("Windows", "aspell_path")
toast = config.get("Windows", "toast")
keycode = {"LEFTCTRL": Key.ctrl_l, "RIGHTCTRL": Key.ctrl_r, "LEFTSHIFT": Key.shift_l, "RIGHTSHIFT": Key.shift_r, "LEFTALT": Key.alt_l, "RIGHTALT": Key.alt_r}
try:
    if config.get("Main", "toggle_key").upper() == "NONE":
        toggle_key = [None]
    else:
        toggle_key = [keycode[x] if len(x)>1 else x.lower() for x in config.get("Main", "toggle_key").upper().split(" + ")]
except:
    toggle_key = [Key.ctrl_l, Key.shift_l, "E"]

if toast == "win10":
    from win10toast import ToastNotifier
    toast = ToastNotifier()
elif toast == "win11":
    import win11toast

dev = None
past = [None] * past_len
keybind_past = [None] * len(toggle_key)
backspace = None
enable = True
skip = False
mod_keys = (pynput.keyboard.Key.ctrl_l, pynput.keyboard.Key.ctrl_r)
cmd = [aspell_path, "-a", f"--sug-mode={aspell_mode}"]

def spell_check(word):
    aspell = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, error = aspell.communicate(word.encode())
    check = output.decode().split("\n")[1]
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

def type(word):
    for letter in word:
        if letter == " ":
            press("space")
        else:
            press(letter)
def notify_send(header, message):
    if toast == "win10":
        toast.show_toast(header, message, duration=5, threaded=True)
    elif toast == "win11":
        win11toast.toast(header, message)


# keyboard events
def on_release(key):
    global enable, past, backspace, skip, keybind_past
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
                    correct = spell_check(word)
                else:
                    correct = None
                
                # if word is bad
                if correct:
                    if debug:
                        print(f"Word {word} corrected to: {correct}")
                    # delete old word
                    delete(len(word)+1)
                    # write corrected word
                    type(correct + " ")
                elif debug:
                    print(f"Word {word} is OK")
            past = [None] * past_len
    elif skip:
        skip = False

def on_press(key):
    global past, keybind_past, skip
    try:
        past.append(key.char)
    except AttributeError:
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
    # TODO
    
    if any(x in mod_keys for x in keybind_past[:-1]):
        # key is not typed
        skip = True

with pynput.keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
