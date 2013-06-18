import cppinl
import context

"""
Handy tools for using pycpc
"""

_ctx = None
_lib = None

def _init_if_needed():
  global _ctx, _lib
  if _ctx is not None:
    return
  _ctx = context.Context()
  lbuild = context.CPPLibBuilder(_ctx)
  ptr = cppinl.CHandle(long)
  dptr = cppinl.CHandle(float)
  
  lbuild.decl_func('long_alloc', r'''
    p = new int64_t[len];
  ''', p=ptr, len=long)

  lbuild.decl_func('long_free', r'''
    delete [] p;
  ''', p=ptr)

  lbuild.decl_func('dub_alloc', r'''
    p = new double[len];
  ''', p=dptr, len=long)

  lbuild.decl_func('dub_free', r'''
    delete [] p;
  ''', p=dptr)

  _lib = lbuild.make()


class BasicIt(object):
  def __init__(self, l):
    self.l = l
    self.i = 0

  def next(self):
    if self.i < len(self.l):
      self.i += 1
      return self.l[self.i-1]
    raise StopIteration

class CLongVector(cppinl.CHandle):
  def __init__(self):
    _init_if_needed()
    cppinl.CHandle.__init__(self, typ=long)

  def set_size(self, size):
    self.size = long(size)

  def allocate(self, size):
    self.set_size(size)
    _lib['long_alloc'](p=self, len=self.size)

  def __setslice__(self, i, j, seq):
    if i > j: 
      raise Exception('cannot get a reversed slice.')
    if i < 0:
      raise Exception('???')
    i = min(i, self.size)
    j = min(j, self.size)

    if len(seq) != (j - i):
      raise Exception('cannot set splice of size %s to a seq of size %s' % (j-i, len(seq)))

    for idx, v in enumerate(seq):
      self[i + idx] = v

  def free(self):
    _lib['long_free'](p=self)
    self.set_size(0)

  def __getitem__(self, idx):
    if idx < 0:
      idx += self.size
    idx = max(idx, 0)
    return self.ptr[0][idx]

  def __setitem__(self, idx, v):
    if idx < 0:
      idx += self.size
    self.ptr[0][idx] = v

  def __len__(self):
    return self.size

  def __iter__(self):
    return BasicIt(self)

  def __str__(self):
    return '['+', '.join(map(str, self)) +']'

  def __repr__(self):
    return '['+', '.join(map(repr, self)) +']'



class CDoubleVector(cppinl.CHandle):
  def __init__(self):
    _init_if_needed()
    cppinl.CHandle.__init__(self, typ=float)
    self.size = 0

  def set_size(self, size):
    self.size = long(size)

  def allocate(self, size):
    self.set_size(size)
    _lib['dub_alloc'](p=self, len=self.size)

  def __setslice__(self, i, j, seq):
    if i > j: 
      raise Exception('cannot get a reversed slice.')
    if i < 0:
      raise Exception('???')
    i = min(i, self.size)
    j = min(j, self.size)

    if len(seq) != (j - i):
      raise Exception('cannot set splice of size %s to a seq of size %s' % (j-i, len(seq)))

    for idx, v in enumerate(seq):
      self[i + idx] = v

  def free(self):
    _lib['dub_free'](p=self)
    self.set_size(0)

  def __getitem__(self, idx):
    if idx < 0:
      idx += self.size
    idx = max(idx, 0)
    return self.ptr[0][idx]

  def __setitem__(self, idx, v):
    if idx < 0:
      idx += self.size
    self.ptr[0][idx] = v

  def __len__(self):
    return self.size

  def __iter__(self):
    return BasicIt(self)

  def __str__(self):
    return '['+', '.join(map(str, self)) +']'

  def __repr__(self):
    return '['+', '.join(map(repr, self)) +']'

