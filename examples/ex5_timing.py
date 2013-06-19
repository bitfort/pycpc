import sys
sys.path.append('python/')
import pycpc
import pycpc.vectors
import random

'''
A comparison of the runtime of optimized and unoptimized code, demonstrating
some useful features of pycpc
'''


# Optimized (-O3) compilation
ctx = pycpc.Context(flags=['O3'])
# Unoptimized (-O0) compilation
ctx_nopt = pycpc.Context(flags=['O0'])

# Include libraries to measure time
ctx.add_macro('#include <sys/time.h>')
ctx_nopt.add_macro('#include <sys/time.h>')

# start building a library
lbuild = pycpc.CPPLibBuilder(ctx)

# define a helper function to get the current microseconds
lbuild.raw_source(r'''
int64_t usec() {
  struct timeval tv;
  gettimeofday(&tv, NULL);
  int64_t s = tv.tv_sec * 1000 * 1000 + tv.tv_usec;
  return s;
}
''')

# Use this as a handle and as a type for the functions we declare
v = pycpc.vectors.CLongVector();

# Define the function we will be benchmarking, a serial sum of an array
lbuild.decl_func('bench', r'''
  int64_t start = usec();

  int64_t acc = 0;
  for (int64_t i = 0; i < l; i++) {
    acc += v[i];
  }

  // prevent for loop for being optimized out
  volatile int64_t side_effect;
  side_effect = acc;

  int64_t end = usec();
  return end-start;
''', v=v, l=long, rtype=long)

# A function to allocate an array
def alloc(ptr, size):
  lbuild.inline_call(r'ptr = new int64_t[size];',
      ptr=ptr, size=size);
  ptr.set_size(size)

#
# Enough C++ code, let's do it
#

# compile 2 versions of the .so
lib_O3 = lbuild.make()
lbuild.set_context(ctx_nopt)
lib_O0 = lbuild.make()

#
# Let's do some bench marking
#

#
# Hypothesis: -O3 will SIMD vectorize the summation
#
# Proxy: 2x speedup comes from vectorization if we have 128bit SIMD registers
#
# Protocol: Measure runtime of both routines, compute runtime and speedup
# Average across multiple runs which are done in random order
#
# Expected results: lib_O3 achieves a 2x speedup over lib_O0 
#

# Allocate 1MB of data
alloc(v, 1 << 17)

o3_runs = []
o0_runs = []
while len(o3_runs) < 1000 and len(o0_runs) < 1000:
  if random.random() < 0.5:
    o3_runs.append(lib_O3['bench'](v=v, l=len(v)))
  else:
    o0_runs.append(lib_O0['bench'](v=v, l=len(v)))

o3_mean = sum(o3_runs) / len(o3_runs)
o0_mean = sum(o0_runs) / len(o0_runs)

print '-O3 runs=%d   min,mean,max = %d,%d,%d' % (len(o3_runs), min(o3_runs), 
    o3_mean, max(o3_runs))
print '-O0 runs=%d   min,mean,max = %d,%d,%d' % (len(o0_runs), min(o0_runs), 
    o0_mean, max(o0_runs))

print 'Speedup is: ', o0_mean * 1.0 / o3_mean

#
# Results, at least on my computer
#
'''
-O3 runs=980   min,mean,max = 65,73,161
-O0 runs=1000   min,mean,max = 657,720,890
Speedup is:  9.86301369863
'''
# Does not support the hypothesis ... we see a 9.8x speedup instead
# of the 2x we expected. 
# Looks like -O3 is other neat optimizations; I guess our original 
# hypothesis was a little contrived.

# oops! we should probably free the memory !! 
# note: the .so files will be deleted for us when python cleans up our objects
lbuild.inline_call(r'delete [] v;', v=v);
