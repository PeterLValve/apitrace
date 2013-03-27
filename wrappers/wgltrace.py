##########################################################################
#
# Copyright 2008-2009 VMware, Inc.
# All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
##########################################################################/


"""WGL tracing code generator."""


from gltrace import GlTracer
from specs.stdapi import Module, API
from specs.glapi import glapi
from specs.wglapi import wglapi


class WglTracer(GlTracer):

    getProcAddressFunctionNames = [
        "wglGetProcAddress",
    ]

    createContextFunctionNames = [
        'wglCreateContext',
        'wglCreateContextAttribsARB',
        'wglCreateLayerContext',
    ]

    destroyContextFunctionNames = [
        'wglDeleteContext',
    ]

    makeCurrentFunctionNames = [
        'wglMakeCurrent',
        'wglMakeContextCurrentARB',
        'wglMakeContextCurrentEXT',
    ]

if __name__ == '__main__':
    print
    print '#define _GDI32_'
    print
    print '#include <string.h>'
    print '#include <windows.h>'
    print
    print '#include "trace_writer_local.hpp"'
    print '#include "os.hpp"'
    print
    print '// To validate our prototypes'
    print '#define GL_GLEXT_PROTOTYPES'
    print '#define WGL_GLXEXT_PROTOTYPES'
    print
    print '#include "glproc.hpp"'
    print '#include "glsize.hpp"'
    print '#include "gltrace_state_snapshot.hpp"'
    print
    print 'namespace trace'
    print '{'
    print 'void snapshotState(void)'
    print '{'
    print '    gltrace::snapshotState();'
    print '}'
    print '}'
    print

    module = Module()
    module.mergeModule(glapi)
    module.mergeModule(wglapi)
    api = API()
    api.addModule(module)
    tracer = WglTracer()
    tracer.traceApi(api)
