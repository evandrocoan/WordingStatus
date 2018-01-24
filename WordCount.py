
import sublime
import sublime_plugin

import re
import time
import threading

from math import ceil as ceil
from os.path import basename

Preferences  = {}
g_sleepEvent = threading.Event()
g_is_already_running = False


def plugin_unloaded():
    global g_is_already_running

    g_is_already_running = False
    sublime_settings.clear_on_change( 'WordCount' )

    for window in sublime.windows():

        for view in window.views():
            view.erase_status('WordCountStatus');


def plugin_loaded():
    global Preferences
    global sublime_settings

    sublime_settings = sublime.load_settings( 'WordCount.sublime-settings' )
    Preferences.load();

    sublime_settings.clear_on_change( 'WordCount' )
    sublime_settings.add_on_change( 'WordCount', lambda: Preferences.load() )

    # Initialize the WordsCount's countView attribute
    WordsCount.setUpView( get_active_view() )

    if not g_is_already_running:
        g_sleepEvent.set()

        # Wait the Preferences class to be loaded
        sublime.set_timeout_async( configure_word_count, 5000 )


def configure_word_count():
    """
        break/interrupt a time.sleep() in python
        https://stackoverflow.com/questions/5114292/break-interrupt-a-time-sleep-in-python
    """
    global g_is_already_running
    g_is_already_running = True

    # Reset the internal flag to false. Subsequently, threads calling wait() will block until set()
    # is called to set the internal flag to true again.
    g_sleepEvent.clear()

    thread = threading.Thread( target=word_count_loop )
    thread.start()


def word_count_loop():
    mininum_time = 0.01
    default_time = 3.0

    while True:
        # Stops the thread when the plugin is reloaded or unloaded
        if not g_is_already_running:
            break

        # sleep time is adaptive, if takes more than `mininum_time` to calculate the word count,
        # sleep_time becomes `elapsed_time*3`
        if not Preferences.is_already_running:
            WordsCount.doCounting()

        # print( "word_count_loop, elapsed_time: %f microseconds" % ( Preferences.elapsed_time * 1000 ) )
        g_sleepEvent.wait( Preferences.elapsed_time*100 if Preferences.elapsed_time > mininum_time else default_time )


class Preferences():

    @staticmethod
    def load():
        Preferences.elapsed_time           = 1.4
        Preferences.is_already_running     = False

        Preferences.wordRegex              = re.compile( sublime_settings.get('word_regexp', "^[^\w]?`*\w+[^\w]*$"), re.U )
        Preferences.wordRegex              = Preferences.wordRegex.match
        Preferences.splitRegex             = sublime_settings.get('word_split', None)

        if Preferences.splitRegex:
            Preferences.splitRegex         = re.compile(Preferences.splitRegex, re.U)
            Preferences.splitRegex         = Preferences.splitRegex.findall

        Preferences.enable_readtime        = sublime_settings.get('enable_readtime', False)
        Preferences.enable_count_lines     = sublime_settings.get('enable_count_lines', False)
        Preferences.enable_count_chars     = sublime_settings.get('enable_count_chars', False)
        Preferences.enable_count_pages     = sublime_settings.get('enable_count_pages', False)
        Preferences.enable_count_words     = sublime_settings.get('enable_count_words', True)

        Preferences.enable_line_word_count = sublime_settings.get('enable_line_word_count', False)
        Preferences.enable_line_char_count = sublime_settings.get('enable_line_char_count', False)

        Preferences.readtime_wpm           = sublime_settings.get('readtime_wpm', 200)
        Preferences.words_per_page         = sublime_settings.get('words_per_page', 300)
        Preferences.char_ignore_whitespace = sublime_settings.get('char_ignore_whitespace', True)
        Preferences.whitelist_syntaxes     = sublime_settings.get('whitelist_syntaxes', [])
        Preferences.blacklist_syntaxes     = sublime_settings.get('blacklist_syntaxes', [])
        Preferences.strip                  = sublime_settings.get('strip', [])

        Preferences.page_count_mode_count_words = sublime_settings.get('page_count_mode_count_words', True)


class WordsCount(sublime_plugin.EventListener):

    countView = None
    wordCountViews = {}

    def on_close(self, view):
        view_id = view.id()

        if view_id in WordsCount.wordCountViews:
            del WordsCount.wordCountViews[view_id]

    def on_selection_modified_async(self, view):

        if Preferences.enable_count_words:
            selections = view.sel()

            if len( selections ):
                WordsCount.countView.is_text_selected = True
                return

            WordsCount.countView.is_text_selected = False

    def on_activated_async(self, view):
        # print( "on_activated_async, view_id: %d" % view.id() )
        WordsCount.setUpView( view )
        WordsCount.doCounting()

    @classmethod
    def setUpView(cls, view):
        view_settings = view.settings()
        wordCountViews = cls.wordCountViews

        if view_settings.get('is_widget'):
            view = get_active_view()
            view_settings = view.settings()

        syntax, is_enabled = cls.should_run_with_syntax( view_settings )
        view_id = view.id()

        # print( "setUpView, view_id: %d" % view_id )
        if view_id in wordCountViews:
            wordCountViews[view_id].syntax = syntax
            wordCountViews[view_id].syntax = is_enabled

        else:
            wordCountViews[view_id] = WordCountView( view, syntax, is_enabled )

        cls.countView = wordCountViews[view_id]

    @staticmethod
    def should_run_with_syntax(view_settings):
        syntax = view_settings.get('syntax')
        syntax = basename( syntax ).split( '.' )[0].lower() if syntax != None else "plain text"

        if len( Preferences.blacklist_syntaxes ) > 0:

            for white in Preferences.blacklist_syntaxes:

                if white == syntax:
                    return syntax, False

        if len(Preferences.whitelist_syntaxes) > 0:

            for white in Preferences.whitelist_syntaxes:

                if white == syntax:
                    return syntax, True

            return syntax, False

        return syntax, True

    @classmethod
    def doCounting(cls):
        countView = cls.countView

        if countView.view.change_count() != countView.change_count \
                or countView.is_text_selected:

            countView.startCounting()


class WordCountView():

    def __init__(self, view, syntax, is_enabled):
        self.syntax = syntax
        self.is_enabled = is_enabled
        self.is_text_selected = False

        # We need to set it to -1, because by default it starts on 0. Then we for an update when a
        # view is first activated by `WordsCount::on_activated_async()`
        self.change_count   = -1
        self.lines_contents = []

        self.view     = view
        self.contents = []

        self.char_count = 0
        self.word_count = 0
        self.line_count = 0

        self.word_count_line = 0
        self.char_count_line = 0

    def updateViewContents(self):
        view = self.view
        selections = view.sel()

        if Preferences.enable_line_char_count or Preferences.enable_line_word_count:
            del self.lines_contents[:]

            for selection in selections:
                self.lines_contents.append( view.substr( view.line( selection.end() ) ) )

        if self.is_text_selected:
            del self.contents[:]

            for selection in selections:
                self.contents.append( view.substr( selection ) )

        else:
            self.contents = [view.substr( sublime.Region( 0, view.size() ) )]

    def startCounting(self):

        if not self.is_enabled:
            return

        Preferences.start_time = time.perf_counter()
        Preferences.is_already_running = True

        view = self.view
        self.updateViewContents()

        if self.syntax and self.syntax in Preferences.strip:

            for regular_expression in Preferences.strip[self.syntax]:
                lines_count = len( self.contents )
                lines_contents_count = len( self.lines_contents )

                for selection_index in range( lines_count ):
                    self.contents[selection_index] = re.sub( regular_expression, '', self.contents[selection_index] )

                for selection_index in range( lines_contents_count ):
                    self.lines_contents[selection_index] = re.sub( regular_expression, '', self.lines_contents[selection_index] )

        if Preferences.enable_count_lines:
            self.line_count = view.rowcol( view.size() )[0] + 1

        if Preferences.enable_count_words:
            self.word_count = count_words( self.contents )

        if Preferences.enable_count_chars:
            self.char_count = count_chars( self.contents )

        if Preferences.enable_line_char_count:
            self.char_count_line = count_chars( self.lines_contents )

        if Preferences.enable_line_word_count:
            self.word_count_line = count_words( self.lines_contents )

        self.displayCountResults()

    def displayCountResults(self):
        display( self.view, self.word_count, self.char_count, self.line_count, self.word_count_line, self.char_count_line )

        Preferences.elapsed_time = time.perf_counter() - Preferences.start_time
        Preferences.is_already_running = False


def display(view, word_count, char_count, line_count, word_count_line, char_count_line):
    status  = []
    minutes = int( word_count / Preferences.readtime_wpm )
    seconds = int( word_count % Preferences.readtime_wpm / ( Preferences.readtime_wpm / 60 ) )

    if line_count > 0:
        status.append( '%d Lines' % line_count )

    if word_count > 0:
        status.append( '%d Words' % word_count )

    if char_count > 0:
        status.append( '%d Chars' % char_count )

    if word_count_line > 0:
        status.append( "%d Words in line" % ( word_count_line ) )

    if char_count_line > 0:
        status.append("%d Chars in line" % ( char_count_line ) )

    if Preferences.enable_count_pages and word_count > 0:

        if not Preferences.page_count_mode_count_words or Preferences.words_per_page < 1:
            visible = view.visible_region()
            rows_per_page = (view.rowcol(visible.end())[0]) - (view.rowcol(visible.begin())[0])
            pages = ceil((view.rowcol(view.size()-1)[0] + 1 ) /  rows_per_page)
            current_line = view.rowcol(view.sel()[0].begin())[0]+1
            current_page = ceil(current_line / rows_per_page)

        else:
            pages = ceil(word_count / Preferences.words_per_page)
            rows = view.rowcol(view.size()-1)[0] + 1
            current_line = view.rowcol(view.sel()[0].begin())[0]+1
            current_page = ceil((current_line / Preferences.words_per_page) / (rows / Preferences.words_per_page))

        if pages > 1:

            if current_page != 0:
                status.append('Page '+str(current_page)+'/'+str(pages))

            else:
                status.append('Page '+str(current_page)+'/'+str(pages))

    if Preferences.enable_readtime and seconds >= 1:
        status.append("~%dm %ds reading time" % (minutes, seconds))

    view.set_status('WordCountStatus', ', '.join(status))
    # print( "view: %d, Setting status to: " % view.id() + ', '.join( status) )


def count_words(text_list):
    words_count = 0

    wordRegex  = Preferences.wordRegex
    splitRegex = Preferences.splitRegex

    if splitRegex:

        for text in text_list:
            words = splitRegex( text )

            for word in words:

                if wordRegex( word ):
                    words_count += 1

    else:

        for text in text_list:
            words_count += len( text.split() )

    return words_count


def count_chars(text_list):
    char_count = 0

    if Preferences.char_ignore_whitespace:
        char_count = sum( sum( len( word ) for word in words.split() ) for words in text_list )

    else:
        char_count = sum( len( words ) for words in text_list )

    return char_count


def get_active_view():
    window = sublime.active_window()

    if window:
         return window.active_view()

    return None

