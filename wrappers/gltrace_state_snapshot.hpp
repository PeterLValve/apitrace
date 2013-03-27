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
#include "wgltrace_tracefuncs.hpp"

namespace gltrace {

HDC g_hdc;

void snapshotState()
{
    HGLRC hglrcResult = (HGLRC)2;
    g_hdc = (HDC)1;
    hglrcResult = _trace_wglCreateContext( g_hdc, hglrcResult, false );

    _trace_glClearColor(0,0,0,1, false);
    _trace_glClear(GL_COLOR_BUFFER_BIT, false);
    BOOL bResult = TRUE;
    bResult = _trace_wglSwapBuffers(g_hdc, bResult, false);
}

}