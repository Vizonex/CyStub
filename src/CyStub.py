import click
from StubCompiler import PyiWriter
from Cython.Compiler.Errors import init_thread
from Cython.Compiler.Main import (
    # These are used to get the parser to 
    # move to the steps we need to get it to 
    # in order to start triggering the parsing 
    # of the modules we want to use...
    Context, 
    FileSourceDescriptor, 
    default_options, 
    CompilationOptions
)

from Cython.Compiler.CythonScope import create_cython_scope, ModuleScope

# NOTE (Vizonex): I am Building a Special Function Visitor Soon for Making return annotations. 
# This is used for what I'm calling return-type-recovery for making Union Typehints...
# from FunctionVisitor import FunctionVisitor
import os 
from pathlib import Path 
from typing import Optional


def compile_tree(source_desc:FileSourceDescriptor,pxd:bool, scope, full_module_name, ctx:Context):
    return ctx.parse(source_desc=source_desc, pxd=pxd, scope=scope, full_module_name=full_module_name)

def make_compilation_tree(source:str,context:Context,full_module_name:Optional[str]=None):
    source_ext = os.path.splitext(source)[1]
    full_module_name = full_module_name or context.extract_module_name(source, None)
    return compile_tree(FileSourceDescriptor(source),source_ext.endswith(".pxd"), ctx=context, full_module_name=full_module_name, scope=context.cython_scope)


def make_tree_from_file(file:str,options:Optional[CompilationOptions]=None):
    if not options:
        options = CompilationOptions(defaults=default_options)
    ctx = Context.from_options(options)
    init_thread()
    return make_compilation_tree(file,ctx) , ctx

# TODO Vizonex Make Compilation Options mergable with click for any of the provided arguments we need to use...


@click.command
@click.argument("pyx_and_pxds",type=click.Path(True, path_type=str),nargs=-1)
@click.option("--inplace/--no-inplace",is_flag=True, default=False,help="Output to the directory you executed this command from instead form the given output folder...")
@click.option("--use-typing/--no-typing","use_typing", is_flag=True,default=True,help="Uses the typing module if it is not already imported for use with other typehints...")
@click.option("--output", "-o",type=click.Path(False,file_okay=False,path_type=str), default="out", help="Changes the save folder loaction for the compiled pyi files default direcory is named \"out\"")
@click.option("-c++", "-cpp/-c","cpp",is_flag=True,default=False,help="sets compiler to use c++ default is disabled which will use C instead..")
def compile_cython_files(pyx_and_pxds:tuple[str, ...],use_typing:bool,output:str,inplace:bool,cpp:bool):
    """Compiles cython modules to readable stubfiles using cython's provided parsers and code tools..."""
    if not os.path.exists(output) and not inplace:
        os.mkdir(output)
        path = Path(output)

    elif not inplace:
        path = Path(output)

    else:
        path = Path(os.getcwd())

    for file in pyx_and_pxds:
        assert file.endswith((".pyx",".pxd"))
        print(f"compiling {file!r}...")
        
        module , ctx = make_tree_from_file(file, options = CompilationOptions(cplus=cpp))
        scope :ModuleScope= create_cython_scope(ctx)
        module.scope = scope
        # mdt = (ctx)
        # mdt(module)
    

        writer = PyiWriter(ctx,scope)
        # writer(module,_debug=True)

        # print(PrintTree()(module))
        with (path / (file.removesuffix(".pyx").removesuffix(".pxd") + ".pyi")).open("w") as w:
            w.write(writer.pyi_code)

    print("finished compiling files")
    if not inplace:
        print(f"Your files were saved to directory: {output!r}")
    
if __name__ == "__main__":
    compile_cython_files()




