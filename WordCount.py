import sublime, sublime_plugin, re
import time
import threading
from math import ceil as ceil
from os.path import basename

Preferences      = {}
sublime_settings = {}

default_word_count_settings = {'modified':True, 'selection':True, 'syntax':'plain text','changes':-1,'status':-1}


def plugin_loaded():
	global sublime_settings, Preferences
	sublime_settings = sublime.load_settings('WordCount.sublime-settings')

	Preferences = Preferences()
	Preferences.load();

	sublime_settings.clear_on_change('reload')
	sublime_settings.add_on_change('reload', lambda:Preferences.load())

	if not 'running_word_count_loop' in globals():
		global running_word_count_loop
		running_word_count_loop = True

		thread = threading.Thread(target=word_count_loop)
		thread.start()


class Preferences:
	def load(self):
		Preferences.view                   = False
		Preferences.elapsed_time           = 0.4
		Preferences.running                = False

		Preferences.wrdRx                  = re.compile(sublime_settings.get('word_regexp', "^[^\w]?`*\w+[^\w]*$"), re.U)
		Preferences.wrdRx                  = Preferences.wrdRx.match
		Preferences.splitRx                = sublime_settings.get('word_split', None)
		if Preferences.splitRx:
			Preferences.splitRx            = re.compile(Preferences.splitRx, re.U)
			Preferences.splitRx            = Preferences.splitRx.findall

		Preferences.enable_live_count      = sublime_settings.get('enable_live_count', True)
		Preferences.enable_readtime        = sublime_settings.get('enable_readtime', False)
		Preferences.enable_line_word_count = sublime_settings.get('enable_line_word_count', False)
		Preferences.enable_line_char_count = sublime_settings.get('enable_line_char_count', False)
		Preferences.enable_count_lines     = sublime_settings.get('enable_count_lines', False)
		Preferences.enable_count_chars     = sublime_settings.get('enable_count_chars', False)
		Preferences.enable_count_pages     = sublime_settings.get('enable_count_pages', True)

		Preferences.words_per_page         = sublime_settings.get('words_per_page', 300)
		Preferences.page_count_mode_count_words = sublime_settings.get('page_count_mode_count_words', True)
		Preferences.char_ignore_whitespace = sublime_settings.get('char_ignore_whitespace', True)
		Preferences.readtime_wpm           = sublime_settings.get('readtime_wpm', 200)
		Preferences.whitelist              = [x.lower() for x in sublime_settings.get('whitelist_syntaxes', []) or []]
		Preferences.blacklist              = [x.lower() for x in sublime_settings.get('blacklist_syntaxes', []) or []]
		Preferences.strip                  = sublime_settings.get('strip', [])

		for window in sublime.windows():

			for view in window.views():

				view.erase_status('WordCount');
				view.settings().erase('WordCount')


class WordCount(sublime_plugin.EventListener):

	def should_run_with_syntax(self, view):
		view_settings = view.settings()

		syntax = view_settings.get('syntax')
		syntax = basename(syntax).split('.')[0].lower() if syntax != None else "plain text"

		wordCountSettings = view_settings.get('WordCount', default_word_count_settings)
		wordCountSettings['syntax'] = syntax
		view_settings.set('WordCount', wordCountSettings)

		if len(Preferences.blacklist) > 0:

			for white in Preferences.blacklist:

				if white == syntax:
					view.erase_status('WordCount');
					return False

		if len(Preferences.whitelist) > 0:

			for white in Preferences.whitelist:

				if white == syntax:
					return True

			view.erase_status('WordCount');
			return False

		return True

	def on_activated_async(self, view):
		self.asap(view)

	def on_post_save_async(self, view):
		self.asap(view)

	def on_modified_async(self, view):
		view_settings     = view.settings()
		wordCountSettings = view_settings.get('WordCount', default_word_count_settings)

		if view_settings:
			wordCountSettings['modified'] = True
			view_settings.set('WordCount', wordCountSettings)

	def on_selection_modified_async(self, view):
		view_settings     = view.settings()
		wordCountSettings = view_settings.get('WordCount', default_word_count_settings)

		wordCountSettings['selection'] =  True
		view_settings.set('WordCount', wordCountSettings)

	def on_close(self, view):
		Preferences.view = False

	def asap(self, view):
		Preferences.view = view
		Preferences.elapsed_time = 0.4
		sublime.set_timeout(lambda:WordCount().run(True), 0)

	def run(self, asap = False):
		if not Preferences.view:
			self.guess_view()

		else:
			view = Preferences.view
			view_settings = view.settings()
			wordCountSettings = view_settings.get('WordCount', default_word_count_settings)

			if view_settings.get('is_widget') or not wordCountSettings: # (if not wordCountSettings)WTF, happens when closing a view
				self.guess_view()

			else:

				if (wordCountSettings['modified'] or wordCountSettings['selection']) and (Preferences.running == False or asap) and self.should_run_with_syntax(view):
					sel = view.sel()

					if sel:

						if len(sel) == 1 and sel[0].empty():

							if not Preferences.enable_live_count or view.size() > 10485760:
								view.erase_status('WordCount')

							elif view.change_count() != wordCountSettings['changes']:

								wordCountSettings['changes'] = view.change_count()
								#  print('running:'+str(view.change_count()))
								WordCountThread(view, [view.substr(sublime.Region(0, view.size()))], view.substr(view.line(view.sel()[0].end())), False).start()

							else:
								# print('running from cache:'+str(view.change_count()))
								view.set_status('WordCount', self.makePlural('Word', wordCountSettings['count'] ))
						else:

							try:
								WordCountThread(view, [view.substr(sublime.Region(sublime_settings.begin(), sublime_settings.end())) for sublime_settings in sel], view.substr(view.line(view.sel()[0].end())), True).start()
							except:
								pass

						wordCountSettings['modified'] = False
						wordCountSettings['selection'] = False
						view_settings.set('WordCount', wordCountSettings)


	def guess_view(self):
		if sublime.active_window() and sublime.active_window().active_view():
			Preferences.view = sublime.active_window().active_view()

	def display(self, view, on_selection, word_count, char_count, word_count_line, char_count_line):

		m = int(word_count / Preferences.readtime_wpm)
		s = int(word_count % Preferences.readtime_wpm / (Preferences.readtime_wpm / 60))

		status = []

		if word_count:
			status.append(self.makePlural('Word', word_count))

		if Preferences.enable_count_chars and char_count > 0:
			status.append(self.makePlural('Char', char_count))

		if Preferences.enable_line_word_count and word_count_line > 1:
			status.append( "%d Words in Line" % (word_count_line))

		if Preferences.enable_line_char_count and char_count_line > 1:
			status.append("%d Chars in Line" % (char_count_line))

		if Preferences.enable_count_lines:
			lines = (view.rowcol(view.size())[0] + 1)

			if lines > 1:
				status.append('%d Lines' % (view.rowcol(view.size())[0] + 1))

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

		if Preferences.enable_readtime and s >= 1:
			status.append("~%dm %ds reading time" % (m, s))

		view.set_status('WordCount', ', '.join(status))

	def makePlural(self, word, count):
		return "%s %s%s" % (count, word, ("s" if count != 1 else ""))


class WordCountThread(threading.Thread):

	def __init__(self, view, content, content_line, on_selection):
		threading.Thread.__init__(self)
		self.view = view
		self.content = content
		self.content_line = content_line
		self.on_selection = on_selection

		self.char_count = 0
		self.word_count_line = 0
		self.chars_in_line = 0

		wordCountSettings = view.settings().get('WordCount', default_word_count_settings)
		self.syntax = wordCountSettings['syntax']

	def run(self):
		# print ('running:'+str(time.time()))
		Preferences.running = True

		if self.syntax and self.syntax in Preferences.strip:
			for item in Preferences.strip[self.syntax]:
				for k in range(len(self.content)):
					self.content[k] = re.sub(item, '', self.content[k])
				self.content_line = re.sub(item, '', self.content_line)

		self.word_count = sum([self.count(region) for region in self.content])

		if Preferences.enable_count_chars:
			if Preferences.char_ignore_whitespace:
				self.char_count = sum([len(''.join(region.split())) for region in self.content])
			else:
				self.char_count = sum([len(region) for region in self.content])

		if Preferences.enable_line_word_count:
			self.word_count_line = self.count(self.content_line)

		if Preferences.enable_line_char_count:
			if Preferences.char_ignore_whitespace:
				self.chars_in_line = len(''.join(self.content_line.split()))
			else:
				self.chars_in_line = len(self.content_line)

		if not self.on_selection:
			view_settings = self.view.settings()
			wordCountSettings = view_settings.get('WordCount', default_word_count_settings)
			wordCountSettings['count'] = self.word_count
			view_settings.set('WordCount', wordCountSettings)

		sublime.set_timeout(lambda:self.on_done(), 0)

	def on_done(self):
		try:
			WordCount().display(self.view, self.on_selection, self.word_count, self.char_count, self.word_count_line, self.chars_in_line)
		except:
			pass
		Preferences.running = False

	def count(self, content):

		# begin = time.time()

		#=====1
		# wrdRx = Preferences.wrdRx
		# """counts by counting all the start-of-word characters"""
		# # regex to find word characters
		# matchingWrd = False
		# words = 0
		# space_symbols = [' ', '\r', '\n']
		# for ch in content:
		# # 	# test if this char is a word char
		# 	isWrd = ch not in space_symbols
		# 	if isWrd and not matchingWrd:
		# 		words = words + 1
		# 		matchingWrd = True
		# 	if not isWrd:
		# 		matchingWrd = False

		#=====2
		wrdRx = Preferences.wrdRx
		splitRx = Preferences.splitRx

		if splitRx:
			words = len([1 for x in splitRx(content) if not x.isdigit() and wrdRx(x)])

		else:
			words = len([1 for x in content.replace("'", '').replace('—', ' ').replace('–', ' ').replace('-', ' ').split()
			            if not x.isdigit() and wrdRx(x)])

		# Preferences.elapsed_time = end = time.time() - begin;
		# print ('Benchmark: '+str(end))

		return words


def word_count_loop():
	word_count = WordCount().run

	while True:
		# sleep time is adaptive, if takes more than 0.4 to calculate the word count
		# sleep_time becomes elapsed_time*3
		if Preferences.running == False:
			sublime.set_timeout(lambda:word_count(), 0)
		time.sleep((Preferences.elapsed_time*3 if Preferences.elapsed_time > 0.4 else 0.4))

