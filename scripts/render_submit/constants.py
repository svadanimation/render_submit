'''
Constants for the render submitter
'''
import os
import maya.cmds as mc # pylint: disable=import-error

RELEASE = mc.about(version=True)
VRAY_VERSION = 'vray/6'

# Note! the osx versions of this are in the vray/bin/vray.sh file
CONVERT_PATH = f'__VRAYBIN{RELEASE}__'

BASE = os.path.normpath('//svad-kahlo/common/Animation/Pipeline/')
SVAD = f'SVAD_{RELEASE}'
BASE_PIPE = os.path.normpath(os.path.join(BASE, SVAD)).replace("\\","/")
VRAY_PATH = os.path.normpath(os.path.join(BASE_PIPE, VRAY_VERSION, '/maya_vray/bin')).replace("\\","/")
VRAY_PLUGINS = os.path.normpath(os.path.join(BASE_PIPE, VRAY_VERSION, 'maya_vray/vrayplugins')).replace("\\","/")
VRAY_OSL_PATH = os.path.normpath(os.path.join(BASE_PIPE, VRAY_VERSION, 'vray/opensl')).replace("\\","/")
VRAY_PLUGIN_LOAD = ['vrayformaya', 'vrayvolumegrid', 'xgenVRay']
OCIO = os.path.normpath(os.path.join(BASE_PIPE, 'OCIO-configs/Maya2022-default', 'config.ocio')).replace("\\","/")

NETWORK_SUFFIX = '.svad.southern.edu'
OMIT_DRIVES = ('C:', 'D:', 'E:', 'F:')

TIMEOUT = '15000' # seconds
CPUS = '50'
PRIORITY = '4000'
MIN_FILE_SIZE = '5000' # bytes


ASPECT_RATIO = 1.7777777777777777

# Needs to be a 12 bit srgb lut. It is tricky getting the correct export from nuke.
# 3dl tables are assumed to have 12 bits of output (range 0...4095)
# are assumed to contain sRGB values by default
LUT = os.path.normpath(os.path.join(BASE_PIPE, VRAY_VERSION, 'look.3dl')).replace("\\","/")

# Used to pass a .json dictionary submission
QUBE  = r'"C:\\Program Files (x86)\\pfx\\qube\bin\\qube.exe"'

# this needs to be installed on every farm machine, right now, only on windows, no mac trashcans.
PDPLAYER = r'"C:\\Program Files\\Pdplayer 64\\pdplayer64.exe"'
