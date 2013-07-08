import os
import ctypes
import tempfile
import cppinl
import shutil

# hold object and source files
TEMP_DIR = tempfile.mkdtemp()

# cleans up after execution
def del_temp_dir():
  shutil.rmtree(TEMP_DIR)


def invoke_function(fn, *vals):
  argv = []
  for v in vals:
    if type(v) is float:
      argv.append(ctypes.c_double(v))
    elif isinstance(v, cppinl.CHandle):
      argv.append(v.ptr)
    else:
      argv.append(v)
  try:
    rtr = fn(*argv)
    return rtr
  except:
    print 'Call into C++ failed.'
    print 'Arguments: ', ', '.join(map(repr, vals))
    raise

class CompileError(Exception): pass

def compile_bin(out_name, src_files, cc="g++", flags=['O3', 'Wall'], 
    includes=[], links=[], defs=[], lib=False):
  """ Compiles a C++ source file
  \param out_name the '-o' flag (eg. '~/bin/foo')
  \param src_files list of source fiels (eg. ['~/src/foo.cc'])
  \param cc the path to the c++ compiler
  \param flags list of falgs for the compiler (eg. ['O3', 'Wall'])
  \param includes list of directories to include (eg. ['~/includes/'])
  \param links list of libraries to link with (eg. ['pthread', 'gtest'])
  \param defs list of names to define with -D (eg. ['ENABLE_FOO'])
  \param lib If true, includes -c and -fPIC in flags.
  """
  flags = list(flags)
  if lib:
    flags.append('c')
    flags.append('fPIC')
  lnks = ' '.join(map(lambda s: '-l%s'%s, links))
  incl = ' '.join(map(lambda s: '-I%s'%s, includes))
  flgs = ' '.join(map(lambda s: '-%s'%s, flags))
  dfs = ' '.join(map(lambda s: '-D%s'%s, defs))
  srcs = ' '.join(src_files)

  cmdline = '{0} {1} {2} {3} {4} {5} -o {6}'.format(cc, flgs, lnks, incl, srcs, 
      dfs, out_name)
  rcode = os.system("%s 1>/dev/null" % cmdline)
  if rcode != 0:
    raise CompileError('failed: %s\n source: %s' % (cmdline, srcs))

def compile_so(outname, obj_files, cc="g++", links=[]):
  """ Compiles a shared object from object files
  \param outname path to output (eg. '/tmp/libfoo.so')
  \param obj_files name of files to compile (eg. ['~/obj/foo.o'])
  \param cc the c++ compiler (eg. '/usr/bin/g++')
  """
  objs = ' '.join(obj_files)
  libname = os.path.basename(outname)
  link_args = ' '.join(map(lambda s:'-l%s'%s, links))
  cmdline = '{0} -shared -Wl,-soname,{1} -o {2} {3} {4}'.format(cc, libname, 
      outname, objs, link_args)
  rcode = os.system("%s 1>/dev/null" % cmdline)
  if rcode != 0:
    raise CompileError('failed: %s' % cmdline)


def compile_and_load(src_files, obj_files=[], cc="g++", flags=['O3', 'Wall'], 
    includes=[], links=[], defs=[]):
  """ Compile and load a shared object from a source file
  \param src_files list of source fiels (eg. ['~/src/foo.cc'])
  \param cc the path to the c++ compiler
  \param obj_files name of files to compile (eg. ['~/obj/foo.o'])
  \param flags list of falgs for the compiler (eg. ['O3', 'Wall'])
  \param includes list of directories to include (eg. ['~/includes/'])
  \param links list of libraries to link with (eg. ['pthread', 'gtest'])
  \param defs list of names to define with -D (eg. ['ENABLE_FOO'])
  \return (lib, fin) link to the library and a function to call to close the library
  """
  __, obj_name = tempfile.mkstemp(suffix='.o', dir=TEMP_DIR)
  os.close(__)
  __, lib_name = tempfile.mkstemp(suffix='.so', dir=TEMP_DIR)
  os.close(__)

  compile_bin(obj_name, src_files, cc=cc, flags=flags, includes=includes, 
      links=links, defs=defs, lib=True)
  # add the newly compiled object file to the list of objects for the lib
  obj_files = list(obj_files)
  obj_files.append(obj_name)
  compile_so(lib_name, obj_files, cc=cc, links=links)
  def finalize():
    if os.path.exists(obj_name):
      os.unlink(obj_name)
    if os.path.exists(lib_name):
      os.unlink(lib_name)
  try:
    lib = ctypes.CDLL(lib_name)
    return lib, finalize
  except OSError:
    print "Failed link with library, source files:"
    print ', '.join(src_files)
    raise


def compile_and_load_source(src, obj_files=[], cc="g++", flags=['O3', 'Wall'], 
    includes=[], links=[], defs=[]):
  """ Compile and load a shared object from a source string
  This is a convienent way to call compile_and_load
  \param src C++ source code
  \param cc the path to the c++ compiler
  \param obj_files name of files to compile (eg. ['~/obj/foo.o'])
  \param flags list of falgs for the compiler (eg. ['O3', 'Wall'])
  \param includes list of directories to include (eg. ['~/includes/'])
  \param links list of libraries to link with (eg. ['pthread', 'gtest'])
  \param defs list of names to define with -D (eg. ['ENABLE_FOO'])
  \return (lib, fin) link to the library and a function to call to close the library
  """
  fd, src_file = tempfile.mkstemp(suffix='.cc', dir=TEMP_DIR)
  os.write(fd, src)
  os.close(fd)
  lib, fin = compile_and_load([src_file], obj_files=obj_files, cc=cc, flags=flags,
      includes=includes, links=links, defs=defs)
  os.unlink(src_file)
  return lib, fin
