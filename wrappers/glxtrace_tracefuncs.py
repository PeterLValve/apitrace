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


"""GLX tracing code generator."""


from gltrace import GlTracer
from specs.stdapi import Module, API
from specs.glapi import glapi
from specs.glxapi import glxapi


class glxTraceCallWriter(GlTracer):

    getProcAddressFunctionNames = [
        "glXGetProcAddress",
        "glXGetProcAddressARB",
    ]

    createContextFunctionNames = [
        'glXCreateContext',
        'glXCreateContextAttribsARB',
        'glXCreateContextWithConfigSGIX',
        'glXCreateNewContext',
    ]

    destroyContextFunctionNames = [
        'glXDestroyContext',
    ]

    makeCurrentFunctionNames = [
        'glXMakeCurrent',
        'glXMakeContextCurrent',
        'glXMakeCurrentReadSGI',
    ]

    def generateTraceFunctionImplBody(self, function):
        if function.name in self.destroyContextFunctionNames:
            print '    if ( makeRealCall ) {'
            print '        gltrace::releaseContext((uintptr_t)ctx);'
            print '    }'

        GlTracer.generateTraceFunctionImplBody(self, function)

        if function.name in self.createContextFunctionNames:
            print '    if ( makeRealCall ) {'
            print '        if (_result && _result != NULL)'
            print '            gltrace::createContext((uintptr_t)dpy, (uintptr_t)_result);'
            print '    }'

        if function.name in self.makeCurrentFunctionNames:
            print '    if ( makeRealCall ) {'
            print '        if (_result) {'
            print '            if (ctx != NULL)'
            print '                gltrace::setContext((uintptr_t)ctx);'
            print '            else'
            print '                gltrace::clearContext();'
            print '        }'
            print '    }'


if __name__ == '__main__':
    print
    print '#define _GDI32_'
    print
    print '#include <string.h>'
    print
    print '#include "trace_writer_local.hpp"'
    print
    print '// To validate our prototypes'
    print '#define GL_GLEXT_PROTOTYPES'
    print '#define WGL_GLXEXT_PROTOTYPES'
    print
    print '#include "glproc.hpp"'
    print '#include "glsize.hpp"'
    print

    module = Module()
    module.mergeModule(glapi)
    module.mergeModule(glxapi)
    api = API()
    api.addModule(module)
    tracer = glxTraceCallWriter()
    tracer.generateTraceCalls(api)