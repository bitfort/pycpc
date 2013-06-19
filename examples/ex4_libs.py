import sys
sys.path.append('python/')
import pycpc
import pycpc.vectors

'''
Multiple functions can be stored in a single shared object
'''

ctx = pycpc.Context()
lbuild = pycpc.CPPLibBuilder(ctx)

#
# Add macros to the library
#
ctx.add_macro('#define FOO 5')
ctx.add_macro('#include <vector>')

#
# Add raw C++ code, note: code is added to the file in the order we make calls
# to the builder (so this code will be at top of the file before other definitions,
# but after the macros)
#
lbuild.raw_source(
r'''
int helper() {
  static int foo = 0;
  printf("Called helper! %d\n", foo);
  return foo++;
}
''')

#
# Explicity hand-code some C++ and make it callable from python
#
lbuild.raw_source(
r'''
extern "C" int ninja() {
  printf("Ninjas can do anything.\n");
  return 1337;
}
''')

#
# Declare a new function, specifying the type of each argument by either epxlicit
# python type or by example value. Remember the name because you'll need that
# to call the function later. Note, we're naming the arguments too!
#
lbuild.decl_func('whizbang', 
r'''
int h = helper();
printf("WHIZBHANG %d\n", h + d);
''', d=long)
#    ^ we have to use 'd' later

#
# Specify return types; (rtype=None is void)
#
lbuild.decl_func('foobar', 
r'''
int h = helper();
return h + d;
''', d=long, rtype=long)

#
# Use pointers! Need an example pointer to specify the type
#
p = pycpc.CHandle(float)
lbuild.decl_func('alloc',
r'''
p = new double[10];
''', p=p)

#
# Inspect the source code of the library
#
print lbuild.emit_source()
print
print
print '*'*79
print
print

#
# Compile and link with the library
#
lib = lbuild.make()

# prints 7
lib['whizbang'](d=7)
# prints 8
lib['whizbang'](d=8)

# Unadulterated access to C++,
foo = lib['ninja']()
print foo, 'ninjas'

# Note, we can't call helper becaues it is not extern "C"
# Don't do this:
#   lib['helper']

# Get primitives as return values (supports int64_t, int32_t, double)
x = 7
bar = lib['foobar'](x=x)
print 'x(=%d) + helper = %s' % (x, bar)

#
# Note: Vectors are CHandles
#
v = pycpc.vectors.CLongVector()
# We need to tell the vector how large it is (going) to be so functions like
# len(v) function properly in python
v.set_size(10)
# note: currently v has no backing memory, so 
# v[0] is a segfault...

# Allocate a double[10] to back v
lib['alloc'](p=v)

# v now backed by memory, so we can play with it
v[:] = range(10)
print v

# We can truncate the array
v.set_size(3)
print 'A length 3 array has len(v) =', len(v) # = 3
for i in v:
  print '%s + 1 = %s' % (i, i + 1)

#
# Now, remember that we have a .so sitting somewhere in /tmp 
# We can clean it up...
del lib

# But wait!! We called new double[10] but never freed the memory, we stil have 
print v
# Infact all of v,
v.set_size(10)
print v

# Since we still have a pointer, we can clean up the memory 
lbuild.inline_call(r''' delete [] v; ''', v=v)

# and note that lbuild will also have shared objects stored in temp. These
# will be deleted when python garbage collects lbuild, or we can force it
# to clean up /tmp/
del lbuild
