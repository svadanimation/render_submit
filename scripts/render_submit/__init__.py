import maya.cmds as mc # pylint: disable=import-error
import maya.mel as mm # pylint: disable=import-error

from render_submit.ui import multi_submit_ui
from render_submit.ui import single_submit_ui

RENDER_FARM_MENU = u'Render_Farm'
global svad_render_menu

# UI
try:
    mc.deleteUI(u'MayaWindow|{}'.format(RENDER_FARM_MENU), menu=True)
    mc.deleteUI(RENDER_FARM_MENU, menu=True)
except:
    pass


def populate_render_menu(*args):
    global svad_render_menu
    mc.menu(svad_render_menu, edit=True, deleteAllItems=True)
    launch_multi_submit_command = (
        'from render_submit.ui import multi_submit_ui;'
        ' multi_submit_ui = multi_submit_ui.MultiSubmitTableWindow();'
        ' multi_submit_ui.show();'
    )
    launch_single_submit_command = (
        'from render_submit.ui import single_submit_ui;'
        ' single_submit_ui = single_submit_ui.SubmitUI()'
    )
    launch_single_submit_osx_command = (
        'from render_submit.ui import single_submit_ui;'
        ' single_submit_ui = single_submit_ui.SubmitUI(osx=True,editable=True)'
    )
    mc.menuItem('Single Submit', 
                i='render_renderLayer.png', 
                command=launch_single_submit_command, 
                parent=svad_render_menu)
    mc.menuItem('Single Submit osx', 
                i='render_renderLayer.png', 
                command=launch_single_submit_osx_command, 
                parent=svad_render_menu)
    
    mc.menuItem(d=True, parent=svad_render_menu)

    mc.menuItem('Multi Submit', 
                i='render_renderPass.png', 
                command=launch_multi_submit_command, 
                parent=svad_render_menu)

maya_window = mm.eval('$_=$gMainWindow')
svad_render_menu = mc.menu(RENDER_FARM_MENU.replace('_',' '), parent=maya_window, tearOff=True, pmc=populate_render_menu)
