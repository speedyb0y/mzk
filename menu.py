import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

UI_INFO = """
<ui>
  <menubar name='MenuBar'>
    <menu action='FileMenu'>
      <menu action='A0'>
		<menuitem action='A0.X' />
        <menu action='A0.B0'>
			<menuitem action='A0.B0.X' />
            <menuitem action='A0.B0.C0' />
            <menuitem action='A0.B0.C1' />
            <menuitem action='A0.B0.C2' />
            <menuitem action='A0.B0.C3' />
            <menuitem action='A0.B0.C4' />
            <menuitem action='A0.B0.C5' />
        </menu>
        <menu action='A0.B1'>
			<menuitem action='A0.B1.X' />
            <menuitem action='A0.B1.C0' />
            <menuitem action='A0.B1.C1' />
            <menuitem action='A0.B1.C2' />
            <menuitem action='A0.B1.C3' />
            <menuitem action='A0.B1.C4' />
            <menuitem action='A0.B1.C5' />
        </menu>
        <menu action='A0.B2'>
			<menuitem action='A0.B2.X' />
            <menuitem action='A0.B2.C0' />
            <menuitem action='A0.B2.C1' />
            <menuitem action='A0.B2.C2' />
            <menuitem action='A0.B2.C3' />
            <menuitem action='A0.B2.C4' />
            <menuitem action='A0.B2.C5' />
        </menu>
      </menu>
      <menu action='A1'>
        <menuitem action='A1.X' />
        <menu action='A1.B0'>
            <menuitem action='A1.B0.X' />
            <menuitem action='A1.B0.C0' />
            <menuitem action='A1.B0.C1' />
            <menuitem action='A1.B0.C2' />
            <menuitem action='A1.B0.C3' />
            <menuitem action='A1.B0.C4' />
            <menuitem action='A1.B0.C5' />
        </menu>
        <menu action='A1.B1'>
            <menuitem action='A1.B1.X' />
            <menuitem action='A1.B1.C0' />
            <menuitem action='A1.B1.C1' />
            <menuitem action='A1.B1.C2' />
            <menuitem action='A1.B1.C3' />
            <menuitem action='A1.B1.C4' />
            <menuitem action='A1.B1.C5' />
        </menu>
      </menu>
      <separator />
      <menuitem action='FileQuit' />
    </menu>
    <menu action='ChoicesMenu'>
      <menuitem action='ChoiceOne'/>
      <menuitem action='ChoiceTwo'/>
      <separator />
      <menuitem action='ChoiceThree'/>
    </menu>
  </menubar>
  <toolbar name='ToolBar'>
    <toolitem action='FileNewStandard' />
    <toolitem action='FileQuit' />
  </toolbar>
</ui>
"""


class MenuExampleWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Menu Example")

        self.set_default_size(200, 200)

        action_group = Gtk.ActionGroup(name="my_actions")

        self.add_file_menu_actions(action_group)
        self.add_choices_menu_actions(action_group)

        uimanager = self.create_ui_manager()
        uimanager.insert_action_group(action_group)

        menubar = uimanager.get_widget("/MenuBar")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(menubar, False, False, 0)

        toolbar = uimanager.get_widget("/ToolBar")
        box.pack_start(toolbar, False, False, 0)

        eventbox = Gtk.EventBox()
        eventbox.connect("button-press-event", self.on_button_press_event)
        box.pack_start(eventbox, True, True, 0)

        label = Gtk.Label(label="Right-click to see the popup menu.")
        eventbox.add(label)

        self.popup = uimanager.get_widget("/PopupMenu")

        self.add(box)

    def add_file_menu_actions(self, action_group):

        action_filemenu = Gtk.Action(name="FileMenu", label="File")
        action_group.add_action(action_filemenu)

        action_filenewmenu = Gtk.Action(name="FileNew", stock_id=Gtk.STOCK_NEW)
        action_group.add_action(action_filenewmenu)

        action_group.add_actions(
            [
                ("A0", None, "A0", None, "Creates a new foo",         self.on_menu_file_new_generic),
                ("A1", None, "A1", None, "Create new goo",    self.on_menu_file_new_generic),
                ("A2", None, "A2", None, "Create new goo",    self.on_menu_file_new_generic),


                ("A0.B0", None, "B0", None, "",    self.on_menu_file_new_generic),
                ("A0.B2", None, "B2", None, "",    self.on_menu_file_new_generic),
                ("A1.B0", None, "B0", None, "",    self.on_menu_file_new_generic),
                ("A1.B1", None, "B1", None, "",    self.on_menu_file_new_generic),
                ("A1.B2", None, "B2", None, "",    self.on_menu_file_new_generic),
                ("A2.B0", None, "B0", None, "",    self.on_menu_file_new_generic),
                ("A2.B1", None, "B1", None, "",    self.on_menu_file_new_generic),
                ("A2.B2", None, "B2", None, "",    self.on_menu_file_new_generic),

#                ("A0.B0.X", None, " ... ", None, "",    self.on_menu_file_new_generic),
                ("A0.B1.X", None, " ... ", None, "",    self.on_menu_file_new_generic),
                ("A0.B2.X", None, " ... ", None, "",    self.on_menu_file_new_generic),
                ("A1.B0.X", None, " ... ", None, "",    self.on_menu_file_new_generic),
                ("A1.B1.X", None, " ... ", None, "",    self.on_menu_file_new_generic),
                ("A1.B2.X", None, " ... ", None, "",    self.on_menu_file_new_generic),

            ]
        )

		# SE UM TEM SUBS, ELE É UM ROOT
        for nome in ('A0.X', 'A1.X', 'A0.B0.X'):
            este = Gtk.ToggleAction(name=nome, label="")
            este.connect("toggled", self.on_menu_choices_toggled)
            action_group.add_action(este)

		# SE UM NAO TEM SUBS, ENTAO ELE EH UM ITEM
        for nome in ('A0.B1',):
            este = Gtk.ToggleAction(name=nome, label=nome.split('.')[-1])
            este.connect("toggled", self.on_menu_choices_toggled)
            action_group.add_action(este)

        action_filequit = Gtk.Action(name="FileQuit", stock_id=Gtk.STOCK_QUIT)
        action_filequit.connect("activate", self.on_menu_file_quit)
        action_group.add_action(action_filequit)

    def add_choices_menu_actions(self, action_group):
        action_group.add_action(Gtk.Action(name="ChoicesMenu", label="Choices"))

        action_group.add_radio_actions(
            [
                ("ChoiceOne", None, "One", None, None, 1),
                ("ChoiceTwo", None, "Two", None, None, 2),
            ],
            1,
            self.on_menu_choices_changed,
        )

        three = Gtk.ToggleAction(name="ChoiceThree", label="Three")
        three.connect("toggled", self.on_menu_choices_toggled)
        action_group.add_action(three)

    def create_ui_manager(self):
        uimanager = Gtk.UIManager()

        # Throws exception if something went wrong
        uimanager.add_ui_from_string(UI_INFO)

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        self.add_accel_group(accelgroup)
        return uimanager

    def on_menu_file_new_generic(self, widget):
        print("A File|New menu item was selected.")

    def on_menu_file_quit(self, widget):
        Gtk.main_quit()

    def on_menu_others(self, widget):
        print("Menu item " + widget.get_name() + " was selected")

    def on_menu_choices_changed(self, widget, current):
        print(current.get_name() + " was selected.")

    def on_menu_choices_toggled(self, widget):
        if widget.get_active():
            print(widget.get_name() + " activated")
        else:
            print(widget.get_name() + " deactivated")

    def on_button_press_event(self, widget, event):
        # Check if right mouse button was preseed
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self.popup.popup(None, None, None, None, event.button, event.time)
            return True  # event has been handled


window = MenuExampleWindow()
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()
