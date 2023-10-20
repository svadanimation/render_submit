'''Reloads all modules in the current package, except for this one.
'''

import sys
import os

from importlib import reload
import maya.cmds as mc # pylint: disable=import-error

BASE = 'Z:/vs_code_svad/prog_art23/render_submit'
SCRIPTS = 'scripts'
ENV = os.path.join(BASE, SCRIPTS)
PACKAGE = 'render_submit'
QB = 'c:/Program Files/pfx/qube/api/python/'
VRAY = 'vrayformaya'
DEPLOY = 'K:\\Animation\\Pipeline\\SVAD_2023\\maya\\apps\\render_submit\\scripts'

add = [ENV, QB]
remove = [DEPLOY]

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

if __name__ == '__main__':
    plugin_check(VRAY)
    realpaths = [os.path.normpath(p) for p in sys.path]
    for path in add:
        if os.path.normpath(path) not in realpaths:
            sys.path.append(path)
    for path in remove:
        path = os.path.normpath(path)
        for i, real in enumerate(realpaths):
            if path == real:
                actual_path = sys.path[i]
                print(f'Removed {actual_path} from sys.path')
                sys.path.remove(actual_path)
    
    # brutal and ugly way to garbage collect old modules in the package
    # mod_to_del = []
    # for mod in sys.modules.keys():
    #     if mod.startswith('render_submit'):
    #         mod_to_del.append(mod)
        
    # for mod in mod_to_del:
    #     print(f'Deleting {mod} from sys.modules')
    #     del sys.modules[mod]
    #     del mod

    current_package = PACKAGE
else:
    # Get the name of the current package
    current_package = __name__.rpartition('.')[0]

# base package
import render_submit
reload(render_submit)

from render_submit import constants
from render_submit import file_grep
from render_submit import render_loop
from render_submit import render_utils
from render_submit import vray_path_translate
from render_submit import vray_mash
from render_submit import vray_submit
from render_submit.ui import single_submit_ui
from render_submit.ui import multi_submit_ui

# Iterate over the modules in sys.modules with the same package name
success = True
for module_name in list(sys.modules.keys()):
    if module_name.startswith(current_package + '.'):

        # Reload the module using the importlib.reload() function
        try:
            reload(sys.modules[module_name])
            print(f'Module {module_name} has been reloaded...')
        except Exception as exc:
            success = False
            print(f'Module {module_name} FAILED reload...')

if success:
    print(f'SUCCESS: All modules in package {current_package} have been reloaded.')
else:
    print('FAILURE: Some modules in package {current_package} have failed to reload.')

if __name__ == "__main__":

    try:
        multi_submit_dialog.close() # pylint: disable=E0601
        multi_submit_dialog.deleteLater() # pylint: disable=E0601
    except:
        pass
    
    multi_submit_dialog = multi_submit_ui.MultiSubmitTableWindow()
    multi_submit_dialog.show()
    # vray_submit.vray_submit_jobs(make_movie=True)
    # submit_ui = single_submit_ui.SubmitUI()
