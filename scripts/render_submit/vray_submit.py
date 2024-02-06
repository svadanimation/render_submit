'''
Qube! vray standalone submitter

TODO: Remake agenda after range is updated
TODO: Set in/out based on updated range in UI

'''
# builtins
import os
from pprint import pprint

import maya.mel as mel # pylint: disable=import-error
import maya.cmds as mc # pylint: disable=import-error
import qb

# internal
from render_submit import constants
from render_submit import render_utils
from render_submit import vray_mash

def calculate_aspect_ratio(res):
    width = None
    height = None
    if res:
        width = int(res*constants.ASPECT_RATIO)
        height = res
    return width, height

def get_jobs(make_movie=False, project=False, high_memory=0):
    '''
    Builds a dictionary of render settings for submission

    '''

    #initial name check
    scene_file = mc.file(q=True, sn=True)
    if len(scene_file) <= 0:
        prompt = mc.confirmDialog(title='Save File', 
                         message='Save file before submitting render!', 
                         button=['OK','Cancel'],
                         defaultButton='OK',
                         cancelButton='Cancel',
                         dismissString='Cancel')
        mc.warning('Save file before submitting render!')
        if prompt == 'OK':
            mel.eval("SaveSceneAs")
            # double check that the file is saved
            scene_file = mc.file(q=True, sn=True)
            if len(scene_file) <= 0:
                mc.warning('File not saved')
                return
        else:
            mc.warning('Canceled render submission')
            return
    if scene_file.startswith(constants.OMIT_DRIVES):
        mc.warning('File must be on a network share')
        return

    # reconstruct shot name
    shot_name_tokens = os.path.basename(scene_file).split('.')
    shot_name_tokens.pop(-1)
    shot_name = '_'.join(shot_name_tokens)

    #paths and names
    job_name = 'vray: ' + shot_name
    ext = 'png'
    if mc.getAttr('vraySettings.imageFormatStr') is not None:
        ext = mc.getAttr('vraySettings.imageFormatStr').split(' ', -1)[0]
    dir_path = os.path.dirname(os.path.abspath(scene_file))
    render_path = os.path.join(dir_path, 'render')
    frame_path = os.path.join(render_path, (shot_name + '.#.' + ext))
    vrscene = os.path.join(render_path, (shot_name + '.vrscene'))
    width = str(mc.getAttr('vraySettings.width'))
    height = str(mc.getAttr('vraySettings.height'))
    start_frame = int(mc.getAttr("defaultRenderGlobals.startFrame"))
    end_frame = int(mc.getAttr("defaultRenderGlobals.endFrame"))

    # switch paths to UNC
    # drive table returns a simple dict of 'Z:':'//server/share/path'


    drive_table = render_utils.unc_drive_table(remove = constants.NETWORK_SUFFIX)
    render_path = render_utils.unc_mapper(render_path, drivetable=drive_table)
    frame_path = render_utils.unc_mapper(frame_path, drivetable=drive_table)
    vrscene = render_utils.unc_mapper(vrscene, drivetable=drive_table)

    # calculate colorspace based on extension
    color_space = 'linear'
    if ext != 'exr':
        color_space = 'srgb'

    #build dictionary
    # the easiest way to find this is to look at
    # qube job properties and job internals to get the key names
    jobs = {}
    vray_job = {}

    # limit the job to s specific host
    #vray_job['hosts']='svad-renderdev.local'

    vray_job['reservations'] = 'global.vray=1,host.processors=1'

    # these two keys work in combination.
    # specifying the cluster doesn't ensure a job won't run a worker, just ajusts the priority
    # so we add a requirement of host.os to make sure it only hits the windows clients
    # this can be extended further using groups
    # overwritten later if it is a project render and crossplatform
    vray_job['cluster'] = '/lab'
    vray_job['requirements'] = 'host.os=winnt'
    vray_job['renderpath'] = render_path
    vray_job['label'] = 'render'
    vray_job['name'] = job_name
    vray_job['cpus'] = constants.CPUS
    vray_job['prototype'] = 'cmdrange'
    vray_job['validate_fileMinSize'] = constants.MIN_FILE_SIZE
    vray_job['agendatimeout'] = constants.TIMEOUT
    vray_job['priority'] = constants.PRIORITY

    # this esoteric flag is to make the job do worker path translation.
    # Every path to be converted according to the qbwork.conf
    # needs to be wrapped in QB_CONVERT_PATH()
    vray_job['flags'] = '131072'

    # recommend by shinya to mitigate crashes with the cmdline proxy on ventura
    vray_job['retrysubjob'] = 3
    vray_job['retrywork'] = 1

    # on osx this is controlled via the vray.sh file which spins these up
    # just in time and then passes any additional flags
    vray_job['env'] = {
        'PATH': f'%PATH%;{constants.VRAY_PATH}',
        'VRAY_TERMINATE_ON_FRAME_END': '0',
        'VRAY_OSL_PATH' : constants.VRAY_OSL_PATH,
        'OCIO': constants.OCIO
        }

    package = {}
    package['submitType'] = 'cmdline'
    # package['submitType'] = 'vray_cmdline'
    package['-imgFile'] = frame_path
    package['-imgHeight'] = height
    package['-imgWidth'] = width
    package['-sceneFile'] = str(vrscene)
    package['-showProgress'] = '0'
    package['-verboseLevel'] = '3'
    package['padding'] = str(mc.getAttr("vraySettings.fileNamePadding"))
    package['range'] = str(start_frame)  + '-' + str(end_frame)
    package['regex_outputPaths'] = 'Successfully written image file "(.*?)"'

    cmd = (
        f'QB_CONVERT_PATH({constants.CONVERT_PATH})'
        ' -frames=QB_FRAME_START-QB_FRAME_END,QB_FRAME_STEP'
        ' -autoClose=1'
        ' -verboseLevel=3'
        f' -sceneFile="QB_CONVERT_PATH({str(vrscene)})"'
        f' -imgWidth={width}'
        f' -imgHeight={height}'
        f' -imgFile="QB_CONVERT_PATH({str(frame_path)})"'
        ' -showProgress=0'
        ' -display=0'
        ' -region=none'
    )

    # the basic format for submission
    # package['cmd_template'] =
    # '%(vray_path)s -frames=QB_FRAME_START-QB_FRAME_END,QB_FRAME_STEP -autoClose=1 %(argv)s'
    package['cmdline'] = cmd
    vray_job['package'] = package

    #auto wrangling needs to be re-instated at some point when they fix it.
    vray_job_callbacks = [
        {
            'triggers': 'timeout-work-self-*',
            'language': 'qube',
            'code': 'fail-work-self'
        },
    ]

    vray_job['callbacks'] = vray_job_callbacks

    #build job dictionary
    jobs['vray_job'] = vray_job

    # Build agenda for vray job
    agenda = qb.genframes(str(start_frame) + '-' + str(end_frame))
    vray_job['agenda'] = agenda
    vray_job['reservations'] = 'global.vray=1,host.processors=1'

    # Allow job to run on all stations without a prioity hit.
    # It will try to run on the /osx cluster first
    if project:
        vray_job['cluster']='/osx/+'
        vray_job['requirements'] = 'host.os=osx || host.os=winnt'
        vray_job['project'] = project

    # Consider exposing this memory value in confirmation script,
    # anything more than 10k won't run on old farm
    if high_memory:
        vray_job['reservations'] = f'global.vray=1,host.processors=1,host.memory={high_memory}'

    # Movie job setup
    if make_movie:
        movie_job = {}
        movie_job['prototype'] = 'cmdrange'
        movie_job['priority'] = 1
        movie_job['cluster'] = '/farm'
        movie_job['omitgroups'] ='can'
        movie_job['requirements'] = 'host.os=winnt'

        base_path = frame_path.split('#',1)[0]

        # Movie agenda has a single task
        agenda_movie = qb.genframes('1')
        # Set the outputPaths in the resultpackage for each agenda item,
        # this is for compatability with shotgun_submitVersion.py
        for i in agenda_movie:
            i['resultpackage']={'outputPaths': str(base_path + 'thumb.jpg')}
        movie_job['agenda'] = agenda_movie
        movie_job['name'] = str('pdplayer: ' + shot_name)
        movie_job['package'] = {}
        movie_job['package']['submitType'] = 'cmdline'

        # important that the machines have the correct codecs installed
        # or the movie conversion will fail
        pdplayercmd = (
            f'{constants.PDPLAYER}'
            f' "{str(frame_path.replace("#","*"))}"'
            ' --force_sequence'
            ' --alpha=ignore'
            f' --color_space={color_space}'
            ' --exposure=0'
            ' --soft_clip=0'
            ' --saturation=0'
            ' --transient'
            ' --scale=100'
            f' --mask_size={width},{height}'
            ' --mask_type=crop'
            ' --fps=24'
            f' --save_mask_as_image="{str(base_path +  "thumb.jpg")}"'
            f' --save_mask_as_sequence="{str(base_path + "movie.mov")}",mp4v,100'
            ' --exit'
        )

        movie_job['package']['cmdline'] = pdplayercmd
        movie_job['package']['thumbnail'] = str(base_path +  'thumb.jpg')
        movie_job['package']['movie'] = str(base_path + 'movie.mov')

        movie_job['dependency'] = 'complete-job-render'

        jobs['movie_job'] = movie_job


    return jobs


def apply_render_settings(  cut_in = None, 
                            cut_out = None,
                            height = None,
                            width = None,
                            filename = None,
                            outfile = None,
                            step = None,
                            image_format = None,
                            motion_blur = None,
                            viewport_subdivision = None,
                            max_subdivs = None):
    if cut_in: mc.setAttr("defaultRenderGlobals.startFrame", cut_in)
    if cut_out: mc.setAttr("defaultRenderGlobals.endFrame", cut_out)
    if filename: mc.setAttr('vraySettings.fileNamePrefix', filename, type='string')
    if image_format: mc.setAttr("vraySettings.imageFormatStr",image_format, type='string')
    if outfile: mc.workspace(fileRule=['images',outfile])
    if height: mc.setAttr("vraySettings.height", height)
    if width: mc.setAttr("vraySettings.width", width)
    if step: mc.setAttr ("defaultRenderGlobals.byFrameStep", step)
    if motion_blur: mc.setAttr ("vraySettings.cam_mbOn", motion_blur)
    if viewport_subdivision: mc.setAttr ("vraySettings.globopt_render_viewport_subdivision", viewport_subdivision)
    if max_subdivs: mc.setAttr ("vraySettings.progressiveMaxSubdivs", max_subdivs)

def vray_submit_jobs(jobs = None,
                    make_movie=False,
                    project=False,
                    show_ui=True):
    '''
    Entry point to build the dictionary for submission
    optinally pass in a job from a UI
    build it if it doesn't exist

    '''
    vray_config()

    #fill the dictionary
    if not jobs:
        jobs = get_jobs(make_movie=make_movie, project=project)
        if not jobs:
            mc.warning('No jobs to submit, file not saved or cancelled by user')
            return

    vray_standalone_post(jobs, show_ui=show_ui)

def vray_config():
    '''Check vray is loaded and set it as the renderer'''

    if not render_utils.plugin_check(constants.VRAY_PLUGIN_LOAD):
        mc.error('Vray is not loaded')

    # vray config
    mc.preferredRenderer( 'vray', makeCurrent=True )

    if not mc.objExists("vraySettings"):
        mel.eval("vrayCreateVRaySettingsNode();")

    if mel.eval("vrend -isRendering") == "1" or mel.eval("vrend -q") == "1":
        mc.error('Already rendering or exporting')


def vray_standalone_post(jobs, show_ui=True):
    '''Script to execute after scene translation

    :param jobs: dictionary of jobs
    :type jobs: dict
    :param show_UI: silent submission, defaults to True
    :type show_UI: bool, optional
    '''
    vrscene = jobs['vray_job']['package']['-sceneFile']
    render_path = jobs['vray_job']['renderpath']
    height = int(jobs['vray_job']['package']['-imgHeight'])
    width = int(jobs['vray_job']['package']['-imgWidth'])


    project = False
    try:
        #if there is an agenda, is an API job
        if  jobs['vray_job']['project']:
            project = True
            print ('Project job...')
    except:
        pass

    # special case to strip out instancer redundant data
    # disable for now
    # mashInstancers = vray_MASH.instancerPreExport()

    #set proxies to be off for faster export
    vray_meshes = mc.ls(type='VRayMesh')
    vray_mesh_status = list()

    if vray_meshes:
        print ('Temporarily disabling vrayMesh preview')
        for vray_mesh in vray_meshes:
            vray_mesh_status.append((vray_mesh, mc.getAttr(vray_mesh + '.geomType') ))
            mc.setAttr(vray_mesh + '.geomType', 0)

    # build path
    if not render_utils.build_directory(filepath=render_path):
        mc.error(f'Failed to build directory: {render_path}')

    # If this is a project job, it needs to be cross-platform,
    # so we will replace all the paths with the UNC equivalent
    # need to drop this to an external file and just import
    # only the original vraySettings node is supported for post translation
    orig_post_translate_py = mc.getAttr('vraySettings.postTranslatePython')
    post_translate_py = (
        'from render_submit import vray_path_translate\n'
        'from importlib import reload\n'
        'reload(vray_path_translate)\n'
        'vray_path_translate.find_and_process_paths()\n'
    )
    # if project:
    if True:
        # add the post translate script to whatever might already be there
        # we have to do this because the vraySettings node doesn't support the post translate python
        mc.setAttr('vraySettings.postTranslatePython',
                   orig_post_translate_py+post_translate_py,
                   type='string')

    # create a temporary vray settings node that
    # mimics the true settings node except for some options
    if mc.objExists("vraySettings_qubeExport"):
        mc.delete("vraySettings_qubeExport")

    mc.createNode("VRaySettingsNode",
                  shared = True,
                  n = "vraySettings_qubeExport")
    mc.copyAttr("vraySettings",
                "vraySettings_qubeExport",
                inConnections = True,
                values = True,
                ksc=True)

    mc.setAttr("vraySettings_qubeExport.height", height)
    mc.setAttr("vraySettings_qubeExport.width", width)
    mc.setAttr("vraySettings_qubeExport.animType", 1)
    mc.setAttr("vraySettings_qubeExport.vrscene_render_on", 0)
    mc.setAttr("vraySettings_qubeExport.vrscene_on", 1)
    mc.setAttr("vraySettings_qubeExport.vrscene_filename", vrscene, type = "string")
    # Disable auto layer token. Path is already absolute, so we don't need to
    # worry about the tags that are auto added to relative paths.
    mc.setAttr("vraySettings_qubeExport.autoLayerTokenInAbsPath", 0)
    mc.setAttr("vraySettings_qubeExport.misc_eachFrameInFile", 0)
    mc.setAttr("vraySettings_qubeExport.misc_separateFiles", 0)
    mc.setAttr("vraySettings_qubeExport.misc_compressedVrscene", 1)
    mc.setAttr("vraySettings_qubeExport.misc_transformAsHex", 1)
    mc.setAttr("vraySettings_qubeExport.misc_meshAsHex", 1)
    mc.setAttr("vraySettings_qubeExport.animBatchOnly", 0)
    mc.setAttr("vraySettings_qubeExport.sys_distributed_rendering_on", 0)


    camera = render_utils.get_renderable_camera()[0]
    print(f'Writing: {vrscene} from camera: {camera}')

    # fire off the export
    mel.eval("vrend -camera "+ camera +" -vraySettingsNode vraySettings_qubeExport;")

    # cleanup
    mc.delete("vraySettings_qubeExport")
    mc.setAttr('vraySettings.postTranslatePython', orig_post_translate_py, type='string')

    #cleanup from special case
    # if vraymashInstancers is not None:
    #     vray_MASH.instancerPostExport(mashInstancers, vrscene)

    # cleanup from mesh preview
    if vray_mesh_status:
        print ('Resetting vrayMesh preview')
        for vray_mesh in vray_mesh_status:
            mc.setAttr(vray_mesh[0] + '.geomType', vray_mesh[1])
            mc.refresh(force=True)

    if not os.path.exists(vrscene):
        mc.error(f'Error translating scene {vrscene} does not exist')


    # submit the jobs
    print ('Jobs: ')
    pprint(jobs)

    if  'movie_job' in jobs:
        print ('Movie job >')
        try:
            submitted = qb.submit([jobs['vray_job'], jobs['movie_job']], deferTableCreation=False)
        except:
            mc.error('Error submitting movie job to qube')
    else:
        print ('Standard job >')
        try:
            submitted = qb.submit([jobs['vray_job']], deferTableCreation=False)
        except:
            mc.error('Error submitting job to qube')


    # Provide submission feedback
    result_string = '<hl>Submitted:</hl>\n'
    for j in submitted:
        result_string += f'{j["id"]} = {j["name"]} \n'

    print(result_string.replace('<hl>', '').replace('</hl>', ''))

    if show_ui:
        render_utils.display_message(result_string)
        # mc.confirmDialog(title='Qube submit report',
        #                  message=result_string,
        #                  button='Ok',
        #                  defaultButton='Ok' )


if __name__ == '__main__':
    vray_submit_jobs(project=False)
