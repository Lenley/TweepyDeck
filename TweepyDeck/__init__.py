#!/usr/bin/env python


# Standard library imports
import getpass
import logging
import os.path
import time
from optparse import OptionParser

# PyGTK imports
import pygtk
pygtk.require('2.0')
import gobject
import gtk
import gtk.gdk
import gtk.glade

# TweepyDeck imports
from TweepyDeck import decorators
from TweepyDeck import timeline
from TweepyDeck import twitter
from TweepyDeck import util

if os.getenv('DEBUG'):
    logging.basicConfig(level=logging.DEBUG)

gobject.threads_init()

class Tweep(object):
    widget_tree = None
    last_status = None
    since_id = None

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def status_key(self, widget, event, **kwargs):
        if gtk.gdk.keyval_name(event.keyval) == 'Return':
            status = widget.get_text()
            if status and not status == self.last_status:
                self.last_status = status
                self.statusbar = 'Updating...'
                self.statusentry = ''
                self.api.update(status, callback=self._status_complete)
    
    def status_autocomplete(self, widget, event, **kwargs):
        if not gtk.gdk.keyval_name(event.keyval) == 'Tab':
            return False
        status = widget.get_text()
        parts = status.split(' ')
        if not parts:
            return False
        
        last = parts[-1].replace('@', '')
        if not last:
            return False
        for timeline in self.timelines:
            for user in timeline.users:
                if user.startswith(last):
                    parts[-1] = '@%s' % user
                    text = ' '.join(parts) 
                    widget.set_text(text)
                    widget.set_position(len(text))
                    return True
    
    def show_about(self, widget, **kwargs):
        dialog = self.widget_tree.get_widget('TweepyAboutDialog')
        if dialog:
            dialog.run()
            dialog.hide()

    @decorators.accessor
    def statusbar():
        doc = 'Set main window status bar'
        
        def fset(self, value):
            label = self.widget_tree.get_widget('TweepyStatusBar')
            if label:
                label.push(1, value)
        return locals()

    @decorators.accessor
    def statusentry():
        doc = 'Get/set the main window status entry textfield'

        def fget(self):
            entry = self.widget_tree.get_widget('StatusEntry')
            if entry:
                return label.get_text()
        def fset(self, value):
            entry = self.widget_tree.get_widget('StatusEntry')
            if entry:
                entry.set_text(value)
        return locals()
    
    def _status_complete(self, data, **kwargs):
        self.statusbar = 'Status last updated at %s' % util.readable_time()

    def login(self, button, **kwargs):
        dialog = self.widget_tree.get_widget('LoginDialog')
        login_entry = self.widget_tree.get_widget('UsernameEntry')
        pass_entry = self.widget_tree.get_widget('PasswordEntry')

        user, password = login_entry.get_text(), pass_entry.get_text()
        
        self.api = twitter.TwitterApi(user, password)


        self.friends = timeline.Timeline(self.widget_tree.get_widget('FriendsTreeView'), self.api)
        self.timelines.append(self.friends)
        self.replies = timeline.RepliesTimeline(self.widget_tree.get_widget('RepliesTreeView'), 
                        self.api)
        self.timelines.append(self.replies)

        #if searches:
        #    self.searches = timeline.SearchesTimeline(self.widget_tree.get_widget('SearchTreeView'), self.api, searches)
        #    self.timelines.append(self.searches)
        #else:
        #    self.widget_tree.get_widget('SearchScrolledWindow').destroy()
        self.widget_tree.get_widget('SearchScrolledWindow').hide()
    
        for t in self.timelines:
            t.start()

        dialog.destroy()


    def __init__(self, *args, **kwargs):
        self.timelines = []
        self.widget_tree = gtk.glade.XML('tweepydeck.glade')
        self.window = self.widget_tree.get_widget('TweepyMainWindow')
        self.window.connect('destroy', self.destroy)

        self._events = {
                'on_QuitMenuItem_activate' : self.destroy,
                'on_AboutMenuItem_activate' : self.show_about,
                'on_StatusEntry_key_release_event' : self.status_key,
                'on_StatusEntry_key_press_event' : self.status_autocomplete,
                'on_LoginCancelButton_clicked' : self.destroy,
                'on_LoginOkayButton_clicked' : self.login,
            }
        self.widget_tree.signal_autoconnect(self._events)



    def main(self):
        gtk.main()


def main():
    Tweep().main()

if __name__ == "__main__":
    main()

# vim: shiftwidth=4 tabstop=4 expandtab