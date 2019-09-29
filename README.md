

## Description

Provides a real-time Word Count and character count in the status-bar for Sublime Text. See: http://www.sublimetext.com/

Count words and/or characters on document or in selections. By default, whitespace is not included in the character count.

The minimal word length is 1 and does not count digits.

An estimated reading time is now appended to the end of the word count.


## Installation

### By Package Control

1. Download & Install **`Sublime Text 3`** (https://www.sublimetext.com/3)
1. Go to the menu **`Tools -> Install Package Control`**, then,
   wait few seconds until the installation finishes up
1. Go to the menu **`Tools -> Command Palette...
   (Ctrl+Shift+P)`**
1. Type **`Preferences:
   Package Control Settings – User`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
   add the following setting to your **`Package Control.sublime-settings`** file, if it is not already there
   ```js
   [
       ...
       "channels":
       [
           "https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json",
           "https://packagecontrol.io/channel_v3.json",
       ],
       ...
   ]
   ```
   * Note,
     the **`https://raw...`** line must to be added before the **`https://packagecontrol...`**,
     otherwise you will not install this forked version of the package,
     but the original available on the Package Control default channel **`https://packagecontrol...`**
1. Now,
   go to the menu **`Preferences -> Package Control`**
1. Type **`Install Package`** on the opened quick panel and press <kbd>Enter</kbd>
1. Then,
search for **`WordCount`** and press <kbd>Enter</kbd>

See also:
1. [ITE - Integrated Toolset Environment](https://github.com/evandrocoan/ITE)
1. [Package control docs](https://packagecontrol.io/docs/usage) for details.


## Preferences
Located under Sublime Text>Preferences>Package Settings>Settings — User
(You probably need to copy the default settings from the uneditable Sublime Text>Preferences>Package Settings>Settings — **Default**)


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
