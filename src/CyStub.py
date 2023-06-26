import click
from StubCompiler import PyiWriter
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
import os 
from pathlib import Path 


def compile_tree(source_desc:FileSourceDescriptor,pxd:bool,scope, full_module_name, ctx:Context):
    return ctx.parse(source_desc=source_desc, pxd=pxd, scope=scope, full_module_name=full_module_name)

def make_compilation_tree(source:str,context:Context,full_module_name:str=None):
    source_ext = os.path.splitext(source)[1]
    full_module_name = full_module_name or context.extract_module_name(source, None)
    return compile_tree(FileSourceDescriptor(source),source_ext.endswith("pxd"),ctx=context,full_module_name=full_module_name,scope=context.cython_scope)


def make_tree_from_file(file:str,options:CompilationOptions=None):
    if not options:
        options = CompilationOptions(defaults=default_options)
    return make_compilation_tree(file,options.create_context())

# TODO Vizonex Make Compilation Options mergable with click for any of the provided arguments we need to use...


@click.command
@click.argument("pyx_and_pxds",type=click.Path(True, path_type=str),nargs=-1)
@click.option("--inplace/--no-inplace",is_flag=True,default=False,help="Output to the directory you executed this command from instead form the given output folder...")
@click.option("--use-typing/--no-typing","use_typing",is_flag=True,help="Uses the typing module if it is not already imported for use with other typehints...")
@click.option("--output","-o",type=click.Path(False,file_okay=False,path_type=str),default="out",help="Changes the save folder loaction for the compiled pyi files default direcory is named \"out\"")
def compile_cython_files(pyx_and_pxds:tuple[str, ...],use_typing:bool,output:str,inplace:bool):
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
        module = make_tree_from_file(file)
        writer = PyiWriter()

        if use_typing:
            writer.use_generator_import = True

        writer(module)
        with (path / (file.removesuffix(".pyx").removesuffix(".pxd") + ".pyi")).open("w") as w:
            w.write(writer.pyi_code)
        
    print(f"Your files were saved to directory: {output!r}")

if __name__ == "__main__":
    compile_cython_files()


