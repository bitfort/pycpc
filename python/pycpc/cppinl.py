import ctypes

"""
Inline C++ for python
"""

def order_args(args):
  a = args.items()
  return sorted(a, key=lambda i:i[0].replace('__PYCPC__', ''))


def cpp_func_decl(name, args, rtype=None):
  """ Creates C++ source code for a function declaration
  >>> cpp_func_decl('foobar', [('x', long)], long)
  'extern "C" int64_t foobar(int64_t x)'
  >>> cpp_func_decl('foobar', [('x', long), ('s', str)], long)
  'extern "C" int64_t foobar(char* s, int64_t x)'
  """
  rstr = get_cpp_type(rtype)
  l = [get_cpp_type(typ) + ' ' + str(aname) for aname, typ in order_args(dict(args))]
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
  for arg, val in order_args(args):
    # mange if val is a Handle
    if isinstance(val, CHandle):
      if val.cast is None:
        remap_code.append('%s &%s = *__PYCPC__%s;' % (val.deref_type(), arg, arg))
      else:
        remap_code.append('%s &%s = * ((%s**) __PYCPC__%s);' % (val.deref_type(), 
           arg, val.cast,arg))
      mangled_args.append(('__PYCPC__%s'%arg, val))
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
  ''' This is a generic handle to memory, it's a C++ pointer.
  This serves multiple purposes:
    - This can be treated as a 'type' for most purposes in pycpc
    - This holds the actual pointer to the memory
    - This gives access to the meomry from python
  
  The class holds a pointer to a pointer to one of following types:
    - void
    - int64_t
    - int32_t
    - double
  The length of memory pointed to is not stored here.

  This a pointer to a pointer for use as an in/out paramter. When constructed,
  a pointer is created with semantics: 
      
      T *ptr[1];
      *ptr = NULL;

  Python owns `ptr`. The value of `ptr` is never modified by C++. This is always
  treated in C++ as:
      
      T* &p = *ptr;

  This way, C++ controls the value of `*ptr`. 

  If this is a pointer to a primitive (int, char, double), then python can
  access the native type using the __getitem__ and __setitem__ methods. If this
  is a void**, then it should not be accessed through python. The field cast
  is an optional string specifying the C++ type of the pointer allows for a 
  adding a cast in the C++ if this a void**. Eg, if cast='T', then C++ is generated
  which casts (note : ptr is type void**):
    
    T* &p = *( (T**) ptr);
  '''
  def __init__(self, typ=None, cast=None):
    ''' Creates a new Handle, only typ or cast should be set, not both
    Valid types are: long, int, float

    The field cast can be any string which is a valid C++ type.
    '''
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

  def ccast(self, typstr):
    ''' Converts this to a void pionter which is cast to the given type
    >>> ch = CHandle()
    >>> ch
    CHandle(typ=None, cast=None)
    >>> ch.ccast('std::vector<int>')
    >>> ch
    CHandle(typ=None, cast='std::vector<int>')
    '''
    self.void = True
    self.cast = typstr

  def cpp_type(self):
    ''' Gets a string which is the type of this handle in C++
    >>> CHandle().cpp_type()
    'void**'
    >>> CHandle(cast='foo').cpp_type()
    'void**'
    >>> CHandle(typ=long).cpp_type()
    'int64_t**'
    '''
    if self.void:
      return 'void**'
    return self.deref_type() + '*'

  def deref_type(self):
    ''' Returns the type string which this doulbe pointer dereferences to
    >>> CHandle().deref_type()
    'void*'
    >>> CHandle(long).deref_type()
    'int64_t*'
    >>> CHandle(float).deref_type()
    'double*'
    >>> CHandle(cast='std::vector<int>').deref_type()
    'std::vector<int>*'
    '''
    if self.cast is not None:
      return self.cast + '*'
    if self.void:
      return 'void*'
    return '%s*' % get_cpp_type(self.typ)

  def __getitem__(self, idx):
    ''' Gets the primitive value stored at idx
    This is the same as:
        
        return (*ptr)[idx];

    This is only defined if the type of this is long, float, or int.
    Undefined if (*ptr) == NULL, idx < 0, or (*ptr)[idx] is unmapped memory
    '''
    return self.ptr[0][idx]

  def __setitem__(self, idx, v):
    ''' Stores the primitive value at the given index
    This is the same as:
        
        (*ptr)[idx] = v;

    This is only defined if the type of this is long, float, or int and
    this is the same as type(v). 
    Undefined if (*ptr) == NULL, idx < 0, or (*ptr)[idx] is unmapped memory
    '''
    #self.ptr[0][idx].value = v
    self.ptr[0][idx] = v

  def __str__(self):
    return 'CHandle:%s' % self.cpp_type()

  def __repr__(self):
    if self.cast is None:
      return 'CHandle(typ=%s, cast=%s)' % (self.typ, self.cast)
    return 'CHandle(typ=%s, cast=\'%s\')' % (self.typ, self.cast)

if __name__ == "__main__":
  import doctest
  doctest.testmod()
