##########################################################################
#
# Copyright 2011 Valve Corporation
# All Rights Reserved.
#
# Originally based on glstate_params.py by Jose Fonseca
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


'''Generate code to snapshot the GL state and recreate in a trace file.'''
'''Primary focus is on supporting OpenGL 3.3'''

# Adjust path
import os.path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from specs.stdapi import *
from specs.gltypes import *
from specs.glparams import *

texture_targets = [
    ('GL_TEXTURE_1D', 'GL_TEXTURE_BINDING_1D'),
    ('GL_TEXTURE_2D', 'GL_TEXTURE_BINDING_2D'),
    ('GL_TEXTURE_3D', 'GL_TEXTURE_BINDING_3D'),
    ('GL_TEXTURE_RECTANGLE', 'GL_TEXTURE_BINDING_RECTANGLE'),
    ('GL_TEXTURE_CUBE_MAP', 'GL_TEXTURE_BINDING_CUBE_MAP')
]

framebuffer_targets = [
    ('GL_DRAW_FRAMEBUFFER', 'GL_DRAW_FRAMEBUFFER_BINDING'),
    ('GL_READ_FRAMEBUFFER', 'GL_READ_FRAMEBUFFER_BINDING'),
]

buffer_targets = (
    ('GL_ARRAY_BUFFER', 'GL_ARRAY_BUFFER_BINDING'),
    ('GL_COPY_READ_BUFFER', 'GL_COPY_READ_BUFFER'),
    ('GL_COPY_WRITE_BUFFER', 'GL_COPY_WRITE_BUFFER'),
    ('GL_ELEMENT_ARRAY_BUFFER', 'GL_ELEMENT_ARRAY_BUFFER_BINDING'),
    ('GL_PIXEL_PACK_BUFFER', 'GL_PIXEL_PACK_BUFFER_BINDING'),
    ('GL_PIXEL_UNPACK_BUFFER', 'GL_PIXEL_UNPACK_BUFFER_BINDING'),
    ('GL_TEXTURE_BUFFER', 'GL_TEXTURE_BUFFER'),
    ('GL_TRANSFORM_FEEDBACK_BUFFER', 'GL_TRANSFORM_FEEDBACK_BUFFER_BINDING'),
    ('GL_UNIFORM_BUFFER', 'GL_UNIFORM_BUFFER_BINDING'),
)

state_that_cannot_replay = (
    'GL_VENDOR',
    'GL_RENDERER',
    'GL_VERSION',
    'GL_MAJOR_VERSION',
    'GL_MINOR_VERSION',
    'GL_EXTENSIONS',
    'GL_NUM_EXTENSIONS',
    'GL_CONTEXT_FLAGS',
    'GL_PROGRAM_ERROR_STRING_ARB',
    'GL_SHADING_LANGUAGE_VERSION',
    'GL_MAX_SERVER_WAIT_TIMEOUT',
    'GL_POINT_SIZE_RANGE',
    'GL_POINT_SIZE_GRANULARITY',
    'GL_LINE_WIDTH_RANGE',
    'GL_LINE_WIDTH_GRANULARITY',
    'GL_MAX_LIST_NESTING',
    'GL_MODELVIEW_STACK_DEPTH',
    'GL_PROJECTION_STACK_DEPTH',
    'GL_TEXTURE_STACK_DEPTH',
    'GL_ATTRIB_STACK_DEPTH',
    'GL_CLIENT_ATTRIB_STACK_DEPTH',
    'GL_AUX_BUFFERS',
    'GL_INDEX_MODE',
    'GL_RGBA_MODE',
    'GL_DOUBLEBUFFER',
    'GL_STEREO',
    'GL_MAX_EVAL_ORDER',
    'GL_MAX_LIGHTS',
    'GL_MAX_CLIP_DISTANCES',
    'GL_MAX_TEXTURE_SIZE',
    'GL_MAX_PIXEL_MAP_TABLE',
    'GL_MAX_ATTRIB_STACK_DEPTH',
    'GL_MAX_MODELVIEW_STACK_DEPTH',
    'GL_MAX_NAME_STACK_DEPTH',
    'GL_MAX_PROJECTION_STACK_DEPTH',
    'GL_MAX_TEXTURE_STACK_DEPTH',
    'GL_MAX_VIEWPORT_DIMS',
    'GL_NAME_STACK_DEPTH',
    'GL_MAX_COMPUTE_SHARED_MEMORY_SIZE',
    'GL_MAX_COMPUTE_UNIFORM_COMPONENTS',
    'GL_MAX_COMPUTE_ATOMIC_COUNTER_BUFFERS',
    'GL_MAX_COMPUTE_ATOMIC_COUNTERS',
    'GL_MAX_COMBINED_COMPUTE_UNIFORM_COMPONENTS',
    'GL_MAX_UNIFORM_LOCATIONS',
    'GL_MAX_TEXTURE_UNITS',
    'GL_MAX_RENDERBUFFER_SIZE',
    'GL_MAX_RECTANGLE_TEXTURE_SIZE',
    'GL_MAX_TEXTURE_LOD_BIAS',
    'GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT',
    'GL_MAX_SHININESS_NV',
    'GL_MAX_SPOT_EXPONENT_NV',
    'GL_MAX_CUBE_MAP_TEXTURE_SIZE',
    'GL_MAX_GENERAL_COMBINERS_NV',
    'GL_NUM_GENERAL_COMBINERS_NV',
    'GL_MAX_PROGRAM_MATRIX_STACK_DEPTH_ARB',
    'GL_MAX_PROGRAM_MATRICES_ARB',
    'GL_CURRENT_MATRIX_STACK_DEPTH_ARB',
    'GL_NUM_COMPRESSED_TEXTURE_FORMATS',
    'GL_MAX_VERTEX_UNITS_ARB',
    'GL_ACTIVE_VERTEX_UNITS_ARB',
    'GL_MAX_DRAW_BUFFERS',
    'GL_MAX_VERTEX_ATTRIBS',
    'GL_MAX_TEXTURE_COORDS',
    'GL_MAX_TEXTURE_IMAGE_UNITS',
    'GL_MAX_DUAL_SOURCE_DRAW_BUFFERS',
    'GL_MAX_ARRAY_TEXTURE_LAYERS',
    'GL_MIN_PROGRAM_TEXEL_OFFSET',
    'GL_MAX_PROGRAM_TEXEL_OFFSET',
    'GL_MAX_VERTEX_UNIFORM_BLOCKS',
    'GL_MAX_GEOMETRY_UNIFORM_BLOCKS',
    'GL_MAX_FRAGMENT_UNIFORM_BLOCKS',
    'GL_MAX_COMBINED_UNIFORM_BLOCKS',
    'GL_MAX_UNIFORM_BUFFER_BINDINGS',
    'GL_MAX_UNIFORM_BLOCK_SIZE',
    'GL_MAX_COMBINED_VERTEX_UNIFORM_COMPONENTS',
    'GL_MAX_COMBINED_GEOMETRY_UNIFORM_COMPONENTS',
    'GL_MAX_COMBINED_FRAGMENT_UNIFORM_COMPONENTS',
    'GL_MAX_FRAGMENT_UNIFORM_COMPONENTS',
    'GL_MAX_VERTEX_UNIFORM_COMPONENTS',
    'GL_MAX_VARYING_COMPONENTS',
    'GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS',
    'GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS',
    'GL_MAX_GEOMETRY_TEXTURE_IMAGE_UNITS',
    'GL_MAX_TEXTURE_BUFFER_SIZE',
    'GL_MAX_COLOR_ATTACHMENTS',
    'GL_MAX_SAMPLES',
    'GL_MAX_ELEMENT_INDEX',
    'GL_MAX_GEOMETRY_VARYING_COMPONENTS_ARB',
    'GL_MAX_VERTEX_VARYING_COMPONENTS_ARB',
    'GL_MAX_GEOMETRY_UNIFORM_COMPONENTS',
    'GL_MAX_GEOMETRY_OUTPUT_VERTICES',
    'GL_MAX_GEOMETRY_TOTAL_OUTPUT_COMPONENTS',
    'GL_MAX_SUBROUTINES',
    'GL_MAX_SUBROUTINE_UNIFORM_LOCATIONS',
    'GL_MAX_BINDABLE_UNIFORM_SIZE_EXT',
    'GL_NUM_SHADER_BINARY_FORMATS',
    'GL_MAX_VERTEX_UNIFORM_VECTORS',
    'GL_MAX_VARYING_VECTORS',
    'GL_MAX_FRAGMENT_UNIFORM_VECTORS',
    'GL_MAX_COMBINED_TESS_CONTROL_UNIFORM_COMPONENTS',
    'GL_MAX_COMBINED_TESS_CONTROL_UNIFORM_COMPONENTS',
    'GL_MAX_COMBINED_TESS_EVALUATION_UNIFORM_COMPONENTS',
    'GL_MAX_SAMPLE_MASK_WORDS',
    'GL_MAX_TRANSFORM_FEEDBACK_BUFFERS',
    'GL_MAX_VERTEX_STREAMS',
    'GL_MAX_PATCH_VERTICES',
    'GL_MAX_TESS_GEN_LEVEL',
    'GL_MAX_TESS_CONTROL_UNIFORM_COMPONENTS',
    'GL_MAX_TESS_EVALUATION_UNIFORM_COMPONENTS',
    'GL_MAX_TESS_CONTROL_TEXTURE_IMAGE_UNITS',
    'GL_MAX_TESS_EVALUATION_TEXTURE_IMAGE_UNITS',
    'GL_MAX_TESS_CONTROL_OUTPUT_COMPONENTS',
    'GL_MAX_TESS_PATCH_COMPONENTS',
    'GL_MAX_TESS_CONTROL_TOTAL_OUTPUT_COMPONENTS',
    'GL_MAX_TESS_EVALUATION_OUTPUT_COMPONENTS',
    'GL_MAX_TESS_CONTROL_UNIFORM_BLOCKS',
    'GL_MAX_TESS_EVALUATION_UNIFORM_BLOCKS',
    'GL_GPU_MEMORY_INFO_DEDICATED_VIDMEM_NVX',
    'GL_GPU_MEMORY_INFO_TOTAL_AVAILABLE_MEMORY_NVX',
    'GL_GPU_MEMORY_INFO_CURRENT_AVAILABLE_VIDMEM_NVX',
    'GL_GPU_MEMORY_INFO_EVICTION_COUNT_NVX',
    'GL_GPU_MEMORY_INFO_EVICTED_MEMORY_NVX',
    'GL_MAX_COMPUTE_SHADER_STORAGE_BLOCKS',
    'GL_MAX_COMPUTE_LOCAL_INVOCATIONS',
    'GL_MAX_COLOR_TEXTURE_SAMPLES',
    'GL_MAX_DEPTH_TEXTURE_SAMPLES',
    'GL_MAX_INTEGER_SAMPLES',
    'GL_MAX_DEBUG_MESSAGE_LENGTH',
    'GL_MAX_DEBUG_LOGGED_MESSAGES',
    'GL_MAX_COMPUTE_UNIFORM_BLOCKS',
    'GL_MAX_COMPUTE_TEXTURE_IMAGE_UNITS',
    'GL_MAX_COMPUTE_IMAGE_UNIFORMS',
    'GL_MAX_COMPUTE_WORK_GROUP_COUNT',
    'GL_MAX_COMPUTE_WORK_GROUP_SIZE',
    'GL_MAX_FRAMEBUFFER_WIDTH',
    'GL_MAX_FRAMEBUFFER_HEIGHT',
    'GL_MAX_FRAMEBUFFER_LAYERS',
    'GL_MAX_FRAMEBUFFER_SAMPLES',
    'GL_MAX_CLIENT_ATTRIB_STACK_DEPTH',
    'GL_MAX_3D_TEXTURE_SIZE',
    'GL_MAX_COLOR_MATRIX_STACK_DEPTH',
    'GL_MAX_ELEMENTS_VERTICES',
    'GL_MAX_FOG_FUNC_POINTS_SGIS',
    'GL_MAX_4D_TEXTURE_SIZE_SGIS',
    'GL_MAX_CLIPMAP_DEPTH_SGIX',
    'GL_MAX_CLIPMAP_VIRTUAL_DEPTH_SGIX',
    'GL_MAX_FRAMEZOOM_FACTOR_SGIX',
    'GL_MAX_VIEWPORTS',
    'GL_MAX_ELEMENTS_INDICES',
    'GL_MAX_FRAGMENT_LIGHTS_SGIX',
    'GL_MAX_ACTIVE_LIGHTS_SGIX',
    'GL_MAX_MATRIX_PALETTE_STACK_DEPTH_ARB',
    'GL_MAX_PALETTE_MATRICES_ARB',
    'GL_MAX_PROGRAM_ALU_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_TEX_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_TEX_INDIRECTIONS_ARB',
    'GL_MAX_PROGRAM_NATIVE_ALU_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_NATIVE_TEX_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_NATIVE_TEX_INDIRECTIONS_ARB',
    'GL_MAX_PROGRAM_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_NATIVE_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_TEMPORARIES_ARB',
    'GL_MAX_PROGRAM_NATIVE_TEMPORARIES_ARB',
    'GL_MAX_PROGRAM_PARAMETERS_ARB',
    'GL_MAX_PROGRAM_NATIVE_PARAMETERS_ARB',
    'GL_MAX_PROGRAM_ATTRIBS_ARB',
    'GL_MAX_PROGRAM_NATIVE_ATTRIBS_ARB',
    'GL_MAX_PROGRAM_ADDRESS_REGISTERS_ARB',
    'GL_MAX_PROGRAM_NATIVE_ADDRESS_REGISTERS_ARB',
    'GL_MAX_PROGRAM_LOCAL_PARAMETERS_ARB',
    'GL_MAX_PROGRAM_ENV_PARAMETERS_ARB',
    'GL_MAX_PROGRAM_EXEC_INSTRUCTIONS_NV',
    'GL_MAX_PROGRAM_CALL_DEPTH_NV',
    'GL_MAX_PROGRAM_IF_DEPTH_NV',
    'GL_MAX_PROGRAM_LOOP_DEPTH_NV',
    'GL_MAX_PROGRAM_LOOP_COUNT_NV',
    'GL_MAX_PROGRAM_ALU_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_TEX_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_TEX_INDIRECTIONS_ARB',
    'GL_MAX_PROGRAM_NATIVE_ALU_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_NATIVE_TEX_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_NATIVE_TEX_INDIRECTIONS_ARB',
    'GL_MAX_PROGRAM_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_NATIVE_INSTRUCTIONS_ARB',
    'GL_MAX_PROGRAM_TEMPORARIES_ARB',
    'GL_MAX_PROGRAM_NATIVE_TEMPORARIES_ARB',
    'GL_MAX_PROGRAM_PARAMETERS_ARB',
    'GL_MAX_PROGRAM_NATIVE_PARAMETERS_ARB',
    'GL_MAX_PROGRAM_ATTRIBS_ARB',
    'GL_MAX_PROGRAM_NATIVE_ATTRIBS_ARB',
    'GL_MAX_PROGRAM_ADDRESS_REGISTERS_ARB',
    'GL_MAX_PROGRAM_NATIVE_ADDRESS_REGISTERS_ARB',
    'GL_MAX_PROGRAM_LOCAL_PARAMETERS_ARB',
    'GL_MAX_PROGRAM_ENV_PARAMETERS_ARB',
    'GL_MAX_PROGRAM_EXEC_INSTRUCTIONS_NV',
    'GL_MAX_PROGRAM_CALL_DEPTH_NV',
    'GL_MAX_PROGRAM_IF_DEPTH_NV',
    'GL_MAX_PROGRAM_LOOP_DEPTH_NV',
    'GL_MAX_PROGRAM_LOOP_COUNT_NV',
    'GL_PROGRAM_LENGTH_ARB',
    'GL_PROGRAM_ALU_INSTRUCTIONS_ARB',
    'GL_PROGRAM_TEX_INSTRUCTIONS_ARB',
    'GL_PROGRAM_TEX_INDIRECTIONS_ARB',
    'GL_PROGRAM_NATIVE_ALU_INSTRUCTIONS_ARB',
    'GL_PROGRAM_NATIVE_TEX_INSTRUCTIONS_ARB',
    'GL_PROGRAM_NATIVE_TEX_INDIRECTIONS_ARB',
    'GL_PROGRAM_FORMAT_ARB',
    'GL_PROGRAM_INSTRUCTIONS_ARB',
    'GL_PROGRAM_NATIVE_INSTRUCTIONS_ARB',
    'GL_PROGRAM_TEMPORARIES_ARB',
    'GL_PROGRAM_NATIVE_TEMPORARIES_ARB',
    'GL_PROGRAM_PARAMETERS_ARB',
    'GL_PROGRAM_NATIVE_PARAMETERS_ARB',
    'GL_PROGRAM_NATIVE_ATTRIBS_ARB',
    'GL_PROGRAM_ADDRESS_REGISTERS_ARB',
    'GL_PROGRAM_NATIVE_ADDRESS_REGISTERS_ARB',
    'GL_PROGRAM_UNDER_NATIVE_LIMITS_ARB',
    'GL_RGBA_FLOAT_MODE_ARB',
    'GL_RGBA_INTEGER_MODE_EXT',
    'GL_FRAMEBUFFER_SRGB_CAPABLE_EXT',
    'GL_SHADER_COMPILER',
    'GL_TRANSFORM_FEEDBACK_BUFFER_PAUSED',
    'GL_TRANSFORM_FEEDBACK_BUFFER_ACTIVE',
    'GL_QUADS_FOLLOW_PROVOKING_VERTEX_CONVENTION',
    'GL_TEXTURE_RENDERBUFFER_DATA_STORE_BINDING_NV',
    'GL_SUBPIXEL_BITS',
    'GL_DEBUG_NEXT_LOGGED_MESSAGE_LENGTH',
    'GL_COMPRESSED_TEXTURE_FORMATS',
)

state_deprecated_before_gl33 = (
    'GL_CURRENT_COLOR',
    'GL_CURRENT_INDEX',
    'GL_CURRENT_NORMAL',
    'GL_CURRENT_TEXTURE_COORDS',
    'GL_CURRENT_RASTER_COLOR',
    'GL_CURRENT_RASTER_INDEX',
    'GL_CURRENT_RASTER_TEXTURE_COORDS',
    'GL_CURRENT_RASTER_POSITION',
    'GL_CURRENT_RASTER_POSITION_VALID',
    'GL_CURRENT_RASTER_DISTANCE',
    'GL_POINT_SMOOTH',
    'GL_POINT_SIZE_MIN',
    'GL_POINT_SIZE_MAX',
    'GL_LINE_STIPPLE',
    'GL_LINE_STIPPLE_PATTERN',
    'GL_LINE_STIPPLE_REPEAT',
    'GL_LIST_MODE',
    'GL_LIST_BASE',
    'GL_LIST_INDEX',
    'GL_POLYGON_STIPPLE',
    'GL_EDGE_FLAG',
    'GL_LIGHTING',
    'GL_LIGHT_MODEL_LOCAL_VIEWER',
    'GL_LIGHT_MODEL_TWO_SIDE',
    'GL_LIGHT_MODEL_AMBIENT',
    'GL_SHADE_MODEL',
    'GL_COLOR_MATERIAL_FACE',
    'GL_COLOR_MATERIAL_PARAMETER',
    'GL_COLOR_MATERIAL',
    'GL_FOG',
    'GL_FOG_INDEX',
    'GL_FOG_DENSITY',
    'GL_FOG_START',
    'GL_FOG_END',
    'GL_FOG_MODE',
    'GL_FOG_COLOR',
    'GL_ACCUM_CLEAR_VALUE',
    'GL_MATRIX_MODE',
    'GL_NORMALIZE',
    'GL_MODELVIEW_MATRIX',
    'GL_PROJECTION_MATRIX',
    'GL_TEXTURE_MATRIX',
    'GL_ALPHA_TEST',
    'GL_ALPHA_TEST_FUNC',
    'GL_ALPHA_TEST_REF',
    'GL_INDEX_CLEAR_VALUE',
    'GL_INDEX_WRITEMASK',
    'GL_RENDER_MODE',
    'GL_PERSPECTIVE_CORRECTION_HINT',
    'GL_POINT_SMOOTH_HINT',
    'GL_FOG_HINT',
    'GL_MAP_COLOR',
    'GL_MAP_STENCIL',
    'GL_INDEX_SHIFT',
    'GL_INDEX_OFFSET',
    'GL_RED_SCALE',
    'GL_RED_BIAS',
    'GL_ZOOM_X',
    'GL_ZOOM_Y',
    'GL_GREEN_SCALE',
    'GL_GREEN_BIAS',
    'GL_BLUE_SCALE',
    'GL_BLUE_BIAS',
    'GL_ALPHA_BIAS',
    'GL_DEPTH_SCALE',
    'GL_DEPTH_BIAS',
    'GL_INDEX_BITS',
    'GL_RED_BITS',
    'GL_GREEN_BITS',
    'GL_BLUE_BITS',
    'GL_ALPHA_BITS',
    'GL_DEPTH_BITS',
    'GL_STENCIL_BITS',
    'GL_ACCUM_RED_BITS',
    'GL_ACCUM_GREEN_BITS',
    'GL_ACCUM_BLUE_BITS',
    'GL_ACCUM_ALPHA_BITS',
    'GL_AUTO_NORMAL',
    'GL_MAP1_COLOR_4',
    'GL_MAP1_INDEX',
    'GL_MAP1_NORMAL',
    'GL_MAP1_TEXTURE_COORD_1',
    'GL_MAP1_TEXTURE_COORD_2',
    'GL_MAP1_TEXTURE_COORD_3',
    'GL_MAP1_TEXTURE_COORD_4',
    'GL_MAP1_VERTEX_3',
    'GL_MAP1_VERTEX_4',
    'GL_MAP2_COLOR_4',
    'GL_MAP2_INDEX',
    'GL_MAP2_NORMAL',
    'GL_MAP2_TEXTURE_COORD_1',
    'GL_MAP2_TEXTURE_COORD_2',
    'GL_MAP2_TEXTURE_COORD_3',
    'GL_MAP2_TEXTURE_COORD_4',
    'GL_MAP2_VERTEX_3',
    'GL_MAP2_VERTEX_4',
    'GL_MAP1_GRID_DOMAIN',
    'GL_MAP1_GRID_SEGMENTS',
    'GL_MAP2_GRID_DOMAIN',
    'GL_MAP2_GRID_SEGMENTS',
    'GL_FEEDBACK_BUFFER_POINTER',
    'GL_FEEDBACK_BUFFER_SIZE',
    'GL_FEEDBACK_BUFFER_TYPE',
    'GL_SELECTION_BUFFER_POINTER',
    'GL_SELECTION_BUFFER_SIZE',
    'GL_CONVOLUTION_HINT_SGIX',
    'GL_CONVOLUTION_1D',
    'GL_CONVOLUTION_2D',
    'GL_SEPARABLE_2D',
    'GL_POST_CONVOLUTION_RED_SCALE',
    'GL_POST_CONVOLUTION_GREEN_SCALE',
    'GL_POST_CONVOLUTION_BLUE_SCALE',
    'GL_POST_CONVOLUTION_ALPHA_SCALE',
    'GL_POST_CONVOLUTION_RED_BIAS',
    'GL_POST_CONVOLUTION_GREEN_BIAS',
    'GL_POST_CONVOLUTION_BLUE_BIAS',
    'GL_POST_CONVOLUTION_ALPHA_BIAS',
    'GL_HISTOGRAM',
    'GL_MINMAX',
    'GL_RESCALE_NORMAL',
    'GL_VERTEX_ARRAY_BUFFER_BINDING',
    'GL_VERTEX_ARRAY',
    'GL_NORMAL_ARRAY_BUFFER_BINDING',
    'GL_NORMAL_ARRAY',
    'GL_COLOR_ARRAY_BUFFER_BINDING',
    'GL_COLOR_ARRAY',
    'GL_INDEX_ARRAY_BUFFER_BINDING',
    'GL_INDEX_ARRAY',
    'GL_TEXTURE_COORD_ARRAY_BUFFER_BINDING',
    'GL_TEXTURE_COORD_ARRAY',
    'GL_EDGE_FLAG_ARRAY_BUFFER_BINDING',
    'GL_EDGE_FLAG_ARRAY',
    'GL_VERTEX_ARRAY_SIZE',
    'GL_VERTEX_ARRAY_TYPE',
    'GL_VERTEX_ARRAY_STRIDE',
    'GL_VERTEX_ARRAY_COUNT_EXT',
    'GL_VERTEX_ARRAY_POINTER',
    'GL_NORMAL_ARRAY_TYPE',
    'GL_NORMAL_ARRAY_STRIDE',
    'GL_NORMAL_ARRAY_COUNT_EXT',
    'GL_COLOR_ARRAY_SIZE',
    'GL_COLOR_ARRAY_TYPE',
    'GL_COLOR_ARRAY_STRIDE',
    'GL_COLOR_ARRAY_COUNT_EXT',
    'GL_INDEX_ARRAY_TYPE',
    'GL_INDEX_ARRAY_STRIDE',
    'GL_INDEX_ARRAY_COUNT_EXT',
    'GL_TEXTURE_COORD_ARRAY_SIZE',
    'GL_TEXTURE_COORD_ARRAY_TYPE',
    'GL_TEXTURE_COORD_ARRAY_STRIDE',
    'GL_TEXTURE_COORD_ARRAY_COUNT_EXT',
    'GL_EDGE_FLAG_ARRAY_STRIDE',
    'GL_EDGE_FLAG_ARRAY_COUNT_EXT',
    'GL_NORMAL_ARRAY_POINTER',
    'GL_COLOR_ARRAY_POINTER',
    'GL_INDEX_ARRAY_POINTER',
    'GL_TEXTURE_COORD_ARRAY_POINTER',
    'GL_EDGE_FLAG_ARRAY_POINTER',
    'GL_COLOR_MATRIX',
    'GL_COLOR_MATRIX_STACK_DEPTH',
    'GL_POST_COLOR_MATRIX_RED_SCALE',
    'GL_POST_COLOR_MATRIX_GREEN_SCALE',
    'GL_POST_COLOR_MATRIX_BLUE_SCALE',
    'GL_POST_COLOR_MATRIX_ALPHA_SCALE',
    'GL_POST_COLOR_MATRIX_RED_BIAS',
    'GL_POST_COLOR_MATRIX_GREEN_BIAS',
    'GL_POST_COLOR_MATRIX_BLUE_BIAS',
    'GL_POST_COLOR_MATRIX_ALPHA_BIAS',
    'GL_TEXTURE_COLOR_TABLE_SGI',
    'GL_COLOR_TABLE',
    'GL_POST_CONVOLUTION_COLOR_TABLE',
    'GL_POST_COLOR_MATRIX_COLOR_TABLE',
    'GL_PIXEL_TEXTURE_SGIS',
    'GL_PIXEL_FRAGMENT_RGB_SOURCE_SGIS',
    'GL_PIXEL_FRAGMENT_ALPHA_SOURCE_SGIS',
    'GL_PIXEL_GROUP_COLOR_SGIS',
    'GL_FRAGMENT_LIGHTING_SGIX',
    'GL_FRAGMENT_COLOR_MATERIAL_SGIX',
    'GL_FRAGMENT_COLOR_MATERIAL_FACE_SGIX',
    'GL_FRAGMENT_COLOR_MATERIAL_PARAMETER_SGIX',
    'GL_CURRENT_RASTER_NORMAL_SGIX',
    'GL_LIGHT_ENV_MODE_SGIX',
    'GL_FRAGMENT_LIGHT_MODEL_LOCAL_VIEWER_SGIX',
    'GL_FRAGMENT_LIGHT_MODEL_TWO_SIDE_SGIX',
    'GL_FRAGMENT_LIGHT_MODEL_AMBIENT_SGIX',
    'GL_FRAGMENT_LIGHT_MODEL_NORMAL_INTERPOLATION_SGIX',
    'GL_FRAGMENT_LIGHT0_SGIX',
    'GL_TANGENT_ARRAY_TYPE_EXT',
    'GL_BINORMAL_ARRAY_TYPE_EXT',
    'GL_TANGENT_ARRAY_POINTER_EXT',
    'GL_BINORMAL_ARRAY_POINTER_EXT',
    'GL_FOG_COORD_SRC',
    'GL_CURRENT_FOG_COORD',
    'GL_FOG_COORD_ARRAY_BUFFER_BINDING',
    'GL_FOG_COORD_ARRAY_TYPE',
    'GL_FOG_COORD_ARRAY_STRIDE',
    'GL_FOG_COORD_ARRAY',
    'GL_COLOR_SUM',
    'GL_COLOR_SUM_CLAMP_NV',
    'GL_CLAMP_VERTEX_COLOR',
    'GL_CLAMP_FRAGMENT_COLOR',
    'GL_CURRENT_SECONDARY_COLOR',
    'GL_SECONDARY_COLOR_ARRAY_BUFFER_BINDING',
    'GL_SECONDARY_COLOR_ARRAY_SIZE',
    'GL_SECONDARY_COLOR_ARRAY_TYPE',
    'GL_SECONDARY_COLOR_ARRAY_STRIDE',
    'GL_SECONDARY_COLOR_ARRAY',
    'GL_ALIASED_POINT_SIZE_RANGE',
    'GL_CLIENT_ACTIVE_TEXTURE',
    'GL_TRANSPOSE_MODELVIEW_MATRIX',
    'GL_TRANSPOSE_PROJECTION_MATRIX',
    'GL_TRANSPOSE_TEXTURE_MATRIX',
    'GL_TRANSPOSE_COLOR_MATRIX',
    'GL_CURRENT_MATRIX_ARB',
    'GL_VERTEX_PROGRAM_TWO_SIDE',
    'GL_TEXTURE_RESIDENT',
    'GL_WEIGHT_ARRAY_BUFFER_BINDING',
    'GL_CURRENT_WEIGHT_ARB',
    'GL_WEIGHT_ARRAY_ARB',
    'GL_WEIGHT_ARRAY_TYPE_ARB',
    'GL_WEIGHT_ARRAY_STRIDE_ARB',
    'GL_WEIGHT_ARRAY_SIZE_ARB',
    'GL_WEIGHT_ARRAY_POINTER_ARB',
    'GL_RGB_SCALE',
    'GL_ALPHA_SCALE',
)

## some enable_disable items are also listed under state_deprecated_before_gl33
## this way if we decide to allow capturing of older state, they should still
## get handled by enable_disable
state_enable_disable = (
    'GL_POINT_SMOOTH',
    'GL_LINE_SMOOTH',
    'GL_LINE_STIPPLE',
    'GL_POLYGON_SMOOTH',
    'GL_POLYGON_STIPPLE',
    'GL_EDGE_FLAG',
    'GL_CULL_FACE',
    'GL_LIGHTING',
    'GL_LIGHT_MODEL_LOCAL_VIEWER',
    'GL_LIGHT_MODEL_TWO_SIDE',
    'GL_COLOR_MATERIAL',
    'GL_FOG',
    'GL_DEPTH_TEST',
    'GL_STENCIL_TEST',
    'GL_NORMALIZE',
    'GL_ALPHA_TEST',
    'GL_DITHER',
    'GL_BLEND',
    'GL_INDEX_LOGIC_OP',
    'GL_COLOR_LOGIC_OP',
    'GL_SCISSOR_TEST',
    'GL_INDEX_MODE',
    'GL_RGBA_MODE',
    'GL_DOUBLEBUFFER',
    'GL_STEREO',
    'GL_TEXTURE_GEN_S',
    'GL_TEXTURE_GEN_T',
    'GL_TEXTURE_GEN_R',
    'GL_TEXTURE_GEN_Q',
    'GL_MAP_COLOR',
    'GL_MAP_STENCIL',
    'GL_AUTO_NORMAL',
    'GL_MAP1_COLOR_4',
    'GL_MAP1_INDEX',
    'GL_MAP1_NORMAL',
    'GL_MAP1_TEXTURE_COORD_1',
    'GL_MAP1_TEXTURE_COORD_2',
    'GL_MAP1_TEXTURE_COORD_3',
    'GL_MAP1_TEXTURE_COORD_4',
    'GL_MAP1_VERTEX_3',
    'GL_MAP1_VERTEX_4',
    'GL_MAP2_COLOR_4',
    'GL_MAP2_INDEX',
    'GL_MAP2_NORMAL',
    'GL_MAP2_TEXTURE_COORD_1',
    'GL_MAP2_TEXTURE_COORD_2',
    'GL_MAP2_TEXTURE_COORD_3',
    'GL_MAP2_TEXTURE_COORD_4',
    'GL_MAP2_VERTEX_3',
    'GL_MAP2_VERTEX_4',
    #'GL_TEXTURE_1D',                   ## handled as part of texture state
    #'GL_TEXTURE_2D',
    #'GL_TEXTURE_3D',
    #'GL_RASTER_POSITION_UNCLIPPED_IBM',
    'GL_POLYGON_OFFSET_POINT',
    'GL_POLYGON_OFFSET_LINE',
    'GL_CLIP_DISTANCE0',
    'GL_CLIP_DISTANCE1',
    'GL_CLIP_DISTANCE2',
    'GL_CLIP_DISTANCE3',
    'GL_CLIP_DISTANCE4',
    'GL_CLIP_DISTANCE5',
    'GL_CLIP_DISTANCE6',
    'GL_CLIP_DISTANCE7',
    #'GL_LIGHT0',           ## handled as part of light state
    #'GL_LIGHT1',
    #'GL_LIGHT2',
    #'GL_LIGHT3',
    #'GL_LIGHT4',
    #'GL_LIGHT5',
    #'GL_LIGHT6',
    #'GL_LIGHT7',
    'GL_CONVOLUTION_1D',
    'GL_CONVOLUTION_2D',
    'GL_SEPARABLE_2D',
    'GL_HISTOGRAM',
    'GL_MINMAX',
    'GL_POLYGON_OFFSET_FILL',
    'GL_RESCALE_NORMAL',
    'GL_VERTEX_ARRAY',
    'GL_NORMAL_ARRAY',
    'GL_COLOR_ARRAY',
    'GL_INDEX_ARRAY',
    'GL_TEXTURE_COORD_ARRAY',
    'GL_EDGE_FLAG_ARRAY',
    'GL_COLOR_TABLE',
    #'GL_OCCLUSION_TEST_HP',    ## for some reason these are commented out of the code that feeds this script
    #'GL_OCCLUSION_TEST_RESULT_HP',
    'GL_CULL_VERTEX_EXT',
#    'GL_TEXTURE_COLOR_WRITEMASK_SGIS',         ## This needs a different setter
    'GL_DEBUG_OUTPUT_SYNCHRONOUS',
    'GL_FOG_COORD_ARRAY',
    'GL_COLOR_SUM',
    'GL_SECONDARY_COLOR_ARRAY',
    #'GL_TEXTURE_RECTANGLE',    ## for some reason these are commented out of the code that feeds this script
    #'GL_TEXTURE_CUBE_MAP',
    #'GL_VERTEX_ARRAY_RANGE_NV',
    #'GL_VERTEX_ARRAY_RANGE_VALID_NV',
    'GL_COLOR_SUM_CLAMP_NV',
    #'GL_VERTEX_PROGRAM_ARB',
    'GL_PROGRAM_POINT_SIZE',
    'GL_VERTEX_PROGRAM_TWO_SIDE',
    'GL_DEPTH_CLAMP',
    #'GL_VERTEX_ATTRIB_ARRAY0_NV',  ## for some reason these are commented out of the code that feeds this script
    #'GL_VERTEX_ATTRIB_ARRAY1_NV',
    #'GL_VERTEX_ATTRIB_ARRAY2_NV',
    #'GL_VERTEX_ATTRIB_ARRAY3_NV',
    #'GL_VERTEX_ATTRIB_ARRAY4_NV',
    #'GL_VERTEX_ATTRIB_ARRAY5_NV',
    #'GL_VERTEX_ATTRIB_ARRAY6_NV',
    #'GL_VERTEX_ATTRIB_ARRAY7_NV',
    #'GL_VERTEX_ATTRIB_ARRAY8_NV',
    #'GL_VERTEX_ATTRIB_ARRAY9_NV',
    #'GL_VERTEX_ATTRIB_ARRAY10_NV',
    #'GL_VERTEX_ATTRIB_ARRAY11_NV',
    #'GL_VERTEX_ATTRIB_ARRAY12_NV',
    #'GL_VERTEX_ATTRIB_ARRAY13_NV',
    #'GL_VERTEX_ATTRIB_ARRAY14_NV',
    #'GL_VERTEX_ATTRIB_ARRAY15_NV',
    'GL_WEIGHT_SUM_UNITY_ARB',
    'GL_VERTEX_BLEND_ARB',
    'GL_WEIGHT_ARRAY_ARB',
    'GL_PACK_INVERT_MESA',
    #'GL_FRAGMENT_PROGRAM_ARB',
    'GL_MATRIX_PALETTE_ARB',
    'GL_MATRIX_INDEX_ARRAY_ARB',
    'GL_TEXTURE_CUBE_MAP_SEAMLESS',
    'GL_POINT_SPRITE',
    'GL_DEPTH_BOUNDS_TEST_EXT',
    'GL_STENCIL_TEST_TWO_SIDE_EXT',
    'GL_RASTERIZER_DISCARD',
    'GL_FRAMEBUFFER_SRGB',
    'GL_FRAMEBUFFER_SRGB_CAPABLE_EXT',
    'GL_SHADER_COMPILER',
    'GL_TRANSFORM_FEEDBACK_BUFFER_PAUSED',
    'GL_TRANSFORM_FEEDBACK_BUFFER_ACTIVE',
    'GL_QUADS_FOLLOW_PROVOKING_VERTEX_CONVENTION',
    'GL_SAMPLE_MASK',
    'GL_SAMPLE_MASK_VALUE',
    'GL_PRIMITIVE_RESTART',
    #'GL_TEXTURE_CUBE_MAP_ARRAY',
    'GL_TEXTURE_BINDING_2D_MULTISAMPLE',
    'GL_DEBUG_OUTPUT',
    'GL_SAMPLE_ALPHA_TO_COVERAGE',
    'GL_SAMPLE_ALPHA_TO_ONE',
    'GL_SAMPLE_COVERAGE',
)

## this is a collection of simple state that can easily be set.
## Currently some are commented out because they require two or more gets
## to obtain all of the parameters to call the setter. Those special cases
## will be handled in another manner in the future.
## Some states do not have a setter because we are not interested in them
## right now (or I have not gotten around to implementing them).
state_setters = (
    ('GL_CURRENT_COLOR', 'glColor4fv(current_color)'),
    ('GL_CURRENT_INDEX', 'glIndexf(current_index)'),
    ('GL_CURRENT_NORMAL', 'glNormal3fv(current_normal)'),
    ('GL_CURRENT_TEXTURE_COORDS', 'glTexCoord4fv(current_texture_coords)'),
    ('GL_CURRENT_RASTER_COLOR', ''),
    ('GL_CURRENT_RASTER_INDEX', ''),
    ('GL_CURRENT_RASTER_TEXTURE_COORDS', ''),
    ('GL_CURRENT_RASTER_POSITION', ''),
    ('GL_CURRENT_RASTER_POSITION_VALID', ''),
    ('GL_CURRENT_RASTER_DISTANCE', ''),
    ('GL_POINT_SIZE', 'glPointSize(point_size)'),
    ('GL_POINT_SIZE_MIN', 'glPointParameterf(GL_POINT_SIZE_MIN, point_size_min)'),
    ('GL_POINT_SIZE_MAX', 'glPointParameterf(GL_POINT_SIZE_MAX, point_size_max)'),
    ('GL_POINT_DISTANCE_ATTENUATION', 'glPointParameterfv(GL_POINT_DISTANCE_ATTENUATION, point_distance_attenuation)'),
    ('GL_POINT_FADE_THRESHOLD_SIZE', 'glPointParameterf(GL_POINT_FADE_THRESHOLD_SIZE, point_fade_threshold_size)'),
    ('GL_LINE_WIDTH', 'glLineWidth(line_width)'),
    ('GL_LINE_STIPPLE_REPEAT,GL_LINE_STIPPLE_PATTERN', 'glLineStipple(line_stipple_repeat, line_stipple_pattern)'),
    ('GL_LIST_BASE', 'glListBase(list_base)'),
    ('GL_LIST_MODE', ''),
    ('GL_LIST_INDEX', ''),
    ('GL_POLYGON_MODE', 'glPolygonMode(GL_FRONT, polygon_mode[0]);glPolygonMode(GL_BACK, polygon_mode[1])'),
    ('GL_CULL_FACE_MODE', 'glCullFace(cull_face_mode)'),
    ('GL_FRONT_FACE', 'glFrontFace(front_face)'),
    ('GL_LIGHT_MODEL_AMBIENT', 'glLightModelfv(GL_LIGHT_MODEL_AMBIENT, light_model_ambient)'),
    ('GL_SHADE_MODEL', 'glShadeModel(shade_model)'),
    ('GL_COLOR_MATERIAL_FACE', ''),
    ('GL_COLOR_MATERIAL_PARAMETER', ''),
    ('GL_FOG_INDEX', 'glFogi(GL_FOG_INDEX, fog_index)'),
    ('GL_FOG_DENSITY', 'glFogf(GL_FOG_DENSITY, fog_density)'),
    ('GL_FOG_START', 'glFogf(GL_FOG_START, fog_start)'),
    ('GL_FOG_END', 'glFogf(GL_FOG_END, fog_end)'),
    ('GL_FOG_MODE', 'glFogi(GL_FOG_MODE, fog_mode)'),
    ('GL_FOG_COLOR', 'glFogfv(GL_FOG_COLOR, fog_color)'),
    ('GL_DEPTH_WRITEMASK', 'glDepthMask(depth_writemask)'),
    ('GL_DEPTH_RANGE', 'glDepthRangef(depth_range[0], depth_range[1])'),
    ('GL_DEPTH_CLEAR_VALUE', 'glClearDepthf(depth_clear_value)'),
    ('GL_DEPTH_FUNC', 'glDepthFunc(depth_func)'),
    ('GL_ACCUM_CLEAR_VALUE', 'glClearAccum(accum_clear_value[0], accum_clear_value[1], accum_clear_value[2], accum_clear_value[3])'),
    ('GL_STENCIL_WRITEMASK', 'glStencilMaskSeparate(GL_FRONT, stencil_writemask)'),
    ('GL_STENCIL_BACK_WRITEMASK', 'glStencilMaskSeparate(GL_BACK, stencil_back_writemask)'),
    ('GL_STENCIL_CLEAR_VALUE', 'glClearStencil(stencil_clear_value)'),
    ('GL_STENCIL_FUNC,GL_STENCIL_REF,GL_STENCIL_VALUE_MASK', 'glStencilFuncSeparate(GL_FRONT, stencil_func, stencil_ref, stencil_value_mask)'),
    ('GL_STENCIL_BACK_FUNC,GL_STENCIL_BACK_REF,GL_STENCIL_BACK_VALUE_MASK', 'glStencilFuncSeparate(GL_BACK, stencil_back_func, stencil_back_ref, stencil_back_value_mask)'),
    ('GL_STENCIL_FAIL,GL_STENCIL_PASS_DEPTH_FAIL,GL_STENCIL_PASS_DEPTH_PASS', 'glStencilOpSeparate(GL_FRONT, stencil_fail, stencil_pass_depth_fail, stencil_pass_depth_pass)'),
    ('GL_STENCIL_BACK_FAIL,GL_STENCIL_BACK_PASS_DEPTH_FAIL,GL_STENCIL_BACK_PASS_DEPTH_PASS', 'glStencilOpSeparate(GL_BACK, stencil_back_fail, stencil_back_pass_depth_fail, stencil_back_pass_depth_pass)'),
    ('GL_MATRIX_MODE', 'glMatrixMode(matrix_mode)'),
    ('GL_VIEWPORT', 'glViewport(viewport[0], viewport[1], viewport[2], viewport[3])'),
    ('GL_PIXEL_UNPACK_BUFFER_BINDING', 'glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pixel_unpack_buffer_binding)'),
    ('GL_UNPACK_SWAP_BYTES', 'glPixelStorei(GL_UNPACK_SWAP_BYTES, unpack_swap_bytes)'),
    ('GL_UNPACK_LSB_FIRST', 'glPixelStorei(GL_UNPACK_LSB_FIRST, unpack_lsb_first)'),
    ('GL_PIXEL_PACK_BUFFER_BINDING', 'glBindBuffer(GL_PIXEL_PACK_BUFFER, pixel_pack_buffer_binding)'),
    ('GL_PACK_SWAP_BYTES', 'glPixelStorei(GL_PACK_SWAP_BYTES, pack_swap_bytes)'),
    ('GL_PACK_LSB_FIRST', 'glPixelStorei(GL_PACK_LSB_FIRST, pack_lsb_first)'),
    ('GL_CLAMP_READ_COLOR', 'glClampColor(GL_CLAMP_READ_COLOR, clamp_read_color)'),
    ('GL_PROVOKING_VERTEX', 'glProvokingVertex(provoking_vertex)'),
    ('GL_ALPHA_TEST_FUNC,GL_ALPHA_TEST_REF', 'glAlphaFunc(alpha_test_func, alpha_test_ref)'),
    ('GL_BLEND_SRC_RGB,GL_BLEND_DST_RGB,GL_BLEND_SRC_ALPHA,GL_BLEND_DST_ALPHA', 'glBlendFuncSeparate(blend_src_rgb, blend_dst_rgb, blend_src_alpha, blend_dst_alpha)'),
    #('GL_BLEND_DST', ''), ## dont handle this since it could override glBlendFuncSeparate
    #('GL_BLEND_SRC', ''), ## dont handle this since it could override glBlendFuncSeparate
    ('GL_LOGIC_OP_MODE', 'glLogicOp(logic_op_mode)'),
    ('GL_DRAW_BUFFER', 'glDrawBuffer(draw_buffer)'),
    ('GL_READ_BUFFER', 'glReadBuffer(read_buffer)'),
    ('GL_SCISSOR_BOX', 'glScissor(scissor_box[0], scissor_box[1], scissor_box[2], scissor_box[3])'),
    ('GL_INDEX_CLEAR_VALUE', 'glClearIndex(index_clear_value)'),
    ('GL_INDEX_WRITEMASK', 'glIndexMask(index_writemask)'),
    ('GL_COLOR_CLEAR_VALUE', 'glClearColor(color_clear_value[0], color_clear_value[1], color_clear_value[2], color_clear_value[3])'),
    ('GL_COLOR_WRITEMASK', 'glColorMask(color_writemask[0], color_writemask[1], color_writemask[2], color_writemask[3])'),
#    ('GL_RENDER_MODE', 'glRenderMode(render_mode)'), ## needs a result..
    ('GL_PERSPECTIVE_CORRECTION_HINT', 'glHint(GL_PERSPECTIVE_CORRECTION_HINT, perspective_correction_hint)'),
    ('GL_POINT_SMOOTH_HINT', 'glHint(GL_POINT_SMOOTH_HINT, point_smooth_hint)'),
    ('GL_LINE_SMOOTH_HINT', 'glHint(GL_LINE_SMOOTH_HINT, line_smooth_hint)'),
    ('GL_POLYGON_SMOOTH_HINT', 'glHint(GL_POLYGON_SMOOTH_HINT, polygon_smooth_hint)'),
    ('GL_FOG_HINT', 'glHint(GL_FOG_HINT, fog_hint)'),
    ('GL_BLEND_COLOR', 'glBlendColor(blend_color[0], blend_color[1], blend_color[2], blend_color[3])'),
    ('GL_BLEND_EQUATION_RGB,GL_BLEND_EQUATION_ALPHA', 'glBlendEquationSeparate(blend_equation_rgb, blend_equation_alpha)'),
    #('GL_BLEND_EQUATION', 'glBlendEquation(blend_equation)'), ## dont handle this since it could override glBlendEquationSeparate
    ('GL_POLYGON_OFFSET_FACTOR,GL_POLYGON_OFFSET_UNITS', 'glPolygonOffset(polygon_offset_factor, polygon_offset_units)'),
    ('GL_UNPACK_SWAP_BYTES', 'glPixelStorei(GL_UNPACK_SWAP_BYTES, unpack_swap_bytes)'),
    ('GL_UNPACK_LSB_FIRST', 'glPixelStorei(GL_UNPACK_LSB_FIRST, unpack_lsb_first)'),
    ('GL_UNPACK_ROW_LENGTH', 'glPixelStorei(GL_UNPACK_ROW_LENGTH, unpack_row_length)'),
    ('GL_UNPACK_SKIP_ROWS','glPixelStorei(GL_UNPACK_SKIP_ROWS, unpack_skip_rows)'),
    ('GL_UNPACK_SKIP_PIXELS','glPixelStorei(GL_UNPACK_SKIP_PIXELS, unpack_skip_pixels)'),
    ('GL_UNPACK_ALIGNMENT','glPixelStorei(GL_UNPACK_ALIGNMENT, unpack_alignment)'),
    ('GL_UNPACK_IMAGE_HEIGHT','glPixelStorei(GL_UNPACK_IMAGE_HEIGHT, unpack_image_height)'),
    ('GL_UNPACK_SKIP_IMAGES','glPixelStorei(GL_UNPACK_SKIP_IMAGES, unpack_skip_images)'),
    ('GL_PACK_SWAP_BYTES', 'glPixelStorei(GL_PACK_SWAP_BYTES, pack_swap_bytes)'),
    ('GL_PACK_LSB_FIRST', 'glPixelStorei(GL_PACK_LSB_FIRST, pack_lsb_first)'),
    ('GL_PACK_ROW_LENGTH', 'glPixelStorei(GL_PACK_ROW_LENGTH, pack_row_length)'),
    ('GL_PACK_SKIP_ROWS','glPixelStorei(GL_PACK_SKIP_ROWS, pack_skip_rows)'),
    ('GL_PACK_SKIP_PIXELS','glPixelStorei(GL_PACK_SKIP_PIXELS, pack_skip_pixels)'),
    ('GL_PACK_ALIGNMENT','glPixelStorei(GL_PACK_ALIGNMENT, pack_alignment)'),
    ('GL_PACK_IMAGE_HEIGHT','glPixelStorei(GL_PACK_IMAGE_HEIGHT, pack_image_height)'),
    ('GL_PACK_SKIP_IMAGES','glPixelStorei(GL_PACK_SKIP_IMAGES, pack_skip_images)'),
    ('GL_ARRAY_BUFFER_BINDING', 'glBindBuffer(GL_ARRAY_BUFFER, array_buffer_binding)'),
    ('GL_ELEMENT_ARRAY_BUFFER_BINDING', 'glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, element_array_buffer_binding)'),
    ('GL_VERTEX_ARRAY_BUFFER_BINDING', 'glBindBuffer(GL_VERTEX_ARRAY_BUFFER, vertex_array_buffer_binding)'),
    ('GL_NORMAL_ARRAY_BUFFER_BINDING', 'glBindBuffer(GL_NORMAL_ARRAY_BUFFER, normal_array_buffer_binding)'),
    ('GL_COLOR_ARRAY_BUFFER_BINDING', 'glBindBuffer(GL_COLOR_ARRAY_BUFFER, color_array_buffer_binding)'),
    ('GL_INDEX_ARRAY_BUFFER_BINDING', 'glBindBuffer(GL_INDEX_ARRAY_BUFFER, index_array_buffer_binding)'),
    ('GL_TEXTURE_COORD_ARRAY_BUFFER_BINDING', 'glBindBuffer(GL_TEXTURE_COORD_ARRAY_BUFFER, texture_coord_array_buffer_binding)'),
    ('GL_EDGE_FLAG_ARRAY_BUFFER_BINDING', 'glBindBuffer(GL_EDGE_FLAG_ARRAY_BUFFER, edge_flag_array_buffer_binding)'),
    ('GL_SECONDARY_COLOR_ARRAY_BUFFER_BINDING', 'glBindBuffer(GL_SECONDARY_COLOR_ARRAY_BUFFER, secondary_color_array_buffer_binding)'),
    ('GL_FOG_COORD_ARRAY_BUFFER_BINDING', 'glBindBuffer(GL_FOG_COORD_ARRAY_BUFFER, fog_coord_array_buffer_binding)'),
    ('GL_WEIGHT_ARRAY_BUFFER_BINDING', 'glBindBuffer(GL_WEIGHT_ARRAY_BUFFER, weight_array_buffer_binding)'),
    ('GL_SAMPLE_COVERAGE_VALUE,GL_SAMPLE_COVERAGE_INVERT', 'glSampleCoverage(sample_coverage_value, sample_coverage_invert)'),

    ## texture-related state that is queried using glGetTexParameter,
    ('GL_TEXTURE_BORDER_COLOR', 'glTexParameterfv(target, GL_TEXTURE_BORDER_COLOR, texture_border_color)'),
    ('GL_TEXTURE_MAG_FILTER', 'glTexParameteri(target, GL_TEXTURE_MAG_FILTER, texture_mag_filter)'),
    ('GL_TEXTURE_MIN_FILTER', 'glTexParameteri(target, GL_TEXTURE_MIN_FILTER, texture_min_filter)'),
    ('GL_TEXTURE_WRAP_S', 'glTexParameteri(target, GL_TEXTURE_WRAP_S, texture_wrap_s)'),
    ('GL_TEXTURE_WRAP_T', 'glTexParameteri(target, GL_TEXTURE_WRAP_T, texture_wrap_t)'),
    ('GL_TEXTURE_WRAP_R', 'glTexParameteri(target, GL_TEXTURE_WRAP_R, texture_wrap_r)'),
    ('GL_TEXTURE_PRIORITY', 'glTexParameterf(target, GL_TEXTURE_PRIORITY, texture_priority)'),
    ('GL_TEXTURE_RESIDENT', 'glTexParameteri(target, GL_TEXTURE_RESIDENT, texture_resident)'),
    ('GL_TEXTURE_COMPARE_FAIL_VALUE_ARB', 'glTexParameterf(target, GL_TEXTURE_COMPARE_FAIL_VALUE_ARB, texture_compare_fail_value_arb)'),
    ('GL_TEXTURE_MIN_LOD', 'glTexParameterf(target, GL_TEXTURE_MIN_LOD, texture_min_lod)'),
    ('GL_TEXTURE_MAX_LOD', 'glTexParameterf(target, GL_TEXTURE_MAX_LOD, texture_max_lod)'),
    ('GL_TEXTURE_BASE_LEVEL', 'glTexParameterf(target, GL_TEXTURE_BASE_LEVEL, texture_base_level)'),
    ('GL_TEXTURE_MAX_LEVEL', 'glTexParameterf(target, GL_TEXTURE_MAX_LEVEL, texture_max_level)'),
    ('GL_TEXTURE_CLIPMAP_CENTER_SGIX', 'glTexParameteriv(target, GL_TEXTURE_CLIPMAP_CENTER_SGIX, texture_clipmap_center_sgix)'),
    ('GL_TEXTURE_CLIPMAP_FRAME_SGIX', 'glTexParameterf(target, GL_TEXTURE_CLIPMAP_FRAME_SGIX, texture_clipmap_frame_sgix)'),
    ('GL_TEXTURE_CLIPMAP_OFFSET_SGIX', 'glTexParameteriv(target, GL_TEXTURE_CLIPMAP_OFFSET_SGIX, texture_clipmap_offset_sgix)'),
    ('GL_TEXTURE_CLIPMAP_VIRTUAL_DEPTH_SGIX', 'glTexParameteriv(target, GL_TEXTURE_CLIPMAP_VIRTUAL_DEPTH_SGIX, texture_clipmap_virtual_depth_sgix)'),
    ('GL_POST_TEXTURE_FILTER_BIAS_SGIX', 'glTexParameterf(target, GL_POST_TEXTURE_FILTER_BIAS_SGIX, post_texture_filter_bias_sgix)'),
    ('GL_POST_TEXTURE_FILTER_SCALE_SGIX', 'glTexParameterf(target, GL_POST_TEXTURE_FILTER_SCALE_SGIX, post_texture_filter_scale_sgix)'),
    ('GL_TEXTURE_LOD_BIAS_S_SGIX', 'glTexParameterf(target, GL_TEXTURE_LOD_BIAS_S_SGIX, texture_lod_bias_s_sgix)'),
    ('GL_TEXTURE_LOD_BIAS_T_SGIX', 'glTexParameterf(target, GL_TEXTURE_LOD_BIAS_T_SGIX, texture_lod_bias_t_sgix)'),
    ('GL_TEXTURE_LOD_BIAS_R_SGIX', 'glTexParameterf(target, GL_TEXTURE_LOD_BIAS_R_SGIX, texture_lod_bias_r_sgix)'),
    ('GL_GENERATE_MIPMAP', 'glTexParameteri(target, GL_GENERATE_MIPMAP, generate_mipmap)'),
    ('GL_TEXTURE_COMPARE_SGIX', 'glTexParameteri(target, GL_TEXTURE_COMPARE_SGIX, texture_compare_sgix)'),
    ('GL_TEXTURE_COMPARE_OPERATOR_SGIX', 'glTexParameteri(target, GL_TEXTURE_COMPARE_OPERATOR_SGIX, texture_compare_operator_sgix)'),
    ('GL_TEXTURE_VIEW_MIN_LEVEL', 'glTexParameteri(target, GL_TEXTURE_VIEW_MIN_LEVEL, texture_view_min_level)'),
    ('GL_TEXTURE_VIEW_NUM_LEVELS', 'glTexParameteri(target, GL_TEXTURE_VIEW_NUM_LEVELS, texture_view_num_levels)'),
    ('GL_TEXTURE_VIEW_MIN_LAYER', 'glTexParameteri(target, GL_TEXTURE_VIEW_MIN_LAYER, texture_view_min_layer)'),
    ('GL_TEXTURE_VIEW_NUM_LAYERS', 'glTexParameteri(target, GL_TEXTURE_VIEW_NUM_LAYERS, texture_view_num_layers)'),
    ('GL_TEXTURE_IMMUTABLE_LEVELS', 'glTexParameteri(target, GL_TEXTURE_IMMUTABLE_LEVELS, texture_immutable_levels)'),
    ('GL_TEXTURE_MAX_CLAMP_S_SGIX', 'glTexParameteri(target, GL_TEXTURE_MAX_CLAMP_S_SGIX, texture_max_clamp_s_sgix)'),
    ('GL_TEXTURE_MAX_CLAMP_T_SGIX', 'glTexParameteri(target, GL_TEXTURE_MAX_CLAMP_T_SGIX, texture_max_clamp_t_sgix)'),
    ('GL_TEXTURE_MAX_CLAMP_R_SGIX', 'glTexParameteri(target, GL_TEXTURE_MAX_CLAMP_R_SGIX, texture_max_clamp_r_sgix)'),
    ('GL_TEXTURE_MAX_ANISOTROPY_EXT', 'glTexParameteri(target, GL_TEXTURE_MAX_ANISOTROPY_EXT, texture_max_anisotropy_ext)'),
    ('GL_TEXTURE_LOD_BIAS', 'glTexParameteri(target, GL_TEXTURE_LOD_BIAS, texture_lod_bias)'),
    ('GL_TEXTURE_STORAGE_HINT_APPLE', 'glTexParameteri(target, GL_TEXTURE_STORAGE_HINT_APPLE, texture_storage_hint_apple)'),
    ('GL_DEPTH_TEXTURE_MODE', 'glTexParameteri(target, GL_DEPTH_TEXTURE_MODE, depth_texture_mode)'),
    ('GL_TEXTURE_COMPARE_MODE', 'glTexParameteri(target, GL_TEXTURE_COMPARE_MODE, texture_compare_mode)'),
    ('GL_TEXTURE_COMPARE_FUNC', 'glTexParameteri(target, GL_TEXTURE_COMPARE_FUNC, texture_compare_func)'),
    ('GL_TEXTURE_UNSIGNED_REMAP_MODE_NV', 'glTexParameteri(target, GL_TEXTURE_UNSIGNED_REMAP_MODE_NV, texture_unsigned_remap_mode_nv)'),
    ('GL_TEXTURE_SRGB_DECODE_EXT', 'glTexParameteri(target, GL_TEXTURE_SRGB_DECODE_EXT, texture_srgb_decode_ext)'),
    ('GL_TEXTURE_CROP_RECT_OES', 'glTexParameteriv(target, GL_TEXTURE_CROP_RECT_OES, texture_crop_rect_oes)'),
    ('GL_TEXTURE_SWIZZLE_R', 'glTexParameteri(target, GL_TEXTURE_SWIZZLE_R, texture_swizzle_r)'),
    ('GL_TEXTURE_SWIZZLE_G', 'glTexParameteri(target, GL_TEXTURE_SWIZZLE_G, texture_swizzle_g)'),
    ('GL_TEXTURE_SWIZZLE_B', 'glTexParameteri(target, GL_TEXTURE_SWIZZLE_B, texture_swizzle_b)'),
    ('GL_TEXTURE_SWIZZLE_A', 'glTexParameteri(target, GL_TEXTURE_SWIZZLE_A, texture_swizzle_a)'),
    ('GL_TEXTURE_SWIZZLE_RGBA', 'glTexParameteriv(target, GL_TEXTURE_SWIZZLE_RGBA, texture_swizzle_rgba)'),
    ('GL_DEPTH_STENCIL_TEXTURE_MODE', 'glTexParameteri(target, GL_DEPTH_STENCIL_TEXTURE_MODE, depth_stencil_texture_mode)'),

    ## queried using glGetTexLevelParameter
    ## These are all queried and set using special-cased functions (see dump_texture_parameters)
    ('GL_TEXTURE_WIDTH', ''),
    ('GL_TEXTURE_HEIGHT', ''),
    ('GL_TEXTURE_INTERNAL_FORMAT', ''),
    ('GL_TEXTURE_BORDER', ''),
    ('GL_TEXTURE_RED_SIZE', ''),
    ('GL_TEXTURE_GREEN_SIZE', ''),
    ('GL_TEXTURE_BLUE_SIZE', ''),
    ('GL_TEXTURE_ALPHA_SIZE', ''),
    ('GL_TEXTURE_LUMINANCE_SIZE', ''),
    ('GL_TEXTURE_INTENSITY_SIZE', ''),
    ('GL_TEXTURE_DEPTH', ''),
    ('GL_TEXTURE_COMPRESSED_IMAGE_SIZE', ''),
    ('GL_TEXTURE_COMPRESSED', ''),
    ('GL_TEXTURE_DEPTH_SIZE', ''),
    ('GL_TEXTURE_STENCIL_SIZE', ''),
    ('GL_TEXTURE_RED_TYPE', ''),
    ('GL_TEXTURE_GREEN_TYPE', ''),
    ('GL_TEXTURE_BLUE_TYPE', ''),
    ('GL_TEXTURE_ALPHA_TYPE', ''),
    ('GL_TEXTURE_LUMINANCE_TYPE', ''),
    ('GL_TEXTURE_INTENSITY_TYPE', ''),
    ('GL_TEXTURE_DEPTH_TYPE', ''),
    ('GL_TEXTURE_SAMPLES', ''),
    ('GL_TEXTURE_FIXED_SAMPLE_LOCATIONS', ''),
    ('GL_TEXTURE_BUFFER_OFFSET', ''),
    ('GL_TEXTURE_BUFFER_SIZE', ''),

)

class GetInflector:
    '''Objects that describes how to inflect.'''

    reduced_types = {
        B: I,
        E: I,
        I: F,
    }

    def __init__(self, radical, inflections, suffix = ''):
        self.radical = radical
        self.inflections = inflections
        self.suffix = suffix

    def reduced_type(self, type):
        if type in self.inflections:
            return type
        if type in self.reduced_types:
            return self.reduced_type(self.reduced_types[type])
        raise NotImplementedError

    def inflect(self, type):
        return self.radical + self.inflection(type) + self.suffix

    def inflection(self, type):
        type = self.reduced_type(type)
        assert type in self.inflections
        return self.inflections[type]

    def __str__(self):
        return self.radical + self.suffix


class StateGetter(Visitor):
    '''Type visitor that is able to extract the state via one of the glGet*
    functions.

    It will declare any temporary variable
    '''

    def __init__(self, radical, inflections, suffix=''):
        self.inflector = GetInflector(radical, inflections)
        self.suffix = suffix

    def iter(self):
        for function, type, count, name in parameters:
            inflection = self.inflector.radical + self.suffix
            if inflection not in function.split(','):
                continue
            if type is X:
                continue
            yield type, count, name

    def __call__(self, *args):
        pname = args[-1]
        for type, count, name in self.iter():
            if name == pname:
                if count != 1:
                    type = Array(type, str(count))

                return type, self.visit(type, args)

        print '// *** "%s" was not implemented' % pname
        raise NotImplementedError

    def temp_name(self, args):
        '''Return the name of a temporary variable to hold the state.'''
        pname = args[-1]

        return pname[3:].lower()

    def visitConst(self, const, args):
        return self.visit(const.type, args)

    def visitScalar(self, type, args):
        temp_name = self.temp_name(args)
        elem_type = self.inflector.reduced_type(type)
        inflection = self.inflector.inflect(type)
        if inflection.endswith('v'):
            print '            %s %s = 0;' % (elem_type, temp_name)
            print '            _%s(%s, &%s);' % (inflection + self.suffix, ', '.join(args), temp_name)
        else:
            print '            %s %s = _%s(%s);' % (elem_type, temp_name, inflection + self.suffix, ', '.join(args))
        return temp_name

    def visitString(self, string, args):
        temp_name = self.temp_name(args)
        inflection = self.inflector.inflect(string)
        assert not inflection.endswith('v')
        print '            %s %s = (%s)_%s(%s);' % (string, temp_name, string, inflection + self.suffix, ', '.join(args))
        return temp_name

    def visitAlias(self, alias, args):
        return self.visitScalar(alias, args)

    def visitEnum(self, enum, args):
        return self.visitScalar(enum, args)

    def visitBitmask(self, bitmask, args):
        return self.visit(GLint, args)

    def visitArray(self, array, args):
        temp_name = self.temp_name(args)
        if array.length == '1':
            return self.visit(array.type)
        elem_type = self.inflector.reduced_type(array.type)
        inflection = self.inflector.inflect(array.type)
        assert inflection.endswith('v')
        array_length = array.length
        if array_length.isdigit():
            # Static integer length
            print '            %s %s[%s + 1];' % (elem_type, temp_name, array_length)
        else:
            # Put the length in a variable to avoid recomputing it every time
            print '            size_t _%s_length = %s;' % (temp_name, array_length)
            array_length = '_%s_length' % temp_name
            # Allocate a dynamic sized array
            print '            %s *%s = _allocator.alloc<%s>(%s + 1);' % (elem_type, temp_name, elem_type, array_length)
        print '            memset(%s, 0, %s * sizeof(*%s));' % (temp_name, array_length, temp_name)
        print '            %s[%s] = (%s)0xdeadc0de;' % (temp_name, array_length, elem_type)
        print '            _%s(%s, %s);' % (inflection + self.suffix, ', '.join(args), temp_name)
        # Simple buffer overflow detection
        print '            assert(%s[%s] == (%s)0xdeadc0de);' % (temp_name, array_length, elem_type)
        return temp_name

    def visitOpaque(self, pointer, args):
        temp_name = self.temp_name(args)
        inflection = self.inflector.inflect(pointer)
        assert inflection.endswith('v')
        print '            GLvoid *%s;' % temp_name
        print '            _%s(%s, &%s);' % (inflection + self.suffix, ', '.join(args), temp_name)
        return temp_name

    def emitSetter(self, *args):
        if self.emit_enable_disable(args):
           pass
        elif not self.emit_setter(args): 
            print '// need the setter here     _trace_func(arg0, arg1, _result, false);'

    def emit_setter(self, args):
        name = args[-1]
        for stateNames, setters in state_setters:
             if name in stateNames.split(','):
                if (setters == ''):
                    print '            // We dont want to replay this state'
                else:
                    for setter in setters.split(';'):
                        if len(setter) > 0:
                            print '            _trace_%s, false);' % setter[:-1]
                return 1
        return 0

    def emit_enable_disable(self, args):
        name = args[-1]
        variable = self.temp_name(args)
        if name in state_enable_disable:
            variable = self.temp_name(args)
            print '            if ( %s == GL_TRUE ) {' % variable
            print '                _trace_glEnable(%s, false);' % name
            print '            } else {'
            print '                _trace_glDisable(%s, false);' % name
            print '            }'
            return 1
        else:
            return 0

glGet = StateGetter('glGet', {
    B: 'Booleanv',
    I: 'Integerv',
    F: 'Floatv',
    D: 'Doublev',
    S: 'String',
    P: 'Pointerv',
})

glGetMaterial = StateGetter('glGetMaterial', {I: 'iv', F: 'fv'})
glGetLight = StateGetter('glGetLight', {I: 'iv', F: 'fv'})
glGetVertexAttrib = StateGetter('glGetVertexAttrib', {I: 'iv', F: 'fv', D: 'dv', P: 'Pointerv'})
glGetTexParameter = StateGetter('glGetTexParameter', {I: 'iv', F: 'fv'})
glGetTexEnv = StateGetter('glGetTexEnv', {I: 'iv', F: 'fv'})
glGetTexLevelParameter = StateGetter('glGetTexLevelParameter', {I: 'iv', F: 'fv'})
glGetShader = StateGetter('glGetShaderiv', {I: 'iv'})
glGetProgram = StateGetter('glGetProgram', {I: 'iv'})
glGetProgramARB = StateGetter('glGetProgram', {I: 'iv', F: 'fv', S: 'Stringv'}, 'ARB')
glGetFramebufferAttachmentParameter = StateGetter('glGetFramebufferAttachmentParameter', {I: 'iv'})
glGetBufferParameter = StateGetter('glGetBufferParameter', {I: 'iv', I64: 'i64v', B: 'iv', P: 'v'})
glGetRenderbufferParameter = StateGetter('glGetRenderbufferParameter', {I: 'iv'})

class StateSnapshot:
    '''Class to generate code to snapshot all GL state and recreate it in the trace file.'''
    '''Assumes that all the created objects are known by the gltrace::Context class.'''

    def __init__(self):
        pass

    def generateUniformCalls(self, funcPrefix, firstParam):
        print '            GLchar uniformName[1024];'
        print '            memset(uniformName, 0, 1024);'
        print '            GLenum uniformType = GL_NONE;'
        print '            GLint uniformSize = 0;'
        print '            GLfloat fParams[16];'
        print '            GLint iParams[16];'
        print '            GLdouble dParams[16];'
        print '            GLuint uParams[16];'
        print '            memset(fParams, 0, 16*sizeof(GLfloat));'
        print '            memset(iParams, 0, 16*sizeof(GLint));'
        print '            memset(dParams, 0, 16*sizeof(GLdouble));'
        print '            memset(uParams, 0, 16*sizeof(GLuint));'
        print '            GLint active_uniforms = 0;'
        print '            _glGetProgramiv(programName, GL_ACTIVE_UNIFORMS, &active_uniforms);'
        print '            for (GLint index = 0; index < active_uniforms; ++index) {'
        print '                _glGetActiveUniform(programName, index, 1024, NULL, &uniformSize, &uniformType, uniformName);'
        print '                if (strncmp(uniformName, "gl_", 3) == 0 ) { continue; }'
        print '                if (uniformSize > 1 && strncmp(&uniformName[strlen(uniformName)-3], "[0]", 3) == 0) { uniformName[strlen(uniformName)-3] = \'\\0\'; }'
        print '                size_t nameLen = strlen(uniformName);'
        print '                for (unsigned int i = 0; i < uniformSize; ++i) {'
        print '                    if (uniformSize > 1) {'
        print '                        std::string nameString(uniformName);'
        print '                        sprintf(uniformName, "%s[%d]", nameString.substr(0, nameLen).c_str(), i);'
        print '                    }'
        print '                    // Get the uniform location'
        print '                    GLint location = _glGetUniformLocation(programName, uniformName);'
        print '                    // Now emit a trace call to get the uniform location, and supply the known result.'
        print '                    // This will allow the replayer to use the correct uniform location.'
        print '                    _trace_glGetUniformLocation(programName, uniformName, location, false);'
        print '                    if (location == -1) { continue; }'
        print '                    if (uniformType == GL_INT || uniformType == GL_BOOL) {'
        print '                        _glGetUniformiv(programName, location, iParams); _trace_gl%sUniform1iv(%slocation, 1, iParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_INT_VEC2 || uniformType == GL_BOOL_VEC2) {'
        print '                        _glGetUniformiv(programName, location, iParams); _trace_gl%sUniform2iv(%slocation, 1, iParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_INT_VEC3 || uniformType == GL_BOOL_VEC3) {'
        print '                        _glGetUniformiv(programName, location, iParams); _trace_gl%sUniform3iv(%slocation, 1, iParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_INT_VEC4 || uniformType == GL_BOOL_VEC4) {'
        print '                        _glGetUniformiv(programName, location, iParams); _trace_gl%sUniform4iv(%slocation, 1, iParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_UNSIGNED_INT) {'
        print '                        _glGetUniformiv(programName, location, iParams); _trace_gl%sUniform1uiv(%slocation, 1, uParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_UNSIGNED_INT_VEC2) {'
        print '                        _glGetUniformiv(programName, location, iParams); _trace_gl%sUniform2uiv(%slocation, 1, uParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_UNSIGNED_INT_VEC3) {'
        print '                        _glGetUniformiv(programName, location, iParams); _trace_gl%sUniform3uiv(%slocation, 1, uParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_UNSIGNED_INT_VEC4) {'
        print '                        _glGetUniformiv(programName, location, iParams); _trace_gl%sUniform4uiv(%slocation, 1, uParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniform1fv(%slocation, 1, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_VEC2) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniform2fv(%slocation, 1, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_VEC3) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniform3fv(%slocation, 1, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_VEC4) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniform4fv(%slocation, 1, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniform1dv(%slocation, 1, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_VEC2) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniform2dv(%slocation, 1, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_VEC3) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniform3dv(%slocation, 1, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_VEC4) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniform4dv(%slocation, 1, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_MAT2) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniformMatrix2fv(%slocation, 1, GL_FALSE, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_MAT3) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniformMatrix3fv(%slocation, 1, GL_FALSE, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_MAT4) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniformMatrix4fv(%slocation, 1, GL_FALSE, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_MAT2x3) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniformMatrix2x3fv(%slocation, 1, GL_FALSE, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_MAT2x4) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniformMatrix2x4fv(%slocation, 1, GL_FALSE, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_MAT3x2) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniformMatrix3x2fv(%slocation, 1, GL_FALSE, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_MAT3x4) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniformMatrix3x4fv(%slocation, 1, GL_FALSE, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_MAT4x2) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniformMatrix4x2fv(%slocation, 1, GL_FALSE, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_FLOAT_MAT4x3) {'
        print '                        _glGetUniformfv(programName, location, fParams); _trace_gl%sUniformMatrix4x3fv(%slocation, 1, GL_FALSE, fParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_MAT2) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniformMatrix2dv(%slocation, 1, GL_FALSE, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_MAT3) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniformMatrix3dv(%slocation, 1, GL_FALSE, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_MAT4) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniformMatrix4dv(%slocation, 1, GL_FALSE, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_MAT2x3) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniformMatrix2x3dv(%slocation, 1, GL_FALSE, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_MAT2x4) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniformMatrix2x4dv(%slocation, 1, GL_FALSE, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_MAT3x2) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniformMatrix3x2dv(%slocation, 1, GL_FALSE, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_MAT3x4) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniformMatrix3x4dv(%slocation, 1, GL_FALSE, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_MAT4x2) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniformMatrix4x2dv(%slocation, 1, GL_FALSE, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else if (uniformType == GL_DOUBLE_MAT4x3) {'
        print '                        _glGetUniformdv(programName, location, dParams); _trace_gl%sUniformMatrix4x3dv(%slocation, 1, GL_FALSE, dParams, false);' % (funcPrefix, firstParam)
        print '                    } else {'
        print '                        switch (uniformType) {'
        print '                            case GL_SAMPLER_1D: case GL_SAMPLER_2D: case GL_SAMPLER_3D: case GL_SAMPLER_CUBE: case GL_SAMPLER_1D_SHADOW: case GL_SAMPLER_2D_SHADOW: case GL_SAMPLER_2D_MULTISAMPLE: case GL_SAMPLER_CUBE_SHADOW: case GL_SAMPLER_BUFFER: case GL_SAMPLER_2D_RECT: case GL_SAMPLER_2D_RECT_SHADOW:'
        print '                            case GL_INT_SAMPLER_1D: case GL_INT_SAMPLER_2D: case GL_INT_SAMPLER_3D: case GL_INT_SAMPLER_CUBE: case GL_INT_SAMPLER_2D_MULTISAMPLE: case GL_INT_SAMPLER_BUFFER: case GL_INT_SAMPLER_2D_RECT:'
        print '                            case GL_UNSIGNED_INT_SAMPLER_1D: case GL_UNSIGNED_INT_SAMPLER_2D: case GL_UNSIGNED_INT_SAMPLER_3D: case GL_UNSIGNED_INT_SAMPLER_CUBE: case GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE: case GL_UNSIGNED_INT_SAMPLER_BUFFER: case GL_UNSIGNED_INT_SAMPLER_2D_RECT:'
        print '                            case GL_SAMPLER_1D_ARRAY: case GL_SAMPLER_2D_ARRAY: case GL_SAMPLER_1D_ARRAY_SHADOW: case GL_SAMPLER_2D_ARRAY_SHADOW: case GL_SAMPLER_2D_MULTISAMPLE_ARRAY:'
        print '                            case GL_INT_SAMPLER_1D_ARRAY: case GL_INT_SAMPLER_2D_ARRAY: case GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY:'
        print '                            case GL_UNSIGNED_INT_SAMPLER_1D_ARRAY: case GL_UNSIGNED_INT_SAMPLER_2D_ARRAY: case GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY:'
        print '                                { _glGetUniformiv(programName, location, iParams); _trace_gl%sUniform1iv(%slocation, 1, iParams, false); }' % (funcPrefix, firstParam)
        print '                        }'
        print '                    }'
        print '                }'
        print '            }'

    def generateFile(self):
        print '#include <assert.h>'
        print '#include <string.h>'
        print
        print '#include "scoped_allocator.hpp"'
        print '#include "glproc.hpp"'
        print '#include "glsize.hpp"'

        print '#ifdef WIN32'
        print '#include "../../retrace/glstate.hpp"'
        print '#include "../../retrace/glstate_internal.hpp"'
        print '#include "wgltrace_tracefuncs.h"'
        print '#endif'
        print '#ifdef __linux'
        print '#include "../retrace/glstate.hpp"'
        print '#include "../retrace/glstate_internal.hpp"'
        print '#include "glxtrace_tracefuncs.h"'
        print '#endif'
        print '#ifdef __APPLE__'
        print '#include "../retrace/glstate.hpp"'
        print '#include "../retrace/glstate_internal.hpp"'
        print '#include "cgltrace_tracefuncs.h"'
        print '#endif'
        print '#include "gltrace.hpp"'
        print
        print 'namespace glstate {'
        print

        print 'static void'
        print 'snapshotFramebufferAttachmentParameters(GLenum target, GLenum attachment)'
        print '{'
        self.snapshot_attachment_parameters('target', 'attachment')
        print '}'
        print

        print 'void snapshotParameters(/*Context &context*/)'
        print '{'
        print '    ScopedAllocator _allocator;'
        print '    (void)_allocator;'
        print

        self.dump_atoms(glGet, '    ')

        self.snapshot_material_params()
        self.snapshot_light_params()
        self.snapshot_samplers()
        self.snapshot_buffers()
        self.snapshot_vertex_attribs()
        self.snapshot_program_params()
        self.snapshot_texture_parameters()
        self.snapshot_renderbuffer_parameters()
        self.snapshot_framebuffer_parameters()

        print '}'
        print
        
        print '} /*namespace glstate */'

    def snapshot_material_params(self):
        print '// MATERIALS (Deprecated as of GL 3.3)'
        print '#if 0'
        print '//    if (!context.ES) {'
        for face in ['GL_FRONT', 'GL_BACK']:
            print '        {'
            print '        GLenum face = %s;' % face
            getter = glGetMaterial
            for _, numValues, name in getter.iter():
                args = (face, name)
                if name not in state_that_cannot_replay and name not in state_deprecated_before_gl33:
                    type, value = getter(*args)
                    funcName = "glMaterialf"
                    if (numValues > 1):
                        funcName = "glMaterialfv"
                    print '            _trace_%s(face, %s, %s, false);' % (funcName, name, getter.temp_name(args))
            print '        }'
        print '//    }'
        print '#endif'
        print

    def snapshot_light_params(self):
        print '// LIGHTS (Deprecated as of GL 3.3)'
        print '#if 0'
        print '    GLint max_lights = 0;'
        print '    _glGetIntegerv(GL_MAX_LIGHTS, &max_lights);'
        print '    for (GLint index = 0; index < max_lights; ++index) {'
        print '        GLenum light = GL_LIGHT0 + index;'
        print '        if (_glIsEnabled(light)) {'
        getter = glGetLight
        for _, numValues, name in getter.iter():
            args = ('GL_LIGHT0 + index', name)
            if name not in state_that_cannot_replay and name not in state_deprecated_before_gl33:
                type, value = getter(*args)
                funcName = "glLightf"
                if (numValues > 1):
                    funcName = "glLightfv"
                print '            _trace_%s(GL_LIGHT0 + index, %s, %s, false);' % (funcName, name, getter.temp_name(args))
        print '        }'
        print '    }'
        print '#endif'
        print

    def texenv_param_target(self, name):
        if name == 'GL_TEXTURE_LOD_BIAS':
           return 'GL_TEXTURE_FILTER_CONTROL'
        elif name == 'GL_COORD_REPLACE':
           return 'GL_POINT_SPRITE'
        else:
           return 'GL_TEXTURE_ENV'

    def snapshot_texenv_params(self):
        print '// TEX ENV'
        print
        for target in ['GL_TEXTURE_ENV', 'GL_TEXTURE_FILTER_CONTROL', 'GL_POINT_SPRITE']:
            print '//    if (!context.ES) {'
            for _, _, name in glGetTexEnv.iter():
                if self.texenv_param_target(name) == target:
                    self.dump_atom(glGetTexEnv, '        ', target, name) 
            print '//    }'

    def snapshot_samplers(self):
        print '    { // SAMPLERS'
        print '        // TODO: instead of iterating over all the created samplers, it would be more efficient'
        print '        // to flag the samplers that have changed and only update those. Or, always trace the '
        print '        // glSamplerParameter* calls to trace what the app calls.'
        print '        gltrace::Context* pContext = gltrace::getContext();'
        print '        for (std::list<GLuint>::iterator iter = pContext->samplers.begin(); iter != pContext->samplers.end(); ++iter) {'
        print '            GLint sampler = *iter;'
        print '            GLint texture_wrap_s = 0;'
        print '            _glGetSamplerParameteriv(sampler, GL_TEXTURE_WRAP_S, &texture_wrap_s);'
        print '            GLint texture_wrap_t = 0;'
        print '            _glGetSamplerParameteriv(sampler, GL_TEXTURE_WRAP_T, &texture_wrap_t);'
        print '            GLint texture_wrap_r = 0;'
        print '            _glGetSamplerParameteriv(sampler, GL_TEXTURE_WRAP_R, &texture_wrap_r);'
        print '            GLint texture_min_filter = 0;'
        print '            _glGetSamplerParameteriv(sampler, GL_TEXTURE_MIN_FILTER, &texture_min_filter);'
        print '            GLint texture_mag_filter = 0;'
        print '            _glGetSamplerParameteriv(sampler, GL_TEXTURE_MAG_FILTER, &texture_mag_filter);'
        print '            GLint texture_min_lod = 0;'
        print '            _glGetSamplerParameteriv(sampler, GL_TEXTURE_MIN_LOD, &texture_min_lod);'
        print '            GLint texture_max_lod = 0;'
        print '            _glGetSamplerParameteriv(sampler, GL_TEXTURE_MAX_LOD, &texture_max_lod);'
        print '            GLint texture_lod_bias = 0;'
        print '            _glGetSamplerParameteriv(sampler, GL_TEXTURE_LOD_BIAS, &texture_lod_bias);'
        print '            GLfloat texture_border_color[4];'
        print '            memset(texture_border_color, 0, sizeof(GLfloat) * 4);'
        print '            _glGetSamplerParameterfv(sampler, GL_TEXTURE_BORDER_COLOR, texture_border_color);'
        print '            GLint texture_compare_mode = 0;'
        print '            _glGetSamplerParameteriv(sampler, GL_TEXTURE_COMPARE_MODE, &texture_compare_mode);'
        print '            GLint texture_compare_func = 0;'
        print '            _glGetSamplerParameteriv(sampler, GL_TEXTURE_COMPARE_FUNC, &texture_compare_func);'
        print '            GLint texture_srgb_decode_ext = 0;'
        print '            _glGetSamplerParameteriv(sampler, GL_TEXTURE_SRGB_DECODE_EXT, &texture_srgb_decode_ext);'
        print
        print '            _trace_glSamplerParameteri(sampler, GL_TEXTURE_WRAP_S, texture_wrap_s, false);'
        print '            _trace_glSamplerParameteri(sampler, GL_TEXTURE_WRAP_T, texture_wrap_t, false);'
        print '            _trace_glSamplerParameteri(sampler, GL_TEXTURE_WRAP_R, texture_wrap_r, false);'
        print '            _trace_glSamplerParameteri(sampler, GL_TEXTURE_MIN_FILTER, texture_min_filter, false);'
        print '            _trace_glSamplerParameteri(sampler, GL_TEXTURE_MAG_FILTER, texture_mag_filter, false);'
        print '            _trace_glSamplerParameteri(sampler, GL_TEXTURE_MIN_LOD, texture_min_lod, false);'
        print '            _trace_glSamplerParameteri(sampler, GL_TEXTURE_MAX_LOD, texture_max_lod, false);'
        print '            _trace_glSamplerParameteri(sampler, GL_TEXTURE_LOD_BIAS, texture_lod_bias, false);'
        print '            _trace_glSamplerParameterfv(sampler, GL_TEXTURE_BORDER_COLOR, texture_border_color, false);'
        print '            _trace_glSamplerParameteri(sampler, GL_TEXTURE_COMPARE_MODE, texture_compare_mode, false);'
        print '            _trace_glSamplerParameteri(sampler, GL_TEXTURE_COMPARE_FUNC, texture_compare_func, false);'
        print '            _trace_glSamplerParameteri(sampler, GL_TEXTURE_SRGB_DECODE_EXT, texture_srgb_decode_ext, false);'
        print '        }'
        print
        print '        // bind samplers to the appropriate texture units'
        glGet("GL_ACTIVE_TEXTURE")
        glGet("GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS")
        print '        for (GLint unit = 0; unit < max_combined_texture_image_units; ++unit) {'
        print '            _glActiveTexture(GL_TEXTURE0 + unit);'
        print '            GLint sampler_binding = 0;'
        print '            _glGetIntegerv(GL_SAMPLER_BINDING, &sampler_binding);'
        print '            if (sampler_binding != 0) {'
        print '                _trace_glBindSampler(unit, sampler_binding, false);'
        print '            }'
        print '        }'
        print
        print '        _glActiveTexture(active_texture);'
        print '    } // end SAMPLERS'


    def snapshot_buffers(self):
        print '    { // BUFFERS'
        print '        // capture current active buffers'
        for target, binding in buffer_targets:
            glGet(binding)
        print
        print '        // recreate all buffer objects'
        print '        gltrace::Context* pContext = gltrace::getContext();'
        print '        for (std::list<GLuint>::iterator iter = pContext->bufferObjects.begin(); iter != pContext->bufferObjects.end(); ++iter) {'
        print '             _trace_glBindBuffer(GL_ARRAY_BUFFER, *iter, true);'
        print '              GLint64 buffer_size = 0;'
        print '             _glGetBufferParameteri64v(GL_ARRAY_BUFFER, GL_BUFFER_SIZE, &buffer_size);'
        print '              GLint buffer_usage = 0;'
        print '             _glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_USAGE, &buffer_usage);'
        print '             _glMapBuffer(GL_ARRAY_BUFFER, GL_READ_ONLY);'
        print '              GLint buffer_mapped = 0;'
        print '             _glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_MAPPED, &buffer_mapped);'
        print '              GLvoid *buffer_map_pointer;'
        print '             _glGetBufferPointerv(GL_ARRAY_BUFFER, GL_BUFFER_MAP_POINTER, &buffer_map_pointer);'
        print '             _glUnmapBuffer(GL_ARRAY_BUFFER);'
        print '             _trace_glBufferData(GL_ARRAY_BUFFER, buffer_size, buffer_map_pointer, buffer_usage, false);'
        print '        }'
        print
        print '        // rebind the previously active buffers'
        for target, binding in buffer_targets:
            print '        _trace_glBindBuffer(%s, %s, true);' % (target, binding[3:].lower())
        print ''
        print '    } // end BUFFERS'
        print

    def snapshot_vertex_attribs(self):
        print '    { // VERTEX ARRAYS'
        print '        GLint vertex_array_binding = 0;'
        print '        _glGetIntegerv(GL_VERTEX_ARRAY_BINDING, &vertex_array_binding);'
        print '        GLint array_buffer = 0;'
        print '        _glGetIntegerv(GL_ARRAY_BUFFER, &array_buffer);'
        print '        GLint max_vertex_attribs = 0;'
        print '        _glGetIntegerv(GL_MAX_VERTEX_ATTRIBS, &max_vertex_attribs);'
        print '        gltrace::Context* pContext = gltrace::getContext();'
        print '        for (std::list<GLuint>::iterator iter = pContext->vertexArrays.begin(); iter != pContext->vertexArrays.end(); ++iter) {'
        print '            _trace_glBindVertexArray(*iter, true);'
        print '            for (GLint index = 0; index < max_vertex_attribs; ++index) {'

        print '                // TODO: this could cause undefined behavior since we currently dont know'
        print '                // what format the data was originally specified in, but we are reading it back as a double.'
        print '                // We might have to track this state from the beginning of the trace.'
        glGetVertexAttrib('index', "GL_CURRENT_VERTEX_ATTRIB")
        print '                _trace_glVertexAttrib4dv(index, current_vertex_attrib, false);'
        print
        glGetVertexAttrib('index', "GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING")
        print '                _trace_glBindBuffer(GL_ARRAY_BUFFER, vertex_attrib_array_buffer_binding, false);'
        print
        glGetVertexAttrib('index', "GL_VERTEX_ATTRIB_ARRAY_DIVISOR")
        print '                _trace_glVertexAttribDivisor(index, vertex_attrib_array_divisor, false);'
        print
        print '                if (vertex_attrib_array_buffer_binding != 0) {'
        glGetVertexAttrib('index', "GL_VERTEX_ATTRIB_ARRAY_SIZE")
        glGetVertexAttrib('index', "GL_VERTEX_ATTRIB_ARRAY_STRIDE")
        glGetVertexAttrib('index', "GL_VERTEX_ATTRIB_ARRAY_TYPE")
        glGetVertexAttrib('index', "GL_VERTEX_ATTRIB_ARRAY_INTEGER")
        glGetVertexAttrib('index', "GL_VERTEX_ATTRIB_ARRAY_POINTER")
        print '                    if (vertex_attrib_array_integer == GL_TRUE) {'
        print '                        _trace_glVertexAttribIPointer(index, vertex_attrib_array_size, vertex_attrib_array_type, vertex_attrib_array_stride, vertex_attrib_array_pointer, false);'
        print '                    } else {'
        glGetVertexAttrib('index', "GL_VERTEX_ATTRIB_ARRAY_NORMALIZED")
        print '                        _trace_glVertexAttribPointer(index, vertex_attrib_array_size, vertex_attrib_array_type, vertex_attrib_array_normalized, vertex_attrib_array_stride, vertex_attrib_array_pointer, false);'
        print '                    }'
        print '                }'
        print
        glGetVertexAttrib('index', "GL_VERTEX_ATTRIB_ARRAY_ENABLED")
        print '                if (vertex_attrib_array_enabled == GL_TRUE) {'
        print '                    _trace_glEnableVertexAttribArray(index, false);'
        print '                } else {'
        print '                    _trace_glDisableVertexAttribArray(index, false);'
        print '                }'
        print '            }'
        print '        }'
        print '        _trace_glBindBuffer(GL_ARRAY_BUFFER, array_buffer, true);'
        print '        _trace_glBindVertexArray(vertex_array_binding, true);'
        print '    } // end VERTEX ARRAYS'
        print

    def snapshot_program_params(self):
        print '    { // PROGRAM PIPELINES'
        print '        GLint program_pipeline_binding = 0;'
        print '        _glGetIntegerv(GL_PROGRAM_PIPELINE_BINDING, &program_pipeline_binding);'
        print

        print '        // recreate all the shader programs'
        print '        gltrace::Context* pContext = gltrace::getContext();'
        print '        for (std::map<GLuint, gltrace::Shader>::iterator shaderIter = pContext->separateShaders.begin(); shaderIter != pContext->separateShaders.end(); ++shaderIter) {'
        print '            GLuint programName = shaderIter->first;'
        print '            gltrace::Shader* pShader = &(shaderIter->second);'
        print '            _trace_glCreateShaderProgramv(pShader->type, pShader->count, pShader->sources, programName, false);'
        self.generateUniformCalls("Program", 'programName, ');
        print '        }'
        print
        print '        GLenum shaderTypes[] = { GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_GEOMETRY_SHADER, GL_TESS_CONTROL_SHADER, GL_TESS_EVALUATION_SHADER };'
        print '        GLenum shaderTypeBits[] = { GL_VERTEX_SHADER_BIT, GL_FRAGMENT_SHADER_BIT, GL_GEOMETRY_SHADER_BIT, GL_TESS_CONTROL_SHADER_BIT, GL_TESS_EVALUATION_SHADER_BIT };'
        print '        GLint shaderNames[] = { 0, 0, 0, 0, 0 };'
        print '        unsigned int count = sizeof(shaderTypes) / sizeof(GLenum);'
        print
        print '        // setup program pipelines with shaders and uniforms'
        print '        for (std::list<GLuint>::iterator pipelineIter = pContext->pipelines.begin(); pipelineIter != pContext->pipelines.end(); ++pipelineIter) {'
        print '            GLuint pipelineName = *pipelineIter;'
        print '            GLint active_program = 0;'
        print '            _glGetProgramPipelineiv(pipelineName, GL_ACTIVE_PROGRAM, &active_program);'
        print
        print '            for (unsigned int i = 0; i < count; ++i ) {'
        print '                _glGetProgramPipelineiv(pipelineName, shaderTypes[i], &shaderNames[i]);'
        print '                if (shaderNames[i] != 0) {'
        print '                    _trace_glUseProgramStages(pipelineName, shaderTypeBits[i], shaderNames[i], false);'
        print '                }'
        print '            }'
        print '            _trace_glActiveShaderProgram(pipelineName, active_program, false);'
        print '        }'
        print
        print '        if (program_pipeline_binding != 0) {'
        print '            _trace_glBindProgramPipeline(program_pipeline_binding, false);'
        print '        }'
        print '    }'
        print
        print '    { // PROGRAMS'
        print '        // get the currently active program before recreating all program uniforms'
        glGet("GL_ACTIVE_PROGRAM")
        print '        gltrace::Context* pContext = gltrace::getContext();'
        print '        for (std::map<GLuint, gltrace::Program>::iterator iter = pContext->programs.begin(); iter != pContext->programs.end(); ++iter) {'
        print '            GLuint programName = iter->first;'
        print '            gltrace::Program* pProgram = &(iter->second);'
        print '            if (pProgram->linked == false) { continue; }'

        print '            // set source, compile, and attach all shaders'
        print '            for (std::map<GLuint, gltrace::Shader>::iterator shaderIter = pProgram->shaders.begin(); shaderIter != pProgram->shaders.end(); ++shaderIter) {'
        print '                GLuint shaderName = shaderIter->first;'
        print '                _trace_glShaderSource(shaderName, 1, shaderIter->second.sources, shaderIter->second.lengths, false);'
        print '                _trace_glCompileShader(shaderName, false);'
        print '                _trace_glAttachShader(programName, shaderName, false);'
        print '            }'
        print '            _trace_glLinkProgram(programName, false);'

        print '            _trace_glUseProgram(programName, true);'

        self.generateUniformCalls("", "");

        print '        }'
        print
        print '        if (pContext->programs.size() > 0) {'
        print '            // restore previously active program;'
        print '            _trace_glUseProgram(active_program, true);'
        print '        }'
        print '    } // end PROGRAMS'
        print


    def snapshot_texture_parameters(self):
        print '    // TEXTURES'
        print '    {'
        print '        gltrace::Context* pContext = gltrace::getContext();'
        print '        // get the current active texture unit'
        print '        GLint active_texture = 0;'
        print '        _glGetIntegerv(GL_ACTIVE_TEXTURE, &active_texture);'
        print 
        print '        // capture all current bindings'
        print '        GLint max_combined_texture_image_units = 0;'
        print '        _glGetIntegerv(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS, &max_combined_texture_image_units);'
        print '        size_t texBindingSize = sizeof(GLint) * max_combined_texture_image_units;'
        print '        size_t texEnabledSize = sizeof(GLboolean) * max_combined_texture_image_units;'
        print '        GLint* pBindings1D = (GLint*)malloc(texBindingSize);'
        print '        GLint* pBindings2D = (GLint*)malloc(texBindingSize);'
        print '        GLint* pBindings3D = (GLint*)malloc(texBindingSize);'
        print '        GLint* pBindingsRect = (GLint*)malloc(texBindingSize);'
        print '        GLint* pBindingsCubeMap = (GLint*)malloc(texBindingSize);'
        print '        memset(pBindings1D, 0, texBindingSize);'
        print '        memset(pBindings2D, 0, texBindingSize);'
        print '        memset(pBindings3D, 0, texBindingSize);'
        print '        memset(pBindingsRect, 0, texBindingSize);'
        print '        memset(pBindingsCubeMap, 0, texBindingSize);'
        print '        GLboolean* pEnabled1D = (GLboolean*)malloc(texEnabledSize);'
        print '        GLboolean* pEnabled2D = (GLboolean*)malloc(texEnabledSize);'
        print '        GLboolean* pEnabled3D = (GLboolean*)malloc(texEnabledSize);'
        print '        GLboolean* pEnabledRect = (GLboolean*)malloc(texEnabledSize);'
        print '        GLboolean* pEnabledCubeMap = (GLboolean*)malloc(texEnabledSize);'
        print '        memset(pEnabled1D, GL_FALSE, texEnabledSize);'
        print '        memset(pEnabled2D, GL_FALSE, texEnabledSize);'
        print '        memset(pEnabled3D, GL_FALSE, texEnabledSize);'
        print '        memset(pEnabledRect, GL_FALSE, texEnabledSize);'
        print '        memset(pEnabledCubeMap, GL_FALSE, texEnabledSize);'
        print
        print '        for (GLint unit = 0; unit < max_combined_texture_image_units; ++unit) {'
        print '            _glActiveTexture(GL_TEXTURE0 + unit);'
        print '            GLenum target;'
        print
        for target, binding in texture_targets:
            bindingArray = 'NONE';
            enabledArray = 'NONE';
            if target == 'GL_TEXTURE_1D':
                bindingArray = 'pBindings1D'
                enabledArray = 'pEnabled1D'
            elif target == 'GL_TEXTURE_2D':
                bindingArray = 'pBindings2D'
                enabledArray = 'pEnabled2D'
            elif target == 'GL_TEXTURE_3D':
                bindingArray = 'pBindings3D'
                enabledArray = 'pEnabled3D'
            elif target == 'GL_TEXTURE_RECTANGLE':
                bindingArray = 'pBindingsRect'
                enabledArray = 'pEnabledRect'
            elif target == 'GL_TEXTURE_CUBE_MAP':
                bindingArray = 'pBindingsCubeMap'
                enabledArray = 'pEnabledCubeMap'
            print '            target = %s;' % target
            print '            _glGetBooleanv(%s, &(%s[unit]));' % (target, enabledArray)
            print '            _glGetIntegerv(%s, &(%s[unit]));' % (binding, bindingArray)
            print
        print '        }'

        print '        // switch to tex unit 0 to recreate all the textures'
        print '        _trace_glActiveTexture(GL_TEXTURE0, true);'

        print '        // recreate all the textures that previously existed'
        print '        for (std::map<GLuint, gltrace::Texture>::iterator iter = pContext->textures.begin(); iter != pContext->textures.end(); ++iter) {'
        print '            GLuint texName = iter->first;'
        print '            gltrace::Texture& texture = iter->second;'

        print '            GLenum target = texture.m_target;'
        print '            // emit a call to bind the texture'
        print '            _trace_glBindTexture(target, texName, true);'
        print '            // get & set all the state'
        self.dump_atoms(glGetTexParameter, '            ', 'target')
        self.snapshot_tex_level_parameters('            ', 'target')
        print '        }'
        print
        print '        // emit calls into the trace to set the proper bindings'
        print '        for (GLint unit = 0; unit < max_combined_texture_image_units; ++unit) {'
        print '            _trace_glActiveTexture(GL_TEXTURE0 + unit, false);'
        for target, binding in texture_targets:
            bindingArray = 'NONE';
            enabledArray = 'NONE';
            if target == 'GL_TEXTURE_1D':
                bindingArray = 'pBindings1D'
                enabledArray = 'pEnabled1D'
            elif target == 'GL_TEXTURE_2D':
                bindingArray = 'pBindings2D'
                enabledArray = 'pEnabled2D'
            elif target == 'GL_TEXTURE_3D':
                bindingArray = 'pBindings3D'
                enabledArray = 'pEnabled3D'
            elif target == 'GL_TEXTURE_RECTANGLE':
                bindingArray = 'pBindingsRect'
                enabledArray = 'pEnabledRect'
            elif target == 'GL_TEXTURE_CUBE_MAP':
                bindingArray = 'pBindingsCubeMap'
                enabledArray = 'pEnabledCubeMap'
            print '            if ( %s[unit] ) {' % enabledArray
            print '                _trace_glEnable(%s, false);' % target
            print '            } else {'
            print '                _trace_glDisable(%s, false);' % target
            print '            }'
            print '            _trace_glBindTexture(%s, %s[unit], true);' % (target, bindingArray)
            print
        print '        }'
        print

        print '        // switch back to the previously active texture unit'
        print '        _glActiveTexture(active_texture);'

        print '        free(pBindings1D); pBindings1D = NULL;'
        print '        free(pBindings2D); pBindings2D = NULL;'
        print '        free(pBindings3D); pBindings3D = NULL;'
        print '        free(pBindingsRect); pBindingsRect = NULL;'
        print '        free(pBindingsCubeMap); pBindingsCubeMap = NULL;'
        print
        print '        free(pEnabled1D); pEnabled1D = NULL;'
        print '        free(pEnabled2D); pEnabled1D = NULL;'
        print '        free(pEnabled3D); pEnabled1D = NULL;'
        print '        free(pEnabledRect); pEnabledRect = NULL;'
        print '        free(pEnabledCubeMap); pEnabled1D = NULL;'
        print
        print '    }'
        print

    ## assumes a gltrace::Texture named texture, and a GLenum named target
    def snapshot_tex_level_parameters(self, indentation, target):
        # get all state from level 0, then trace an upload of all levels
        print '%s{ // upload levels' % indentation
        print '%sGLint texture_format = texture.m_format;' % indentation
        print '%sGLint texture_type = texture.m_type;' % indentation
        print '%sGLvoid* texture_data = NULL;' % indentation

        print '%s// TODO: Pixel Pack buffer and pack alignment could affect this' % indentation
        print '%sfor ( std::list<gltrace::TextureLevel>::iterator levelIter = texture.m_levels.begin(); levelIter != texture.m_levels.end(); ++levelIter) {' % indentation
        print '%s    GLuint texLevel = levelIter->m_level;' % indentation
        print '%s    GLsizei texture_image_size = levelIter->m_imageSize;' % indentation
        print '%s    GLint texture_width = levelIter->m_width;' % indentation
        print '%s    GLint texture_height = levelIter->m_height;' % indentation
        print '%s    GLint texture_depth = levelIter->m_depth;' % indentation
        print '%s    GLenum texture_target = levelIter->m_target;' % indentation
        print '%s    texture_data = malloc(texture_image_size);' % indentation
        print '%s    if ( target == GL_TEXTURE_CUBE_MAP ) {' % indentation
        glGetTexLevelParameter("texture_target", "texLevel", "GL_TEXTURE_INTERNAL_FORMAT")
        glGetTexLevelParameter("texture_target", "texLevel", "GL_TEXTURE_COMPRESSED")
        glGetTexLevelParameter("texture_target", "texLevel", "GL_TEXTURE_BORDER")
        print '%s        if ( texture_compressed ) {' % indentation
        print '%s            _glGetCompressedTexImage(texture_target, texLevel, texture_data);' % (indentation,)
        print '%s        } else {' % indentation
        print '%s            _glGetTexImage(texture_target, texLevel, texture_format, texture_type, texture_data);' % (indentation,)
        print '%s        }' % indentation
        print
        print '%s        if ( texture_compressed ) {' % indentation
        print '%s            _trace_glCompressedTexImage2D(texture_target, texLevel, texture_internal_format, texture_width, texture_height, texture_border, texture_image_size, texture_data, false);' % (indentation,)
        print '%s        } else {' % indentation
        print '%s            _trace_glTexImage2D(texture_target, texLevel, texture_internal_format, texture_width, texture_height, texture_border, texture_format, texture_type, texture_data, false);' % (indentation,)
        print '%s        }' % indentation
        print '%s    } else {' % indentation
        glGetTexLevelParameter("target", "texLevel", "GL_TEXTURE_INTERNAL_FORMAT")
        glGetTexLevelParameter("target", "texLevel", "GL_TEXTURE_COMPRESSED")
        glGetTexLevelParameter("target", "texLevel", "GL_TEXTURE_BORDER")
        print '%s        if ( texture_compressed ) {' % indentation
        print '%s            _glGetCompressedTexImage(target, texLevel, texture_data);' % indentation
        print '%s        } else {' % indentation
        print '%s            _glGetTexImage(target, texLevel, texture_format, texture_type, texture_data);' % indentation
        print '%s        }' % indentation
        print '%s        // Now emit a call to recreate the texture' % indentation
        print '%s        if (target == GL_TEXTURE_1D) {' % indentation
        print '%s            if ( texture_compressed ) {' % indentation
        print '%s                _trace_glCompressedTexImage1D(GL_TEXTURE_1D, texLevel, texture_internal_format, texture_width, texture_border, texture_image_size, texture_data, false);' % indentation
        print '%s            } else {' % indentation
        print '%s                _trace_glTexImage1D(GL_TEXTURE_1D, texLevel, texture_internal_format, texture_width, texture_border, texture_format, texture_type, texture_data, false);' % indentation
        print '%s            }' % indentation
        print '%s        } else if (target == GL_TEXTURE_2D || target == GL_TEXTURE_RECTANGLE ) {' % indentation
        print '%s            if ( texture_compressed ) {' % indentation
        print '%s                _trace_glCompressedTexImage2D(GL_TEXTURE_2D, texLevel, texture_internal_format, texture_width, texture_height, texture_border, texture_image_size, texture_data, false);' % indentation
        print '%s            } else {' % indentation
        print '%s                _trace_glTexImage2D(GL_TEXTURE_2D, texLevel, texture_internal_format, texture_width, texture_height, texture_border, texture_format, texture_type, texture_data, false);' % indentation
        print '%s            }' % indentation
        print '%s        } else if (target == GL_TEXTURE_3D ) {' % indentation
        print '%s            if ( texture_compressed ) {' % indentation
        print '%s                _trace_glCompressedTexImage3D(GL_TEXTURE_3D, texLevel, texture_internal_format, texture_width, texture_height, texture_depth, texture_border, texture_image_size, texture_data, false);' % indentation
        print '%s            } else {' % indentation
        print '%s                _trace_glTexImage3D(GL_TEXTURE_3D, texLevel, texture_internal_format, texture_width, texture_height, texture_depth, texture_border, texture_format, texture_type, texture_data, false);' % indentation
        print '%s            }' % indentation
        print '%s        }' % indentation
        print '%s    }' % indentation

        print '%s    free(texture_data);' % indentation
        print '%s    texture_data = NULL;' % indentation
        print '%s}' % indentation
        print '%s}' % indentation

    def snapshot_renderbuffer_parameters(self):
        print '    // RENDERBUFFERS'
        print '    {'
        print '        gltrace::Context* pContext = gltrace::getContext();'
        print '        // get the current active renderbuffer'
        print '        GLint renderbuffer_binding = 0;'
        print '        _glGetIntegerv(GL_RENDERBUFFER_BINDING, &renderbuffer_binding);'
        print 
        print '        // recreate all the renderbuffers'
        print '        for (std::list<GLuint>::iterator iter = pContext->renderbuffers.begin(); iter != pContext->renderbuffers.end(); ++iter) {'
        print '            _trace_glBindRenderbuffer(GL_RENDERBUFFER, *iter, true);'
        glGetRenderbufferParameter("GL_RENDERBUFFER", "GL_RENDERBUFFER_SAMPLES")
        glGetRenderbufferParameter("GL_RENDERBUFFER", "GL_RENDERBUFFER_INTERNAL_FORMAT")
        glGetRenderbufferParameter("GL_RENDERBUFFER", "GL_RENDERBUFFER_WIDTH")
        glGetRenderbufferParameter("GL_RENDERBUFFER", "GL_RENDERBUFFER_HEIGHT")
        print '            _trace_glRenderbufferStorageMultisample(GL_RENDERBUFFER, renderbuffer_samples, renderbuffer_internal_format, renderbuffer_width, renderbuffer_height, false);'

        print '            // TODO: Need to read from existing renderbuffers and write that data into the new Renderbuffers (to recreate their contents)'
        print '            // This may or may not be required depending on how the renderbuffer is being used. If its drawn to and used every frame, then'
        print '            // there is no need to restore its contents, but if it is rendered in one frame and used in subsequent frames, then restoring them is important.'

        print '        }'
        print
        print '        // switch back to the previously active renderbuffer'
        print '        _glBindRenderbuffer(GL_RENDERBUFFER, renderbuffer_binding);'
        print '    }'
        print

    def snapshot_framebuffer_parameters(self):
        print '    { // FRAMEBUFFERS'
        print '        // backup current bindings'
        print '        GLint draw_framebuffer_binding = 0;'
        print '        _glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &draw_framebuffer_binding);'
        print '        GLint read_framebuffer_binding = 0;'
        print '        _glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &read_framebuffer_binding);'
        print
        print '        GLint max_draw_buffers = 0;'
        print '        _glGetIntegerv(GL_MAX_DRAW_BUFFERS, &max_draw_buffers);'
        print '        for (GLint i = 0; i < max_draw_buffers; ++i) {';
        print '            GLboolean color_writemask[4];'
        print '            _glGetBooleanIndexedvEXT(GL_COLOR_WRITEMASK, i, color_writemask);'
        print '            _trace_glColorMaskIndexedEXT(i, color_writemask[0], color_writemask[1], color_writemask[2], color_writemask[3], false);'
        print '        }'
        print
        print '        GLint max_color_attachments = 0;'
        print '        _glGetIntegerv(GL_MAX_COLOR_ATTACHMENTS, &max_color_attachments);'
        print
        print '        gltrace::Context *ctx = gltrace::getContext();'
        for target in ('GL_DRAW_FRAMEBUFFER', 'GL_READ_FRAMEBUFFER'):
            print '        // %s' % target
            print '        for (std::list<GLuint>::iterator iter = ctx->framebuffers.begin(); iter != ctx->framebuffers.end(); ++iter) {'
            print '            _trace_glBindFramebuffer(%s, *iter, true);' % target
            print '            for (GLint i = 0; i < max_color_attachments; ++i) {'
            print '                GLint color_attachment = GL_COLOR_ATTACHMENT0 + i;'
            print '                snapshotFramebufferAttachmentParameters(%s, color_attachment);' % target
            print '            }'
            print '            snapshotFramebufferAttachmentParameters(%s, GL_DEPTH_ATTACHMENT);' % target
            print '            snapshotFramebufferAttachmentParameters(%s, GL_STENCIL_ATTACHMENT);' % target
            print '        }'
        print '        _trace_glBindFramebuffer(GL_DRAW_FRAMEBUFFER, draw_framebuffer_binding, true);'
        print '        _trace_glBindFramebuffer(GL_READ_FRAMEBUFFER, read_framebuffer_binding, true);'
        print '    } // end FRAMEBUFFERS'
        print

    def snapshot_attachment_parameters(self, target, attachment):
        print '    {'
        print '        GLint object_type = GL_NONE;'
        print '        _glGetFramebufferAttachmentParameteriv(%s, %s, GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE, &object_type);' % (target, attachment)
        print '        if (object_type == GL_TEXTURE) {'
        glGetFramebufferAttachmentParameter(target, attachment, "GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME")
        print '            if (framebuffer_attachment_object_name != 0) {'
        glGetFramebufferAttachmentParameter(target, attachment, "GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LEVEL")
        print '                GLenum texTarget = GL_NONE;'
        print '                gltrace::Context *ctx = gltrace::getContext();'
        print '                texTarget = ctx->textures[framebuffer_attachment_object_name].m_target;'
        print '                if (texTarget == GL_TEXTURE_1D) {'
        print '                    _trace_glFramebufferTexture1D(%s, %s, texTarget, framebuffer_attachment_object_name, framebuffer_attachment_texture_level, false);' % (target, attachment)
        print '                } else if (texTarget == GL_TEXTURE_2D) {'
        print '                    _trace_glFramebufferTexture2D(%s, %s, texTarget, framebuffer_attachment_object_name, framebuffer_attachment_texture_level, false);' % (target, attachment)
        print '                } else if (texTarget == GL_TEXTURE_3D) {'
        glGetFramebufferAttachmentParameter(target, attachment, "GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LAYER")
        print '                    _trace_glFramebufferTexture3D(%s, %s, texTarget, framebuffer_attachment_object_name, framebuffer_attachment_texture_level, framebuffer_attachment_texture_layer, false);' % (target, attachment)
        print '                } else if (texTarget == GL_TEXTURE_CUBE_MAP) {'
        glGetFramebufferAttachmentParameter(target, attachment, "GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_CUBE_MAP_FACE")
        print '                    _trace_glFramebufferTexture2D(%s, %s, framebuffer_attachment_texture_cube_map_face, framebuffer_attachment_object_name, framebuffer_attachment_texture_level, false);' % (target, attachment)
        print '                }'
        print '            }'
        print '        } else if (object_type == GL_RENDERBUFFER) {'
        glGetFramebufferAttachmentParameter(target, attachment, "GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME")
        print '            if (framebuffer_attachment_object_name != 0) {'
        print '                _trace_glFramebufferRenderbuffer(%s, %s, GL_RENDERBUFFER, framebuffer_attachment_object_name, false);' % (target, attachment)
        print '            }'
        print '        }'
        print '    }'
        print

    def dump_atoms(self, getter, indentation, *args):
        for _, _, name in getter.iter():
            if name not in state_that_cannot_replay and name not in state_deprecated_before_gl33:
                self.dump_atom(getter, indentation, *(args + (name,)))
                
    def dump_atom(self, getter, indentation, *args):
        name = args[-1]

        # Avoid crash on MacOSX
        # XXX: The right fix would be to look at the support extensions..
        import platform
        if name == 'GL_SAMPLER_BINDING' and platform.system() == 'Darwin':
            return

        # only output state that we have a setter for
        stateNames = ''
        for names, _ in state_setters:
            if name in names.split(','):
                if (name == names.split(',')[0]):
                    stateNames = names
                    break
                else:
                    ## this state will be handled by a different one
                    #print '// handled somewhere else: %s' % name
                    #print
                    return;
        if stateNames == '':
            for stateName in state_enable_disable:
                if stateName == name:
                    stateNames = name
                    break
        if stateNames == '':
            if name in state_deprecated_before_gl33:
                #print '// deprecated: %s' % name
                pass
            else:
                #print '// unhandled state: %s' % name
                pass
            #print
            return

        print '%s// %s' % (indentation, stateNames)
        print '%s{' % indentation
        #print '%s    assert(_glGetError() == GL_NO_ERROR);' % indentation

        if stateNames in state_enable_disable:
            type, value = getter(*args)
        else:
            for stateName in stateNames.split(','):
                type, value = getter(*(args[:-1] + (stateName,)))

        print '%s    if (_glGetError() != GL_NO_ERROR) {' % indentation
        #print '%s       std::cerr << "warning: %s(%s) failed\\n";' % (indentation, inflection, name)
        print '%s        while (_glGetError() != GL_NO_ERROR) {}' % indentation
        print '%s    } else {' % indentation

        getter.emitSetter(*args)

        print '%s    }' % indentation
        print '%s}' % indentation
        print

if __name__ == '__main__':
    StateSnapshot().generateFile()
