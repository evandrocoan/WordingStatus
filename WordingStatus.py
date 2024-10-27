# reformatted/added spaces/icons to https://github.com/evandrocoan/WordingStatus
import sublime
import sublime_plugin

import re
import time
import threading

from math   	import ceil as ceil
from os.path	import basename

VIEW_SIZE_LIMIT	= 4194304

Pref                	= {}
g_sleepEvent        	= threading.Event()
g_is_already_running	= False


def plugin_unloaded():
  global g_is_already_running

  g_is_already_running = False
  subl_setting.clear_on_change('WordingStatus')

  for window in sublime.windows():
    for view in window.views():
      view.erase_status(Pref.status_name);


def plugin_loaded():
  global Pref
  global subl_setting

  subl_setting = sublime.load_settings('WordingStatus.sublime-settings')
  Pref.load();

  subl_setting.clear_on_change('WordingStatus')
  subl_setting.add_on_change(  'WordingStatus', lambda:Pref.load())

  WordingStatuses.setUpView(get_active_view()) # Initialize the WordingStatuses's countView attribute

  if not g_is_already_running:
    g_sleepEvent.set()
    sublime.set_timeout_async(configure_word_count, 5000) # Wait the Pref class to be loaded


def configure_word_count():
  """
    break/interrupt a time.sleep() in python
    https://stackoverflow.com/questions/5114292/break-interrupt-a-time-sleep-in-python """
  global g_is_already_running
  g_is_already_running = True

  g_sleepEvent.clear() # Reset the internal flag to false. Subsequently, threads calling wait() will block until set() is called to set the internal flag to true again.

  thread = threading.Thread(target=word_count_loop)
  thread.start()


def word_count_loop():
  mininum_time = 0.01
  default_time = 3.0

  while True:
    if not g_is_already_running: # Stops the thread when the plugin is reloaded or unloaded
      break

    if not Pref.is_already_running: # sleep time is adaptive, if takes more than `mininum_time` to calculate the word count, sleep_time becomes `elapsed_time*3`
      if g_sleepEvent.is_set(): # set g_sleepEvent._flag, a.k.a., g_sleepEvent.is_set() to False
        g_sleepEvent.clear()
        WordingStatuses.setUpView(WordingStatuses.activeView)

      WordingStatuses.doCounting()

    # print("word_count_loop, elapsed_time: %f microseconds" % (Pref.elapsed_time * 1000))
    g_sleepEvent.wait(Pref.elapsed_time*100 if Pref.elapsed_time > mininum_time else default_time)


class Pref():

  @staticmethod
  def load():
    Pref.elapsed_time           = 1.4
    Pref.is_already_running     = False

    Pref.wordRegex              = re.compile(subl_setting.get('word_regexp',r"^[^\w]?`*\w+[^\w]*$"), re.U)
    Pref.wordRegex              = Pref.wordRegex.match
    Pref.splitRegex             = subl_setting.get('word_split', None)

    if Pref.splitRegex:
      Pref.splitRegex           = re.compile(Pref.splitRegex, re.U)
      Pref.splitRegex           = Pref.splitRegex.findall

    Pref.status_name            = subl_setting.get('status_order_prefix', '') + 'WordCountStatus'

    Pref.enable_readtime        = subl_setting.get('enable_readtime'   , False)
    Pref.enable_count_lines     = subl_setting.get('enable_count_lines', False)
    Pref.enable_count_chars     = subl_setting.get('enable_count_chars', False)
    Pref.enable_count_pages     = subl_setting.get('enable_count_pages', False)
    Pref.enable_count_words     = subl_setting.get('enable_count_words', True)
    Pref.file_size_limit        = subl_setting.get('file_size_limit'   , VIEW_SIZE_LIMIT)

    Pref.enable_line_word_count = subl_setting.get('enable_line_word_count', False)
    Pref.enable_line_char_count = subl_setting.get('enable_line_char_count', False)

    Pref.readtime_wpm           = subl_setting.get('readtime_wpm'          , 200)
    Pref.words_per_page         = subl_setting.get('words_per_page'        , 300)
    Pref.char_ignore_whitespace = subl_setting.get('char_ignore_whitespace', True)
    Pref.whitelist_syntaxes     = subl_setting.get('whitelist_syntaxes'    , [])
    Pref.blacklist_syntaxes     = subl_setting.get('blacklist_syntaxes'    , [])
    Pref.strip                  = subl_setting.get('strip'                 , [])

    Pref.thousands_separator    = subl_setting.get('thousands_separator'   , ".")

    Pref.label_line             = subl_setting.get('label_line'        , " Lines"          )
    Pref.label_word             = subl_setting.get('label_word'        , " Words"          )
    Pref.label_char             = subl_setting.get('label_char'        , " Chars"          )
    Pref.label_word_in_line     = subl_setting.get('label_word_in_line', " Words in lines" )
    Pref.label_char_in_line     = subl_setting.get('label_char_in_line', " Chars in lines" )
    Pref.label_time             = subl_setting.get('label_time'        , " reading time"   )
    Pref.label_page             = subl_setting.get('label_page'        , "Page "           )

    Pref.page_count_mode_count_words = subl_setting.get('page_count_mode_count_words', True)


class WordingStatuses(sublime_plugin.ViewEventListener):
  countView     	= None
  activeView    	= None
  wordCountViews	= {}

  def on_close(self):
    view   	= self.view
    view_id	= view.id()

    if view_id in WordingStatuses.wordCountViews:
      del         WordingStatuses.wordCountViews[view_id]

  def on_selection_modified_async(self):
    view	= self.view

    if Pref.enable_count_words:
      selections = view.sel()

      for selection in selections:

        if len(selection):
          WordingStatuses.countView.is_text_selected = True
          return

      WordingStatuses.countView.is_text_selected = False

  def on_activated_async(self):
    view	= self.view
    # print("on_activated_async, view_id: %d" % view.id())
    WordingStatuses.activeView = view
    g_sleepEvent.set()

  @classmethod
  def doCounting(cls):
    countView = cls.countView

    if countView.view.change_count() != countView.change_count \
        or countView.is_text_selected:

      countView.startCounting()

  @classmethod
  def setUpView(cls, view):
    view_settings = view.settings()
    wordCountViews = cls.wordCountViews

    if view_settings.get('is_widget'):
      _view = get_active_view()

      if _view:
        view = _view
        view_settings = view.settings()

    syntax, is_enabled = cls.should_run_with_syntax(view_settings)
    view_id = view.id()

    # print("setUpView, view_id: %d" % view_id)
    if view_id in wordCountViews:
      wordCountView       	= wordCountViews[view_id]
      wordCountView.syntax	= syntax
      wordCountView.syntax	= is_enabled

    else:
      wordCountView          	= WordingStatusesView(view, syntax, is_enabled)
      wordCountViews[view_id]	= wordCountView

    cls.countView = wordCountView

  @staticmethod
  def should_run_with_syntax(view_settings):
    syntax	= view_settings.get('syntax')
    syntax	= basename(syntax).split('.')[0].lower() if syntax != None else "plain text"

    if len(Pref.blacklist_syntaxes) > 0:
      for white in Pref.blacklist_syntaxes:
        if white == syntax:
          return syntax, False

    if len(Pref.whitelist_syntaxes) > 0:
      for white in Pref.whitelist_syntaxes:
        if white == syntax:
          return syntax, True

      return syntax, False

    return syntax, True


class WordingStatusesView():

  def __init__(self, view, syntax, is_enabled):
    self.syntax          	= syntax
    self.is_enabled      	= is_enabled
    self.is_text_selected	= False

    # We need to set it to -1, because by default it starts on 0. Then we for an update when a view is first activated by `WordingStatuses::on_activated_async()`
    self.change_count  	= -1
    self.lines_contents	= []

    self.view    	= view
    self.contents	= []

    self.char_count	= 0
    self.word_count	= 0
    self.line_count	= 0

    self.word_count_line	= 0
    self.char_count_line	= 0

  def updateViewContents(self):
    view = self.view
    del self.contents[:]

    selections	= view.sel()
    view_size 	= view.size()

    if Pref.enable_line_char_count or Pref.enable_line_word_count:
      del self.lines_contents[:]

      for selection in selections:
        self.lines_contents.append(view.substr(view.line(selection.end())))

    file_size_limit	= Pref.file_size_limit
    is_limited     	= view_size > file_size_limit

    if is_limited:
      self.is_text_selected = False

    if self.is_text_selected:

      for selection in selections:
        self.contents.append(view.substr(selection))

    else:
      self.contents.append(view.substr(sublime.Region(0, file_size_limit if is_limited else view_size)))

  def startCounting(self):

    if not self.is_enabled:
      return

    Pref.start_time        	= time.perf_counter()
    Pref.is_already_running	= True

    view = self.view
    self.updateViewContents()

    if self.syntax and self.syntax in Pref.strip:

      for regular_expression in Pref.strip[self.syntax]:
        lines_count         	= len(self.contents      )
        lines_contents_count	= len(self.lines_contents)

        for selection_index in range(lines_count):
          self.contents      [selection_index] = re.sub(regular_expression, '', self.contents      [selection_index])

        for selection_index in range(lines_contents_count):
          self.lines_contents[selection_index] = re.sub(regular_expression, '', self.lines_contents[selection_index])

    if Pref.enable_count_lines:
      self.line_count      = view.rowcol(view.size())[0] + 1
    if Pref.enable_count_words:
      self.word_count      = count_words(self.contents      )
    if Pref.enable_count_chars:
      self.char_count      = count_chars(self.contents      )
    if Pref.enable_line_char_count:
      self.char_count_line = count_chars(self.lines_contents)
    if Pref.enable_line_word_count:
      self.word_count_line = count_words(self.lines_contents)

    self.displayCountResults()

  def displayCountResults(self):
    display(self.view, self.word_count, self.char_count, self.line_count, self.word_count_line, self.char_count_line)

    Pref.elapsed_time      	= time.perf_counter() - Pref.start_time
    Pref.is_already_running	= False


def display(view, word_count, char_count, line_count, word_count_line, char_count_line):
  status 	= []
  seconds	= int(word_count % Pref.readtime_wpm / (Pref.readtime_wpm / 60))
  k_sep  	= Pref.thousands_separator

  out_line,pos_line,out_word,pos_word,out_char,out_word_line,pos_word_line = '','','','','','',''
  if line_count:
    out_line	= "{:,}{}".format(line_count	,Pref.label_line	).replace(',',k_sep)
    pos_line	= ' '
  if word_count:
    out_word	= "{:,}{}".format(word_count	,Pref.label_word	).replace(',',k_sep)
    pos_word	= ' '
  if char_count:
    out_char	= "{:,}{}".format(char_count	,Pref.label_char	).replace(',',k_sep)

  if word_count_line:
    out_word_line	= "{:,}{}".format(word_count_line,Pref.label_word_in_line	).replace(',',k_sep)
    pos_word_line	= ' '
  if char_count_line:
    out_char_line	= "{:,}{}".format(char_count_line,Pref.label_char_in_line	).replace(',',k_sep)

  if (line_count      > 0 or
      word_count      > 0 or
      char_count      > 0):
    status.append(out_line +pos_line+ out_word +pos_word+ out_char)
  if (word_count_line > 0 or
      char_count_line > 0):
    status.append(out_word_line +pos_word_line+ out_char_line)

  if Pref.enable_count_pages and word_count > 0:
    if not Pref.page_count_mode_count_words or Pref.words_per_page < 1:
      visible      	= view.visible_region()
      rows_per_page	=      (view.rowcol(visible.end())[0]) - (view.rowcol(visible.begin())[0])
      pages        	= ceil((view.rowcol(view.size()-1)[0] + 1) /  rows_per_page)
      current_line 	=       view.rowcol(view.sel()[0].begin())[0]+1
      current_page 	= ceil(current_line / rows_per_page)
    else:
      pages       	= ceil(word_count / Pref.words_per_page)
      rows        	= view.rowcol(view.size()-1)[0] + 1
      current_line	= view.rowcol(view.sel()[0].begin())[0]+1
      current_page	= ceil((current_line / Pref.words_per_page) / (rows / Pref.words_per_page))

    if pages > 1:
      status.append("{}{:,}/{:,}".format(Pref.label_page, current_page, pages).replace(',',k_sep))

  if Pref.enable_readtime and seconds >= 1:
    minutes = int(word_count / Pref.readtime_wpm)
    status.append("~{:,}m {:,}s{}".format( minutes, seconds, Pref.label_time).replace(',',k_sep))

  status_text = ', '.join(status)
  view.set_status(Pref.status_name, status_text)
  # print("view: %d, Setting status to: " % view.id() + status_text)


def count_words(text_list):
  words_count = 0

  wordRegex 	= Pref.wordRegex
  splitRegex	= Pref.splitRegex

  if splitRegex:
    for text in text_list:
      words = splitRegex(text)
      for word in words:
        if wordRegex(word):
          words_count += 1
  else:
    for text in text_list:
      words_count += len(text.split())

  return words_count


def count_chars(text_list):
  char_count = 0

  if Pref.char_ignore_whitespace:
    char_count = sum(sum(len(word) for word in words.split()) for words in text_list)
  else:
    char_count = sum(len(words) for words in text_list)

  return char_count


def get_active_view():
  window = sublime.active_window()
  if window:
     return window.active_view()

  return None
