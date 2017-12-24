
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

    # Initialize the WordsCount's countView attribute
    WordsCount.setUpView( get_active_view() )

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

        Preferences.readtime_wpm           = sublime_settings.get('readtime_wpm', 200)
        Preferences.words_per_page         = sublime_settings.get('words_per_page', 300)
        Preferences.char_ignore_whitespace = sublime_settings.get('char_ignore_whitespace', True)

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

            for selection in selections:

                if len( selection ):
                    WordsCount.countView.is_text_selected = True
                    return

            WordsCount.countView.is_text_selected = False

    def on_activated_async(self, view):
        # print( "on_activated_async, view_id: %d" % view.id() )
        WordsCount.setUpView( view )
        WordsCount.doCounting()

    @staticmethod
    def setUpView(view):
        view_settings  = view.settings()
        wordCountViews = WordsCount.wordCountViews

        if view_settings.get('is_widget'):
            view = get_active_view()

        view_id = view.id()
        # print( "setUpView, view_id: %d" % view_id )

        if view_id not in wordCountViews:
            wordCountViews[view_id] = WordCountView( view )

        WordsCount.countView = wordCountViews[view_id]

    @staticmethod
    def doCounting():
        countView = WordsCount.countView

        if countView.view.change_count() != countView.change_count \
                or countView.is_text_selected:

            countView.startCounting()


class WordCountView():

    def __init__(self, view):
        self.is_text_selected = False

        # We need to set it to -1, because by default it starts on 0. Then we for an update when a
        # view is first activated by `WordsCount::on_activated_async()`
        self.change_count = -1

        self.view    = view
        self.content = ""

        self.char_count = 0
        self.word_count = 0
        self.line_count = 0

    def updateViewContents(self):
        view = self.view

        if self.is_text_selected:
            contents = []
            selections = view.sel()

            for selection in selections:
                contents.append( view.substr( selection ) )

            self.content = " ".join( contents )

        else:
            self.content = view.substr( sublime.Region( 0, view.size() ) )

    def startCounting(self):
        Preferences.start_time = time.perf_counter()
        Preferences.is_already_running = True

        view = self.view
        self.updateViewContents()

        if Preferences.enable_count_words:
            self.word_count = count_words( self.content )

        if Preferences.enable_count_chars:

            if Preferences.char_ignore_whitespace:
                self.char_count = len( ''.join( self.content.split() ) )

            else:
                self.char_count = len( self.content )

        if Preferences.enable_count_lines:

            if self.is_text_selected:
                self.line_count = 0

            else:
                self.line_count = view.rowcol( view.size() )[0] + 1

        self.displayCountResults()

    def displayCountResults(self):
        display( self.view, self.word_count, self.char_count, self.line_count )

        Preferences.elapsed_time = time.perf_counter() - Preferences.start_time
        Preferences.is_already_running = False


def display(view, word_count, char_count, line_count):
    status  = []
    minutes = int( word_count / Preferences.readtime_wpm )
    seconds = int( word_count % Preferences.readtime_wpm / ( Preferences.readtime_wpm / 60 ) )

    if line_count > 1:
        status.append( '%d Lines' % line_count )

    if Preferences.enable_count_words:
        status.append( '%d Words' % word_count )

    if char_count > 1 \
            and line_count > 1:

        status.append( '%d Chars' % char_count )

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


def count_words(text):
    wordRegex  = Preferences.wordRegex
    splitRegex = Preferences.splitRegex

    if splitRegex:
        words = len( [ 1 for x in splitRegex(text) if not x.isdigit() and wordRegex(x) ] )

    else:
        words = len( [ 1 for x in text.split() if not x.isdigit() and wordRegex(x) ] )

    return words


def get_active_view():
    window = sublime.active_window()

    if window:
         return window.active_view()

    return None

