# Wording Status

## Unreleased

- Add `Command Palette` commands to open settings files `Preferences: WordingStatus Settings` or `WordingStatus Settings: User`/`WordingStatus Settings: Default`
- 🐞 don't leave old statusbar messages when changing its position via `status_order_prefix`
- moved to the new 3.8 Sublime Text plugin host
- add `minute_separator` user setting for separating `5m 2s` in time
- add `in_group_separator` user setting for separating line/word/char counts
- group total / per-line counts into two groups for the statusbar to avoid `,` separators forced by Sublime Text

## 2.0.1

Created the setting `status_order_prefix` Evgeny (eugenesvk).
```
"status_order_prefix"           : ""        , // |""|       Prefix the status name to change its order in the status bar, which uses alphabetical sorting
```

## 2.0.0

Renamed package from Word Count (forked from https://github.com/evandrocoan/WordingStatus/issues/5) to WordingStatus.

## 1.1.0

Created the following settings by Evgeny (eugenesvk) and reformatted the settings file as follows:
```
"thousands_separator"           : "."       , // |"."|      Thousands separator's symbol
"label_line"            : " Lines"          , // |" Lines"|             Label for the number of lines
"label_word"            : " Words"          , // |" Words"|             Label for the number of words
"label_char"            : " Chars"          , // |" Chars"|             Label for the number of chars
"label_word_in_line"    : " Words in lines" , // |" Words in lines"|    Label for the number of words in lines
"label_char_in_line"    : " Chars in lines" , // |" Chars in lines"|    Label for the number of chars in lines
"label_time"            : " reading time"   , // |" reading time"|      Label for the reading time
"label_page"            : "Page "           , // |"Page "|              Label for the page number
```
