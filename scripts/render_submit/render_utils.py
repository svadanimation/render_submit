'''
A collection of utility functions for render submission
'''
import platform
import os
import re
import subprocess
from pprint import pprint
import maya.cmds as mc # pylint: disable=import-error

def get_renderable_camera():
    '''Get a list of renderable cameras

    :return: list of camera names
    :rtype: list of str
    '''
    cameras = mc.listCameras(p=True)
    render_cam =  []
    for camera in cameras:
        if mc.getAttr(camera +'.renderable'):
            render_cam.append(camera)
    if len(render_cam) > 1:
        mc.warning(f'More than one render camera. Using {render_cam[0]}' )
    elif len(render_cam) <= 0:
        render_cam.append('perspShape')
        mc.warning(f'No rendearble cameras found. Using {render_cam[0]}' )
    return render_cam

def display_message(message, duration=10, color=(1,1,1)):
    """
    Displays a message in the Maya viewport using inViewMessage.

    Args:
        message (str): The message to display.
        duration (int): The duration in seconds that the message will be displayed for. Defaults to 5.
        color (tuple): The RGB color of the message. Values should be between 0 and 1. Defaults to (1,1,1).
    """
    mc.inViewMessage(message=message,
                     pos='midCenter',
                     fade=True,
                     alpha=0.7,
                     bkc=color,
                     fgc=(0,0,0),
                     fadeStayTime=duration,
                     fadeOutTime=0.5,
                     ck=True)

def build_directory(filepath=''):
    '''Creates a render directory relative to the out

    :param renderPath: _description_, defaults to ''
    :type renderPath: str, optional
    :return: _description_
    :rtype: _type_
    '''
    filepath = os.path.abspath(filepath)
    if not os.path.isdir(filepath):
        os.makedirs(filepath)
        if not os.path.isdir(filepath):
            mc.error(f'Unable to create directory: {filepath} \n Check permissions.')
            return False
        else:
            print(f'Created directory: {filepath}')
            return True
    else:
        print(f'Directory exists: {filepath}')
        return True

def plugin_check(plugins):
    '''checks the loaded state of a plugin and loads it if needed
    provide the plugin in the name.ext format to support .py and .mll
    plugin in types

    :param plugins: a list of strings formatted in name.ext
    :type plugins: string or list
    '''
    plugins = plugins if isinstance(plugins, list) else [plugins]

    loaded_plugins =  mc.pluginInfo( query=True, listPlugins=True )

    success = True
    for plugin in plugins:
        if plugin.split('.')[0] not in loaded_plugins:
            try:
                mc.loadPlugin( plugin )
            except:
                success = False
                mc.warning(f'Could not load plugin {plugin}')
    return success

def unc_drive_table(remove=''):
    '''Create a table of drive letters and their corresponding unc paths

    :param remove: optionally remove a string to allow for more consise patths , defaults to ''
    :type remove: str, optional
    :return: _description_
    :rtype: _type_
    '''

    if platform.system() == "Windows":
        drives = subprocess.getoutput('net use')
        letters = re.findall(".?:", drives)
        networks = re.findall(r"\\\\.*$", drives, re.MULTILINE)
        networks = [n.rstrip().replace(remove, '') for n in networks]
        drivemap = dict(zip(letters, networks))

        if drivemap:
            return drivemap
    else:
        print("Not submitting from windows, no drive letter substitution")

def unc_mapper(path, remove='', drivetable = None):
    '''Remap a path from named letters to unc paths

    :param path: path
    :type path: string
    :param remove: optionally remove a string in the path, defaults to ''
    :type remove: str, optional
    :param driveTable: a dict keyed by drive letter, generated from uncDriveTable, defaults to {}
    :type driveTable: dict, optional
    :return: a substituted path
    :rtype: string
    '''
    if not drivetable:
        drivetable = unc_drive_table()
    #get the drive letter
    drive, tail = os.path.splitdrive(path)
    # print (drive, tail)
    if ':' not in drive: return path.replace(remove,'')

    # we may not have a mapping for the drive, like a removable disk, so skip if that's the case.
    if drive not in drivetable: return path.replace(remove,'')

    if drivetable[drive]: return os.path.abspath(drivetable[drive] + tail)

if __name__ == '__main__':
    print ('Drive table: ')
    pprint(unc_drive_table)
