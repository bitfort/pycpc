import sys
sys.path.append('python/')
import pycpc

'''
Execute simple C++ in python

Primitive types are mapped from python to C++
  python type : c++ type
  int : int32_t
  long : int64_t
  float : double
  str : char*
'''

# specify compiler and flags
ctx = pycpc.Context(cc='g++', flags=['O3', 'Wall'])

# create a Library Builder which uses the given compiler and flags
lbuild = pycpc.CPPLibBuilder(ctx)

print
print 'Ex 0'
# execute inline C++ code
lbuild.inline_call(
# IMPORTANT: use r''' ... ''' so \n doesn't become a newline
#     #
#     #
#   # # #
#    ###
#     #
      r'''
  // x is python type int, so gets C++ type int32_t
  printf("C++ says %d\n", x);
''', x = 5)

print
print 'Ex 1'
# Primitive conversions are for python types long, int, float and str
lbuild.inline_call(
r'''
  printf("int64_t %lx, int32_t %d, double %f, char* %s\n", l, i, f, s);
''', l=long(0xFFFFFFFFFF), i=0xF, f=5.2, s='hello, world.')

print
print 'Ex 2'
# Strings are mutable!
mystr = 'Hello, world'
lbuild.inline_call(
r'''
  // char *s;
  s[0] = ' '; s[1] = ' ';
  s[2] = 'b'; s[3] = 'y'; s[4] = 'e';
''', s=mystr)
# prints "  bye, world"
print mystr
