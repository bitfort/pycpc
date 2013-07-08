import context
import cppinl
import cmake
import os
import sys

compile_and_load_source = cmake.compile_and_load_source
CHandle = cppinl.CHandle
CPPLibBuilder = context.CPPLibBuilder
Context = context.Context

def invoke_main(main, cleanup=True):
  pid = os.fork()
  if pid == 0:
    main()
    sys.exit(0)
  else:
    pid, stat = os.wait()

    if stat != 0:
      print 'Error: exit status', stat
    if cleanup:
      cmake.del_temp_dir()
