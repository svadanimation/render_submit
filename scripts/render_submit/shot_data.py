'''
This module contains the functions to get the shot data from the json file
'''

import json
import os
from pprint import pprint

import maya.cmds as mc # pylint: disable=import-error
from render_submit import vray_submit

appdata = os.getenv('APPDATA')
recents_path = os.path.join(appdata, 'render_submit', 'recents.json')

SHOT_TEMPLATE = {
                'active': True,
                'file': '',
                'note': '',
                'cut_in': '',
                'cut_out': '',
                'res': '',
                'step': '',
                'movie': True, 
                'osx': False 
                }

SHOT_TEMPLATE_TYPE = {
                'active': 'bool',
                'file': 'str',
                'note': 'str',
                'cut_in': 'int',
                'cut_out': 'int',
                'res': 'int',
                'step': 'int',
                'movie': 'bool',
                'osx': 'bool'
                }

def query_scene_data():
    '''Returns the scene data for the current scene
    '''
    # TODO build this based on the shot template
    scene_data = SHOT_TEMPLATE.copy()
    scene_data['file'] = mc.file(q=True, sn=True)
    scene_data['cut_in'] = int(mc.playbackOptions(q=True, min=True))
    scene_data['cut_out'] = int(mc.playbackOptions(q=True, max=True))
    scene_data['res'] = int(mc.getAttr('defaultResolution.height'))
    scene_data['step'] = int(mc.getAttr('defaultRenderGlobals.byFrameStep'))
    
    return scene_data

def apply_scene_data(shot: dict):
    '''Applies the shot data to the current scene
    '''
    # TODO build this based on the shot template
    width, height = vray_submit.calculate_aspect_ratio(shot.get('res'))
    vray_submit.apply_render_settings(
                # get the shot data
                cut_in = shot.get('cut_in'),
                cut_out = shot.get('cut_out'),
                height = height,
                width = width,
                filename = shot.get('filename'),
                outfile = shot.get('outfile'),
                step = shot.get('step')
    )

def validate_shot_data(shots_data):
    '''
    This function is called by the UI to conform the shot data
    '''
    # if the shot data doesn't have the correct keys, throw it away
    # consider other cleanup if it is close
    if isinstance(shots_data, list):
        for shot in shots_data:
            if not isinstance(shot, dict):
                mc.warning('Shot is not a dictionary')
                return False
            # make sure we have the file key
            if 'file' not in shot:
                mc.warning('Shot data is missing critical file key')
                return False
            for key in SHOT_TEMPLATE:
                if key not in shot:
                    mc.warning(f'Shot data is missing key: {key}. Defaulting...')
                    # add the default key to the shot
                    shot[key] = SHOT_TEMPLATE[key]
        return True
    else:
        mc.warning('Shots data is not a list')
        return False

def reorder_shots(shots_data, new_order):
    '''Reorders the shot data'''
    shot_list = {shots_data[id] for id in new_order if id in shots_data}
    return shot_list

def replace_shot(shots_data, id, replacement):
    shots_data[id] = replacement

def insert_shot(shots_data, filepath, id=None):
    '''Inserts a shot into the shot data
    '''
    shot = SHOT_TEMPLATE.copy()
    shot['file'] = filepath
    if id is None:
        shots_data.append(shot)
    else:
        shots_data.insert(id, shot)

    return shots_data

def shot_exists(shots_data, filepath):
    '''Checks if a shot already exists in the shot data
    '''
    for shot in shots_data:
        if shot['file'] == filepath:
            return True
    return False

def remove_shot(shots_data, filepath=None, id=None):
    '''Removes a shot from the shot data
    '''
    if filepath:
        for shot in shots_data:
            if shot['file'] == filepath:
                shots_data.remove(shot)
                return shots_data
    if id:
        shots_data.pop(id)
        return shots_data
    
    mc.warning('No shot found to remove')
    return shots_data


def load_shot_data(filepath):
    '''
    This function is called by the UI to get the shot data
    '''
    # validate the file path
    if not os.path.isfile(filepath):
        mc.warning(f'File not found: {filepath}')
        return None

    with open(filepath, 'r', encoding='ascii') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as err:
            print(f'Unable to load file: {err.doc} \n'
                f'Pos: {err.pos} '
                f'Line: {err.lineno} '
                f'Column: {err.colno} ')
            mc.confirmDialog(title='Error',
                             message=f'Unable to load file: {filepath}',
                             button=['OK'], defaultButton='OK', 
                             cancelButton='OK', dismissString='OK')
            return None

    if validate_shot_data(data.get('shots')):
        return data.get('shots'), data.get('preset')

def save_shot_data(filepath, shots_data, preset=''):
    '''
    This function is called by the UI to save the shot data
    '''
    # validate the path
    if not os.path.isdir(os.path.dirname(filepath)):
        mc.warning(f'Directory not found: {filepath}')
        return None
    
    data = {'shots': shots_data, 'preset': preset}
  
    with open(filepath, 'w', encoding='ascii') as f:
        try:
            json.dump(data, f, indent=4)
        except ValueError as err:
            mc.confirmDialog(title='Error',
                             message=f'Unable to save file: {filepath} \n {err}',
                             button=['OK'], defaultButton='OK', 
                             cancelButton='OK', dismissString='OK')
            return None

def save_recent_data(recent_files):
    '''
    This function is called by the UI to save the recent files
    '''
    if build_directory(recents_path):
        with open(recents_path, 'w', encoding='ascii') as f:
            json.dump(recent_files, f, indent=4)

def load_recent_data():
    '''
    This function is called by the UI to load the recent files
    '''
    if not os.path.isfile(recents_path):
        print(f'No recent files found: {recents_path}')
        return 

    with open(recents_path, 'r', encoding='ascii') as f:
        recent_files = json.load(f)
    return recent_files if recent_files else None

def build_directory(filepath: str):
    '''Creates a folder if it doesn't exit
    '''
    filepath = os.path.abspath(filepath)
    dirpath = os.path.dirname(filepath)

    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)
        if not os.path.isdir(dirpath):
            mc.error(f'Unable to create directory: {dirpath} \n Check permissions.')
            return False
        else:
            print(f'Created directory: {dirpath}')
            return True
    else:
        # print(f'Directory exists: {dirpath}')
        return True
    
if __name__ == '__main__':
    test_shot_path = 'Z:\\VSCODE\\prog_art23\\render_submit\\test\\test_shot_data.json'
    pprint(load_shot_data(test_shot_path))


