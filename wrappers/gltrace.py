##########################################################################
#
# Copyright 2008-2010 VMware, Inc.
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


"""GL tracing generator."""


from trace import Tracer
from dispatch import function_pointer_type, function_pointer_value
import specs.stdapi as stdapi
import specs.glapi as glapi
import specs.glparams as glparams
from specs.glxapi import glxapi


class TypeGetter(stdapi.Visitor):
    '''Determine which glGet*v function that matches the specified type.'''

    def __init__(self, prefix = 'glGet', long_suffix = True, ext_suffix = ''):
        self.prefix = prefix
        self.long_suffix = long_suffix
        self.ext_suffix = ext_suffix

    def visitConst(self, const):
        return self.visit(const.type)

    def visitAlias(self, alias):
        if alias.expr == 'GLboolean':
            if self.long_suffix:
                suffix = 'Booleanv'
                arg_type = alias.expr
            else:
                suffix = 'iv'
                arg_type = 'GLint'
        elif alias.expr == 'GLdouble':
            if self.long_suffix:
                suffix = 'Doublev'
                arg_type = alias.expr
            else:
                suffix = 'dv'
                arg_type = alias.expr
        elif alias.expr == 'GLfloat':
            if self.long_suffix:
                suffix = 'Floatv'
                arg_type = alias.expr
            else:
                suffix = 'fv'
                arg_type = alias.expr
        elif alias.expr in ('GLint', 'GLuint', 'GLsizei'):
            if self.long_suffix:
                suffix = 'Integerv'
                arg_type = 'GLint'
            else:
                suffix = 'iv'
                arg_type = 'GLint'
        else:
            print alias.expr
            assert False
        function_name = self.prefix + suffix + self.ext_suffix
        return function_name, arg_type
    
    def visitEnum(self, enum):
        return self.visit(glapi.GLint)

    def visitBitmask(self, bitmask):
        return self.visit(glapi.GLint)

    def visitOpaque(self, pointer):
        return self.prefix + 'Pointerv' + self.ext_suffix, 'GLvoid *'


class GlTracer(Tracer):

    arrays = [
        ("Vertex", "VERTEX"),
        ("Normal", "NORMAL"),
        ("Color", "COLOR"),
        ("Index", "INDEX"),
        ("TexCoord", "TEXTURE_COORD"),
        ("EdgeFlag", "EDGE_FLAG"),
        ("FogCoord", "FOG_COORD"),
        ("SecondaryColor", "SECONDARY_COLOR"),
    ]
    arrays.reverse()

    # arrays available in PROFILE_ES1
    arrays_es1 = ("Vertex", "Normal", "Color", "TexCoord")

    def header(self, api):
        Tracer.header(self, api)

        print '#include "gltrace.hpp"'
        print
        
        # Which glVertexAttrib* variant to use
        print 'enum vertex_attrib {'
        print '    VERTEX_ATTRIB,'
        print '    VERTEX_ATTRIB_ARB,'
        print '    VERTEX_ATTRIB_NV,'
        print '};'
        print
        print 'static vertex_attrib _get_vertex_attrib(void) {'
        print '    gltrace::Context *ctx = gltrace::getContext();'
        print '    if (ctx->user_arrays_arb || ctx->user_arrays_nv) {'
        print '        GLboolean _vertex_program = GL_FALSE;'
        print '        _glGetBooleanv(GL_VERTEX_PROGRAM_ARB, &_vertex_program);'
        print '        if (_vertex_program) {'
        print '            if (ctx->user_arrays_nv) {'
        print '                GLint _vertex_program_binding_nv = 0;'
        print '                _glGetIntegerv(GL_VERTEX_PROGRAM_BINDING_NV, &_vertex_program_binding_nv);'
        print '                if (_vertex_program_binding_nv) {'
        print '                    return VERTEX_ATTRIB_NV;'
        print '                }'
        print '            }'
        print '            return VERTEX_ATTRIB_ARB;'
        print '        }'
        print '    }'
        print '    return VERTEX_ATTRIB;'
        print '}'
        print

        self.defineShadowBufferHelper()

        # Whether we need user arrays
        print 'static inline bool _need_user_arrays(void)'
        print '{'
        print '    gltrace::Context *ctx = gltrace::getContext();'
        print '    if (!ctx->user_arrays) {'
        print '        return false;'
        print '    }'
        print

        for camelcase_name, uppercase_name in self.arrays:
            # in which profile is the array available?
            profile_check = 'ctx->profile == gltrace::PROFILE_COMPAT'
            if camelcase_name in self.arrays_es1:
                profile_check = '(' + profile_check + ' || ctx->profile == gltrace::PROFILE_ES1)';

            function_name = 'gl%sPointer' % camelcase_name
            enable_name = 'GL_%s_ARRAY' % uppercase_name
            binding_name = 'GL_%s_ARRAY_BUFFER_BINDING' % uppercase_name
            print '    // %s' % function_name
            print '  if (%s) {' % profile_check
            self.array_prolog(api, uppercase_name)
            print '    if (_glIsEnabled(%s)) {' % enable_name
            print '        GLint _binding = 0;'
            print '        _glGetIntegerv(%s, &_binding);' % binding_name
            print '        if (!_binding) {'
            self.array_cleanup(api, uppercase_name)
            print '            return true;'
            print '        }'
            print '    }'
            self.array_epilog(api, uppercase_name)
            print '  }'
            print

        print '    // ES1 does not support generic vertex attributes'
        print '    if (ctx->profile == gltrace::PROFILE_ES1)'
        print '        return false;'
        print
        print '    vertex_attrib _vertex_attrib = _get_vertex_attrib();'
        print
        print '    // glVertexAttribPointer'
        print '    if (_vertex_attrib == VERTEX_ATTRIB) {'
        print '        GLint _max_vertex_attribs = 0;'
        print '        _glGetIntegerv(GL_MAX_VERTEX_ATTRIBS, &_max_vertex_attribs);'
        print '        for (GLint index = 0; index < _max_vertex_attribs; ++index) {'
        print '            GLint _enabled = 0;'
        print '            _glGetVertexAttribiv(index, GL_VERTEX_ATTRIB_ARRAY_ENABLED, &_enabled);'
        print '            if (_enabled) {'
        print '                GLint _binding = 0;'
        print '                _glGetVertexAttribiv(index, GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING, &_binding);'
        print '                if (!_binding) {'
        print '                    return true;'
        print '                }'
        print '            }'
        print '        }'
        print '    }'
        print
        print '    // glVertexAttribPointerARB'
        print '    if (_vertex_attrib == VERTEX_ATTRIB_ARB) {'
        print '        GLint _max_vertex_attribs = 0;'
        print '        _glGetIntegerv(GL_MAX_VERTEX_ATTRIBS_ARB, &_max_vertex_attribs);'
        print '        for (GLint index = 0; index < _max_vertex_attribs; ++index) {'
        print '            GLint _enabled = 0;'
        print '            _glGetVertexAttribivARB(index, GL_VERTEX_ATTRIB_ARRAY_ENABLED_ARB, &_enabled);'
        print '            if (_enabled) {'
        print '                GLint _binding = 0;'
        print '                _glGetVertexAttribivARB(index, GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING_ARB, &_binding);'
        print '                if (!_binding) {'
        print '                    return true;'
        print '                }'
        print '            }'
        print '        }'
        print '    }'
        print
        print '    // glVertexAttribPointerNV'
        print '    if (_vertex_attrib == VERTEX_ATTRIB_NV) {'
        print '        for (GLint index = 0; index < 16; ++index) {'
        print '            GLint _enabled = 0;'
        print '            _glGetIntegerv(GL_VERTEX_ATTRIB_ARRAY0_NV + index, &_enabled);'
        print '            if (_enabled) {'
        print '                return true;'
        print '            }'
        print '        }'
        print '    }'
        print

        print '    return false;'
        print '}'
        print

        print 'static void _trace_user_arrays(GLuint count);'
        print

        # Buffer mappings
        print '// whether glMapBufferRange(GL_MAP_WRITE_BIT) has ever been called'
        print 'static bool _checkBufferMapRange = false;'
        print
        print '// whether glBufferParameteriAPPLE(GL_BUFFER_FLUSHING_UNMAP_APPLE, GL_FALSE) has ever been called'
        print 'static bool _checkBufferFlushingUnmapAPPLE = false;'
        print
        # Buffer mapping information, necessary for old Mesa 2.1 drivers which
        # do not support glGetBufferParameteriv(GL_BUFFER_ACCESS_FLAGS/GL_BUFFER_MAP_LENGTH)
        print 'struct buffer_mapping {'
        print '    void *map;'
        print '    GLint length;'
        print '    bool write;'
        print '    bool explicit_flush;'
        print '};'
        print
        for target in self.buffer_targets:
            print 'struct buffer_mapping _%s_mapping;' % target.lower();
        print
        print 'static inline struct buffer_mapping *'
        print 'get_buffer_mapping(GLenum target) {'
        print '    switch (target) {'
        for target in self.buffer_targets:
            print '    case GL_%s:' % target
            print '        return & _%s_mapping;' % target.lower()
        print '    default:'
        print '        os::log("apitrace: warning: unknown buffer target 0x%04X\\n", target);'
        print '        return NULL;'
        print '    }'
        print '}'
        print

        # Generate a helper function to determine whether a parameter name
        # refers to a symbolic value or not
        print 'static bool'
        print 'is_symbolic_pname(GLenum pname) {'
        print '    switch (pname) {'
        for function, type, count, name in glparams.parameters:
            if type is glapi.GLenum:
                print '    case %s:' % name
        print '        return true;'
        print '    default:'
        print '        return false;'
        print '    }'
        print '}'
        print
        
        # Generate a helper function to determine whether a parameter value is
        # potentially symbolic or not; i.e., if the value can be represented in
        # an enum or not
        print 'template<class T>'
        print 'static inline bool'
        print 'is_symbolic_param(T param) {'
        print '    return static_cast<T>(static_cast<GLenum>(param)) == param;'
        print '}'
        print

        # Generate a helper function to know how many elements a parameter has
        print 'static size_t'
        print '_gl_param_size(GLenum pname) {'
        print '    switch (pname) {'
        for function, type, count, name in glparams.parameters:
            if type is not None:
                print '    case %s: return %s;' % (name, count)
        print '    default:'
        print r'        os::log("apitrace: warning: %s: unknown GLenum 0x%04X\n", __FUNCTION__, pname);'
        print '        return 1;'
        print '    }'
        print '}'
        print

        # states such as GL_UNPACK_ROW_LENGTH are not available in GLES
        print 'bool'
        print 'can_unpack_subimage(void) {'
        print '    gltrace::Context *ctx = gltrace::getContext();'
        print '    return (ctx->profile == gltrace::PROFILE_COMPAT);'
        print '}'
        print

    getProcAddressFunctionNames = ["glXGetProcAddress", "glXGetProcAddressARB", "wglGetProcAddress"]

    def generateEntrypoints(self, api):
        Tracer.generateEntrypoints(self, api)

        if self.getProcAddressFunctionNames:
            # Generate a function to wrap proc addresses
            getProcAddressFunction = api.getFunctionByName(self.getProcAddressFunctionNames[0])
            argType = getProcAddressFunction.args[0].type
            retType = getProcAddressFunction.type
            print '%s _wrapProcAddress(%s procName, %s procPtr) {' % (retType, argType, retType)
            print '    if (!procPtr) {'
            print '        return procPtr;'
            print '    }'
            for function in api.getAllFunctions():
                ptype = function_pointer_type(function)
                pvalue = function_pointer_value(function)
                print '    if (strcmp("%s", (const char *)procName) == 0) {' % function.name
                print '        %s = (%s)procPtr;' % (pvalue, ptype)
                print '        return (%s)&%s;' % (retType, function.name,)
                print '    }'
            print '    os::log("apitrace: warning: unknown function \\"%s\\"\\n", (const char *)procName);'
            print '    return procPtr;'
            print '}'
            print

    def defineShadowBufferHelper(self):
        print 'void _shadow_glGetBufferSubData(GLenum target, GLintptr offset,'
        print '                                GLsizeiptr size, GLvoid *data)'
        print '{'
        print '    gltrace::Context *ctx = gltrace::getContext();'
        print '    if (!ctx->needsShadowBuffers() || target != GL_ELEMENT_ARRAY_BUFFER) {'
        print '        _glGetBufferSubData(target, offset, size, data);'
        print '        return;'
        print '    }'
        print
        print '    GLint buffer_binding = 0;'
        print '    _glGetIntegerv(GL_ELEMENT_ARRAY_BUFFER_BINDING, &buffer_binding);'
        print '    if (buffer_binding > 0) {'
        print '        gltrace::Buffer & buf = ctx->buffers[buffer_binding];'
        print '        buf.getSubData(offset, size, data);'
        print '    }'
        print '}'

    def shadowBufferMethod(self, method):
        # Emit code to fetch the shadow buffer, and invoke a method
        print '    gltrace::Context *ctx = gltrace::getContext();'
        print '    if (ctx->needsShadowBuffers() && target == GL_ELEMENT_ARRAY_BUFFER) {'
        print '        GLint buffer_binding = 0;'
        print '        _glGetIntegerv(GL_ELEMENT_ARRAY_BUFFER_BINDING, &buffer_binding);'
        print '        if (buffer_binding > 0) {'
        print '            gltrace::Buffer & buf = ctx->buffers[buffer_binding];'
        print '            buf.' + method + ';'
        print '        }'
        print '    }'
        print

    def shadowBufferProlog(self, function):
        if function.name in ('glBufferData', 'glBufferDataARB'):
            self.shadowBufferMethod('bufferData(size, data)')

        if function.name in ('glBufferSubData', 'glBufferSubDataARB'):
            self.shadowBufferMethod('bufferSubData(offset, size, data)')

        if function.name in ('glDeleteBuffers', 'glDeleteBuffersARB'):
            print '    gltrace::Context *ctx = gltrace::getContext();'
            print '    if (ctx->needsShadowBuffers()) {'
            print '        for (GLsizei i = 0; i < n; i++) {'
            print '            ctx->buffers.erase(%s[i]);' % function.args[1].name
            print '        }'
            print '    }'

    array_pointer_function_names = set((
        "glVertexPointer",
        "glNormalPointer",
        "glColorPointer",
        "glIndexPointer",
        "glTexCoordPointer",
        "glEdgeFlagPointer",
        "glFogCoordPointer",
        "glSecondaryColorPointer",
        
        "glInterleavedArrays",

        "glVertexPointerEXT",
        "glNormalPointerEXT",
        "glColorPointerEXT",
        "glIndexPointerEXT",
        "glTexCoordPointerEXT",
        "glEdgeFlagPointerEXT",
        "glFogCoordPointerEXT",
        "glSecondaryColorPointerEXT",

        "glVertexAttribPointer",
        "glVertexAttribPointerARB",
        "glVertexAttribPointerNV",
        "glVertexAttribIPointer",
        "glVertexAttribIPointerEXT",
        "glVertexAttribLPointer",
        "glVertexAttribLPointerEXT",
        
        #"glMatrixIndexPointerARB",
    ))

    draw_function_names = set((
        'glDrawArrays',
        'glDrawElements',
        'glDrawRangeElements',
        'glMultiDrawArrays',
        'glMultiDrawElements',
        'glDrawArraysInstanced',
        "glDrawArraysInstancedBaseInstance",
        'glDrawElementsInstanced',
        'glDrawArraysInstancedARB',
        'glDrawElementsInstancedARB',
        'glDrawElementsBaseVertex',
        'glDrawRangeElementsBaseVertex',
        'glDrawElementsInstancedBaseVertex',
        "glDrawElementsInstancedBaseInstance",
        "glDrawElementsInstancedBaseVertexBaseInstance",
        'glMultiDrawElementsBaseVertex',
        'glDrawArraysIndirect',
        'glDrawElementsIndirect',
        'glMultiDrawArraysIndirect',
        'glMultiDrawArraysIndirectAMD',
        'glMultiDrawElementsIndirect',
        'glMultiDrawElementsIndirectAMD',
        'glDrawArraysEXT',
        'glDrawRangeElementsEXT',
        'glDrawRangeElementsEXT_size',
        'glMultiDrawArraysEXT',
        'glMultiDrawElementsEXT',
        'glMultiModeDrawArraysIBM',
        'glMultiModeDrawElementsIBM',
        'glDrawArraysInstancedEXT',
        'glDrawElementsInstancedEXT',
    ))

    interleaved_formats = [
         'GL_V2F',
         'GL_V3F',
         'GL_C4UB_V2F',
         'GL_C4UB_V3F',
         'GL_C3F_V3F',
         'GL_N3F_V3F',
         'GL_C4F_N3F_V3F',
         'GL_T2F_V3F',
         'GL_T4F_V4F',
         'GL_T2F_C4UB_V3F',
         'GL_T2F_C3F_V3F',
         'GL_T2F_N3F_V3F',
         'GL_T2F_C4F_N3F_V3F',
         'GL_T4F_C4F_N3F_V4F',
    ]

    frame_terminator_functions = set((
        "wglSwapBuffers",
    ))

    ## these are always traced
    state_setup_entrypoints = (
        'glGenLists',
        'glDeleteLists',
        'glGenTextures',
        'glDeleteTextures',
        'glGenQueries',
        'glDeleteQueries',
        'glGenBuffers',
        'glDeleteBuffers',
        'glGenBuffersARB',
        'glDeleteBuffersARB',
        'glGenQueriesARB',
        'glDeleteQueriesARB',
        'glDeleteObjectARB',
        'glGenRenderbuffers',
        'glDeleteRenderbuffers',
        'glGenFramebuffers',
        'glDeleteFramebuffers',
        'glGenVertexArrays',
        'glDeleteVertexArrays',
        'glFenceSync',
        'glDeleteSync',
        'glDeleteNamedStringARB',
        'glGenSamplers',
        'glDeleteSamplers',
        'glGenTransformFeedbacks',
        'glDeleteTransformFeedbacks',
        'glGenTexturesEXT',
        'glDeleteTexturesEXT',
        'glGenAsyncMarkersSGIX',
        'glDeleteAsyncMarkersSGIX',
        'glGenFencesNV',
        'glDeleteFencesNV',
        'glGenProgramsNV',
        'glDeleteProgramsNV',
        'glGenFragmentShadersATI',
        'glDeleteFragmentShaderATI',
        'glGenVertexShadersEXT',
        'glDeleteVertexShaderEXT',
        'glGenSymbolsEXT',
        'glGenOcclusionQueriesNV',
        'glDeleteOcclusionQueriesNV',
        'glGenFencesAPPLE',
        'glDeleteFencesAPPLE',
        'glGenVertexArraysAPPLE',
        'glDeleteVertexArraysAPPLE',
        'glGenRenderbuffersEXT',
        'glDeleteRenderbuffersEXT',
        'glGenFramebuffersEXT',
        'glDeleteFramebuffersEXT',
        'glGenTransformFeedbacksNV',
        'glDeleteTransformFeedbacksNV',
        'glGenNamesAMD',
        'glDeleteNamesAMD',
        'glNewBufferRegion',
        'glDeleteBufferRegion',
        'wglCreateContext',
        'wglDeleteContext',
        'wglMakeCurrent',
        'wglCopyContext',
        'wglChoosePixelFormat',
        'wglShareLists',
        'wglCreateLayerContext',
        'wglSetLayerPaletteEntries',
        'wglRealizeLayerPalette',
        'wglUseFontBitmapsA',
        'wglUseFontBitmapsW',
        'wglUseFontOutlinesA',
        'wglUseFontOutlinesW',
        'wglCreateBufferRegionARB',
        'wglSaveBufferRegionARB',
        'wglRestoreBufferRegionARB',
        'wglChoosePixelFormatARB',
        'wglChoosePixelFormatARB',
        'wglMakeContextCurrentARB',
        'wglCreatePbufferARB',
        'wglReleasePbufferDCARB',
        'wglDestroyPbufferARB',
        'wglBindTexImageARB',
        'wglReleaseTexImageARB',
        'wglSetPbufferAttribARB',
        'wglCreateContextAttribsARB',
        'wglMakeContextCurrentEXT',
        'wglChoosePixelFormatEXT',
        'wglSwapIntervalEXT',
        'wglAllocateMemoryNV',
        'wglFreeMemoryNV',


        ## texture state
        'glTexImage1D',
        'glTexImage2D',
        'glTexImage3D',
        'glCompressedTexImage1D',
        'glCompressedTexImage2D',
        'glCompressedTexImage3D',
        'glGenerateMipmap',



        ## texture EXT_direct_state_access
        'glTextureImage1D',
        'glTextureImage2D',
        'glTextureImage3D',
        'glCompressedTextureImage1D',
        'glCompressedTextureImage2D',
        'glCompressedTextureImage3D',

        ## shaders and programs
        'glCreateProgram',
        'glDeleteProgram',
        'glCreateShader',
        'glDeleteShader',
        'glLinkProgram',

        ## ARB shaders and programs
        'glGenProgramsARB',
        'glDeleteProgramsARB',
        'glCreateShaderObjectARB',
        'glCreateProgramObjectARB',
        'glLinkProgramARB',

        ## ARB separate shader objects
        'glGenProgramPipelines',
        'glDeleteProgramPipelines',
        'glCreateShaderProgramv',
        'glCreateShaderProgramEXT',
    )

    def generateTraceCallDecls(self, api):
        self.generateTraceCallHeader(api)

        print 'bool can_unpack_subimage(void);'

        # declare a function to wrap proc addresses
        getProcAddressFunction = api.getFunctionByName(self.getProcAddressFunctionNames[0])
        argType = getProcAddressFunction.args[0].type
        retType = getProcAddressFunction.type
        print 'extern %s _wrapProcAddress(%s procName, %s procPtr);' % (retType, argType, retType)
        print

        for function in api.getAllFunctions():
            self.traceFunctionDecl(function)

    def generateTraceFunctionImplBody(self, function):
        # Defer tracing of user array pointers...
        if function.name in self.array_pointer_function_names:
            print '    GLint _array_buffer = 0;'
            print '    _glGetIntegerv(GL_ARRAY_BUFFER_BINDING, &_array_buffer);'
            print '    if (!_array_buffer) {'
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        ctx->user_arrays = true;'
            if function.name == "glVertexAttribPointerARB":
                print '        ctx->user_arrays_arb = true;'
            if function.name == "glVertexAttribPointerNV":
                print '        ctx->user_arrays_nv = true;'
            self.invokeFunction(function, '        ')

            # And also break down glInterleavedArrays into the individual calls
            if function.name == 'glInterleavedArrays':
                print

                # Initialize the enable flags
                for camelcase_name, uppercase_name in self.arrays:
                    flag_name = '_' + uppercase_name.lower()
                    print '        GLboolean %s = GL_FALSE;' % flag_name
                print

                # Switch for the interleaved formats
                print '        switch (format) {'
                for format in self.interleaved_formats:
                    print '            case %s:' % format
                    for camelcase_name, uppercase_name in self.arrays:
                        flag_name = '_' + uppercase_name.lower()
                        if format.find('_' + uppercase_name[0]) >= 0:
                            print '                %s = GL_TRUE;' % flag_name
                    print '                break;'
                print '            default:'
                print '               return;'
                print '        }'
                print

                # Emit fake glEnableClientState/glDisableClientState flags
                for camelcase_name, uppercase_name in self.arrays:
                    flag_name = '_' + uppercase_name.lower()
                    enable_name = 'GL_%s_ARRAY' % uppercase_name

                    # Emit a fake function
                    print '        {'
                    print '            static const trace::FunctionSig &_sig = %s ? _glEnableClientState_sig : _glDisableClientState_sig;' % flag_name
                    print '            unsigned _call = trace::localWriter.beginEnter(&_sig);'
                    print '            trace::localWriter.beginArg(0);'
                    self.serializeValue(glapi.GLenum, enable_name)
                    print '            trace::localWriter.endArg();'
                    print '            trace::localWriter.endEnter();'
                    print '            trace::localWriter.beginLeave(_call);'
                    print '            trace::localWriter.endLeave();'
                    print '        }'

            print '        return;'
            print '    }'

        # ... to the draw calls
        if function.name in self.draw_function_names:
            print '    if (_need_user_arrays()) {'
            arg_names = ', '.join([arg.name for arg in function.args[1:]])
            print '        GLuint _count = _%s_count(%s);' % (function.name, arg_names)
            print '        _trace_user_arrays(_count);'
            print '    }'

        # Emit a fake memcpy on buffer uploads
        if function.name == 'glBufferParameteriAPPLE':
            print '    if (pname == GL_BUFFER_FLUSHING_UNMAP_APPLE && param == GL_FALSE) {'
            print '        _checkBufferFlushingUnmapAPPLE = true;'
            print '    }'
        if function.name in ('glUnmapBuffer', 'glUnmapBufferARB'):
            if function.name.endswith('ARB'):
                suffix = 'ARB'
            else:
                suffix = ''
            print '    GLint access = 0;'
            print '    _glGetBufferParameteriv%s(target, GL_BUFFER_ACCESS, &access);' % suffix
            print '    if (access != GL_READ_ONLY) {'
            print '        GLvoid *map = NULL;'
            print '        _glGetBufferPointerv%s(target, GL_BUFFER_MAP_POINTER, &map);'  % suffix
            print '        struct buffer_mapping *mapping = get_buffer_mapping(target);'
            print '        if (map == NULL && mapping != NULL) {'
            print '            map = mapping->map;'
            print '        }'
            print '        if (map) {'
            print '            GLint length = -1;'
            print '            bool flush = true;'
            print '            if (_checkBufferMapRange) {'
            print '                _glGetBufferParameteriv%s(target, GL_BUFFER_MAP_LENGTH, &length);' % suffix
            print '                GLint access_flags = 0;'
            print '                _glGetBufferParameteriv(target, GL_BUFFER_ACCESS_FLAGS, &access_flags);'
            print '                flush = flush && !(access_flags & GL_MAP_FLUSH_EXPLICIT_BIT);'
            print '                if (length == -1) {'
            print '                    // Mesa drivers refuse GL_BUFFER_MAP_LENGTH without GL 3.0'
            print '                    static bool warned = false;'
            print '                    if (!warned) {'
            print '                        os::log("apitrace: warning: glGetBufferParameteriv%s(GL_BUFFER_MAP_LENGTH) failed\\n");' % suffix
            print '                        warned = true;'
            print '                    }'
            print '                    if (mapping) {'
            print '                        length = mapping->length;'
            print '                        flush = flush && !mapping->explicit_flush;'
            print '                    } else {'
            print '                        length = 0;'
            print '                        flush = false;'
            print '                    }'
            print '                }'
            print '            } else {'
            print '                length = 0;'
            print '                _glGetBufferParameteriv%s(target, GL_BUFFER_SIZE, &length);' % suffix
            print '            }'
            print '            if (_checkBufferFlushingUnmapAPPLE) {'
            print '                GLint flushing_unmap = GL_TRUE;'
            print '                _glGetBufferParameteriv%s(target, GL_BUFFER_FLUSHING_UNMAP_APPLE, &flushing_unmap);' % suffix
            print '                flush = flush && flushing_unmap;'
            print '            }'
            print '            if (flush && length > 0) {'
            self.emit_memcpy('map', 'map', 'length')
            print '            }'
            print '        }'
            print '    }'
        if function.name == 'glUnmapBufferOES':
            print '    GLint access = 0;'
            print '    _glGetBufferParameteriv(target, GL_BUFFER_ACCESS_OES, &access);'
            print '    if (access == GL_WRITE_ONLY_OES) {'
            print '        GLvoid *map = NULL;'
            print '        _glGetBufferPointervOES(target, GL_BUFFER_MAP_POINTER_OES, &map);'
            print '        struct buffer_mapping *mapping = get_buffer_mapping(target);'
            print '        if (map == NULL && mapping != NULL) {'
            print '            map = mapping->map;'
            print '        }'
            print '        GLint size = 0;'
            print '        _glGetBufferParameteriv(target, GL_BUFFER_SIZE, &size);'
            print '        if (map && size > 0) {'
            self.emit_memcpy('map', 'map', 'size')
            self.shadowBufferMethod('bufferSubData(0, size, map)')
            print '        }'
            print '    }'
        if function.name == 'glUnmapNamedBufferEXT':
            print '    GLint access_flags = 0;'
            print '    _glGetNamedBufferParameterivEXT(buffer, GL_BUFFER_ACCESS_FLAGS, &access_flags);'
            print '    if ((access_flags & GL_MAP_WRITE_BIT) && !(access_flags & GL_MAP_FLUSH_EXPLICIT_BIT)) {'
            print '        GLvoid *map = NULL;'
            print '        _glGetNamedBufferPointervEXT(buffer, GL_BUFFER_MAP_POINTER, &map);'
            print '        struct buffer_mapping *mapping = get_buffer_mapping(buffer);'
            print '        if (map == NULL && mapping != NULL) {'
            print '            map = mapping->map;'
            print '        }'
            print '        GLint length = 0;'
            print '        _glGetNamedBufferParameterivEXT(buffer, GL_BUFFER_MAP_LENGTH, &length);'
            print '        if (map && length > 0) {'
            self.emit_memcpy('map', 'map', 'length')
            print '        }'
            print '    }'
        if function.name == 'glFlushMappedBufferRange':
            print '    GLvoid *map = NULL;'
            print '    _glGetBufferPointerv(target, GL_BUFFER_MAP_POINTER, &map);'
            print '    struct buffer_mapping *mapping = get_buffer_mapping(target);'
            print '    if (map == NULL && mapping != NULL) {'
            print '        map = mapping->map;'
            print '    }'
            print '    if (map && length > 0) {'
            self.emit_memcpy('(char *)map + offset', '(const char *)map + offset', 'length')
            print '    }'
        if function.name == 'glFlushMappedBufferRangeAPPLE':
            print '    GLvoid *map = NULL;'
            print '    _glGetBufferPointerv(target, GL_BUFFER_MAP_POINTER, &map);'
            print '    struct buffer_mapping *mapping = get_buffer_mapping(target);'
            print '    if (map == NULL && mapping != NULL) {'
            print '        map = mapping->map;'
            print '    }'
            print '    if (map && size > 0) {'
            self.emit_memcpy('(char *)map + offset', '(const char *)map + offset', 'size')
            print '    }'
        if function.name == 'glFlushMappedNamedBufferRangeEXT':
            print '    GLvoid *map = NULL;'
            print '    _glGetNamedBufferPointervEXT(buffer, GL_BUFFER_MAP_POINTER, &map);'
            print '    struct buffer_mapping *mapping = get_buffer_mapping(buffer);'
            print '    if (map == NULL && mapping != NULL) {'
            print '        map = mapping->map;'
            print '    }'
            print '    if (map && length > 0) {'
            self.emit_memcpy('(char *)map + offset', '(const char *)map + offset', 'length')
            print '    }'

        self.shadowBufferProlog(function)

        if function.name in ('glCreateShaderProgramv', 'glCreateShaderProgramEXT'):
            print '    // When tracing setup functions we do not want to trace the call.'
            print '    // Instead will query some parameters and emit the trace call at a later time.'
            print '    if (trace::isTracingStateSetupFunctions() == false)'
            print '    {'
            Tracer.generateTraceFunctionImplBodyArgs(self, function)
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            Tracer.generateTraceFunctionImplBodyReturn(self, function)
            print '    } else {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            if function.name == 'glCreateShaderProgramEXT':
                print '        GLuint count = 1;'
                print '        const GLchar * const * strings = &string;'
            print '        if (count > 0 && strings != NULL) {'
            print '            gltrace::Context *ctx = gltrace::getContext();'
            print '            ctx->separateShaders[_result].SetSources(type, count, strings, NULL);'
            print '        }'
            print '        return _result;'
            print '    }'
            print

        elif function.name in ('glLinkProgram', 'glLinkProgramARB'):
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)

            print '    // When tracing setup functions we do not want to trace the call.'
            print '    // Instead will query some parameters and emit the trace call at a later time.'
            print '    if (trace::isTracingStateSetupFunctions() == false) {'

            # Don't leave vertex attrib locations to chance.  Instead emit fake
            # glBindAttribLocation calls to ensure that the same locations will be
            # used when retracing.  Trying to remap locations after the fact would
            # be an herculian task given that vertex attrib locations appear in
            # many entry-points, including non-shader related ones.
            if function.name == 'glLinkProgram':
                print '        GLint active_attributes = 0;'
                print '        _glGetProgramiv(program, GL_ACTIVE_ATTRIBUTES, &active_attributes);'
                print '        for (GLint attrib = 0; attrib < active_attributes; ++attrib) {'
                print '            GLint size = 0;'
                print '            GLenum type = 0;'
                print '            GLint active_attribute_max_length = 0;'
                print '            _glGetProgramiv(program, GL_ACTIVE_ATTRIBUTE_MAX_LENGTH, &active_attribute_max_length);'
                print '            GLchar* name = (GLchar*)malloc(sizeof(GLchar) * active_attribute_max_length);'
                print '            _glGetActiveAttrib(program, attrib, sizeof name, NULL, &size, &type, name);'
                print "            if (name[0] != 'g' || name[1] != 'l' || name[2] != '_') {"
                print '                GLint location = _glGetAttribLocation(program, name);'
                print '                if (location >= 0) {'
                bind_function = glapi.glapi.getFunctionByName('glBindAttribLocation')
                self.fake_call(bind_function, ['program', 'location', 'name'])
                print '                }'
                print '            }'
                print '            free(name);'
                print '        }'
            if function.name == 'glLinkProgramARB':
                print '        GLint active_attributes = 0;'
                print '        _glGetObjectParameterivARB(programObj, GL_OBJECT_ACTIVE_ATTRIBUTES_ARB, &active_attributes);'
                print '        for (GLint attrib = 0; attrib < active_attributes; ++attrib) {'
                print '            GLint size = 0;'
                print '            GLenum type = 0;'
                print '            GLint active_attribute_max_length = 0;'
                print '            _glGetObjectParameterivARB(programObj, GL_OBJECT_ACTIVE_UNIFORM_MAX_LENGTH_ARB, &active_attribute_max_length);'
                print '            GLcharARB* name = (GLcharARB*)malloc(sizeof(GLcharARB) * active_attribute_max_length);'
                print '            _glGetActiveAttribARB(programObj, attrib, sizeof name, NULL, &size, &type, name);'
                print "            if (name[0] != 'g' || name[1] != 'l' || name[2] != '_') {"
                print '                GLint location = _glGetAttribLocationARB(programObj, name);'
                print '                if (location >= 0) {'
                bind_function = glapi.glapi.getFunctionByName('glBindAttribLocationARB')
                self.fake_call(bind_function, ['programObj', 'location', 'name'])
                print '                }'
                print '            }'
                print '            free(name);'
                print '        }'
            Tracer.generateTraceFunctionImplBodyArgs(self, function)
            Tracer.generateTraceFunctionImplBodyReturn(self, function)
            print '    } else {'
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        GLint numAttachedShaders = 0;'
            print '        _glGetProgramiv(%s, GL_ATTACHED_SHADERS, &numAttachedShaders);' % function.args[0].name
            print '        GLuint* shaders = (GLuint*)malloc(sizeof(GLuint) * numAttachedShaders);'
            print '        _glGetAttachedShaders(%s, numAttachedShaders, NULL, shaders);' % function.args[0].name
            print '        for (GLint shaderIndex = 0; shaderIndex < numAttachedShaders; ++shaderIndex) {'
            print '            if (_glIsProgram(%s) == GL_TRUE) {' % function.args[0].name
            print '                ctx->programs[%s].AddShader(shaders[shaderIndex]);' % function.args[0].name
            print '            } else if (_glIsProgramARB(%s) == GL_TRUE) {' % function.args[0].name
            print '                ctx->programsARB[%s].AddShader(shaders[shaderIndex]);' % function.args[0].name
            print '            } else {'
            print '                assert(!"Unknown program type");'
            print '            }'
            print '        }'
            print '        free(shaders);'
            print '        shaders = NULL;'
            if function.name == 'glLinkProgramARB':
                print '        if (_glIsProgram(%s) == GL_TRUE) {' % function.args[0].name
                print '            ctx->programs[%s].m_linkedWithARB = true;' % function.args[0].name
                print '        } else {'
                print '            ctx->programsARB[%s].m_linkedWithARB = true;' % function.args[0].name
                print '        }'
            print '    }'
        elif function.name in ('glGenerateMipmap'):
            print '    // glGenerateMipmap calls are special cased'
            print '    // when tracing setup functions we only want to track the parameters, not trace the call.'
            print '    // The actual call will be added to the trace at a later time.'
            print '    unsigned _tmpCall = 0;'
            print '    if (trace::isTracingStateSetupFunctions()) {'
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        GLint boundTexture = 0;'
            print '        if (target == GL_TEXTURE_1D) _glGetIntegerv(GL_TEXTURE_BINDING_1D, &boundTexture);'
            print '        else if (target == GL_TEXTURE_1D_ARRAY) _glGetIntegerv(GL_TEXTURE_BINDING_1D_ARRAY, &boundTexture);'
            print '        else if (target == GL_TEXTURE_2D) _glGetIntegerv(GL_TEXTURE_BINDING_2D, &boundTexture);'
            print '        else if (target == GL_TEXTURE_2D_ARRAY) _glGetIntegerv(GL_TEXTURE_BINDING_2D_ARRAY, &boundTexture);'
            print '        else if (target == GL_TEXTURE_3D) _glGetIntegerv(GL_TEXTURE_BINDING_3D, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            
            print '        _glGetIntegerv(target, &boundTexture);'
            print '        if (boundTexture > 0) {'
            print '            ctx->textures[boundTexture].m_generateMipmap = true;'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBodyArgs(self, function)
            print '    _tmpCall = _call;'
            print '    }'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '    if (trace::isTracingStateSetupFunctions() == false) {'
            print '    unsigned _call = _tmpCall;'
            Tracer.generateTraceFunctionImplBodyReturn(self, function)
            print '    }'
        elif function.name in ('glGenerateMipmap'):
            print '    // glGenerateMipmap calls are special cased'
            print '    // when tracing setup functions we only want to track the parameters, not trace the call.'
            print '    // The actual call will be added to the trace at a later time.'
            print '    unsigned _tmpCall = 0;'
            print '    if (trace::isTracingStateSetupFunctions()) {'
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        GLint boundTexture = 0;'
            print '        if (target == GL_TEXTURE_1D) _glGetIntegerv(GL_TEXTURE_BINDING_1D, &boundTexture);'
            print '        else if (target == GL_TEXTURE_1D_ARRAY) _glGetIntegerv(GL_TEXTURE_BINDING_1D_ARRAY, &boundTexture);'
            print '        else if (target == GL_TEXTURE_2D) _glGetIntegerv(GL_TEXTURE_BINDING_2D, &boundTexture);'
            print '        else if (target == GL_TEXTURE_2D_ARRAY) _glGetIntegerv(GL_TEXTURE_BINDING_2D_ARRAY, &boundTexture);'
            print '        else if (target == GL_TEXTURE_3D) _glGetIntegerv(GL_TEXTURE_BINDING_3D, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            
            print '        _glGetIntegerv(target, &boundTexture);'
            print '        if (boundTexture > 0) {'
            print '            ctx->textures[boundTexture].m_generateMipmap = true;'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBodyArgs(self, function)
            print '    _tmpCall = _call;'
            print '    }'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '    if (trace::isTracingStateSetupFunctions() == false) {'
            print '    unsigned _call = _tmpCall;'
            Tracer.generateTraceFunctionImplBodyReturn(self, function)
            print '    }'
        elif function.name in ('glTexImage1D', 'glTexImage2D', 'glTexImage3D', 'glCompressedTexImage1D', 'glCompressedTexImage2D', 'glCompressedTexImage3D', 'glTextureImage1DEXT', 'glTextureImage2DEXT', 'glTextureImage3DEXT', 'glCompressedTextureImage1DEXT', 'glCompressedTextureImage2DEXT', 'glCompressedTextureImage3DEXT'):
            print '    // glTex*Image* calls are special cased'
            print '    // when tracing setup functions we only want to track the parameters, not trace the call.'
            print '    // The actual call will be added to the trace at a later time.'
            print '    unsigned _tmpCall = 0;'
            print '    if (trace::isTracingStateSetupFunctions()) {'
            self.generateTraceTexImage(function)
            print '    } else {'
            Tracer.generateTraceFunctionImplBodyArgs(self, function)
            print '    _tmpCall = _call;'
            print '    }'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '    if (trace::isTracingStateSetupFunctions() == false) {'
            print '    unsigned _call = _tmpCall;'
            Tracer.generateTraceFunctionImplBodyReturn(self, function)
            print '    }'
        elif function.name  in ('glGenTextures', 'glGenTexturesEXT'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            if function.name == 'glGetTexturesEXT':
                print '            ctx->textures[textures[i]].m_createdWithEXT = true;'
            else:
                print '            ctx->textures[textures[i]].m_createdWithEXT = false;'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glDeleteTextures', 'glDeleteTexturesEXT'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            print '            ctx->textures.erase(textures[i]);'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glGenFramebuffers', 'glGenFramebuffersEXT'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            if function.name == 'glGenFramebuffersEXT':
                print '            ctx->framebuffers[framebuffers[i]].m_createdWithEXT = true;'
            else:
                print '            ctx->framebuffers[framebuffers[i]].m_createdWithEXT = false;'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glDeleteFramebuffers', 'glDeleteFramebuffersEXT'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            print '            ctx->framebuffers.erase(framebuffers[i]);'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name == 'glGenVertexArrays':
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            print '            ctx->vertexArrays.push_back(arrays[i]);'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name == 'glDeleteVertexArrays':
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            print '            ctx->vertexArrays.remove(arrays[i]);'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glGenBuffers', 'glGenBuffersARB'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            if function.name == 'glGenBuffersARB':
                print '            ctx->bufferObjects[%s[i]].m_createdWithARB = true;' % function.args[1].name
            else:
                print '            ctx->bufferObjects[%s[i]].m_createdWithARB = false;' % function.args[1].name
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glDeleteBuffers', 'glDeleteBuffersARB'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            print '            ctx->bufferObjects.erase(%s[i]);' % function.args[1].name
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name == 'glGenSamplers':
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < count; ++i){'
            print '            ctx->samplers.push_back(samplers[i]);'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name == 'glDeleteSamplers':
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < count; ++i){'
            print '            ctx->samplers.remove(samplers[i]);'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glGenRenderbuffers', 'glGenRenderbuffersEXT'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            if function.name == 'glGenRenderbuffersEXT':
                print '            ctx->renderbuffers[renderbuffers[i]].m_createdWithEXT = true;'
            else:
                print '            ctx->renderbuffers[renderbuffers[i]].m_createdWithEXT = false;'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glDeleteRenderbuffers', 'glDeleteRenderbuffersEXT'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            print '            ctx->renderbuffers.erase(renderbuffers[i]);'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glCreateShaderObjectARB', 'glCreateShader'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context* ctx = gltrace::getContext();'
            print '        gltrace::Shader shader;'
            print '        shader.SetSources(%s, 0, NULL, NULL);' % function.args[0].name
            if function.name == 'glCreateShaderObjectARB':
                print '        shader.m_createdWithObjectARB = true;'
            else:
                print '        shader.m_createdWithObjectARB = false;'
            print '        ctx->shaderObjects[_result] = shader;'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glDeleteShaderObjectARB', 'glDeleteShader'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context* ctx = gltrace::getContext();'
            print '        ctx->shaderObjects.erase(shader);'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glCreateProgram', 'glCreateProgramObjectARB'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context* ctx = gltrace::getContext();'
            if function.name == 'glCreateProgramObjectARB':
                print '        ctx->programs[_result].m_createdWithObjectARB = true;'
            else:
                print '        ctx->programs[_result];'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glDeleteProgram', 'glDeleteObjectARB'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context* ctx = gltrace::getContext();'
            print '        ctx->programs.erase(%s);' % function.args[0].name
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glGenProgramsARB'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            print '            ctx->programsARB[programs[i]].m_createdWithGenProgramsARB = true;'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glDeleteProgramsARB'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            print '            ctx->programsARB.erase(programs[i]);'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name  in ('glGenProgramPipelines',):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            print '            ctx->pipelines.push_back(pipelines[i]);'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glDeleteProgramPipelines',):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            print '            ctx->pipelines.remove(pipelines[i]);'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glGenQueries', 'glGenQueriesARB'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            if function.name == 'glGenQueriesARB':
                print '            ctx->queries[ids[i]].m_createdWithARB = true;'
            else:
                print '            ctx->queries[ids[i]];'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glDeleteQueries', 'glDeleteQueriesARB'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        for (GLint i = 0; i < n; ++i){'
            print '            ctx->queries.erase(ids[i]);'
            print '        }'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glFenceSync'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        gltrace::Sync syncObj(condition, flags);'
            print '        ctx->syncObjects[_result] = syncObj;'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        elif function.name in ('glDeleteSync'):
            print '    if (trace::isTracingStateSetupFunctions()) {'
            Tracer.generateTraceFunctionImplBodyRealCall(self, function)
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        ctx->syncObjects.erase(sync);'
            print '    } else {'
            Tracer.generateTraceFunctionImplBody(self, function)
            print '    }'
        else:
            Tracer.generateTraceFunctionImplBody(self, function)

    def generateTraceTexImage(self, function):
        print '        gltrace::Context *ctx = gltrace::getContext();'
        if function.name in ('glTexImage1D',):
            print '        GLint boundTexture = 0;'
            print '        _glGetIntegerv(GL_TEXTURE_BINDING_1D, &boundTexture);'
            print '        ctx->textures[boundTexture].texImage(boundTexture, GL_TEXTURE_1D, level, internalformat, width, format, type);'
        if function.name in ('glTextureImage1DEXT',):
            print '        ctx->textures[texture].texImage(texture, GL_TEXTURE_1D, level, internalformat, width, format, type);'
        if function.name in ('glCompressedTexImage1D',):
            print '        GLint boundTexture = 0;'
            print '        _glGetIntegerv(GL_TEXTURE_BINDING_1D, &boundTexture);'
            print '        ctx->textures[boundTexture].compressedTexImage(boundTexture, GL_TEXTURE_1D, level, internalformat, width, imageSize);'
        if function.name in ('glCompressedTextureImage1DEXT',):
            print '        ctx->textures[texture].compressedTexImage(texture, GL_TEXTURE_1D, level, internalformat, width, imageSize);'
        if function.name in ('glTexImage2D',):
            print '        GLint boundTexture = 0;'
            print '        if (target == GL_TEXTURE_2D) _glGetIntegerv(GL_TEXTURE_BINDING_2D, &boundTexture);'
            print '        else if (target == GL_TEXTURE_RECTANGLE) _glGetIntegerv(GL_TEXTURE_BINDING_RECTANGLE, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_POSITIVE_X) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_POSITIVE_Y) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_POSITIVE_Z) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_NEGATIVE_X) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_NEGATIVE_Y) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_NEGATIVE_Z) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        ctx->textures[boundTexture].texImage(boundTexture, target, level, internalformat, width, height, format, type);'
        if function.name in ('glTextureImage2DEXT',):
            print '        ctx->textures[texture].texImage(texture, target, level, internalformat, width, height, format, type);'
        if function.name in ('glCompressedTexImage2D',):
            print '        GLint boundTexture = 0;'
            print '        if (target == GL_TEXTURE_2D) _glGetIntegerv(GL_TEXTURE_BINDING_2D, &boundTexture);'
            print '        else if (target == GL_TEXTURE_RECTANGLE) _glGetIntegerv(GL_TEXTURE_BINDING_RECTANGLE, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_POSITIVE_X) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_POSITIVE_Y) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_POSITIVE_Z) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_NEGATIVE_X) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_NEGATIVE_Y) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        else if (target == GL_TEXTURE_CUBE_MAP_NEGATIVE_Z) _glGetIntegerv(GL_TEXTURE_BINDING_CUBE_MAP, &boundTexture);'
            print '        ctx->textures[boundTexture].compressedTexImage(boundTexture, target, level, internalformat, width, height, imageSize);'
        if function.name in ('glCompressedTextureImage2DEXT',):
            print '        ctx->textures[texture].compressedTexImage(texture, target, level, internalformat, width, height, imageSize);'
        if function.name in ('glTexImage3D',):
            print '        GLint boundTexture = 0;'
            print '        _glGetIntegerv(GL_TEXTURE_BINDING_3D, &boundTexture);'
            print '        ctx->textures[boundTexture].texImage(boundTexture, GL_TEXTURE_3D, level, internalformat, width, height, depth, format, type);'
        if function.name in ('glTextureImage3DEXT',):
            print '        ctx->textures[texture].texImage(texture, GL_TEXTURE_3D, level, internalformat, width, height, depth, format, type);'
        if function.name in ('glCompressedTexImage3D',):
            print '        GLint boundTexture = 0;'
            print '        _glGetIntegerv(GL_TEXTURE_BINDING_3D, &boundTexture);'
            print '        ctx->textures[boundTexture].compressedTexImage(boundTexture, GL_TEXTURE_3D, level, internalformat, width, height, depth, imageSize);'
        if function.name in ('glCompressedTextureImage3DEXT',):
            print '        ctx->textures[texture].compressedTexImage(texture, GL_TEXTURE_3D, level, internalformat, width, height, depth, imageSize);'

    marker_functions = [
        # GL_GREMEDY_string_marker
        'glStringMarkerGREMEDY',
        # GL_GREMEDY_frame_terminator
        'glFrameTerminatorGREMEDY',
        # GL_EXT_debug_marker
        'glInsertEventMarkerEXT',
        'glPushGroupMarkerEXT',
        'glPopGroupMarkerEXT',
    ]

    def frameTerminationTraceFunction(self, function, indentation):
        if function.name in self.frame_terminator_functions:
            indentation = indentation + '    '
            print '    if ( makeRealCall ) {'
            self.frameTermination(function, indentation)
            print '    }'

    def frameTermination(self, function, indentation):
        if function.name in self.frame_terminator_functions:
            print '%strace::incrementFrameNumber();' % indentation

    def invokeFunction(self, function, indentation):
        Tracer.invokeFunction(self, function, indentation)

    def doInvokeFunction(self, function, indentation):
        # Same as invokeFunction() but called both when trace is enabled or disabled.
        #
        # Used to modify the behavior of GL entry-points.

        # Override GL extensions
        if function.name in ('glGetString', 'glGetIntegerv', 'glGetStringi'):
            Tracer.doInvokeFunction(self, function, indentation, prefix = 'gltrace::_', suffix = '_override')
            return

        # We implement GL_EXT_debug_marker, GL_GREMEDY_*, etc., and not the
        # driver
        if function.name in self.marker_functions:
            return

        if function.name in self.getProcAddressFunctionNames:
            else_ = ''
            for marker_function in self.marker_functions:
                if self.api.getFunctionByName(marker_function):
                    print '%s%sif (strcmp("%s", (const char *)%s) == 0) {' % (indentation, else_, marker_function, function.args[0].name)
                    print '%s    _result = (%s)&%s;' % (indentation, function.type, marker_function)
                    print '%s}' % indentation
                else_ = 'else '
            print '%s%s{' % (indentation, else_)
            Tracer.doInvokeFunction(self, function, indentation + '    ')

            # Replace function addresses with ours
            # XXX: Doing this here instead of wrapRet means that the trace will
            # contain the addresses of the wrapper functions, and not the real
            # functions, but in practice this should make no difference.
            if function.name in self.getProcAddressFunctionNames:
                print '%s    _result = _wrapProcAddress(%s, _result);' % (indentation, function.args[0].name,)

            print '%s}' % indentation
            return

        Tracer.doInvokeFunction(self, function, indentation)

    buffer_targets = [
        'ARRAY_BUFFER',
        'ELEMENT_ARRAY_BUFFER',
        'PIXEL_PACK_BUFFER',
        'PIXEL_UNPACK_BUFFER',
        'UNIFORM_BUFFER',
        'TEXTURE_BUFFER',
        'TRANSFORM_FEEDBACK_BUFFER',
        'COPY_READ_BUFFER',
        'COPY_WRITE_BUFFER',
        'DRAW_INDIRECT_BUFFER',
        'ATOMIC_COUNTER_BUFFER',
    ]

    def wrapRet(self, function, instance):
        Tracer.wrapRet(self, function, instance)

        # Keep track of buffer mappings
        if function.name in ('glMapBuffer', 'glMapBufferARB'):
            print '    struct buffer_mapping *mapping = get_buffer_mapping(target);'
            print '    if (mapping) {'
            print '        mapping->map = %s;' % (instance)
            print '        mapping->length = 0;'
            print '        _glGetBufferParameteriv(target, GL_BUFFER_SIZE, &mapping->length);'
            print '        mapping->write = (access != GL_READ_ONLY);'
            print '        mapping->explicit_flush = false;'
            print '    }'
        if function.name == 'glMapBufferRange':
            print '    if (access & GL_MAP_WRITE_BIT) {'
            print '        _checkBufferMapRange = true;'
            print '    }'
            print '    struct buffer_mapping *mapping = get_buffer_mapping(target);'
            print '    if (mapping) {'
            print '        mapping->map = %s;' % (instance)
            print '        mapping->length = length;'
            print '        mapping->write = access & GL_MAP_WRITE_BIT;'
            print '        mapping->explicit_flush = access & GL_MAP_FLUSH_EXPLICIT_BIT;'
            print '    }'

    boolean_names = [
        'GL_FALSE',
        'GL_TRUE',
    ]

    def gl_boolean(self, value):
        return self.boolean_names[int(bool(value))]

    # Names of the functions that unpack from a pixel buffer object.  See the
    # ARB_pixel_buffer_object specification.
    unpack_function_names = set([
        'glBitmap',
        'glColorSubTable',
        'glColorTable',
        'glCompressedMultiTexImage1DEXT',
        'glCompressedMultiTexImage2DEXT',
        'glCompressedMultiTexImage3DEXT',
        'glCompressedMultiTexSubImage1DEXT',
        'glCompressedMultiTexSubImage2DEXT',
        'glCompressedMultiTexSubImage3DEXT',
        'glCompressedTexImage1D',
        'glCompressedTexImage2D',
        'glCompressedTexImage3D',
        'glCompressedTexSubImage1D',
        'glCompressedTexSubImage2D',
        'glCompressedTexSubImage3D',
        'glCompressedTextureImage1DEXT',
        'glCompressedTextureImage2DEXT',
        'glCompressedTextureImage3DEXT',
        'glCompressedTextureSubImage1DEXT',
        'glCompressedTextureSubImage2DEXT',
        'glCompressedTextureSubImage3DEXT',
        'glConvolutionFilter1D',
        'glConvolutionFilter2D',
        'glDrawPixels',
        'glMultiTexImage1DEXT',
        'glMultiTexImage2DEXT',
        'glMultiTexImage3DEXT',
        'glMultiTexSubImage1DEXT',
        'glMultiTexSubImage2DEXT',
        'glMultiTexSubImage3DEXT',
        'glPixelMapfv',
        'glPixelMapuiv',
        'glPixelMapusv',
        'glPolygonStipple',
        'glSeparableFilter2D',
        'glTexImage1D',
        'glTexImage1DEXT',
        'glTexImage2D',
        'glTexImage2DEXT',
        'glTexImage3D',
        'glTexImage3DEXT',
        'glTexSubImage1D',
        'glTexSubImage1DEXT',
        'glTexSubImage2D',
        'glTexSubImage2DEXT',
        'glTexSubImage3D',
        'glTexSubImage3DEXT',
        'glTextureImage1DEXT',
        'glTextureImage2DEXT',
        'glTextureImage3DEXT',
        'glTextureSubImage1DEXT',
        'glTextureSubImage2DEXT',
        'glTextureSubImage3DEXT',
    ])

    def serializeArgValue(self, function, arg):
        # Recognize offsets instead of blobs when a PBO is bound
        if function.name in self.unpack_function_names \
           and (isinstance(arg.type, stdapi.Blob) \
                or (isinstance(arg.type, stdapi.Const) \
                    and isinstance(arg.type.type, stdapi.Blob))):
            print '    {'
            print '        gltrace::Context *ctx = gltrace::getContext();'
            print '        GLint _unpack_buffer = 0;'
            print '        if (ctx->profile == gltrace::PROFILE_COMPAT)'
            print '            _glGetIntegerv(GL_PIXEL_UNPACK_BUFFER_BINDING, &_unpack_buffer);'
            print '        if (_unpack_buffer) {'
            print '            trace::localWriter.writePointer((uintptr_t)%s);' % arg.name
            print '        } else {'
            Tracer.serializeArgValue(self, function, arg)
            print '        }'
            print '    }'
            return

        # Several GL state functions take GLenum symbolic names as
        # integer/floats; so dump the symbolic name whenever possible
        if function.name.startswith('gl') \
           and arg.type in (glapi.GLint, glapi.GLfloat, glapi.GLdouble) \
           and arg.name == 'param':
            assert arg.index > 0
            assert function.args[arg.index - 1].name == 'pname'
            assert function.args[arg.index - 1].type == glapi.GLenum
            print '    if (is_symbolic_pname(pname) && is_symbolic_param(%s)) {' % arg.name
            self.serializeValue(glapi.GLenum, arg.name)
            print '    } else {'
            Tracer.serializeArgValue(self, function, arg)
            print '    }'
            return

        Tracer.serializeArgValue(self, function, arg)

    def footer(self, api):
        Tracer.footer(self, api)

        # A simple state tracker to track the pointer values
        # update the state
        print 'static void _trace_user_arrays(GLuint count)'
        print '{'
        print '    gltrace::Context *ctx = gltrace::getContext();'

        for camelcase_name, uppercase_name in self.arrays:
            # in which profile is the array available?
            profile_check = 'ctx->profile == gltrace::PROFILE_COMPAT'
            if camelcase_name in self.arrays_es1:
                profile_check = '(' + profile_check + ' || ctx->profile == gltrace::PROFILE_ES1)';

            function_name = 'gl%sPointer' % camelcase_name
            enable_name = 'GL_%s_ARRAY' % uppercase_name
            binding_name = 'GL_%s_ARRAY_BUFFER_BINDING' % uppercase_name
            function = api.getFunctionByName(function_name)

            print '    // %s' % function.prototype()
            print '  if (%s) {' % profile_check
            self.array_trace_prolog(api, uppercase_name)
            self.array_prolog(api, uppercase_name)
            print '    if (_glIsEnabled(%s)) {' % enable_name
            print '        GLint _binding = 0;'
            print '        _glGetIntegerv(%s, &_binding);' % binding_name
            print '        if (!_binding) {'

            # Get the arguments via glGet*
            for arg in function.args:
                arg_get_enum = 'GL_%s_ARRAY_%s' % (uppercase_name, arg.name.upper())
                arg_get_function, arg_type = TypeGetter().visit(arg.type)
                print '            %s %s = 0;' % (arg_type, arg.name)
                print '            _%s(%s, &%s);' % (arg_get_function, arg_get_enum, arg.name)
            
            arg_names = ', '.join([arg.name for arg in function.args[:-1]])
            print '            size_t _size = _%s_size(%s, count);' % (function.name, arg_names)

            # Emit a fake function
            self.array_trace_intermezzo(api, uppercase_name)
            print '            unsigned _call = trace::localWriter.beginEnter(&_%s_sig);' % (function.name,)
            for arg in function.args:
                assert not arg.output
                print '            trace::localWriter.beginArg(%u);' % (arg.index,)
                if arg.name != 'pointer':
                    self.serializeValue(arg.type, arg.name)
                else:
                    print '            trace::localWriter.writeBlob((const void *)%s, _size);' % (arg.name)
                print '            trace::localWriter.endArg();'
            
            print '            trace::localWriter.endEnter();'
            print '            trace::localWriter.beginLeave(_call);'
            print '            trace::localWriter.endLeave();'
            print '        }'
            print '    }'
            self.array_epilog(api, uppercase_name)
            self.array_trace_epilog(api, uppercase_name)
            print '  }'
            print

        # Same thing, but for glVertexAttribPointer*
        #
        # Some variants of glVertexAttribPointer alias conventional and generic attributes:
        # - glVertexAttribPointer: no
        # - glVertexAttribPointerARB: implementation dependent
        # - glVertexAttribPointerNV: yes
        #
        # This means that the implementations of these functions do not always
        # alias, and they need to be considered independently.
        #
        print '    // ES1 does not support generic vertex attributes'
        print '    if (ctx->profile == gltrace::PROFILE_ES1)'
        print '        return;'
        print
        print '    vertex_attrib _vertex_attrib = _get_vertex_attrib();'
        print
        for suffix in ['', 'ARB', 'NV']:
            if suffix:
                SUFFIX = '_' + suffix
            else:
                SUFFIX = suffix
            function_name = 'glVertexAttribPointer' + suffix
            function = api.getFunctionByName(function_name)

            print '    // %s' % function.prototype()
            print '    if (_vertex_attrib == VERTEX_ATTRIB%s) {' % SUFFIX
            if suffix == 'NV':
                print '        GLint _max_vertex_attribs = 16;'
            else:
                print '        GLint _max_vertex_attribs = 0;'
                print '        _glGetIntegerv(GL_MAX_VERTEX_ATTRIBS, &_max_vertex_attribs);'
            print '        for (GLint index = 0; index < _max_vertex_attribs; ++index) {'
            print '            GLint _enabled = 0;'
            if suffix == 'NV':
                print '            _glGetIntegerv(GL_VERTEX_ATTRIB_ARRAY0_NV + index, &_enabled);'
            else:
                print '            _glGetVertexAttribiv%s(index, GL_VERTEX_ATTRIB_ARRAY_ENABLED%s, &_enabled);' % (suffix, SUFFIX)
            print '            if (_enabled) {'
            print '                GLint _binding = 0;'
            if suffix != 'NV':
                # It doesn't seem possible to use VBOs with NV_vertex_program.
                print '                _glGetVertexAttribiv%s(index, GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING%s, &_binding);' % (suffix, SUFFIX)
            print '                if (!_binding) {'

            # Get the arguments via glGet*
            for arg in function.args[1:]:
                if suffix == 'NV':
                    arg_get_enum = 'GL_ATTRIB_ARRAY_%s%s' % (arg.name.upper(), SUFFIX)
                else:
                    arg_get_enum = 'GL_VERTEX_ATTRIB_ARRAY_%s%s' % (arg.name.upper(), SUFFIX)
                arg_get_function, arg_type = TypeGetter('glGetVertexAttrib', False, suffix).visit(arg.type)
                print '                    %s %s = 0;' % (arg_type, arg.name)
                print '                    _%s(index, %s, &%s);' % (arg_get_function, arg_get_enum, arg.name)
            
            arg_names = ', '.join([arg.name for arg in function.args[1:-1]])
            print '                    size_t _size = _%s_size(%s, count);' % (function.name, arg_names)

            # Emit a fake function
            print '                    unsigned _call = trace::localWriter.beginEnter(&_%s_sig);' % (function.name,)
            for arg in function.args:
                assert not arg.output
                print '                    trace::localWriter.beginArg(%u);' % (arg.index,)
                if arg.name != 'pointer':
                    self.serializeValue(arg.type, arg.name)
                else:
                    print '                    trace::localWriter.writeBlob((const void *)%s, _size);' % (arg.name)
                print '                    trace::localWriter.endArg();'
            
            print '                    trace::localWriter.endEnter();'
            print '                    trace::localWriter.beginLeave(_call);'
            print '                    trace::localWriter.endLeave();'
            print '                }'
            print '            }'
            print '        }'
            print '    }'
            print

        print '}'
        print

    #
    # Hooks for glTexCoordPointer, which is identical to the other array
    # pointers except the fact that it is indexed by glClientActiveTexture.
    #

    def array_prolog(self, api, uppercase_name):
        if uppercase_name == 'TEXTURE_COORD':
            print '    GLint client_active_texture = 0;'
            print '    _glGetIntegerv(GL_CLIENT_ACTIVE_TEXTURE, &client_active_texture);'
            print '    GLint max_texture_coords = 0;'
            print '    if (ctx->profile == gltrace::PROFILE_COMPAT)'
            print '        _glGetIntegerv(GL_MAX_TEXTURE_COORDS, &max_texture_coords);'
            print '    else'
            print '        _glGetIntegerv(GL_MAX_TEXTURE_UNITS, &max_texture_coords);'
            print '    for (GLint unit = 0; unit < max_texture_coords; ++unit) {'
            print '        GLint texture = GL_TEXTURE0 + unit;'
            print '        _glClientActiveTexture(texture);'

    def array_trace_prolog(self, api, uppercase_name):
        if uppercase_name == 'TEXTURE_COORD':
            print '    bool client_active_texture_dirty = false;'

    def array_epilog(self, api, uppercase_name):
        if uppercase_name == 'TEXTURE_COORD':
            print '    }'
        self.array_cleanup(api, uppercase_name)

    def array_cleanup(self, api, uppercase_name):
        if uppercase_name == 'TEXTURE_COORD':
            print '    _glClientActiveTexture(client_active_texture);'
        
    def array_trace_intermezzo(self, api, uppercase_name):
        if uppercase_name == 'TEXTURE_COORD':
            print '    if (texture != client_active_texture || client_active_texture_dirty) {'
            print '        client_active_texture_dirty = true;'
            self.fake_glClientActiveTexture_call(api, "texture");
            print '    }'

    def array_trace_epilog(self, api, uppercase_name):
        if uppercase_name == 'TEXTURE_COORD':
            print '    if (client_active_texture_dirty) {'
            self.fake_glClientActiveTexture_call(api, "client_active_texture");
            print '    }'

    def fake_glClientActiveTexture_call(self, api, texture):
        function = api.getFunctionByName('glClientActiveTexture')
        self.fake_call(function, [texture])

    def emitFakeTexture2D(self):
        function = glapi.glapi.getFunctionByName('glTexImage2D')
        instances = function.argNames()
        print '        unsigned _fake_call = trace::localWriter.beginEnter(&_%s_sig);' % (function.name,)
        for arg in function.args:
            assert not arg.output
            self.serializeArg(function, arg)
        print '        trace::localWriter.endEnter();'
        print '        trace::localWriter.beginLeave(_fake_call);'
        print '        trace::localWriter.endLeave();'

