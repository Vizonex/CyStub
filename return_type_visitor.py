"""
THV or Type-Hint-Visitor is Reserach into Making and resolving Typehint Return variables
after each standard run that is made... 

See: https://github.com/cython/cython/wiki/HackerGuide#id12
"""

from Cython.Compiler.Visitor import ScopeTrackingTransform, CythonTransform
from Cython.Compiler.ParseTreeTransforms import SkipDeclarations
from Cython.Compiler.Nodes import * 
from Cython.Compiler.ExprNodes import * 
from Cython.Compiler import PyrexTypes
from Cython.Compiler.Symtab import Entry
from Cython.Compiler.CythonScope import ModuleScope
from contextlib import contextmanager


# I have put together about 5 re-writes so far trying to make the perfect
# setup and this one was the closest towards my goals so I have added this 
# code snippet mainly to show and demonstrate that it is possible to return 
# return annotations I will upload how I get these to execute eventually but 
# it has to go rather deep into cython's pipeline in order for the scopes to 
# register the entries which makes this easier than it was using the raw node 
# tree when first produced and raw. - Vizonex 

# You will find some of these names that I've mentioned in my dev journal...

class NameRecursor:
    """Used to define Names to functions as they are visited and left. 
    This helps make readable keywords to functions, classes and classes with class functions to use throught the code"""
    def __init__(self) -> None:
        self._name = ""
        self.stack : list[str] = []
        self.stack_has_class = 1

    def update_name(self):
        self._name = ".".join(self.stack)

    def dec(self):
        self.stack.pop()
        if self.stack_has_class and len(self.stack) < 1:
            self.stack_has_class = 0
        self.update_name()
        return self._name

    def inc(self, name:str):
        self.stack.append(name)
        self.update_name()
        return self._name
    
    def last_stacked(self):
        """Pulls from the last function name in the stack used 
        to lookup names for the module's scope"""
        return self.stack[-1]

    # To be less confusting...
    set_func = inc 

    def has_class(self):
        return len(self.stack) > 1 or self.stack_has_class

    def get_class(self):
        return self.stack[0]

    def set_class(self, class_name:str):
        self.stack_has_class = 1
        self.inc(class_name)
    

# Inspired by the Cython's Scope-Visitor but made for a much different Purpose
# which is to propperly track down all return type variables and later define 
# thier return annotations...

class NamedVisitor(ScopeTrackingTransform, SkipDeclarations):
    """Used to help subclass different Visitors with their propperly given names
    so that when it comes to make all return annotatins they can all be given..."""
    
    # current_name      Stores information about the current 
    #                   path to the function being currenlty
    #                   stored to be later called upon....

    # nr                The NameRecursor responsible for controling 
    #                   What name based on object path is being recursed via '.'
    

    def __init__(self, context):
        self.nr = NameRecursor()
        self.current_name = ""
        super().__init__(context)


    def add_new_func(self):
        """Used to declare function definitions to a return table"""
        pass
    
    @contextmanager
    def recurse_name(self, name:str):
        """Used to yield currently known information about a function's path to execution"""
        self.current_name = self.nr.inc(name)
        self.add_new_func()
        yield 
        self.current_name = self.nr.dec()

    def visit_CClassDefNode(self, node):
        with self.recurse_name(node.class_name):
            return super().visit_CClassDefNode(node)


    def visit_PyClassDefNode(self, node):
        with self.recurse_name(node.name):
            return super().visit_PyClassDefNode(node)
   

    def visit_FuncDefNode(self, node):
        if isinstance(node, CFuncDeclaratorNode):
            return 
        if hasattr(node,"name"):
            name = node.name
        else:
            name = node.entry.name
        with self.recurse_name(name):
            return super().visit_FuncDefNode(node)
   


# TODO Modify using cython's pure python tools for faster complations...


class ReturnInfo(object):
    """Handles return information"""
    def __init__(self) -> None:
        self.types:list[PyrexTypes.PyrexType] = []
        self.is_generator = 0
    
    def add(self, type:PyrexTypes.PyrexType):
        self.types.append(type)

    def set_as_generator(self):
        self.is_generator = 1
    
    def copy_return_types(self):
        """Used to copy rich return types into another function"""
        return self.types.copy()


class ReturnTable:
    """A Simplistic way to carry return types for functions"""
    # table     dict[str, list[PyrexTypes.PyrexType]]   Used to Carry out
    #           function definitions to possible return values to later 
    #           write return annotations for missing functions that dont have them inplace

    def __init__(self) -> None:
        self.table:dict[str, ReturnInfo] = {}

    def new_function(self, func:str):
        # assert is currently for debugging only...
        assert not self.table.get(func) , f"{func!r} was already reigistered!"
        self.table[func] = ReturnInfo()
    
    def add_return_type(self, func:str, type:PyrexTypes.PyrexType):
        self.table[func].add(type)

    def add_yield_type(self, func:str, type:PyrexTypes.PyrexType):
        info = self.table[func]
        if not info.is_generator:
            info.set_as_generator() 
        info.add(type)
    
    def clone_return_types(self, func:str, return_call:str):
        """Used to gather rich typehints out of certain groups of functions"""
        self.table[func].types.extend(self.table[return_call].copy_return_types())



class ReturnTypeFinder(NamedVisitor):
    """Handles a return type table to handle all missing return annotations 
    based on a table interlaced with return type Variables to use based on what 
    the `return` and `yield` keywords are able to find... 
    
    NOTE: Some information like Class init () calls maybe ignored in a later stage of writing 
    to the pyi-wrier so something that should be pointed out

    All Functions even if only C Defined are also refrenced for checking for return types if
    absolutely required!
    """

    # return_table   ReturnTable   A table that carries return-type-hint information to carry low-level 
    #                              to later help with resolving missing return annotations 

    module_scope = None
    return_table = None 

    def __init__(self, context):
        self.return_table = ReturnTable()
        super().__init__(context)

    def __call__(self, node):
        self.module_scope:ModuleScope = node.scope
        return self.visit_Node(node)
    
    def add_new_func(self):
        """Used to call in and add in a new function definition"""
        self.return_table.new_function(self.current_name)
    
    def visit_ReturnStatNode(self, node:ReturnStatNode):
        # TODO Improve naming the types if it is in fact possible...
        self.return_table.add_return_type(self.current_name, node.return_type)
        
    def visit_YieldExprNode(self, node:YieldExprNode):
        # XXX Still bruteforcing for a good check system on this part
        if node.arg:
            # print(node.arg.__dict__)

            scope:ClosureScope = self.scope_node.local_scope
            # currently debugging these data objects to come up with a solution to extract possible type objects...
            print(scope.arg_entries)
            # self.return_table.add_yield_type(self.current_name, )
        else:
            # used to try and retain rich typehints...
            self.return_table.add_yield_type(self.current_name, PyrexTypes.c_void_type)

