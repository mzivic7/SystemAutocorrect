# System wide autocorrect
Python script that automatically corrects text as you type.  
Uses hunspell or aspell to check for mistakes and obtain correction.  

## Usage
This script can be run individually or as service on Linux and Windows 10 and 11, on Linux it works with Wayland and X11.
Aspell package is required on linux.  
Aspell-win32 is required on windows.  
If you have any feature suggestion, first check todo at the end of this file, if that feature is not there, open new issue.  

## Installation
### Linux
Notes: everything must be installed as root, including evdev 
Dependencies that must be manually installed: python-evdev, hunspell or aspell  
build.py and requirements.txt are for Windows.  
#### Linux - Service
This will install dependencies and configure script as service that runs at startup.  
```sh
git clone https://github.com/mzivic7/system-autocorrect.git
cd system-autocorrect
sudo pip install evdev
# if environment is externally managed:
sudo pacman -S python-evdev
# install dependancy: hunspell or aspell, with your package manager
sudo install.sh
```

#### Linux - Manual
If you don't want it to be installed as service:  
```sh
git clone https://github.com/mzivic7/system-autocorrect.git
cd system-autocorrect
sudo pip install evdev
# if environment is externally managed:
sudo pacman -S python-evdev
# install dependancy: hunspell or aspell, with your package manager
# Then just run:
sudo python autocorrect.py
# or add it as system command:
sudo cp autocorrect.py /usr/local/sbin/autocorrect
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
For Windows, aspell installation path may be different, so check it in config.ini  

## How it works
Keyboard module is used to record typed text. After space or enter key is recorded, typed word is sent to aspell, who returns corrected word. Then using pynput: backspace is pressed to delete old word and type new one, really fast.  

## TODO
on/off keybinding  
Disable after click  
Change language dictionary  
Automatically add word to dictionary  
Record capital letters  
Capitalize after ".  "  
