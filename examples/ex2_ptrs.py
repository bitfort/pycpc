import sys
sys.path.append('python/')
import pycpc

'''
Execute simple C++ in python using pointers

Pointers can be passed between C++
The following primitive pointers are supported:
  int32_t *
  int64_t *
  double *
'''

# specify compiler and flags
ctx = pycpc.Context(cc='g++', flags=['O3', 'Wall'])

# create a Library Builder which uses the given compiler and flags
lbuild = pycpc.CPPLibBuilder(ctx)


print
print 'Ex 0 -- create a pointer'
# Handles can be created for in/out variables
myint64 = pycpc.CHandle(long)
# Lets inspect the actual C++ source:
src = lbuild.inline_source(r'i = new int64_t; *i = 77;', i=myint64)
print "The soruce is:"
print src
print

# allocate
lbuild.inline_call(r'i = new int64_t; *i = 77;', i=myint64)

# make sure to clean up the memory
print 'Did I get back 77? ', myint64[0]

# clean up the memory
lbuild.inline_call(r'delete i;', i=myint64)

# don't call this again -- bad things will happen!! :
# print 'Did I get back 77? ', myint64[0]


print 
print 
print 'Ex 1 -- create arrays'
# double* arr = NULL;
arr = pycpc.CHandle(float)

lbuild.inline_call(r'arr = new double[5];', arr=arr)

lbuild.inline_call(
r'''
  for (int i = 0; i < 5; i++) {
    arr[i] = i + 0.5;
  }
''', arr=arr)

print 'arr =', arr[0], arr[1], arr[2], arr[3], arr[4]

# we can modify the array from python
arr[0] = 77.2
arr[3] = 88.7

lbuild.inline_call(
r'''
  printf("C++ deleting: ");
  for (int i = 0; i < 5; i++) {
    printf("%f ", arr[i]);
  }
  printf("\n");
  delete [] arr;
''', arr=arr)


print 
print 
print 'Ex 2 -- void pointers'
# We can support non-primitive types as void pointers
# We'll import std::vector
ctx.add_macro('#include <vector>')

# create a void*
voidp = pycpc.CHandle()

lbuild.inline_call(
r'''
  // void* voidp;
  std::vector<int> &v = *(new std::vector<int>());
  v.push_back(7);
  v.push_back(67);
  voidp = (void*) &v;
''', voidp=voidp)

# Don't try to call voidp[0] ... that won't work!!

lbuild.inline_call(
r'''
  std::vector<int> &v = *(std::vector<int>*) (voidp);
  printf("v[0] = %d, v[1] = %d\n", v[0], v[1]);
''', voidp=voidp)

# And don't forget to clean up!
lbuild.inline_call(r''' delete (char*) voidp; ''', voidp=voidp)


# short hand for types using "cast"

print 
print 
print 'Ex 3 -- void pointers short hand'
# We can support non-primitive types as void pointers
# We'll import std::vector
ctx.use_namespace('std')

# create a void*
vecp = pycpc.CHandle(cast='vector<int>')

# see what is going on in C++ 
print lbuild.inline_source(
r'''
  // do stuff here
  vecp = new vector<int>();
  delete vecp;
''', vecp=vecp)

# show that it works
lbuild.inline_call(
r'''
  // do stuff here
  vecp = new vector<int>();
  delete vecp;
''', vecp=vecp)
