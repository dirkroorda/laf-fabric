import os
import traceback
import collections
import argparse
import sys, tty, termios

from .settings import Settings
from .task import GrafTask

class Shell(object):
    '''Execute tasks, either in a single run, or with an interactive prompt.

    This class knows about the environment, such as command line arguments
    and configuration files. 
    It collects those information pieces and passes them in suitable form
    to the factual task processor.

    '''

    def __init__(self):
        '''Upon creation, create a :class:`GrafTask <graf.task.GrafTask>` object based on settings.

        '''

        self.default = [
            0, # source
            0, # annox
            0, # task
        ]
        '''Defaults for the selectable items: *source*, *annox* and *task*.
        If the user does not pass values for them both on the command lines, these ones are used.
        If the user does pass some of these values and the command prompt is started, the
        command line values are parsed here, and the command prompt will use them as initial values.
        '''

        self.settings = Settings()

        argsparser = argparse.ArgumentParser(description = 'Conversion of LAF to Binary')
        argsparser.add_argument(
            "--source",
            dest = 'source',
            type = str,
            choices = self.settings.source_choices,
            metavar = 'Source',
            help = "which source to take",
        )
        argsparser.add_argument(
            "--annox",
            dest = 'annox',
            type = str,
            choices = self.settings.annox_choices,
            metavar = 'Annox',
            help = "which annox to take",
        )
        argsparser.add_argument(
            "--task",
            dest = 'task',
            type = str,
            choices = self.settings.task_choices,
            metavar = 'Task',
            help = "which task to perform",
        )
        argsparser.add_argument(
            "--force-compile-source",
            dest = 'forcecompilesource',
            action = "store_true",
            help = "Force new compilation of source to binary representation",
        )
        argsparser.add_argument(
            "--force-compile-annox",
            dest = 'forcecompileannox',
            action = "store_true",
            help = "Force new compilation of annox to binary representation",
        )
        argsparser.add_argument(
            "--menu",
            dest = 'menu',
        action = "store_true",
            help = "Display menu, use other arguments as defaults"
        )
        (self.args, remaining) = argsparser.parse_known_args()

        (self.prompt_data, self.index, self.iindex) = self.weave((
            sorted(self.settings.source_choices),
            sorted(self.settings.annox_choices),
            sorted(self.settings.task_choices),
        ))
        if self.args.source:
            self.default[0] = self.iindex[0][self.args.source]
        if self.args.annox:
            self.default[1] = self.iindex[1][self.args.annox]
        if self.args.task:
            self.default[2] = self.iindex[2][self.args.task]

        '''Data used to build a self-explanatory prompt, based on the available options'''
        self.message = ''
        '''Response messages to be displayed after the prompt'''

        self.cur = [self.default[i] for i in range(len(self.index))]
        '''Holds the current selection: the *source*, the *annox*, the *task* and the *force_compile_source*, *force_compile_annox* options, in that order.'''
        self.cur.append(self.args.forcecompilesource)
        self.cur.append(self.args.forcecompileannox)

        self.graftask = GrafTask(self.settings.settings)

    def run(self, source, annox, task, force_compile, load, function=None, stage=None):
        '''Does a single task. Useful for stand alone tasks.

        If invoked after the completion of another task, it unloads data from memory that is not needed anymore,
        and loads addtional required data.

        Args:
            source(str):
                the name of the source data
            annox(str):
                the name of an additional annotation package (use ``--`` for no additional package.
            task(str):
                the name of the task to execute. All tasks reside in a directory specified in the main config file.
            load(dict):
                a dictionary specifying what data to load. See :doc:`Writing Tasks <../taskwriting>`.
            function(callable): 
                the function that implements the task. It should accept one argument, being the GrafTask object
                through which all data in the LAF resource can be accessed.
        '''
        self.graftask.run(source, annox, task, force_compile=force_compile, load=load, function=function, stage=stage)
        
    def processor(self):
        '''Does work. Decides to run one task or start the command prompt.

        The decision is based on the presence of command line arguments.
        If all arguments are present to specify a task, the *run once* option will be chosen,
        unless the user has explicitly stated ``--menu``.
        Otherwise the command prompt is started. If that is the case, the
        command line args that did come through, are used as initial values.
        '''
        if self.args.source and self.args.annox and self.args.task and not self.args.menu:
            self.graftask.run(
                self.args.source,
                self.args.annox,
                self.args.task,
                force_compile={'source': self.args.forcecompilesource, 'annox': self.args.forcecompileannox},
            )
        else:
            self.command_loop()

    def command_loop(self):
        '''Command prompt for repeated running of tasks.
        '''

        while True:
            self.prompt()
            command = self.do_command("laf-fabric", "satCcx", '''
    s=select source
    a=select annox
    t=select task
    C=toggle force compile source
    c=toggle force compile annox
    x=execute selected task on selected source
''')
            if command == None:
                break

    def main_command(self, command):
        '''Interprets a top level command.

        Depending on the command passed, this methods prompts for additional information.
        This happens for the commands that modify the source and task selection.

        Args:
            command(char):
                the command character.

        Returns:
            message (str):
                response text after the command execution.
        '''
        message = ''
        if command == 's':
            source = self.get_num("source", 1, len(self.settings.source_choices))
            if source:
                self.cur[0] = source - 1
        if command == 'a':
            annox = self.get_num("annox", 1, len(self.settings.annox_choices))
            if annox:
                self.cur[1] = annox - 1
        elif command == 't':
            task = self.get_num("task", 1, len(self.settings.task_choices))
            if task:
                self.cur[2] = task - 1
        elif command == "C":
            self.cur[len(self.index)] = not self.cur[len(self.index)]
        elif command == "c":
            self.cur[len(self.index)+1] = not self.cur[len(self.index)+1]
        elif command == "x":
            sys.stderr.write("\n")
            try:
                self.graftask.run(*[self.index[col][self.cur[col]] for col in range(len(self.index))], force_compile={"source": self.cur[len(self.cur) - 2], "annox": self.cur[len(self.cur) - 1]})
                self.cur[len(self.index)] = False
                self.cur[len(self.index)+1] = False
            except:
                print(traceback.print_exc())
            self.get_ch(prompt="Press any key to continue ...")
        return message

    def do_command(self, prompt, choices, helpstr):
        '''Prompts the user to enter a command and dispatches it, if correct.

        This method asks the user for a command consisting of a single letter.
        It checks whether the letter is a legal option.
        It add options for quitting (Esc) and displaying help (?).
        If he user enters ``?``, the helpstring is displayed.

        Args:
            prompt (str):
                the prompt string to be displayed. This string will be extended with a description of the allowed keys to press.

            choices (str):
                a string consisting of legal  one letter commands, not separated.

            helpstr (str):
                help string to be displayed if the user presses ``?``

        Returns:
            command (str):
                the command entered by the user, or ``None`` if escape has been pressed.
        '''
        command = None
        self.message = ''
        Cont = True
        while True:
            sys.stderr.write(self.message)
            if not Cont:
                break
            self.message = ''
            sys.stderr.write("{} [{}/?/Esc] > ".format(prompt, '/'.join(choices)))
            sys.stderr.flush()
            command = self.get_ch()
            if command in choices:
                Cont = False
                self.message += self.main_command(command)
            elif command == '?':
                self.message = "\n" + helpstr + "\t? = this help\n\tEsc = quit\n"
            elif ord(command) == 27: # Escape
                Cont = False
                self.message = "Quit\n"
                command = None
            else:
                self.message = "{} ERROR\n".format(command)

        return command

    def get_num(self, prompt, start, end):
        '''Asks for a numeric value, and checks whether teh value is in a legal range.

        Args:
            prompt (str):
                prompt to be displayed

            start (str):
                minimum legal value

            end (str):
                maximum legal value

        Returns:
            number (int):
                the number if the user entered something legal, and ``None`` otherwise.
        '''
        number = None
        while True:
            number = input("{} [{}-{}] >".format(prompt, start, end))
            number.rstrip("\n")
            if number.isdigit():
                number = int(number)
                if number < start or number > end:
                    sys.stderr.write("NOT IN RANGE [{}-{}]\n".format(start, end))
                else:
                    break
            elif chr(27) in number or number == '':
                number = None
                break
            else:
                sys.stderr.write("NOT A NUMBER {}\n".format(number))
                number = None
        return number

    def get_ch(self, prompt=""):
        '''Asks for unbuffered single character input, with an optional prompt.

        Args:
            prompt (str):
                Optional text to be displayed as prompt.

        Returns:
            ch (char):
                character pressed by the user. If something gets wrong, returns the *Esc* character.
        '''
        if prompt:
            sys.stderr.write(prompt)
            sys.stderr.flush()
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(sys.stdin.fileno())
        ch = None
        try:
            ch = sys.stdin.read(1)
        except:
            ch = chr(27) # Escape
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def prompt(self):
        '''Writes an self-explanatory prompt text to the terminal.
        '''
        os.system("clear")
        sys.stderr.write(''' ┌─SOURCE───────────────────────────┬─ANNOX────────────────────────────┬─TASK─────────────────────────────┐
''')
        sepchar = '│'
        sepchar_cur = '█'
        fillchar = ' '
        fillchar_cur = '█'

        n_row = -1
        for row in self.prompt_data:
            n_row += 1
            this = [None for i in range(len(row))]
            this_n = [None for i in range(len(row))]
            for i in range(len(row)):
                this[i] = row[i] if row[i] else ''
                this_n[i] = str(n_row + 1) if row[i] else ''
            
            fill = [fillchar for i in range(len(row))]
            sep = [sepchar for i in range(len(row) + 1)]

            for i in range(len(row)):
                if n_row == self.cur[i]:
                    fill[i] = fillchar_cur
                    sep[i] = sepchar_cur
                    sep[i+1] = sepchar_cur

            this_f = [None for i in range(len(row))]
            this_nf = [None for i in range(len(row))]
            for i in range(len(row)):
                this_f[i] = this[i] + (fill[i] * (30 - len(this[i])))
                this_nf[i] = (fill[i] * (3 - len(this_n[i]))) + this_n[i]

            line = ' '
            for i in range(len(row)):
                line += sep[i] + this_nf[i] + fill[i] + this_f[i]
            sys.stderr.write(line + sep[len(row)] + "\n")

        sys.stderr.write(''' └──────────────────────────────────┴──────────────────────────────────┴──────────────────────────────────┘
 ┌─SETTING──────────────────────────┬─VALUE────────────────────────────┐
 │ force compile source             │ {:<3}                              │
 │ force compile annox              │ {:<3}                              │
 └──────────────────────────────────┴──────────────────────────────────┘
'''.format('ON' if self.cur[len(self.index)] else 'OFF', 'ON' if self.cur[len(self.index)+1] else 'OFF'))
        sys.stderr.write(self.message)

    def weave(self, data):
        '''Utility value that prepares data for presenting several columns of options
        on a terminal screen.

        Args:
            data(lists of lists):
                corresponds to a number of lists of options.
        
        Returns:
            woven(list of lists):
                correponds to a table where columns are the lists of options
                and the options occupy rows. The outermost list are the rows. 

            index(dict of dict):
                given column number and then row number as keys yields the name of the item at that slot

            iindex(dict of dict):
                given column number and then the name of an item as keys yields the 
                row number of that item

        '''

        n_rows = max([len(col) for col in data])
        woven = []
        for i in range(n_rows):
            woven.append([col[i] if i < len(col) else None for col in data])

        index = collections.defaultdict(lambda: {}) 
        iindex = collections.defaultdict(lambda: {}) 

        n_row = -1
        for row in woven:
            n_row += 1
            n_col = -1
            for item in row:
                n_col += 1
                if item:
                    index[n_col][n_row] = item
                    iindex[n_col][item] = n_row

        return (woven, index, iindex)
