# poLanguageChecker

This is a small python script that can be used to validate a if gettext `.pot` / `.po` file contains valid grammar and spelling.

## Features

- Spell check.
- Grammar / phraseology checking.
- Can check either the `msid` or `msgstr`.
- Support for a custom dictionary, including providing spellcheck suggestions.

## Using Local LanguageTool Copy

Download the offline version of LanguageTool from the direct link (here)[https://languagetool.org/download/LanguageTool-stable.zip].
Then, extract it to somewhere easy to remember and when using the tool, specify the path using the `LTP_JAR_DIR_PATH` environment variable.

```bash
LTP_JAR_DIR_PATH="/home/user/LanguageTool-6.6" python check.py --path /home/user/Downloads/mySource.po
```

## Screenshot

![Screenshot](https://raw.githubusercontent.com/FOSSBilling/poLanguageChecker/main/screenshot.png)
