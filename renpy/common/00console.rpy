# console.rpy 
# Ren'Py console
# Copyright (C) 2012 Shiz, C, delta, PyTom
#
# This program is free software. It comes without any warranty, to the extent permitted by applicable law.
# You can redistribute it and/or modify it under the terms of the Do What The Fuck You Want To Public License, 
# Version 2, as published by Sam Hocevar. See http://sam.zoy.org/wtfpl/COPYING for more details.
#
# Usage:
#  With config.developer set to True, press the key assigned to config.console_keybind (~, the tilde, by default) to open the console.
#  Type 'help' for in-console help. Press the same key again to close the console.
#
# The following configuration variables are offered for customization:
#  - config.console_history_size: the number of commands to store in history. default: 100
#  - config.console_custom_commands: a simple name -> function dictionary for custom commands. Command functions should take a single parameter, the full command and return a tuple of (result, no_error).
#
# The following styles are offered for customization:
#  - _console: the debug console frame.
#
#  - _console_input: the input frame.
#  - _console_prompt: the '>' or '...' text preceding a command input.
#  - _console_input_text: the actual text that is being input by the user.
#
#  - _console_history: the history frame.
#  - _console_history_item: an item frame in the history.
#  - _console_command: a command frame in the command history.
#  - _console_command_text: the actual command text.
#  - _console_result: the result frame from a command in the command history, if applicable.
#  - _console_result_text: the actual result text, if no error occurred.
#  - _console_result_text: the actual result text, if an error occurred.
#
#  - _console_trace: the trace box used to show expression and variable traces.
#  - _console_trace_var: the variable in a trace box.
#  - _console_trace_value: the value in a trace box.


# Configuration and style initalization.
init -1500 python:

    # If true, the console is enabled despite config.developer being False.
    config.console = False

    config.console_history_size = 100
    config.console_commands = { }
    
    # Create default styles. See above for documentation.
    style.create('_console', '_default')
    style._console.background = None
    
    style.create('_console_text', '_default')
    style._console_text.size = 14
    style._console_text.color = "#ffffff"
    
    style.create('_console_input', '_default')
    style._console_input.background = "#00000040"
    style._console_input.xfill = True
    
    style.create('_console_prompt', '_console_text')
    style._console_prompt.minwidth = 25
    style._console_prompt.text_align = 1.0
    
    style.create('_console_input_text', '_console_text')
    style._console_input_text.color = "#fafafa"
    
    style.create('_console_history', '_default')
    style._console_history.background = "#00000000"
    style._console_history.xpos = 0
    style._console_history.ypos = 0
    style._console_history.xpadding = 0
    style._console_history.ypadding = 0
    style._console_history.xfill = True
    style._console_history.yfill = True 
    
    style.create('_console_history_item', '_default')
    style._console_history_item.background = "#00000040"
    style._console_history_item.xpos = 0
    style._console_history_item.ypos = 0
    style._console_history_item.xpadding = 0
    style._console_history_item.ypadding = 0
    style._console_history_item.top_margin = 4
    style._console_history_item.xfill = True
    
    style.create('_console_command', '_default')
    style._console_command.background = "#00000040"
    
    style.create('_console_command_text', '_default')
    style._console_command_text.color = "#ffffff"
    
    style.create('_console_result', '_default')
    style._console_result.background = "#00000000"
    
    style.create('_console_result_text', '_console_text')
    style._console_result_text.color = "#ffffff"
    
    style.create('_console_error_text', '_console_text')
    style._console_error_text.color = "#ff0000"
    
    style.create('_console_trace', '_default')
    style._console_trace.background = "#00000040"
    style._console_trace.xalign = 1.0
    style._console_trace.top_margin = 20
    style._console_trace.right_margin = 20
    
    style.create('_console_trace_var', '_console_text')
    style._console_trace_var.bold = True
    
    style.create('_console_trace_value', '_console_text')

init -1500 python in _console:
    from store import config
    import sys
    import traceback
    import store
    
    class BoundedList(list):
        """
        A list that's bounded at a certain size.
        """
        
        def __init__(self, size):
            self.size = size

        def append(self, value):
            super(BoundedList, self).append(value)
    
            while len(self) >= self.size:
                self.data.pop(0)
        
        def clear(self):
            self[:] = [ ]

    class HistoryEntry(object):
        """
        Represents an entry in the history list.
        """
        
        def __init__(self, command, result=None, is_error=False):
            self.command = command
            self.result = result
            self.is_error = is_error
    
    class ScriptErrorHandler(object):
        """
        Handles error in Ren'Py script.
        """
        
        def __init__(self):
            self.target_depth = renpy.call_stack_depth()
            
        def __call__(self, short, full, traceback_fn):
            he = console.history[-1] 
            he.result = short.split("\n")[-2]
            he.is_error = True

            while renpy.call_stack_depth() > self.target_depth:
                renpy.pop_call()
                
            renpy.jump("_console")


    class DebugConsole(object):
        
        def __init__(self):
            
            self.reset()
            
            self.history = BoundedList(config.console_history_size)
            self.first_time = True
            
        def start(self):
            he = HistoryEntry(None)
        
            message = ""
            
            if self.first_time:      
                message += renpy.version() + " console, originally by Shiz, C, and delta.\n"
                message += "Press <esc> to exit console. Type help for help.\n"
                self.first_time = None
            
            if self.can_renpy():
                message += "Ren'Py script enabled."
            else:
                message += "Ren'Py script disabled."

            he.result = message
            self.history.append(he)

        def reset(self):
        
            # The list of lines that have been entered by the user, but not yet
            # processed.
            self.lines = [ ]

        def interact(self):

            def get_indent(s):
                """
                Computes the indentation for the line following line s.
                """
                
                rv = ""
                
                for i in s:
                    if i == " ":
                        rv += " "
                    else:
                        break

                if s.rstrip().endswith(":"):
                    rv += "    "

                if not s.rstrip():
                    rv = rv[:-4]
                    
                return rv
            
            renpy.game.context().exception_handler = None
                    
            # Prompt the user for a line of code.
            if self.lines:
                indent = get_indent(self.lines[-1])
            else:
                indent = ""
                
            default = indent
            renpy.show_screen("_console", lines=self.lines, indent=indent, default=default, history=self.history, _transient=True)
            line = ui.interact()

            self.lines.append(line)

            if get_indent(line) != "":
                return

            lines = self.lines
            self.reset()
            
            self.run(lines)
            
        def can_renpy(self):
            """
            Returns true if we can run Ren'Py code.
            """
            
            return renpy.game.context().rollback
            
        def format_exception(self):
            etype, evalue, etb = sys.exc_info()
            return traceback.format_exception_only(etype, evalue)[-1]
            
        def run(self, lines):

            line_count = len(lines)
            code = "\n".join(lines)

            he = HistoryEntry(code)
            self.history.append(he)

            try:

                # If we have 1 line, try to parse it as a command.
                if line_count == 1:
                    block = [ ( "<console>", 1, code, [ ]) ]
                    l = renpy.parser.Lexer(block)
                    l.advance()
                    
                    # Command can be None, but that's okay, since the lookup will fail.
                    command = l.name()
                    
                    command_fn = config.console_commands.get(command, None)

                    if command_fn is not None:
                        he.result = command_fn(l)
                        return
                    
                error = None
                    
                # Try to run it as Ren'Py.
                if self.can_renpy():
                        
                    # TODO: Can we run Ren'Py code?
                    name = renpy.load_string(code + "\nreturn")

                    if name is not None:
                        renpy.game.context().exception_handler = ScriptErrorHandler()
                        renpy.call(name)
                    else:
                        error = "\n\n".join(renpy.get_parse_errors())
                
                # Try to eval it. 
                try:
                    renpy.python.py_compile(code, 'eval')
                except:
                    pass
                else:
                    result = renpy.python.py_eval(code)
                    he.result = repr(result)
                    return
 
                # Try to exec it.
                try:
                    renpy.python.py_compile(code, "exec")
                except:
                    if error is None:
                        error = self.format_exception()
                else:
                    renpy.python.py_exec(code)
                    return
                        
                if error is not None:
                    he.result = error
                    he.is_error = True

            except renpy.game.CONTROL_EXCEPTIONS:
                raise

            except:
                he.result = self.format_exception()
                he.is_error = True


    console = None

    traced_expressions = [ ]

    def enter():
        """
        Called to enter the debug console.
        """

        if console is None:
            return

        console.start()

        if renpy.game.context().rollback:
            try:
                renpy.rollback(checkpoints=0, force=True, greedy=False, label="_console")
            except renpy.game.CONTROL_EXCEPTIONS:
                raise
            except:
                pass
                
        renpy.call_in_new_context("_console")

init 1500 python in _console:
    
    if config.developer or config.console:
        console = DebugConsole()
        
init -1500 python in _console:

    def command(help=None):
        def wrap(f):
            f.help = help
            config.console_commands[f.__name__] = f
            return f

        return wrap

    @command("help: show this help")
    def help(l):
        keys = list(config.console_commands.iterkeys())
        keys.sort()
        
        rv = "commands:\n"
        
        for k in keys:
            f = config.console_commands[k]
            if f.help is None:
                continue
                
            rv += " " + f.help + "\n" 
        
        return rv.rstrip()
        
    @command()
    def halp(l):
        return help(l).replace("e", "a")
        
    @command("clear: clear the console history")
    def clear(l):
        console.history[:] = [ ]

    @command("exit: exit the console")
    def exit(l):
        renpy.jump("_console_return")
        
    @command()
    def quit(l):
        renpy.jump("_console_return")
 
    @command("reload: reload the game")
    def reload(l):
        store._reload_game()
        
    @command()
    def R(l):
        store._reload_game()
        
    @command("watch <expression>: watch a python expression")
    def watch(l):
        expr = l.rest()
        expr.strip()
        renpy.python.py_compile(expr, 'eval')
        
        traced_expressions.append(expr)
        renpy.show_screen("_trace_screen")

    @command("unwatch <expression>: stop watching an expression")
    def unwatch(l):
        expr = l.rest()
        expr.strip()
        
        if expr in traced_expressions:
            traced_expressions.remove(expr)

    @command("unwatchall: stop watching all expressions")
    def unwatchall(l):
        traced_expressions[:] = [ ]
        renpy.hide_screen("_trace_screen")
        
        
    @command("jump <label>: jumps to label")
    def jump(l):
        label = l.name()
        
        if not console.can_renpy():
            raise Exception("Ren'Py script not enabled. Not jumping.")
            
        if not renpy.has_label(label):
            raise Exception("Label %s not found." % label)
            
        renpy.pop_call()
        renpy.jump(label)
        

screen _console:
    # This screen takes as arguments:
    #
    # lines
    #    The current set of lines in the input buffer.
    # indent
    #    Indentation to apply to the new line.
    # history
    #    A list of command, result, is_error tuples. 
    zorder 1500
    modal True

    frame:
        style "_console"
        
        has vbox

        # Draw the current input.
        frame style "_console_input":
        
            has vbox
            
            for line in lines:
                hbox:
                    spacing 4
                    
                    if line[:1] != " ":
                        text "> " style "_console_prompt"
                    else:
                        text "... " style "_console_prompt"
                    
                    text "[line!q]" style "_console_input_text"
                    
            hbox:
                spacing 4
                
                if not indent:
                    text "> " style "_console_prompt"
                else:
                    text "... " style "_console_prompt"
                                
                input default default style "_console_input_text"


        # Draw historical console input.
        $ rev_history = list(history)
        $ rev_history.reverse()
        
        frame style "_console_history":
            
            has viewport:
                mousewheel True
                
            has vbox:
                xfill True
                
            for he in rev_history:
                
                frame style "_console_history_item":
                    has vbox
                        
                    if he.command is not None:
                        frame style "_console_command":
                            xfill True
                            text "[he.command!q]" style "_console_command_text"
                    
                    if he.result is not None:
                        
                        frame style "_console_result":
                            if he.is_error:
                                text "[he.result!q]" style "_console_error_text"
                            else:
                                text "[he.result!q]" style "_console_result_text"
    
    key "game_menu" action Jump("_console_return")
    

screen _trace_screen:

    zorder 1501

    if _console.traced_expressions:
    
        frame style "_console_trace":
            
            vbox:
                
                for expr in _console.traced_expressions:
                    python:
                        try:
                            value = repr(eval(expr))
                        except:
                            value = "eval failed"
                    
                    hbox:
                        text "[expr!q]: " style "_console_trace_var"
                        text "[value!q]" style "_console_trace_value"
    
# The label that is called by _console.enter to actually run the console.
# This can be called in the current context (for normal Ren'Py code) or 
# in a new context (in menus).
label _console:
    
    while True:
        python in _console:
            console.interact()

label _console_return:
    return
