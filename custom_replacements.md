### Format
Custom replacements are dictionary in json file, with formatting:  
```json
{
"word": "replacement",
"word2": "replacement2"
}
```

### Notes
For now it does not matter if word is capitalized or not.  
Words and letters from other languages are supported, but you have to write them as in that specific language, not unicode.  
Replacements can have space in them, and any of following signs:  
``[];',./\\`-=``  
Note that `\` must be written as double backslash: `\\`  

