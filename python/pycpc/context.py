import cmake
import cppinl
import ctypes



class Context(object):
  def __init__(self, obj_files=[], cc="g++", flags=['O3', 'Wall'], includes=[], 
      links=[], defs=[], macros=[]):
    """ 
    \param src C++ source code
    \param cc the path to the c++ compiler
    \param obj_files name of files to compile (eg. ['~/obj/foo.o'])
    \param flags list of falgs for the compiler (eg. ['O3', 'Wall'])
    \param includes list of directories to include (eg. ['~/includes/'])
    \param links list of libraries to link with (eg. ['pthread', 'gtest'])
    \param defs list of names to define with -D (eg. ['ENABLE_FOO'])
    """
    self.obj_files = obj_files
    self.cc = cc
    self.flags = flags
    self.includes = includes
    self.links = links
    self.defs = defs
    self.macros = macros
    self.name_spaces = []
    self.add_basic_libs()

  def add_basic_libs(self):
    ''' Adds include statements for commonly used libraries
    '''
    self.macros.extend(['#include <cstdio>', '#include <cstdlib>', 
        '#include <inttypes.h>', '#include <string>', '#include <cstring>'])

  def add_macro(self, mac):
    self.macros.append(mac)

  def use_namespace(self, ns):
    self.name_spaces.append('using namespace %s;' % ns)

  def __hash__(self):
    return hash((repr(self.obj_files), repr(self.cc), repr(self.flags),
        repr(self.includes), repr(self.links), repr(self.defs), 
        repr(self.macros), repr(self.name_spaces)))


class CPPLib(object):
  def __init__(self, lib, fin):
    self.fin = fin
    self.lib = lib

  def __getitem__(self, fnname):
    ''' Gets the given function by name, invoked with keyword arguments
    E.g. CPPLilb(...)['foo'](x=5, y=7)
    '''
    def wrap(**args):
      vals = args.values()
      return cmake.invoke_function(self.lib.__getattr__(fnname), *vals)
    return wrap

  def __del__(self):
    ''' Clean up shared object files in /tmp
    '''
    self.fin()

class CPPLibBuilder(object):
  def __init__(self, ctx):
    self.context = ctx
    self.src = []
    self.raw = []
    self.fins = []
    self.inlines = {}

  def raw_source(self, txt):
    self.src.append(txt)

  def set_context(self, ctx):
    self.context = ctx

  def __hash__(self):
    return hash( (repr(self.src, hash(self.context))) )

  def decl_func(self, name, body, rtype=None, **args):
    self.src.append(cppinl.cpp_func_def_convert(name, body, rtype, **args))

  def inline_source(self, body, **args):
    decl = cppinl.cpp_func_def_convert('temp2e5e3662020b4edea3ab3a5598010207', 
        body, None, **args)
    src = self.emit_source(lines=[decl])
    return src

  def inline_call(self, body, **args):
    ctxh = hash(self.context)
    bodyh = hash(body)

    ke = (ctxh, bodyh)
    if ke not in self.inlines:
      lib, fin = self._make_inline_call(body, **args)
      self.fins.append(fin)
      self.inlines[ke] = lib

    vals = args.values()
    cmake.invoke_function(self.inlines[ke].temp2e5e3662020b4edea3ab3a5598010207, 
        *vals)

  def _make_inline_call(self, body, **args):
    # using a uuid for the function name, hopefully avoids conflicts
    decl = cppinl.cpp_func_def_convert('temp2e5e3662020b4edea3ab3a5598010207', 
        body, None, **args)
    src = self.emit_source(lines=[decl])
    lib, fin = self._make(src=src)
    return lib, fin

  def emit_source(self, lines=None):
    ''' Returns C++ source code that will be compiled when make() is called
    '''
    if lines is None:
      lines = self.src
    src = '\n'.join(lines)
    src = '\n'.join(self.context.macros) + '\n\n' \
        + '\n'.join(self.context.name_spaces) + '\n\n' + src
    return src

  def make(self, src=None):
    ''' Compiles the soruce and returns a CPPLib to call into the object file
    '''
    lib, fin = self._make(src=src)
    return CPPLib(lib, fin)

  def _make(self, src=None):
    ''' Compiles source code and links with the shared object 
    Returns a handle for the library and a function hook to delete the .so
    '''
    if src is None:
      src = self.emit_source()
    lib, fin = cmake.compile_and_load_source(src,
        obj_files=self.context.obj_files,
        cc=self.context.cc,
        flags=self.context.flags,
        includes=self.context.includes,
        links=self.context.links,
        defs=self.context.defs)
    return lib, fin

  def __del__(self):
    """ Clean up temporary shared object files """
    for fin in self.fins:
      fin()


if __name__ == '__main__':
  ctx = Context()
  ctx.add_basic_libs()
  ctx.use_namespace('std')
  cppb = CPPLibBuilder(ctx)
  cppb.decl_func('inc', 'return x + 1;', rtype=long, x=long)
  cppb.decl_func('dec', 'return x - 1;', rtype=long, x=long)

  print cppb.emit_source()

  lib = cppb.make()

  print lib['inc'](x=5)
