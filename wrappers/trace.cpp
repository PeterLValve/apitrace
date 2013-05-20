/**************************************************************************
 *
 * Copyright 2010-2011 VMware, Inc.
 * All Rights Reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 **************************************************************************/


#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

#ifdef ANDROID
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/system_properties.h>
#endif

#include "os.hpp"
#include "os_string.hpp"
#include "os_process.hpp"
#include "trace.hpp"


namespace trace {

static bool s_checkedEnv = false;
static bool s_singleFrameTraceEnabled = false;
static unsigned long s_frameNumToStartTrace = 0xFFFFFFFF;
static unsigned long s_frameNumToStopTrace = 0xFFFFFFFF;
static unsigned long s_currentFrameNum = 0;

static bool s_checkForSnap = false;
static bool s_checkForStart = false;
static bool s_checkForStop = false;

void incrementFrameNumber(void) {
    ++s_currentFrameNum;
    if (isFrameToTrace() && s_singleFrameTraceEnabled && s_currentFrameNum == s_frameNumToStartTrace)
    {
        snapshotState();
    }
    
    if (s_singleFrameTraceEnabled && s_currentFrameNum == s_frameNumToStopTrace)
    {
        os::log("apitrace: Trace completed. Captured %ld frames.\n", s_frameNumToStopTrace - s_frameNumToStartTrace);
    }
}

bool isTracingStateSetupFunctions(void)
{
    return s_singleFrameTraceEnabled && (s_currentFrameNum < s_frameNumToStartTrace);
}

bool isFrameToTrace(void) {
    if ( !s_checkedEnv ) {
        s_checkedEnv = true;
        char* strFrame = getenv( "TRACE_FRAME" );
        os::unsetEnvironment("TRACE_FRAME");
        s_singleFrameTraceEnabled = ( strFrame != NULL );
        if ( s_singleFrameTraceEnabled ) {
            bool parsedFrameNumbers = false;
            if (strstr(strFrame, "-"))
            {
                const char* strStart = strtok(strFrame, "-");
                const char* strStop = strtok(NULL, "-");
                if (isdigit(strStart[0]) && isdigit(strStop[0]))
                {
                    s_frameNumToStartTrace = strtoul( strStart, NULL, 10 );
                    s_frameNumToStopTrace = strtoul( strStop, NULL, 10 );
                    
                    // flip the numbers if stop is less than start
                    if (s_frameNumToStopTrace < s_frameNumToStartTrace)
                    {
                        unsigned long tmp = s_frameNumToStopTrace;
                        s_frameNumToStopTrace = s_frameNumToStartTrace;
                        s_frameNumToStartTrace = tmp;
                    }
                    parsedFrameNumbers = true;
                    os::log("apitrace: Tracing frame %ld - %ld.\n", s_frameNumToStartTrace, s_frameNumToStopTrace);
                }
            }
            else if (isdigit(strFrame[0]))
            {
                s_frameNumToStartTrace = strtoul( strFrame, NULL, 10 );
                s_frameNumToStopTrace = s_frameNumToStartTrace + 1;
                parsedFrameNumbers = true;
                os::log("apitrace: Tracing frame %ld.\n", s_frameNumToStartTrace);
            }

            // if start/stop frame numbers were not parsed from the env var,
            // then check for existance of 'snap' or 'start' files throughout the trace
            if (parsedFrameNumbers == false)
            {
                s_checkForSnap = true;
                s_checkForStart = true;
            }
        }
    }

    if (s_checkForSnap)
    {
        FILE* fSnap = fopen("snap", "r");
        if (fSnap != NULL)
        {
            char strFrameCount[12]; // NOTE: there are only 10 characters in an unsigned long
            memset(strFrameCount, 0, 12 *sizeof(char));
            size_t result = fread(strFrameCount, 12*sizeof(char), 12*sizeof(char), fSnap);
            fclose(fSnap);
            remove("snap");
            s_frameNumToStartTrace = s_currentFrameNum + 1;
            unsigned long frameCount = 1;
            if (result == 0)
            {
                frameCount = strtoul(strFrameCount, NULL, 10 );
            }
            s_frameNumToStopTrace = s_frameNumToStartTrace + frameCount;
            s_checkForSnap = false;
            s_checkForStart = false;
            os::log("apitrace: snap detected: Tracing %ld frame(s).\n", frameCount);
        }
    }

    if (s_checkForStart)
    {
        FILE* fStart = fopen("starttrace", "r");
        if (fStart != NULL)
        {
            fclose(fStart);
            remove("starttrace");
            s_frameNumToStartTrace = s_currentFrameNum + 1;
            s_checkForSnap  = false;
            s_checkForStart = false;
            s_checkForStop = true;
            os::log("apitrace: start detected: beginning trace range.\n");
        }
    }

    if (s_checkForStop)
    {
        FILE* fStop = fopen("stoptrace", "r");
        if (fStop != NULL)
        {
            fclose(fStop);
            remove("stoptrace");
            s_frameNumToStopTrace = s_currentFrameNum + 1;
            s_checkForSnap  = false;
            s_checkForStart = false;
            s_checkForStop = false;
            os::log("apitrace: stop detected: ending trace range.\n");
        }
    }
    
    if ( !s_singleFrameTraceEnabled )
    {
        return true;
    } else {
        return s_frameNumToStartTrace <= s_currentFrameNum && s_currentFrameNum < s_frameNumToStopTrace;
    }
}

#ifdef ANDROID

static bool
isZygoteProcess(void)
{
    os::String proc_name;

    proc_name = os::getProcessName();
    proc_name.trimDirectory();

    return strcmp(proc_name, "app_process") == 0;
}

static os::String
getZygoteProcessName(void)
{
    os::String path;
    size_t size = PATH_MAX;
    char *buf = path.buf(size);
    ssize_t len;

    int fd = open("/proc/self/cmdline", O_RDONLY);

    assert(fd >= 0);
    len = read(fd, buf, size - 1);
    close(fd);
    path.truncate(len);

    return path;
}

bool
isTracingEnabled(void)
{
    if (!isFrameToTrace()) {
        return false;
    }

    static pid_t cached_pid;
    static bool enabled;
    pid_t pid;

    pid = getpid();
    if (cached_pid == pid)
        return enabled;
    cached_pid = pid;

    if (!isZygoteProcess()) {
        os::log("apitrace[%d]: enabled for standalone %s",
                pid, (const char *)os::getProcessName());
        enabled = true;
        return true;
    }

    char target_proc_name[PROP_VALUE_MAX] = "";
    os::String proc_name;

    proc_name = getZygoteProcessName();
    proc_name.trimDirectory();

    __system_property_get("debug.apitrace.procname", target_proc_name);
    enabled = !strcmp(target_proc_name, proc_name);
    os::log("apitrace[%d]: %s for %s",
            pid, enabled ? "enabled" : "disabled", (const char *)proc_name);

    return enabled;
}

#endif /* ANDROID */


} /* namespace trace */

