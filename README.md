# Wording Status

## Description

Provides a real-time word and character count in the status-bar for Sublime Text. See: http://www.sublimetext.com/

Count words and/or characters on document or in selections. By default, whitespace is not included in the character count.

The minimal word length is 1 and does not count digits.

An estimated reading time is now appended to the end of the word count.

## Change log

See [./CHANGELOG.md](./CHANGELOG.md).

## Installation

### By Package Control

1. Download & Install **`Sublime Text 3`** (https://www.sublimetext.com/3)
1. Go to the menu **`Tools -> Install Package Control`**, then,
    wait few seconds until the installation finishes up
1. Now,
    Go to the menu **`Preferences -> Package Control`**
1. Type **`Add Channel`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
    input the following address and press <kbd>Enter</kbd>
    ```
    https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json
    ```
1. Go to the menu **`Tools -> Command Palette...
    (Ctrl+Shift+P)`**
1. Type **`Preferences:
    Package Control Settings – User`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
    find the following setting on your **`Package Control.sublime-settings`** file:
    ```js
    "channels":
    [
        "https://packagecontrol.io/channel_v3.json",
        "https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json",
    ],
    ```
1. And,
    change it to the following, i.e.,
    put the **`https://raw.githubusercontent...`** line as first:
    ```js
    "channels":
    [
        "https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json",
        "https://packagecontrol.io/channel_v3.json",
    ],
    ```
    * The **`https://raw.githubusercontent...`** line must to be added before the **`https://packagecontrol.io...`** one, otherwise,
      you will not install this forked version of the package,
      but the original available on the Package Control default channel **`https://packagecontrol.io...`**
1. Now,
    go to the menu **`Preferences -> Package Control`**
1. Type **`Install Package`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
    search for **`WordingStatus`** and press <kbd>Enter</kbd>

See also:

1. [ITE - Integrated Toolset Environment](https://github.com/evandrocoan/ITE)
1. [Package control docs](https://packagecontrol.io/docs/usage) for details.


## Preferences

Menu `Sublime Text`>`Settings…`>`Package Settings`>`WordingStatus`>`Settings` opens both the default and user settings files, where you can see every option explained in comments and copy/change the ones you need to adjust.

Or use the `Command Palette` commands `Preferences: WordingStatus Settings` or `WordingStatus Settings: User`/`WordingStatus Settings: Default`

## Inspiration

 - The main loop inspired by sublimelint https://github.com/lunixbochs/sublimelint
 - The count inspired by the original WordCount plugin http://code.google.com/p/sublime-text-community-packages/source/browse/#svn%2Ftrunk%2FWordCount committed by mindfiresoftware

## Contributors

 - Liam Cain
 - Lee Grey
 - Hawken Rives
 - Yaw Anokwa
 - James Brooks
 - Antony Male
 - Alex Galonsky
 - RikkiMongoose
 - ChrisJefferson
 - Harry Ng. (From [Word Count Tool](http://wordcounttools.com/))
 - MangleKuo
 - Nick Cody
 - Amanda Neumann
 - evandrocoan
 - Evgeny (eugenesvk)
