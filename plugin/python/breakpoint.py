import base64
import log

class Store:

    def __init__(self):
        self.breakpoints = {}
        self.api = None

    def link_api(self,api):
        self.api = api
        log.Log("Registering "+str(len(self.breakpoints))+\
                " breakpoints with the debugger",\
                log.Logger.DEBUG)
        for id, bp in self.breakpoints.iteritems():
            self.api.breakpoint_set(bp.get_cmd())


    def unlink_api(self):
        self.api = None

    def add_breakpoint(self,breakpoint):
        log.Log("Adding breakpoint "+\
                str(breakpoint),\
                log.Logger.DEBUG)
        self.breakpoints[str(breakpoint.get_id())] = breakpoint
        breakpoint.on_add()
        if self.api is not None:
            self.api.breakpoint_set(breakpoint.get_cmd())

    def remove_breakpoint(self,breakpoint):
        self.remove_breakpoint_by_id(\
                breakpoint.get_id())

    def remove_breakpoint_by_id(self,id):
        id = str(id)
        log.Log("Removing breakpoint "+\
                str(self.breakpoints[id]),\
                log.Logger.DEBUG)
        self.breakpoints[id].on_remove()
        del self.breakpoints[id]

    def clear_breakpoints(self):
        for id, bp in self.breakpoints.iteritems():
            self.remove_breakpoint_by_id(id)
        self.breakpoints = {}

    def find_breakpoint(self,file,line):
        found = None
        for id, bp in self.breakpoints.iteritems():
            if bp.type == "line":
                if bp.get_file() == file and\
                        bp.get_line() == line:
                    found = bp.get_id()
                    break
        return found


class BreakpointError(Exception):
    pass

class Breakpoint:
    """ Abstract factory for creating a breakpoint object.

    Use the class method parse to create a concrete subclass
    of a specific type.
    """
    type = None
    id = 11000

    def __init__(self,ui):
        self.id = Breakpoint.id
        Breakpoint.id += 1 
        self.ui = ui

    def get_id(self):
        return self.id

    def on_add(self):
        pass

    def on_remove(self):
        pass

    @classmethod
    def parse(self,ui,args):
        args = args.strip()
        if len(args) == 0:
            """ Line breakpoint """
            row = ui.get_current_row()
            file = ui.get_current_file()
            return LineBreakpoint(ui,file,row)
        else:
            arg_parts = args.split(' ')
            type = arg_parts.pop(0)
            type.lower()
            if type == 'conditional':
                row = ui.get_current_row()
                file = ui.get_current_file()
                if len(arg_parts) == 0:
                    raise BreakpointError, "Conditional breakpoints " +\
                            "require a condition to be specified"
                cond = " ".join(arg_parts)
                return ConditionalBreakpoint(ui,file,row,cond)
            elif type == 'exception':
                if len(arg_parts) == 0:
                    raise BreakpointError, "Exception breakpoints " +\
                            "require an exception name to be specified"
                return ExceptionBreakpoint(ui,arg_parts[0])
            elif type == 'return':
                if len(arg_parts) == 0:
                    raise BreakpointError, "Return breakpoints " +\
                            "require a function name to be specified"
                return ReturnBreakpoint(ui,arg_parts[0])
            elif type == 'call':
                if len(arg_parts) == 0:
                    raise BreakpointError, "Call breakpoints " +\
                            "require a function name to be specified"
                return CallBreakpoint(ui,arg_parts[0])

    def get_cmd(self):
        pass

    def __str__(self):
        return "["+self.type+"] "+str(self.id)

class LineBreakpoint(Breakpoint):
    type = "line"

    def __init__(self,ui,file,line):
        Breakpoint.__init__(self,ui)
        self.file = file
        self.line = line

    def on_add(self):
        self.ui.place_breakpoint(\
                self.id,\
                self.file,\
                self.line)
    
    def on_remove(self):
        self.ui.remove_breakpoint(self.id)

    def get_line(self):
        return self.line

    def get_file(self):
        return self.file

    def get_cmd(self):
        cmd = "-t " + self.type
        cmd += " -f " + self.file
        cmd += " -n " + str(self.line)
        return cmd

class ConditionalBreakpoint(LineBreakpoint):
    type = "conditional"

    def __init__(self,ui,file,line,condition):
        LineBreakpoint.__init__(self,ui,file,line)
        self.condition = condition

    def get_cmd(self):
        cmd = LineBreakpoint.get_cmd(self)
        cmd += " -- " + base64.encodestring(self.condition)
        return cmd

class ExceptionBreakpoint(Breakpoint):
    type = "exception"

    def __init__(self,ui,exception):
        Breakpoint.__init__(self,ui)
        self.exception = exception

    def get_cmd(self):
        cmd = "-t " + self.type
        cmd += " -x " + self.exception
        return cmd

class CallBreakpoint(Breakpoint):
    type = "call"

    def __init__(self,ui,function):
        Breakpoint.__init__(self,ui)
        self.function = function

    def get_cmd(self):
        cmd = "-t " + self.type
        cmd += " -m " + self.function
        return cmd

class ReturnBreakpoint(CallBreakpoint):
    type = "return"