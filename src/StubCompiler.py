from Cython.CodeWriter import DeclarationWriter
from contextlib import contextmanager
from Cython.Compiler import Version

# Inspired by and based around https://github.com/cython/cython/pull/3818
# by with some less lazy changes to it and maybe a few additions and optimzations...

# NOTE This project is really my rough draft for the big pull request that 
# I'm planning on doing once this works and is done (No crazy bugs) I'll start working on the PR...

from Cython.Compiler.Nodes import *
from Cython,Compiler.ExprNodes import * 
from Cython.Compiler.PyrexTypes import type_identifier
from Cython.Compiler.ModuleNode import ModuleNode
from Cython.Compiler.PyrexTypes import CIntType, CArrayType

from typing import Optional, Callable

from Cython.Compiler.Nodes import CClassDefNode, CFuncDefNode, SingleAssignmentNode
import sys


if sys.version_info >= (3, 9):
    typing_module = "typing"
else:
    typing_module = "typing_extensions"




def translate_annotations(node, type_conv:Callable[..., str]) -> list[str]:
    func_annotations = []
    for arg, py_arg in zip(node.type.args, node.declarator.args):

        annotation = ""
        # TODO Maybe have a flag to check if were currently using a class inside of here as an extra check?
        if arg.name == "self":
            annotation = arg.name
        else:
            annotation = "%s: %s" % (arg.name, type_conv(arg, node))

        if not py_arg.default or not py_arg.default_value:
            # TODO See if there's a better way to go about finding an ellipsis...
            annotation += " = ..."
        func_annotations.append(annotation)
    


# TODO (Vizonex) Maybe make a New variable Registry class to help with Registry managment?

class VariableStack:
    """Used to help store variables required for later use elsewhere..."""
    def __init__(self,name:str) -> None:
        self.name = name 
        self.empty:bool = True

# NOTE I'm Currently using VS Code to write this so it can cause me some bigger issues 
# to have access to any variables via tool-tip or no access by hoverlist. 
# If you have a problem with any of my type-hints provided 
# I can always remove them when I'm done making my Pull Request - Vizonex

def ctype_name(arg,node:Node):

    # TODO Make a better conversion function...
    if arg.type and hasattr(arg.type, "name"):
        # Used C declared type...
        # TODO see about using a check to see if users wants to include cython's shadow varaibales...
        return arg.type.name
        
    py_name = node.type.return_type.py_type_name()
    if "(int, long)":
        return "int"
    
    return py_name

# Instead of doing it into C we're doing it backwards...
def translate_base_type_to_py(
    base:CSimpleBaseTypeNode, 
    use_typing:bool=False, 
    cython_shadow:bool=False # cython shadow typehints feature coming soon...
    ):

    if not base.is_basic_c_type:
        # Likely that it's already a python object that's being handled...
        return base.name 
    
    elif base.name == "bint":
        # TODO Implement as bool unless cython_shadow's flag is set...
        return "bool"
    
    ctype = PyrexTypes.simple_c_type(base.signed, base.longness,base.name)

    # TODO (Vizonex) implement Pyrex to cython shadow typehints converter...
    if isinstance(ctype, PyrexTypes.CIntType):
        return "int"
    
    elif isinstance(ctype, PyrexTypes.CFloatType):
        return "float"
    
    # return "Any" For now unless typing is ignored, I will change this in the future...
    return "Any" if use_typing else None


# FIXME I'm planning on dropping these different node typehints in the future 
# if they cannot be handled by ealier versions than 3.9 of python... 
# there currently just here to help me figure out how to write this all 
# down since Im working inside of Vs Code.


class PyiWriter(DeclarationWriter):
    """Used By Cython to help Write stubfiles
    this comes in handy for ides like visual 
    studio code which suffer from having 
    no code acess to the compiled python 
    modules..."""

    # "_" used to show that it shouldn't be accessed outside of this module...
    _forbiddenFunctionNames = frozenset((
            "__cinit__",
            "__dealloc__",
            "__getbuffer__",
            "__releasebuffer__",
            "__getreadbuffer__",
            "__getwritebuffer__",
            "__getsegcount__",
            "__getcharbuffer__"
    ))

    def __init__(self, result=None):
        # TODO (Vizonex) Maybe have arguments 
        # for how shadow.pyi is implemented be passed into here 
        # if we want them to be even imported at 
        # all and if so C Variables should be translated as such...
        super().__init__(result)

        # These will be our containers for variables and nodes alike...
        self.stack: list[VariableStack] = []

        self.use_typing : bool = False
        """if true we must import typing's generator typehint..."""


    # -- Extra line handlers --
    # TODO Maybe add indent_next_lines to the main cython module in the final PR to be more organized if proven to be faster?
    @contextmanager
    def indent_next_lines(self):
        """Made for use as a context manager it is identical to doing the following
    ::

        self.indent()
        self.putline("# this is an example")
        self.dedent()
        
    ::
        """
        self.indent()
        yield 
        self.dedent()


    def emptyline(self):
        self.result.putline("")

    def visit(self, obj):
        return self._visit(obj)
    
    def visitchildren_indented(self, parent_node:Node, attrs:Optional[dict] = None):
        """Visits Node's children but with 4 spaces moved over when writing below is an example to visualize
    what's going on...
    ::

        # example...
        class Written:
            # < - we are here...
    ::"""
    
        with self.indent_next_lines():
            self.visitchildren(parent_node, attrs)

    def visit_ModuleNode(self, node: ModuleNode):
        # visit the children and start looking for anything usefull...
        self.visitchildren(node)

    def is_forbidden(self, name:str):
        """Functions that are meant to be in C only can 
        be checked here to see if they need to be skipped"""
        # this is an imporvement based on 
        return name in self._forbiddenFunctionNames or name.startswith("__pyx")
    
    def visit_CImportStatNode(self,node):
        return node

    

    def visit_CVarDefNode(self,node: CVarDefNode):

        # if they aren't public or readonly then the variable inside of a class 
        # or outisde should be ignored by default...
        if node.visibility in ["readonly", "public"]:

            # TODO (Vizonex) handle ctypedef nodes and give them a 
            # new type-registry system to help translate all incomming variables... 

            # TODO (Vizonex) Maybe Make all C variables hidden by default instead excluding Class Objects found?.... 
            py_name = translate_base_type_to_py(node.base_type, self.use_typing)
            
            # Final check...
            if py_name:
                # Write in all the objects listed on the defined line...
                for d in node.declarators:
                    self.putline("%s: %s" % (d.name, py_name))
    
        return node


    def atModuleRoot(self):
        return len(self.stack) == 1

    def set_Stack_As_Occupied(self):
        """Sets all the stack's flags to occupied..."""
        for variable in self.stack:
            variable.empty = False
    
    @property
    def LastRegisteredVariable(self):
        return self.stack[-1]


    def visit_ImportNode(self, node: ImportNode):
        module_name:str = node.module_name.value
        self.set_Stack_As_Occupied()

        if not node.name_list:
            self.putline("import %s" % module_name) 
        else:
            all_imported_children = ", ".join((arg.value for arg in node.name_list.args))

            if node.level > 0:
                # I couldn't think of a better name...
                ext_module_branch = "." * node.level
                # alter module's name...
                module_name = "%s%s" % (ext_module_branch , module_name)

            self.putline("from %s import %s" % (module_name, all_imported_children))

        return node

    # TODO add a cython shadow variable registry system to help import them all 
    # to the frontend variables nessesary to the pyi stub along with a watermark...

    def visit_SingleAssignmentNode(self, node: SingleAssignmentNode):
        if not isinstance(node.rhs, ImportNode):
            return node 

        module_name = node.rhs.module_name.value

        # TODO Vizonex maybe come up with a faster method for 
        # setting variables to occupied?
        self.set_Stack_As_Occupied()

        # get parent_module by parsing it...
        parent_module = module_name

        pos = module_name.find('.')

        if pos != -1:
            parent_module = module_name[:pos]
        
        imported_name = node.lhs.name

        if parent_module == imported_name:
            self.visitchildren(node)
            return node

        self.putline("import %s as %s" % (module_name, imported_name))
        return node 
    
    # Optimized orginal code by having there be one function to take 
    # the place of two of them I could see what scoder meant when said this needed to be cleaned up...
    def write_classNode(self, node:ClassDefNode):
        """wirtes a new class to a stub file..."""

        # TODO Maybe Add a Subclass checker to see if the variable was subclassed?... 
        self.putline("class %s:" % node.class_name)
        self.stack.append(VariableStack(node.class_name))

        # visit the classnode's children...
        self.visitchildren_indented(node)

        # check that we didn't screw up as a safety measure...
        assert self.LastRegisteredVariable.name == node.class_name

        if self.LastRegisteredVariable.empty:
            self.set_Stack_As_Occupied()
        
            with self.indent_next_lines():
                self.putline("pass")

        self.stack.pop()
        self.emptyline()
        return node

    def visit_CClassDefNode(self, node: CClassDefNode):
        return self.write_classNode(node)
    
    def visit_PyClassDefNode(self, node:PyClassDefNode):
        return self.write_classNode(node)

    def visit_CFuncDefNode(self, node: CFuncDefNode):
        # cdefs are for C only...

        # TODO Write parts of this as a sperate function just to be safe...
        if not node.overridable:
            return node 

        self.set_Stack_As_Occupied()

        func_name = node.declared_name()

        if self.is_forbidden(func_name):
            return node
        

        self.startline()
        self.put("def %s(" % func_name)

        

        # Cleaned up alot of what the orginal author did by making a new function
        self.put(", ".join(translate_annotations(node, ctype_name)))
        # TODO Maybe Try passing docstrings in the future for vscode users' sake or have it aslo be a compiler argument?...
        self.endline(") -> %s: ..." % ctype_name(node.type.return_type))
        return node

    def print_Decorator(self, decorator):

        # NOTE Not implemented and afaik not required..
        if isinstance(decorator, CallNode):
            return

        self.startline("@")

        if isinstance(decorator, NameNode):
            self.put("%s" % decorator.name)
        else:
            assert isinstance(decorator, AttributeNode)
            self.put("%s.%s" % (decorator.obj.name,decorator.attribute))
        
    def annotation_Str(self, annotation:ExprNode) -> str:
        return annotation.name


    def print_DefNode(self,node:DefNode):
        func_name = node.name

        if self.hide_Function(func_name):
            return node

        self.set_Stack_As_Occupied()

        
        def argument_str(arg:CArgDeclNode):
            value = arg.declarator.name
            if arg.annotation is not None:
                value += (": %s" % self.annotation_Str(arg.annotation))

            if (arg.default is not None or
                arg.default_value is not None):
                value += " = ..."

            return value
        
        # TODO (Vizonex) See if "*," or "/," or an "Ellipsis" 
        # can be passed through and accepted into all the stub 
        # files as a unittest.
        
        async_name = "async " if node.is_async_def or getattr(node,"is_coroutine", None) else ""

        if node.decorators is not None:
            for decorator in node.decorators:
                self.print_Decorator(decorator.decorator)

        self.startline("%sdef %s(" % (async_name, node.name))

        args = []

        # Ordinary arguments:
        args += (argument_str(arg) for arg in node.args)

        # Star(star) arguments:
        star_arg = node.star_arg
        starstar_arg = node.starstar_arg

        if star_arg is not None:
            args.append("*%s" % star_arg.name)

        if starstar_arg is not None:
            args.append("**%s" % starstar_arg.name)

        self.put(", ".join(args))

        retype = node.return_type_annotation

        if retype is not None:
            # This is a little bit different than the original pull request 
            # since I wanted there to be propper typehints given to all the 
            # objects which is why I added the "Generator" as a typehint & keyword...
            annotation = self.annotation_Str(retype)
            if (node.is_generator and not annotation.startswith("Generator") and self.use_typing):
                # TODO (Vizonex) figure out how the extract the other two required variables...
                # Also the function could be an Iterator but I hadn't added the "__iter__" function name-check just yet...
                self.put(") -> Genertor[ %s, None , None]:..." % annotation)
            else:
                self.put(") -> %s: ..." % annotation)

        else:
            self.put("): ...")

        self.endline()

    def visit_DefNode(self, node:DefNode):
        self.print_DefNode(node)
        return node

    def visit_ExprNode(self,node:ExprNode):
        if not self.atModuleRoot():
            return node
        
    def visit_SingleAssignmentNode(self,node:SingleAssignmentNode):
        if isinstance(node.rhs,ImportNode):
            self.visitchildren(node)
            return node

        self.set_Stack_As_Occupied()

        name = node.lhs.name
        if node.lhs.annotation:
            # TODO Check if this is still existant...
            self.putline("%s: %s = ..." % (name, node.lhs.annotation.string.value))
        else:
            self.putline("%s = ...")

    def visit_ExprStatNode(self,node:ExprStatNode):
        if isinstance(node.expr, NameNode):
            # Might change name to registry
            self.set_Stack_As_Occupied()

            expr = node.expr
            name = expr.name
            if expr.annotation:
                self.putline("%s: %s" % (name, self.annotation_Str(expr.annotation)))
            else:
                self.putline("%s" % name)
    
    def visit_DefNode(self, node):
        self.print_DefNode(node)
        return node

    def visit_Node(self, node:Node):
        self.visitchildren(node)
        return node

    
    def __call__(self, root:Node, _debug:bool = False):
        # Top Notice will likely chage once I've made a full on pull request...
        self.putline("# Python stub file generated by Cython %s And CyStub.py" % Version.watermark)
        self.emptyline()
        
        # Check if using is ok with using type-hints before use...
        if self.use_typing:
            self.putline("from %s import Generator" % typing_module)

        node = self._visit(root)
        # added a new debugger incase needed for now...
        if _debug:
            print("-- Pyi Result --")
            print(self.result)
            print("-- End Of Pyi Result --")

        return node

    @property
    def pyi_code(self) -> str:
        return "\n".join(self.result.lines)
    
