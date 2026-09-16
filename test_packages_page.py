import sys, types, importlib.util, os

sys.path.insert(0, 'usr/share/caic')

# ---- GI stubs ----
gi_mod = types.ModuleType('gi'); gi_mod.require_version = lambda *a, **k: None
repo_mod = types.ModuleType('gi.repository')
class CatchMod(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith('_'): raise AttributeError(name)
        return lambda *a, **k: None
for n in ['Gdk', 'Gtk', 'Gio', 'GLib', 'GtkSource', 'Pango', 'GdkPixbuf', 'GObject', 'Vte']:
    setattr(repo_mod, n, CatchMod(n))
sys.modules['gi'] = gi_mod; sys.modules['gi.repository'] = repo_mod
sys.modules.setdefault('magic', types.ModuleType('magic'))

# ---- caic / caic.constants ----
pkg = types.ModuleType('caic'); pkg.__path__ = ['usr/share/caic/caic']
sys.modules['caic'] = pkg
const = types.ModuleType('caic.constants')
for name in ['BOLD_RED','NORMAL','OK','ERROR']: setattr(const, name, 0 if name=='OK' else '')
for name in ['BLANK_VERSION_0000','BACKUP_LIVE_DIRECTORY','BACKUP_ROOT_DIRECTORY','CUSTOM_DISK_DIRECTORY',
             'CUSTOM_LIVE_DIRECTORY','CUSTOM_ROOT_DIRECTORY','CUSTOM_TEMP_DIRECTORY','ISO_MOUNT_POINT',
             'LOG_FILE_NAME','NUMBERS_LOWER_CASE','NUMBERS_TITLE_CASE','TIME_STAMP_FORMAT',
             'TIME_STAMP_FORMAT_YYYYMMDDHHMMSS','VERSION_NUMBER_FORMAT']:
    setattr(const, name, None)
for name in ['SLEEP_0125_MS','SLEEP_0250_MS','SLEEP_0500_MS','SLEEP_1000_MS']:
    setattr(const, name, 0)
const.OPTIONAL = 'optional'; const.BULLET = 'bullet'; const.PROCESSING = 'processing'; const.BLANK = ''
sys.modules['caic.constants'] = const

# ---- model stub ----
model = types.ModuleType('caic.utilities.model')
sys.modules['caic.utilities'] = types.ModuleType('caic.utilities')
sys.modules['caic.utilities'].__path__ = ['usr/share/caic/caic/utilities']
sys.modules['caic.utilities.model'] = model

# Attributes-like layout
class Attr:
    def __init__(self, d): self.__dict__['_d'] = d
    def __getattr__(self, name):
        return self._d.get(name, '')
    def __setattr__(self, name, value):
        self._d[name] = value[0]
layout = Attr({'squashfs_directory': 'arch/x86_64', 'standard_remove_file_name': ''})
model.layout = layout
model.options = type('O', (), {'has_minimal_install': False})()
model.package_details_list = []
model.project = type('P', (), {'custom_root_directory': '/tmp/custom-root', 'configuration': type('C', (), {'save': lambda self: None})()})()
model.application = type('A', (), {'directory': '/usr/share/caic'})()
model.builder = type('B', (), {'get_object': staticmethod(lambda n, *a: None)})()

# ---- logger / displayer stubs ----
log = types.ModuleType('caic.utilities.logger')
sys.modules['caic.utilities.logger'] = log
log.log_label = lambda *a, **k: None; log.log_value = lambda *a, **k: None

disp = types.ModuleType('caic.utilities.displayer')
disp = types.ModuleType('caic.utilities.displayer')
sys.modules['caic.utilities.displayer'] = disp
calls = []
disp.update_label = lambda *a, **k: calls.append(('label', a)); disp.update_status = lambda *a, **k: calls.append(('status', a))
disp.set_sensitive = lambda *a, **k: calls.append(('sensitive', a)); disp.set_visible = lambda *a, **k: calls.append(('visible', a))
disp.update_list_store = lambda *a, **k: calls.append(('store', a)); disp.activate_switch = lambda *a, **k: None
disp.set_column_visible = lambda *a, **k: None; disp.reset_buttons = lambda *a, **k: None

# ---- file_utilities stub ----
fu = types.ModuleType('caic.utilities.file_utilities')
sys.modules['caic.utilities.file_utilities'] = fu; fu.write_lines = lambda *a, **k: None

# ---- iso_utilities stub ----
iu = types.ModuleType('caic.utilities.iso_utilities')
sys.modules['caic.utilities.iso_utilities'] = iu; iu.unmount_iso_and_delete_mount_point = lambda *a, **k: None

# ---- processor stub with a strict fake execute_synchronous ----
proc = types.ModuleType('caic.utilities.processor')
sys.modules['caic.utilities.processor'] = proc
captured = []
def fake_execute_synchronous(command, *a, **k):
    captured.append(command)
    return 'ok', 0, None
proc.execute_synchronous = fake_execute_synchronous

spec = importlib.util.spec_from_file_location('packages_page', 'usr/share/caic/caic/pages/packages_page.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# 1. is_arch_layout (Arch)
assert mod.is_arch_layout() is True, 'arch/x86_64 should be Arch'
# 2. is_arch_layout (Ubuntu)
layout._d['squashfs_directory'] = 'casper'
assert mod.is_arch_layout() is False, 'casper should not be Arch'

# 3. remove_selected_packages with no selection -> no command
layout._d['squashfs_directory'] = 'arch/x86_64'
class StoreIter:
    def __init__(self, rows): self.rows = rows
    def get_iter_first(self): 
        self.i = 0
        return self if self.rows else None
    def get_value(self, item, col): return self.rows[self.i][col]
    def iter_next(self, item):
        self.i += 1
        return self if self.i < len(self.rows) else None

rows = [[True, False, False, False, 'vim', '1.0'], [False, False, False, False, 'bash', '2.0']]
store = StoreIter(rows)
model.builder.get_object = staticmethod(lambda n: store if n == 'packages_page__list_store' else None)
captured.clear()
assert mod.remove_selected_packages() is False
assert len(captured) == 1, f'expected 1 command, got {captured}'
cmd = captured[0]
assert cmd[0] == 'pkexec' and cmd[1] == '/usr/share/caic/commands/pacman-in-root'
assert cmd[2] == '/tmp/custom-root'
assert '--remove' in cmd and '--recursive' in cmd and '--noconfirm' in cmd
assert cmd[-1] == 'vim'

# 4. install_packages entry
widget = type('W', (), {'get_text': lambda self: 'htop tmux'})()
model.builder.get_object = staticmethod(lambda n: None)
captured.clear()
# monkeypatch the lazy import target pre-emptively
prep = types.ModuleType('caic.pages.prepare_page')
prep.create_package_details_list = lambda root: [[False,False,False,False,'htop','0.1'],[False,False,False,False,'tmux','0.2']]
pages_pkg = types.ModuleType('caic.pages')
pages_pkg.__path__ = ['usr/share/caic/caic/pages']
sys.modules['caic.pages'] = pages_pkg
sys.modules['caic.pages.prepare_page'] = prep
# re-import with get_text mixed into builder
entry_widget = type('W', (), {'get_text': lambda self: 'htop tmux'})()
model.builder.get_object = staticmethod(lambda n: entry_widget if n == 'packages_page__install_entry' else None)
captured.clear()
mod.install_packages()
assert len(captured) == 1, f'expected 1 command, got {captured}'
cmd = captured[0]
assert '--sync' in cmd and '--needed' in cmd
assert cmd[-2] == 'htop' and cmd[-1] == 'tmux'

print('ALL PACKAGES PAGE TESTS PASSED')