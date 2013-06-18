import ctypes

"""
Inline C++ for python
"""


def cpp_func_decl(name, args, rtype=None):
  """ Creates C++ source code for a function declaration
  >>> cpp_func_decl('foobar', [('x', long)], long)
  'extern "C" int64_t foobar(int64_t x)'
  >>> cpp_func_decl('foobar', [('x', long), ('s', str)], long)
  'extern "C" int64_t foobar(int64_t x, char* s)'
  """
  rstr = get_cpp_type(rtype)
  l = [get_cpp_type(typ) + ' ' + str(aname) for aname, typ in args]
  sig = 'extern "C" %s %s(%s)' % (rstr, name, ', '.join(l))
  return sig

def cpp_func_def(name, args, body, rtype=None):
  ''' Creates a function definition in C++ source code
  >>> cpp_func_def('foo', [('x', long)], 'return x;', long)
  'extern "C" int64_t foo(int64_t x) {\\nreturn x;\\n}'
  '''
  sig = cpp_func_decl(name, args, rtype=rtype)
  return '%s {\n%s\n}' % (sig, body)

def cpp_func_def_convert(name, body, rtype=None, **args):
  ''' Makes conversion from CHandle(T) to T*&, allowing for return-by-poitner
  >>> cpp_func_def_convert('foo', 'x = new int64_t[2];', None, x=CHandle(long))
  'extern "C" void foo(int64_t** __x__) {\\nint64_t* &x = *__x__;\\nx = new int64_t[2];\\n}'
  '''
  mangled_args = []
  remap_code = []
  for arg in args:
    val = args[arg]
    # mange if val is a Handle
    if isinstance(val, CHandle):
      if val.cast is None:
        remap_code.append('%s &%s = *__%s__;' % (val.deref_type(), arg, arg))
      else:
        remap_code.append('%s &%s = * ((%s**) __%s__);' % (val.deref_type(), 
           arg, val.cast,arg))
      mangled_args.append(('__%s__'%arg, val))
    else:
      mangled_args.append((arg, val))
  remap_code.append(body)
  body = '\n'.join(remap_code)
  return cpp_func_def(name, mangled_args, body, rtype=rtype)


def get_cpp_type(foo):
  ''' Converts a tpye or object to a string with the C++ type
  >>> get_cpp_type(long)
  'int64_t'
  >>> get_cpp_type(int)
  'int32_t'
  >>> get_cpp_type(None)
  'void'
  >>> get_cpp_type(CHandle())
  'void**'
  >>> get_cpp_type(CHandle(float))
  'double**'
  >>> get_cpp_type(ctypes.c_double(5))
  'double'
  '''
  if isinstance(foo, CHandle):
    return foo.cpp_type()

  if type(foo) is not type:
    foo = type(foo)
  if foo is type(None):
    return 'void'
  if foo is ctypes.c_longlong:
    return 'int64_t'
  if foo is ctypes.c_int:
    return 'int32_t'
  if foo is ctypes.c_char_p: 
    return 'char*'
  if foo is ctypes.c_double:
    return 'double'
  if foo is ctypes.c_void_p:
    return 'void*'
  prims = {int : 'int32_t', long : 'int64_t', str : 'char*', float : 'double'}

  if foo in prims:
    return prims[foo]
  raise Exception('Cannot resolev type: %s' % foo)


def get_ctype(foo):
  prims = {int : ctypes.c_int, long : ctypes.c_longlong, str : ctypes.c_char_p, 
      float : ctypes.c_double, None : ctypes.c_void_p}
  return prims[foo]

class CHandle(object):
  def __init__(self, typ=None, cast=None):
    self.typ = typ
    self.void = False
    self.cast = cast
    if typ is not None:
      # T **ptr = NULL;
      self.ptr = ctypes.pointer(ctypes.POINTER(get_ctype(typ))())
    else:
      # void **ptr = NULL;
      self.void = True
      self.ptr = ctypes.pointer(ctypes.c_void_p())

  def cast(self, typstr):
    return CHandle(self.typ, cast=typstr)

  def cpp_type(self):
    if self.void:
      return 'void**'
    return self.deref_type() + '*'

  def deref_type(self):
    if self.cast is not None:
      return self.cast + '*'
    if self.void:
      return 'void*'
    return '%s*' % get_cpp_type(self.typ)

  def __getitem__(self, idx):
    return self.ptr[0][idx]

  def __setitem__(self, idx, v):
    #self.ptr[0][idx].value = v
    self.ptr[0][idx] = v

if __name__ == "__main__":
  import doctest
  doctest.testmod()
