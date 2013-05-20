/*********************************************************************
 *
 * Copyright 2012 Valve Corporation
 * All Rights Reserved.
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 *********************************************************************/
#include <gltrace.hpp>
#ifdef WIN32
#include "wgltrace_tracefuncs.h"
#include "../../../retrace/glstate.hpp"
#endif
#ifdef __linux
#include "../build32/wrappers/glxtrace_tracefuncs.h"
#include "../../retrace/glstate.hpp"
#endif
#ifdef __APPLE__
#include "../build/wrappers/cgltrace_tracefuncs.h"
#include "../../retrace/glstate.hpp"
#endif

namespace gltrace {

void snapshotState()
{
    gltrace::Context* pCurrentContext = gltrace::getContext();

    glstate::snapshotParameters();

    _trace_glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT, false);
#ifdef WIN32
    BOOL bResult = TRUE;
    bResult = _trace_wglSwapBuffers((HDC)pCurrentContext->hdc, bResult, false);
#endif

#ifdef __linux
    _trace_glXSwapBuffers((Display*)pCurrentContext->dpy, pCurrentContext->m_drawable, false);
#endif

#ifdef __APPLE__
    CGLError result = kCGLNoError;
    result = _trace_CGLFlushDrawable((CGLContextObj)pCurrentContext->hdc, result, false);
#endif
}

}
