import sys, types, importlib.util, os, tempfile

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

# ---- constants ----
pkg = types.ModuleType('caic'); pkg.__path__ = ['usr/share/caic/caic']
sys.modules['caic'] = pkg
const = types.ModuleType('caic.constants')
for n in ['BOLD_RED','NORMAL','OK','ERROR','OPTIONAL','BULLET','PROCESSING','BLANK','FIFTY_PERCENT','FINAL_PERCENT','GAP','MIB','GIB','MAXIMUM_DISK_SIZE_BYTES','MAXIMUM_DISK_SIZE_GIB','SLEEP_0500_MS','TIME_STAMP_FORMAT_YYYYMMDD']:
    setattr(const, n, 0 if n == 'OK' else (1000000 if n == 'MIB' else (1073741824 if n == 'GIB' else '')))
sys.modules['caic.constants'] = const

# ---- model ----
m = types.ModuleType('caic.utilities.model')
sys.modules['caic.utilities'] = types.ModuleType('caic.utilities')
sys.modules['caic.utilities'].__path__ = ['usr/share/caic/caic/utilities']
sys.modules['caic.utilities.model'] = m
class Attr:
    def __init__(self, d): self._d = d
    def __getattr__(self, name): return self._d.get(name, '')
layout = Attr({'squashfs_directory': 'arch/x86_64', 'size_file_name': '', 'manifest_file_name': '', 'minimal_size_file_name': '', 'standard_size_file_name': '', 'live_size_file_name': '', 'live_generic_size_file_name': ''})
m.layout = layout
m.custom = Attr({'iso_disk_name': 'arch', 'iso_release_notes_url': ''})
m.application = Attr({'directory': 'x'})
m.project = Attr({'custom_disk_directory': tempfile.mkdtemp(), 'custom_root_directory': '/tmp/root'})
m.builder = type('B', (), {'get_object': staticmethod(lambda n: None)})()
m.generated = Attr({'iso_directory': '', 'iso_file_name': ''})
m.status = Attr({'iso_template': ''})
m.options = Attr({'has_minimal_install': False})
m.package_details_list = []
m.file_system_size = 0
m.kernel_details_list = []
m.selected_kernel_index = 0

# ---- stubs ----
log = types.ModuleType('caic.utilities.logger')
sys.modules['caic.utilities.logger'] = log
log.log_label = lambda *a, **k: None; log.log_value = lambda *a, **k: None
log.log_title = lambda *a, **k: None

disp = types.ModuleType('caic.utilities.displayer')
sys.modules['caic.utilities.displayer'] = disp
C = []
disp.update_label = lambda *a, **k: C.append(a); disp.update_status = lambda *a, **k: C.append(a)
disp.update_progress_bar_percent = lambda *a, **k: None; disp.update_progress_bar_text = lambda *a, **k: None

fu = types.ModuleType('caic.utilities.file_utilities')
sys.modules['caic.utilities.file_utilities'] = fu
fu.write_line = lambda *a, **k: None; fu.write_lines = lambda *a, **k: None
fu.read_lines = lambda *a, **k: []; fu.read_file = lambda *a, **k: '0'
fu.make_directory = lambda *a, **k: None; fu.make_directories = lambda *a, **k: None
fu.is_regular_file = lambda *a, **k: False

iu = types.ModuleType('caic.utilities.iso_utilities')
sys.modules['caic.utilities.iso_utilities'] = iu

coh = types.ModuleType('caic.utilities.constructor')
sys.modules['caic.utilities.constructor'] = coh
coh.decode = lambda s: s or ''

proc = types.ModuleType('caic.utilities.processor')
sys.modules['caic.utilities.processor'] = proc
proc.execute_synchronous = lambda *a, **k: ('', 0, None)

prog = types.ModuleType('caic.utilities.progressor')
sys.modules['caic.utilities.progressor'] = prog
prog.track_progress = lambda *a, **k: (None, 0, None)

nav = types.ModuleType('caic.navigator')
sys.modules['caic.navigator'] = nav
class InterruptException(Exception): pass
nav.InterruptException = InterruptException

opt = types.ModuleType('caic.pages.options_page')
opt_page = types.ModuleType('caic.pages')
opt_page.__path__ = ['usr/share/caic/caic/pages']; sys.modules['caic.pages'] = opt_page
sys.modules['caic.pages.options_page'] = opt

spec = importlib.util.spec_from_file_location('generate_page', 'usr/share/caic/caic/pages/generate_page.py')
gp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gp)

# Test 1: is_arch_layout for Arch
assert gp.is_arch_layout() is True
# Test 2: update_disk_and_installer_info should skip (no file writes) for Arch
assert gp.update_disk_and_installer_info() is False
# No "diskdefines" or ".disk" write attempt should have happened:
assert not any('diskdefines' in str(a) for a in C), f'Unexpected writes: {C}'
assert not any('.disk' in str(a) for a in C), f'Unexpected writes: {C}'
# Test 3: is_arch_layout false for Ubuntu
layout._d['squashfs_directory'] = 'casper'
assert gp.is_arch_layout() is False

from caic.pages import generate_page as _g2  # noqa - force ref check
print('ALL GENERATE PAGE TESTS PASSED')