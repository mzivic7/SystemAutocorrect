# System wide autocorrect
Python script that automatically corrects text as you type.  
Uses hunspell or aspell to check for mistakes and obtain correction.  

## Usage
This script can be run individually or as service on Linux and Windows 10 and 11, on Linux it works with Wayland and X11.  
Aspell package is required on Linux.  
Aspell-win32 is required on Windows.  
Default toggle ON/OFF key combination is CTRL+SHIFT+E.  
Default language cycle key combination is CTRL+SHIFT+R.  
Default blacklist word key combination is CTRL+SHIFT+B.  
To blacklist word, type it, but don't press space, then press key combination.  
Blacklisted words are saved in `blacklist.json` which can be found next to `config.ini`.  
Keyboard layout in your system must be changed to matching language.  



## Installation
### Linux
Notes: everything must be installed as root, including evdev.  
Dependencies that must be manually installed: python-evdev, hunspell/aspell.  
build.py and requirements.txt are for Windows.  
config.ini is in /etc/autocorrect/config.ini  
#### Linux - Service
This will install dependencies and configure script as service that runs at startup.  
```sh
git clone https://github.com/mzivic7/SystemAutocorrect.git
cd SystemAutocorrect
sudo pip install evdev
# if environment is externally managed:
sudo pacman -S python-evdev
# install dependancy: hunspell or aspell, with your package manager
sudo install.sh
```

#### Linux - Manual
If you don't want it to be installed as service:  
```sh
git clone https://github.com/mzivic7/SystemAutocorrect.git
cd SystemAutocorrect
sudo pip install evdev
# if environment is externally managed:
sudo pacman -S python-evdev
# install dependancy: hunspell or aspell, with your package manager
# Then just run:
sudo python autocorrect.py
# or add it as system command:
sudo cp autocorrect.py /usr/local/sbin/autocorrect
# in that case, also create config:
sudo mkdir /etc/autocorrect/
sudo cp config.ini /etc/autocorrect/config.ini
```

### Windows
When run, no window will be open, so if you want to stop it, you must kill it from task manager.  
Dependency that must be manually installed: [aspell-win32](https://github.com/adamyg/aspell-win32). Don't install x64 version.  
Dictionary for specific language must be installed alongside aspell base program.  
Autocorrect WILL NOT WORK without aspell and dictionary.  
install.shm uninstall.sh and autocorrect.service are for Linux.  

#### Windows - Build
1. Install [Python](https://www.python.org/)
2. Clone this repository, unzip it
3. Open terminal, cd to unzipped folder
4. install requirements: `pip install -r requirements.txt`
5. Run build script: `python build.py`

#### Windows - Run from source
Same as above, but instead `python build.py` run: `python autocorrect_win.py`

## Configuration
For linux, config is searched for in 2 locations: `/etc/autocorrect/config.ini` and in same dir as script file.  
For Windows, aspell installation path may be different, so make sure it is correct in config.ini  

### Adding languages
Languages that have irregular characters, with diacritics, etc. must have kaymap. See Language keymaps.  
Language must be installed in order to be used with aspell.  
For Linux: check (eg. aspell-en) with your package manager (also on AUR for Arch), alternatively languages can be downloaded [here](https://ftp.gnu.org/gnu/aspell/dict/0index.html).
See readme in downloaded archivefor install instructions.
For Windows: languages can be downloaded from [aspell-win32 repo](https://github.com/adamyg/aspell-win32).
To install language, run downloaded exe file.  
Added languages can be added in config.ini to be cycled when key combination is pressed.
Leave only one language to use instead english.

### Language keymaps
Languages wit irregular characters, with diacritics, etc. must have keymap in `keymaps` directory (can be found next to `config.ini`).  
Keymap is used to remap this character to its keyboard key. For example german letter "Ü" is remapped to "[".  
Also note that keyboard layout in your system must be changed to matching language.  
If language is not in `keymaps` directory, you can write your own keymap, see [KEYMAPS.md](KEYMAPS.md).  
WARNING: On Windows, aspell may return text in wrong encoding, which will cause some letters to be written in byte format, or even crash autocorrect.  

## How it works
Keyboard module is used to record typed text. After space or enter key is recorded, typed word is sent to aspell, who returns corrected word. Then using pynput: backspace is pressed to delete old word and type new one, really fast.  

## TODO
Special characters on input  
Custom replacements  
Skip after click  
Skip after arrows  
Automatically add word to dictionary  
Record capital letters  
Capitalize after ".  "  
