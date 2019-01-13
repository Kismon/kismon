from gi.repository import Gtk


class ChannelWindow:
    def __init__(self, sources, client_thread, parent):
        self.sources = sources
        self.client_thread = client_thread
        self.changes = {}
        self.widgets = {}

        self.gtkwin = Gtk.Window()
        self.gtkwin.set_transient_for(parent)
        self.gtkwin.set_position(Gtk.WindowPosition.CENTER)
        self.gtkwin.set_default_size(320, 240)
        self.gtkwin.set_title("Configure Channel")

        self.vbox = None
        self.sources_list = None
        self.init_box()

    def init_box(self):
        vbox = Gtk.VBox()
        vbox.set_property('margin', 5)

        self.sources_list = Gtk.VBox()
        sources_list_scroll = Gtk.ScrolledWindow()
        sources_list_scroll.add(self.sources_list)
        sources_list_scroll.get_children()[0].set_shadow_type(Gtk.ShadowType.NONE)
        sources_list_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(sources_list_scroll, True, True, 0)

        for uuid in self.sources:
            self.widgets[uuid] = {}
            source = self.sources[uuid]
            frame = Gtk.Frame()
            frame.set_label(source['name'])
            self.sources_list.pack_start(frame, False, False, 0)

            table = Gtk.Table(n_rows=3, n_columns=3)
            frame.add(table)
            hop_button = Gtk.RadioButton.new_with_label_from_widget(None, 'Hop')
            if source["hop"] > 0:
                hop_button.clicked()
            hop_button.connect("clicked", self.on_change_mode, uuid, "hop")
            hop_button.set_property("xalign", 0)
            hop_button.set_property("yalign", 0.4)
            table.attach(hop_button, 0, 1, 0, 1)

            field = Gtk.SpinButton()
            field.set_numeric(True)
            field.set_max_length(3)
            field.set_increments(1, 10)
            field.set_range(1, 100)
            field.set_value(source["hop_rate"])
            if source["hop"] == 0:
                field.set_sensitive(False)
            self.widgets[uuid]["hop"] = field
            field.connect("changed", self.on_change_value, uuid, "hop")
            table.attach(field, 1, 2, 0, 1, xoptions=Gtk.AttachOptions.SHRINK)

            label = Gtk.Label(label="rate")
            label.set_justify(Gtk.Justification.LEFT)
            label.set_property("xalign", 0.1)
            label.set_property("yalign", 0.5)
            table.attach(label, 2, 3, 0, 1, xoptions=Gtk.AttachOptions.FILL)

            lock_button = Gtk.RadioButton.new_with_label_from_widget(hop_button, "Lock")
            if source["hop"] == 0:
                lock_button.clicked()
            lock_button.connect("clicked", self.on_change_mode, uuid, "lock")
            lock_button.set_property("xalign", 0)
            lock_button.set_property("yalign", 0.4)
            table.attach(lock_button, 0, 1, 1, 2)

            field = Gtk.SpinButton()
            field.set_numeric(True)
            field.set_max_length(3)
            field.set_increments(1, 10)
            field.set_range(1, 100)
            if source["hop"] == 0:
                field.set_value(int(source["channel"]))
            else:
                field.set_value(1)
                field.set_sensitive(False)

            self.widgets[uuid]["lock"] = field
            field.connect("changed", self.on_change_value, uuid, "lock")
            table.attach(field, 1, 2, 1, 2, xoptions=Gtk.AttachOptions.SHRINK)

            label = Gtk.Label(label="channel")
            label.set_justify(Gtk.Justification.FILL)
            label.set_property("xalign", 0.1)
            label.set_property("yalign", 0.5)
            table.attach(label, 2, 3, 1, 2, xoptions=Gtk.AttachOptions.FILL)

        button_box = Gtk.HButtonBox()
        vbox.pack_end(button_box, False, False, 0)

        cancel_button = Gtk.Button.new_with_mnemonic('_Cancel')
        cancel_button.connect("clicked", self.on_cancel)
        button_box.add(cancel_button)

        apply_button = Gtk.Button.new_with_mnemonic('_Apply')
        apply_button.connect("clicked", self.on_apply)
        button_box.add(apply_button)

        update_button = Gtk.Button.new_with_mnemonic('_Refresh')
        update_button.connect("clicked", self.on_refresh)
        button_box.add(update_button)

        if self.vbox:
            self.gtkwin.remove(self.vbox)
        self.vbox = vbox

        self.gtkwin.add(vbox)
        self.gtkwin.show_all()

    def on_change_mode(self, widget, uuid, mode):
        if not widget.get_active():
            return

        self.changes[uuid] = mode
        self.widgets[uuid][mode].set_sensitive(True)
        if mode == "lock":
            self.widgets[uuid]["hop"].set_sensitive(False)
        else:
            self.widgets[uuid]["lock"].set_sensitive(False)

    def on_change_value(self, widget, uuid, mode):
        self.changes[uuid] = mode

    def on_apply(self, widget):
        for uuid in self.changes:
            mode = self.changes[uuid]
            value = int(self.widgets[uuid][mode].get_value())
            self.client_thread.client.set_channel(uuid, mode, value)

        self.gtkwin.destroy()

    def on_cancel(self, widget):
        self.gtkwin.destroy()

    def on_refresh(self, widget):
        self.init_box()
