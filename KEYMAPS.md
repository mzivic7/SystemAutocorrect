### Format
Keymap is dictionary in json file, with formatting:  
```json
{
"letter": "replacement",
"letter2": "replacement2"
}
```

### Letter
Letter can be any of regular letters(a,b,c).  
If this is some language specific character not found in en_US keyboard, unicode must be used to write it.  
Format used is: `"\u<NUMBER>`.  
Where `<NUMBER>` is unicode value for this letter. This value corresponds to regular unicode format: `U+<VALUE>`.  

### Replacement
Replacement can be any of regular letters (a,b,c) or one following signs:  
``[];',./\\`-=``  
Note that `\` must be written as double backslash: `\\`  

### Contributing
If you want yor keymap to be added to this project:  
First, test your keymap.
Open new issue, specify language and keyboard layout, and uplaod your keymap.
