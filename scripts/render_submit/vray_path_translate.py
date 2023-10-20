'''
Post translate paths in vray scenes
'''

# built-ins
import os
import vray.utils as vu # pylint: disable=import-error

# internal
from render_submit import constants
from render_submit import render_utils


GEOMETRY = 'GeomMeshFile'
BITMAP = 'BitmapBuffer'
SCENE = 'VRayScene'
VDB = 'PhxShaderCache'

def find_and_replace_nodes(node_list, 
                           local_drive_table, 
                           flag = 'file', 
                           debug=True):
    for node in node_list:
        if debug: print (f'Node: {node}')
        path = node.get(flag)
        path = render_utils.unc_mapper(path,
                                     remove = constants.NETWORK_SUFFIX,
                                     drivetable=local_drive_table)
        path = path.replace(os.sep, '/')
        if debug: print (f'Path: {path}')
        node.set(flag, str(path))

def find_and_process_paths(debug=True):
    '''post translate python script to replace all drive mapped paths with unc paths

    :param debug: verbose printing, defaults to True
    :type debug: bool, optional
    '''
    local_drive_table = render_utils.unc_drive_table(remove = constants.NETWORK_SUFFIX)

    if debug: print ('Vray post translate paths: Finding meshes and bitmaps')

    nodes = []
    nodes.extend( vu.findByType(GEOMETRY) )
    nodes.extend( vu.findByType(BITMAP) )

    find_and_replace_nodes(local_drive_table=local_drive_table,
                           node_list=nodes,
                           flag='file',
                           debug=debug)

    if debug: print ('Finding scenes')

    scenes=[]
    scenes.extend( vu.findByType(SCENE) )

    find_and_replace_nodes(local_drive_table=local_drive_table,
                           node_list=scenes,
                           flag='filepath',
                           debug=debug)

    if debug: print ('Finding vdb files')
    vdbs=[]
    vdbs.extend( vu.findByType(VDB))

    find_and_replace_nodes(local_drive_table=local_drive_table,
                            node_list=vdbs,
                            flag='cache_path',
                            debug=debug)


if __name__ == "__main__":
    find_and_process_paths()
