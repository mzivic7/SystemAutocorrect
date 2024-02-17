import time
import keyboard
import pynput
import sys
import subprocess
import configparser
from ast import literal_eval as leval

config = configparser.ConfigParser()
config.read("config.ini")

past_len = config.getint("Main", "past_len")
aspell_mode = config.get("Main", "aspell_mode")
aspell_path = config.get("Main", "aspell_path")
toast = config.get("Main", "toast")
debug = leval(config.get("Main", "debug"))

if toast == "win10":
    from win10toast import ToastNotifier
    toast = ToastNotifier()
elif toast == "win11":
    import win11toast

dev = None
past = [None] * past_len
backspace = None
enable = True
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
    global enable
    global past
    global backspace
    if enable:
        try:
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
                word = "".join([i for i in past if i is not None and len(i) == 1])
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
    
    if False and key == pynput.keyboard.Key.ctrl_l:   # disabled for now
        enable = not enable
        if enable:
            message = "Automatic text corrections enabled"
        else:
            message = "Automatic text corrections disabled"
        notify_send("Autocorrect", message)

with pynput.keyboard.Listener(on_release=on_release) as listener:
    listener.join()
