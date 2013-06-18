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
    self.macros.extend(['#include <cstdio>', '#include <cstdlib>', 
        '#include <inttypes.h>', '#include <string>', '#include <cstring>'])

  def add_macro(self, mac):
    self.macros.append(mac)

  def use_namespace(self, ns):
    self.name_spaces.append('using namespace %s;' % ns)


class CPPLibBuilder(object):
  def __init__(self, ctx):
    self.context = ctx
    self.src = []

  def decl_func(self, name, body, rtype=None, **args):
    self.src.append(cppinl.cpp_func_def_convert(name, body, rtype, **args))

  def inline_source(self, body, **args):
    decl = cppinl.cpp_func_def_convert('temp2e5e3662020b4edea3ab3a5598010207', 
        body, None, **args)
    src = self.emit_source(lines=[decl])
    return src

  def inline_call(self, body, **args):
    # using a uuid for the function name, hopefully avoids conflicts
    decl = cppinl.cpp_func_def_convert('temp2e5e3662020b4edea3ab3a5598010207', 
        body, None, **args)
    src = self.emit_source(lines=[decl])
    lib, fin = self.make(src=src)
    vals = args.values()
    cmake.invoke_function(lib.temp2e5e3662020b4edea3ab3a5598010207, *vals)
    # clean up temorary files
    fin()

  def emit_source(self, lines=None):
    if lines is None:
      lines = self.src
    src = '\n'.join(lines)
    src = '\n'.join(self.context.macros) + '\n\n' \
        + '\n'.join(self.context.name_spaces) + '\n\n' + src
    return src

  def make(self, src=None):
    if src is None:
      src = self.emit_source()
    return cmake.compile_and_load_source(src,
        obj_files=self.context.obj_files,
        cc=self.context.cc,
        flags=self.context.flags,
        includes=self.context.includes,
        links=self.context.links,
        defs=self.context.defs)


if __name__ == '__main__':
  ctx = Context()
  ctx.add_basic_libs()
  ctx.use_namespace('std')
  cppb = CPPLibBuilder(ctx)
  cppb.decl_func('inc', 'return x + 1;', rtype=long, x=long)
  cppb.decl_func('dec', 'return x - 1;', rtype=long, x=long)

  print cppb.emit_source()

  lib, fin = cppb.make()

  #test the inline stuff
  s = 77
  cppb.inline_call(r'printf("++foo = %d\n", ++s);', s=s)
  print 's = ', s

  print 'my func: ', lib.inc(5)
  fin()
