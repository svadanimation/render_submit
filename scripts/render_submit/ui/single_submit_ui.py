'''
    Display a validation UI for the Qube job dictionary

'''
import maya.cmds as mc # pylint: disable=import-error
import qb

from render_submit import vray_submit
from render_submit import constants

class SubmitUI(object):
    '''
    Display a validation UI for the Qube job dictionary
    Creates a window with a table of the jobs and a button to submit the jobs

    '''
    WINDOW = 'submit_ui'
    keys = [['vray_job', 'name'],
            ['vray_job', 'package', 'range'],
            ['vray_job', 'package', '-imgHeight'],
            ['vray_job', 'package', '-imgWidth'],
            ['vray_job', 'package', '-imgFile'],
            ['vray_job', 'renderpath'],
            ['vray_job', 'cpus'],
            ['vray_job', 'priority'],
            ['vray_job', 'package', 'padding'],
            ['vray_job', 'cluster'],
            ['vray_job', 'reservations'],
            ['vray_job', 'validate_fileMinSize']]

    def __init__(self, jobs: dict = None, osx: bool = False, editable: bool = False):
        self.osx = osx
        self.jobs = jobs
        if not jobs:
            self.jobs = vray_submit.get_jobs(project=osx)
            if not self.jobs:
                mc.warning('No jobs to submit or cancelled by user')
                return
        self.editable = editable
        self.window = None
        self.form = None
        self.table = None
        self.ok_button = None
        self.movie_button = None
        self.cancel_button = None
        self.hilight = None
        self.job_count = None

        vray_submit.vray_config()
        self.validate_submit_dict()
        self.show()

    def show(self):
        '''Show the UI'''
        mc.window(self.window, edit=True, sizeable=False, resizeToFitChildren=True)
        mc.showWindow( self.window )

    def remove(self, *args):
        '''Remove the ui'''
        if mc.window( self.WINDOW, q = 1, ex = 1 ):
            mc.deleteUI(self.WINDOW)

    @staticmethod
    def deep_get(_dict, keys, default=None):
        """
        Safely gets a value in a nested dictionary given a list of keys.

        Args:
            nested_dict (dict): The nested dictionary to update.
            key_list (list): A list of keys specifying the path to the value to update.
            default: The default value to return if the key is not found.

        Returns:
            Requested key, None
        """
        for key in keys:
            if isinstance(_dict, dict):
                _dict = _dict.get(key, default)
            else:
                return default
        return _dict

    @staticmethod
    def deep_update(nested_dict, key_list, value, default=None):
        """
        Safely updates a value in a nested dictionary given a list of keys.
        If intermediate dictionaries or the key do not exist,
        they are created with the specified default value.

        Args:
            nested_dict (dict): The nested dictionary to update.
            key_list (list): A list of keys specifying the path to the value to update.
            value: The new value to set.
            default: The default value to use when creating intermediate dictionaries.

        Returns:
            None
        """
        if not isinstance(nested_dict, dict):
            return

        for key in key_list[:-1]:
            nested_dict = nested_dict.setdefault(key, {})
            if not isinstance(nested_dict, dict):
                return

        if key_list[-1] in nested_dict:
            nested_dict[key_list[-1]] = value
        else:
            nested_dict.setdefault(key_list[-1], value if value is not None else default)


    @staticmethod
    def edit_cell(row, column, value):
        '''Callback for when a cell is edited in the table'''
        # print(f'row: {row}, column: {column}, value: {value}')
        return 1

    def validate_submit_dict(self):
        '''Validate the Qube job dictionary

        :param jobs: dictonary of qube jobs
        :type jobs: dict
        '''
        # delete the old window if it exists
        self.remove()

        self.window = mc.window(self.WINDOW, widthHeight=(766, 490), sizeable=False)

        self.form = mc.formLayout('submit_form')
        self.table = mc.scriptTable(rows=len(self.keys),
                            columns=2,
                            label=[(1,"Key"), (2,"Value")],
                            cellChangedCmd=self.edit_cell)
        self.table = mc.scriptTable(self.table, edit=True, editable=self.editable)
        mc.scriptTable(self.table, cw = [1,250], edit=True)
        mc.scriptTable(self.table, cw = [2,500], edit=True)

        self.ok_button = mc.button('okButton',
                            label="Submit",
                            command=self.submit)

        self.movie_button = mc.button('movie_button',
                            label="Submit && Make Movie",
                            command=self.submit_movie)

        self.cancel_button = mc.button(label="Cancel",command=self.remove)

        mc.formLayout(self.form,
            edit=True,
            attachForm=[(self.table, 'top', 0),
                        (self.table, 'left', 0),
                        (self.table, 'right', 0),
                        (self.ok_button, 'left', 0),
                        (self.ok_button, 'bottom', 0),
                        (self.movie_button, 'bottom', 0),
                        (self.cancel_button, 'bottom', 0),
                        (self.cancel_button, 'right', 0)],
            # attachOppositeForm=[(self.table, 'left', 0)],
            attachControl=[(self.table, 'bottom', 0, self.ok_button),
                           (self.movie_button, 'left', 0, self.ok_button),
                        (self.movie_button, 'right', 0, self.cancel_button)],
            attachNone=[(self.ok_button, 'top'),(self.cancel_button, 'top'),(self.movie_button, 'top')],
            attachPosition=[(self.ok_button, 'right', 0, 33),
                            (self.cancel_button, 'left', 0, 66)]
            )

        self.draw_table()
        mc.setFocus(self.ok_button)


    def draw_table(self):
        '''Fill the table with the selected items from the jobs dictionary
        '''

        for i, key in enumerate(self.keys):
            value =''
            if isinstance(key, list):
                value = self.deep_get(self.jobs, key)
            else:
                value = self.jobs[key]

            mc.scriptTable(self.table, cellIndex=(i+1,1),
                           edit=True, cellValue=str(':'.join(key)), cbc=self.cell_color)
            mc.scriptTable(self.table, cellIndex=(i+1,2),
                           edit=True, cellValue=str(value), cbc=self.cell_color)

    @staticmethod
    def cell_color(row, _, color_range='255'):
        colors = [(0.25,0.25,0.25), (0.3,0.3,0.3)]
        color = colors[row % 2]

        if row==1:
            color = (0.3,0.5,0.7)

        if row > 6:
            color = tuple((c*1.5) for c in color)

        if color_range == '1':
            return color
        elif color_range == '255':
            return tuple(int(c*255) for c in color)
        else:
            mc.error("Invalid color range specified. Must be '1' or '255'.")

    def scrape_table(self):
        '''Scrape the table and update the jobs dictionary
        '''
        rows = mc.scriptTable(self.table, rows=True, query=True)
        for row in range(1,rows):
            key = mc.scriptTable(self.table, cellIndex=(row,1), cellValue=True, query=True)[0]
            value = mc.scriptTable(self.table, cellIndex=(row,2), cellValue=True, query=True)[0]
            # if value != dict:
            #     #required because of some funky unicode encoding that happens during exec
            #     # value = "'" + value.replace('\\', '\\\\') + "'"
            #     value = value.replace('\\', '\\\\')

            # break up by token
            keys = key.split(':')
            self.deep_update(self.jobs, keys, value)

        # pprint(self.jobs)

    def update_agenda(self):
        # this is so terrible, but we need to update the dict and cmd

        vrscene = self.jobs['vray_job']['package']['-sceneFile']
        frame_path = self.jobs['vray_job']['package']['-imgFile']
        height = int(self.jobs['vray_job']['package']['-imgHeight'])
        width = int(self.jobs['vray_job']['package']['-imgWidth'])

        render_range = self.jobs['vray_job']['package']['range']
        start_frame, end_frame = render_range.rsplit('-', 1)
        mc.setAttr("defaultRenderGlobals.startFrame", int(start_frame))
        mc.setAttr("defaultRenderGlobals.endFrame", int(end_frame))

        # Rebuild agenda for vray job
        agenda = qb.genframes(str(start_frame) + '-' + str(end_frame))
        self.jobs['vray_job']['agenda'] = agenda

        # so terrible
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


        self.jobs['vray_job']['package']['cmdline'] = cmd


        
        


    def submit_movie(self,*args):

        # There is probably a better pattern, but we make the new submit dict with a movie
        # then overwite the new one with ui values
        self.jobs = vray_submit.get_jobs(make_movie=True)
        self.scrape_table()
        self.update_agenda()
        self.remove()
        vray_submit.vray_submit_jobs(self.jobs)

    def submit(self,*args):
        self.scrape_table()
        self.update_agenda()
        self.remove()
        vray_submit.vray_submit_jobs(self.jobs)


if __name__ == '__main__':
    submit_ui = SubmitUI()
