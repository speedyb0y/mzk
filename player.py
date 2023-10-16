import sys
import time
import mpv

player = mpv.MPV()
#player.play('/mnt/CONVERTED/J644ag9HCN.flac')
#time.sleep(30)
#player.wait_for_playback()

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

#
GRUPOS = (

    ('lang', (
        'portugues', 'french', 'english', 'arabic',
        'filipino', 'russo', 'espanhol', 'chines', 'japonês', 'germany', 'indian', 'tailand',
        'vietinamita', 'italiano', 'noruegues', 'hebraico', 'grego', 'latin', 'sanscript', 'egipicy'
    )),

    ('activity', (
        'run', 'fight', 'war', 'sex', 'namorar', 'romantic-dinner', 'sleep',
        'study', 'work', 'meditation', 'healing',
    )),

    ('genre', (
        'rock', 'pop', 'jazz', 'samba', 'bossa-nova', 'mpb', 'rock.christian',
        'classical', 'classical.piano', 'classical.violin', 'bassdrive', 'hip-hop',
        'new-age', 'punk', 'electronic', 'electronic.boris', 'opera', 'rock.castle',
        'electronic.blitz', 'nasheed',
    )),

    ('artist', (
        'legiao-urbana', 'staind', 'michelle-branch',
        'miss-monique', 'hanna',
    )),

    ('feel', (
        'love', 'happy', 'sad', 'calm', 'peace', 'concentrated',
        'determined', 'depressed', 'rage',
    )),

    ('voice', (
        'mute', 'single', 'double', 'group',
        'female', 'male',        
    )),

    ('culture', (
        'brazil', 'slav', 'arabian',
    ))
)

PlsCodes = tuple(sorted( f'{gName}.{gCode}'
    for gName, gCodes in GRUPOS
        for gCode in gCodes
))

PlsMap = { code: i for i, code in enumerate(PlsCodes) }

class MyWindow(Gtk.Window):
    def __init__(self):

        super().__init__(title="Hello World")

        lr = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        v1 = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        v2 = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        v3 = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)

        lr.set_wide_handle(True)
        v1.set_wide_handle(True)
        v2.set_wide_handle(True)
        v3.set_wide_handle(True)

        playlists = Gtk.Label(label='PLAYLISTS')
        currents = Gtk.Label(label='CURRENTS')
        songs = Gtk.Label(label='SONGS')

        # PUT THINGS ON STACK
        tagsStack = Gtk.Stack()

        # TAGS
        for gName, gPrefix, gCodes in GRUPOS

            lines = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

            line = None

            for gStr, gID in gDic.items():
                if langID % 4 == 0:
                    line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                    lines.pack_start(line, expand=True, fill=True, padding=0)
                but = Gtk.ToggleButton.new_with_label(langStr)
                but.connect('toggled', self.tag_toggled, gMap, gID)
                line.pack_start(but, expand=True, fill=True, padding=0)
                        
            tagsStack.add_titled(tags0, 'tags.activity', 'ACTIVITY')

        # SWITCH REFERS TO STACK
        tagsSwitcher = Gtk.StackSwitcher()
        tagsSwitcher.set_homogeneous(True)
        tagsSwitcher.set_stack(tagsStack)

        tagsNotebook = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        tagsNotebook.set_homogeneous(False)
        tagsNotebook.pack_start(tagsStack, expand=True, fill=True, padding=0)               
        tagsNotebook.pack_start(tagsSwitcher, expand=False, fill=True, padding=0)

        # PLAYBACK CONTROL
        pcontrols = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)

        pcontrols.prev = Gtk.Button(label="<-")
        pcontrols.play = Gtk.Button(label=">")
        pcontrols.next = Gtk.Button(label="->")

        pcontrols.prev.connect("clicked", self.prev_clicked)
        pcontrols.play.connect("clicked", self.play_clicked)
        pcontrols.next.connect("clicked", self.next_clicked)

        pcontrols.pack_start(pcontrols.prev, True, True, 0)
        pcontrols.pack_start(pcontrols.play, True, True, 0)
        pcontrols.pack_start(pcontrols.next, True, True, 0)

        self.add(lr)
        lr.add1(playlists)
        lr.add2(v1)
        v1.add1(songs)
        v1.add2(v2)
        v2.add1(currents)
        v2.add2(v3)
        v3.add1(pcontrols)
        v3.add2(tagsNotebook)

        self.currents = currents
        self.songs = songs
        self.playlists = playlists
        self.pcontrols = pcontrols
        self.tags = tagsStack
        self.lr = lr
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

    def prev_clicked (self, widget):
        print("PREVIOUS")

    def next_clicked (self, widget):
        print("NEXT")

    def play_clicked (self, widget):
        print("PLAY")

    def tag_toggled (self, but, grupo, i):
        print(self, but, grupo, i)

win = MyWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
