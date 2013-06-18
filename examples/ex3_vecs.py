import sys
sys.path.append('python/')
import pycpc
import pycpc.vectors

"""
A simple way to move arrays between C++ and Python
"""

# declare an empty vector
l = pycpc.vectors.CLongVector()

# populate it using C++ new (this is new int64_t[3])
l.allocate(3)

# set the values
l[:] = [1, 2, 3]

print l[0], l[1], l[2]

# reset the values!
l[:] = [4, 5, 6]
l[-1] = 7

# use python style iteration
for i in l:
  print i,
print

# crate a python list
copy = list(l)
copy.append(77)
print "My copy is: ", copy

# omg! Acts like a int64_t*
lbuild = pycpc.CPPLibBuilder(pycpc.Context())
lbuild.inline_call(r'''
  for (int i = 0; i < l_len; i++)
    printf("l[%d] = %ld\n", i, v[i]);
''', v=l, l_len=len(l))

# also supports doubles 
fl = pycpc.vectors.CDoubleVector()
fl.allocate(2)
fl[:] = [1.7, 7.2]

# prints like python lists
print 'fl =', fl

l[0] = 6
# Easy to sort in python
# note: this will incur a copy of the data, bad for big things
print 'unsorted list : ', l
l[:] = sorted(l)
print 'sorted list : ', l

# remember to free memory!
l.free()
fl.free()
print 'freed fl =', fl
