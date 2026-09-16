import sys, types, importlib.util

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

# ---- model stub ----
model_mod = types.ModuleType('caic.utilities.model')
sys.modules['caic.utilities'] = types.ModuleType('caic.utilities')
sys.modules['caic.utilities'].__path__ = ['usr/share/caic/caic/utilities']
sys.modules['caic.utilities.model'] = model_mod
class Attr:
    def __init__(self, d): self._d = d
    def __getattr__(self, name): return self._d.get(name, '')
layout = Attr({'squashfs_directory': 'arch/x86_64', 'casper_directory': 'arch/boot/x86_64', 'install_sources_file_name': ''})
model_mod.layout = layout
model_mod.kernel_details_list = [{'new_vmlinuz_file_name': 'vmlinuz-linux', 'new_initrd_file_name': 'initramfs-linux.img'}]
model_mod.selected_kernel_index = 0
b = types.ModuleType('caic.utilities.model.builder')
model_mod.builder = type('B', (), {'get_object': staticmethod(lambda n: None)})()

# logger stub
log = types.ModuleType('caic.utilities.logger')
sys.modules['caic.utilities.logger'] = log
log.log_label = lambda *a, **k: None; log.log_value = lambda *a, **k: None

disp = types.ModuleType('caic.utilities.displayer')
sys.modules['caic.utilities.displayer'] = disp
disp.update_label = lambda *a, **k: None

# ---- files_tab stub base class ----
ft = types.ModuleType('caic.utilities.files_tab')
sys.modules['caic.utilities.files_tab'] = ft
class FilesTab:
    def __init__(self): pass
    def get_line_text(self, buffer, n): return buffer.lines[n]
    def delete_text(self, buffer, n, s, e): buffer.lines[n] = buffer.lines[n][:s] + buffer.lines[n][e:]
    class Iter:
        def get_line_offset(self): return len(self.lines[self.n])
        def forward_char(self): pass
    def insert_text(self, buffer, text, n, off):
        buffer.lines[n] = buffer.lines[n][:off] + text + buffer.lines[n][off:]
        it1 = self.Iter(); it1.lines = buffer.lines; it1.n = n
        it2 = self.Iter(); it2.lines = buffer.lines; it2.n = n
        return (it1, it2)
    def update_file(self, relative_file, fn): pass
ft.FilesTab = FilesTab

spec = importlib.util.spec_from_file_location('boot_tab', 'usr/share/caic/caic/pages/boot_tab.py')
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)
tab = bt.BootTab.__new__(bt.BootTab)


class MockBuffer:
    def __init__(self, lines): self.lines = lines
    def get_line_count(self): return len(self.lines)
    def apply_tag_by_name(self, *a, **k): pass


def apply(config_lines):
    buffer = MockBuffer(config_lines)
    source_view = type('S', (), {'file_path': 'x', 'get_buffer': lambda self: buffer})()
    # paste the buffer into the FilesTab stub
    tab.buffer = buffer
    tab.edit_source_view(source_view)
    return buffer.lines

# Arch: systemd-boot loader entry (no 'boot=' should be added)
layout._d['squashfs_directory'] = 'arch/x86_64'
lines = apply(['title Arch Linux', 'linux /arch/boot/x86_64/vmlinuz-linux', 'initrd /arch/boot/x86_64/initramfs-linux.img', 'options archisobasedir=arch archisolabel=ARCH_202609'])
assert 'boot=arch' not in ' '.join(lines), f'Arch must NOT get boot= param: {lines}'
assert lines[1] == 'linux /arch/boot/x86_64/vmlinuz-linux', lines
print('Arch systemd-boot entry OK:', lines)

# Arch: syslinux APPEND + LINUX + INITRD
lines = apply(['LABEL arch', 'LINUX /arch/boot/x86_64/vmlinuz-linux', 'INITRD /arch/boot/x86_64/initramfs-linux.img', 'APPEND archisobasedir=arch archisolabel=ARCH_202609'])
assert 'boot=arch' not in ' '.join(lines), f'Arch syslinux must NOT get boot= param: {lines}'
print('Arch syslinux config OK:', lines)

# Ubuntu: casper, must update /casper and add boot=casper
layout._d['squashfs_directory'] = 'casper'
layout._d['casper_directory'] = 'casper'
model_mod.kernel_details_list = [{'new_vmlinuz_file_name': 'vmlinuz', 'new_initrd_file_name': 'initrd'}]
lines = apply(['default live', 'label live', 'kernel /casper/vmlinuz', 'append initrd=/casper/initrd boot=casper quiet'])
joined = ' '.join(lines)
assert '/casper/vmlinuz' in joined, lines
print('Ubuntu casper config OK:', lines)

print('ALL BOOT TAB TESTS PASSED')
# Ubuntu: verify rewrite of a different kernel path
layout._d['squashfs_directory'] = 'casper'
layout._d['casper_directory'] = 'casper'
model_mod.kernel_details_list = [{'new_vmlinuz_file_name': 'vmlinuz', 'new_initrd_file_name': 'initrd'}]
lines = apply(['default live', 'label live', 'kernel /old/vmlinuz-6.5', 'append initrd=/old/initrd.img boot=casper quiet'])
joined = ' '.join(lines)
assert '/casper/vmlinuz' in joined, lines
assert '/casper/initrd' in joined, lines
print('UBUNTU REWRITE OK:', lines)
