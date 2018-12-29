from gi.repository import Gtk

class DatasourcesWindow:
    def __init__(self, client_thread, parent):
        self.gtkwin = Gtk.Window()
        self.gtkwin.set_transient_for(parent)
        self.gtkwin.set_modal(True)
        self.gtkwin.set_position(Gtk.WindowPosition.CENTER)
        self.gtkwin.set_default_size(480, 240)
        self.gtkwin.set_title("Manage Datasources")

        self.client_thread = client_thread

        self.widget = None
        self.init_box()

    def init_box(self):
        table = Gtk.Grid()
        sources_list_scroll = Gtk.ScrolledWindow()
        sources_list_scroll.add(table)
        sources_list_scroll.get_children()[0].set_shadow_type(Gtk.ShadowType.NONE)
        sources_list_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        x = 0
        y = 0
        for title in ('Interface', 'Hardware', 'Status', 'Action'):
            label = Gtk.Label()
            label.set_markup('<b>%s</b>' % title)
            table.attach(label, x, y, 1, 1)
            x += 1
        y += 1
        table.set_baseline_row(0)
        table.set_column_spacing(10)
        table.set_row_spacing(10)

        available_datasources = self.client_thread.client.get_available_datasources()
        for interface in available_datasources:
            unsupported = False
            if interface['kismet.datasource.probed.in_use_uuid'] == '00000000-0000-0000-0000-000000000000':
                in_use = False
            else:
                in_use = True

            interface_label = Gtk.Label(label=interface['kismet.datasource.probed.interface'])
            table.attach(interface_label, 0, y, 1, 1)

            hardware_label = Gtk.Label(label=interface['kismet.datasource.probed.hardware'])
            table.attach(hardware_label, 1, y, 1, 1)

            if in_use:
                status_text = 'in use'
            elif interface['kismet.datasource.type_driver']['kismet.datasource.driver.type'] != 'linuxwifi':
                status_text = 'unsupported type "%s"' % interface['kismet.datasource.type_driver']['kismet.datasource.driver.type']
                unsupported = True
            else:
                status_text = 'inactive'

            status_label = Gtk.Label(label=status_text)
            table.attach(status_label, 2, y, 1, 1)

            if not in_use and not unsupported:
                activate_button = Gtk.Button.new_with_mnemonic('_Activate')
                activate_button.connect("clicked", self.on_activate, interface)
                table.attach(activate_button, 3, y, 1, 1)
            y += 1

        refresh_button = Gtk.Button.new_with_mnemonic('_Refresh')
        refresh_button.connect("clicked", self.on_refresh)
        table.attach(refresh_button, 3, y, 1, 1)

        if self.widget:
            self.gtkwin.remove(self.widget)

        self.gtkwin.add(sources_list_scroll)
        self.gtkwin.show_all()
        self.widget = sources_list_scroll

    def on_activate(self, widget, interface):
        self.client_thread.client.add_datasource(interface['kismet.datasource.probed.interface'])
        self.on_refresh()

    def on_destroy(self, window):
        self.gtkwin = None

    def on_refresh(self, widget=None):
        self.init_box()
