pycpc
=====

This is a light weight library that enables native C++ inline code in python.
For example, 

    lbuild.inline_call(r'''
    for (int i = 0; i < 3; i++) {
      printf("%d, ", i + foo);
    }
    printf("\n");
    ''', foo=7);

Which prints

    7, 8, 9, 

This is similar to packages such as scipy.weave.inline 
but pycpc is designed to be easy to install and have no dependenices. 
(e.g. http://docs.scipy.org/doc/scipy/reference/generated/scipy.weave.inline.html)

See the examples folder for example usage of this package. 


