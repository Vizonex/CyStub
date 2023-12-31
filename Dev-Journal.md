## Dev Journal & Progress

- 6/28/2023 - I already have tested this tool on smaller files which work very
well however tools like `selectolax` and `pyimgui's core.pyx` files need some work to accomplish. There's still 
a few more nodes left that need attention especially when extracing the details from which is why I have currently made stubfiles for cython's 
files such as typedefines. pxd files are still needing support of thier own as carrying class definitions in with and normal python classes still
need some work especially subclasses. Currently pyduktape2's stubfile when generating still needs a few attentions to details however no typehints were able to be carried which is something that might have to be fixed in future versions of this compiler before I merge it to cython. 
Allow me to share with all of you some examples of what this tool can currently do...
```cython
# test.pyx
#cython:language_level=3
cimport cython 


cdef class TestClass:
    cdef:
        readonly str test
        readonly Py_ssize_t size


cdef public enum flag:
    red = 0
    yellow = 1
    blue = 2 
```
Note that the top and where I talk about enums is manually added as well as the output in comments...
```python
# -- test.pyi --
# Python stub file generated by Cython 0.29.35 And CyStub.py

from typing import Any, Generator

class TestClass:
    test: str
    size: int
    pass

# enums have C behavrios which is why they cannot be carried as python enums, enums must be public to be passed on through...
# -- enum flag --
red = 0
yellow = 1
blue = 2
```

I have already generated stubfiles for some of cython's nodes in order to help me out since I'm working with vs code and I wanted to be sure that what I end up doing is absolutely correct.

Now that I come to think of it . It might not be a bad idea to have the tool scan for classes and 
parts of functions before-hand as a two step method rather than just one, like an external Cython TreeVisitor for visiting different varibale Types, C structures and Python Classes beforehand use so that way when it's time to write down all the definitions. They will more likely be avalible when it's time to write them all down... 

I'll also try make a smarter system so that it's not scanning one entirely one file so that way all imported modules and including all `.pxi` `.py` `.pyx` and `.pxd` and all external definitions in files are also being accounted for like a roll-call/head-count ... 

One the system works I'll then start optimizing. The other thing I thought about was using quotes when the object hasn't appeared or been declared yet after a the roll-call. This may require a new-class maybe that can be a new argument of it's own.

This might require a rewrite of what I've done so far but I'll upload another file before called VariableCatcher or VariableRegistry unlike the one already made. Which aims to read nodes for all of the following

- ctypedef Definitions so that they can be translated quicker...
- cdef classes and python classes so they can be annoted when quotes are not nessesary...
- I'll be sure regristry is fast by using a dictionary for help this will make especially larger files easier to load. This however might just be an extra flag so that systems that don't have a whole lot of ram avalible can ignore this feature if needed.

Here's a visual representation of exactly what I'm reffering to:
```python
# -- example.pyi --

# object "A" Must be quoted because it hasn't been declared yet...
def before(a:"A") -> int:...

# object "A" is now being declared...
class A:
    def __init__(self) -> None:...
    # this is just an example of a stub ouput so 
    # I'm not going to go super deep into this but you get the idea...
    def some_function(self) -> str:...

# object "A" has already been declared so no more quotes are needed to be wrapped around it... 
def after(a:A) -> A:...

```
Please note that not everything can be catched by this program but I hope that developers who use typehints in cython and have to in C can be rewarded this way with this library not just with regualr annotations but also C annotations such as what I have visually given down below...

```cython

cpdef str faster_utf8(bytes raw_data, Py_ssize_t size = 0):
    # Some data will be written inside of here that may have a faster algorythm for 
    # encoding utf-8 strings than what even CPython has written for itself...
    # a perfect example of utf-8 string encoding can be found in the cython parts of aiohttp
    # see: https://github.com/aio-libs/aiohttp/blob/master/aiohttp/_http_writer.pyx
    ...
```

```python
def faster_utf8(raw_data : bytes, size:int = 0) -> str:...
```

I'll go into more details about this when I have the chance to resume it. In the meantime I'll work on the pre-variable-visitor build to work more on this concept of capturing variables before writing...

- 6/30/2023: So as I have shown before that we need to be able to translate values and return types and yesterday I made a video about this new feat go and see it if you havent already https://www.youtube.com/watch?v=hIjV9vX0uiI 

So what exactly needs to be done before we can call it good to be merged to cython?
There's serveral conditions that I would like to be met before I can say that it's over luckily the orginal author taclked most of these things for us and only needed a few changes from my end to meet expectations and compatability with `0.29.35` this is a list of what items were still being missed out on...

- 1. If a Function does not have a python return type typehinted or annotated in C or Python fasion then have the node figure out where to get the last function or item being yielded by python's `def` function. If this cannot be done fallback to
either `-> Generator[Any, None, None]:...` if the object is a generator and the typing module flag is enabled as an argument as well as `-> Any:...` otherwise do `-> object:...` which is the closest possible guess, otherwise if all fails for our end let the user resolve it. However it would be smart to find a way to eliminate or avoid this problem all together as the more functions that were written in cython, __the more time ads up from the user's side__ . __That's Not Good at all__. Finding an effective methoad to bring up the return value of the `FuncDefNode` for all
normally defined functions will be one of this repository's main priorities that differ from the original author's work...

- 2. Keeping the code nice and clean when and where ever it can be achived. For now my code may look messy to some since I'm trying to temporarly use annotations until it works correctly. Dont be upset if I end up changing anything this code is still prone to rewrites due to the fact that I'm still playing around with it until it can be memorized by me. This is why I have annotations in place in some of my functions for now. Then whenever someone else were to tell me that my annotations are no longer required I will be able to simply remove all of them when we start to do our pr to cython. 

- 3. Good Cython Code samples would be nice to get our hands on for testing and unittesting. I'll post a markdownfile soon where you can send me a pull request to have your module be added to a list for testing it. If you have valid cython code and you want to see your repository tested in my research please let me know by adding a link to your repository and the name of your library. I'll make another markdown for the list of repositories in order to test for automated typehinting completeness such as finding `yield` keywords and `return` keywords. We will also be looking for obscure libraries and modules that utilize real cython code like `pyduktape2` to use in our experimentation. The more code we get our hands on the more sturdy our future compiler will be at reconizing different nodes , values 
 and types...

- 4. Allowing for flags to be set to also allow for cython's pure python type variables over using a `Union` with `fused` if using cython's shadow typehints are enabled. This may also share some benefits on the python side of things as well.

- 7/1/2023 After a long debate with myself I decided to end up releasing where I got my inspriation off of to start working on this amazing new idea and feature for cython. I have it under the nickname `pyllparse` which was inpired by the original llparse and It hasn't been worked on by me in many months but I never got around to releasing it yet until now because I didn't want to take away from the magical experience of the original library and I mainly wrote it as an educational thing so I could understand a little more about how something so incredable works. However, let me know if you find any bugs with it so that I fix them. The parody has some flaws and bugs that I have not fixed yet...

Back to this library, I'm almost done with it the concept and there's still a few things left. I'm almost finished with this but a new TreeVisitor Subclass will be needed and that will be a special function visitor that allows us hunt down the return values for python functions and tranlsate those off. I think I will be calling it the `ReturnValueVisitor`. After that I will start forking the cython branch and get to work on merging this newly improved feature for writing pyi stub files. Cython's pure python module was never really my style but I hope that this new feature will make things better and easier to work with compiled cython modules, I'll update you on more as time goes on. Never stop coding...

- 7/3/2023 When I was looking into this a little bit more I found that It Might actually be a lot smarter to maybe see about looking into using some of the parts from
`AutoDocTransforms` to help us. The problem is that it uses a `Context` but we would have to bypass the embedsignature setting from the context, this way we could get this code to become alot cleaner. This will cost a rewrite but it seems to be worth it. We are very close to forking `Cython` And I can start planning where this could take place I was thinking that this could be done like so. This is a concept for that name of the setting that would need to take place when writing in cython.
```cython
# cython : language_level = 3
# cython : compile_pyi_signatures = True
# This will initally make the .pyi file This is different from
# embedsignature which seems to not be accessable to VS Code which
# maybe part of our problem that I find to be very dumb... - Vizonex
```

I was thinking of terms like `compile_pyi_signatures` `make_stubfile` `make_vs_code_readable` To generate the stubfile but only time will tell what the contributors for cython would like for it to actually say and do...


- 7/6/2023 

I couldn't seem to figure out how to make a return extractor for normal `def` functions yet but I'm planning to contact scoder again about the idea of bringing in this pyi-writer again but this time with a much cleaner interface for this writer in particular. What I would like is help with making the final version look as clean as possible while using existing writer to make it possible. I think I will likely use a context with it but we shall see. I am however going to start forking this soon as possible since I am starting a new job that's only going to add to my workload if I don't get this done anytime sooner than now...

- 7/17/2023
  So This project is not dead I was just taking a long break but as I did the entire way cython had the context cut out for me has been completely shifted and altered because now cython 3.0 is released and some APIs that I was working with are now broken :( so I'm going to have to likely rewrite everything which is an absolute bummer. It's too back that there is no backwards compatability so were going to have to come up with other options if we want this dream to continue to live on. I'll be back within 2 days to work more on this but chnaging the way the system is now might be a must as well as my last resort...

- 9/14/2023
  Currently programming a new way to handle unresolved return object types in cython since the behavior of typhinting can greatly affect the outcomes of how a python library or module works. Also you need to imagine how overwriting a function after making changes to a cython module could be very annoying and rewriting the pypi typehints would be a pain to redefine the return values for so a new solution will be needed to overcome these challengaes. The pipeline for it would go something like this which will require new TreeVisitor Subclasses. The goal will be to be clean with them no overdoing it. It should be as simple to read as possible for even the clueless programmers to tell what's going on.

## Step 1 - TypeDefVisitor
-    1. A TypeDefVisitor Looks for cdef objects and external values brought from C/C++ or have been declared in Cython itself. Now I would merge this with the ReturnTypeVisitor which is the next step but my goal is not to be confusing.
     2. When an Object has been found it will throw it into a translator or a dictionary with a str or PyrexType likely will do `dict[str,PyrexType]` or something fancy like that to help with type translation to the lowest C or Python variable so that translating the return type to python will be very simple. 
     3. When Finished, the TypeDefVisior will pass the translator dictionary or something simillar along to the `ReturnTypeVisitor` which is step 2

## Step 2-A NameRecursor
    - I better talk about what this new object is and what it is used for but basically it will be used to help organize data and allows for class Objects to be added to a special stack and is used to carry around function information. To illustrate I have thrown in an example to help you better undertsand how the NameRecursor's patterns with be handled...
```python
def func_A(self):
    ...
class B:
    def __init__(self):
        ...
    def func(self):
        ...
```
    When picking up this information it will organize a string that will be used to help organize a return object table making it simple and easy to find the functions that it needs to have and I will now demonstrate it's name and stack objects visually for you to see...

1.     stack -> ["func_A"]
       name -> func_A
   Stack will pick up func_A and then drop it because there's noting after it...
2.    stack -> ["B"]
      name -> "B"
    Stack finds an object class Named `B` and it will add it to the stack
3.     stack -> ["B","__init__"]
       name -> "B.__init__"
    So why does this happen this way you might ask? Simply because joining that stack with a dot will help create a better visual and not just for debugging but allow us to easily find this object again when we have put it onto the table so that all return annotations can later be looked up this will have the same behavior for B's func() method and that is all you need to really understand how this new `NameRecursor` class object will work...

 
## Step 2-B - ReturnTypeVisitor 
(it will be a Subclass of likely a ScopeVisitor object because it carries the function and class Nodes which is in my opion is extremely helpful to have in our case...)
-    1. A `ReturnTypeVisitor` object or RTV for short is a Cython Node Visitor for collecting Nodes With No Return Annotations and making a table for those missing objects with either a PyrexType object or string with it's name when a return object has been found for it. A Speical Table (Not the TypeDefVisitor's but it will be used for help as well) it will also use the NameRecursor to help organize this data better and creates namespaces with simillar classes to keep everything clean and organized for the final stage of the plan. the table object will be a dictionary carrying str keys with Seqences of PyrexTypes or Strings if needed I plan to program a `__hash__` function for these objects as needed to use with a `set()` to keep these return values it gets to be organized. Another Variable added will be the TypeDefVisitor's translation table to help optimize down to more famillair objects whenever found so that a better return object can be defined a little bit more clearly.
  
     2. When any function is found (Yes Even a C-Function(aka cdef or cpdef function)) it will check for a declaration first before adding it to the stack otheriwse it will visit it's children to find some answers this is true for all python objects. The NameRecursor will takes these names and add them to the table 
     3. When a `ReturnStatNode` or YieldNode is found it will add those objects to the function that the NameRecursor assigns to it and it will throw them into a sequence on the table 
     if there are no objects in the return or yeild it will mark that return Object as python's definition of `None` or `void` if it's a c function, it's better that way if a yeild or return Node is calling a call at the end for a function these will have to be looked up at a later time to prevent lookup errors so they will be simply ignored and then later updated before converting our `.pyx` module to a suitable typehinting module.

## Step 3  PostReturnTypeVisitor 
basically takes all the return calls that we had saved for later and convert them now so that the types are accurately laid out for the final stage...

## Step 4  PyiWriter (The Final Step)
You've already seen it if you've seen this library but all missing return annotations will have the ReturnTypeVisitor's table with it on hand so it can be ready to add in addtional resources whenever a return annotation is not avalible to us or hasn't been defined yet by the programmer who defined the function in Cython. The table is then called and it's Sequence can be joined as either a `typing.Union` object or joined with a pipe '|' in python versions 3.10 and onward. I work with 3.9.15 currently for compatability and support for later versions of python but this is everything in my plan explaned to the best of my abilities. If this were implemented in cython there should be a flag inside of the cythonize command to do so, I just think it's a little insane that some people would freak out over writing the pyi modules when pip is installing the cython library before it is used by the programmed who installed the package. instead it should be compiled before releasing it into the wild but that is just my personal opion on that subject. Anyways I hope to get ready to implement this in I have had numerous failed attempts but I think this time with these 4 steps in mind this should work now that I've explained everything in greater detail. - Vizonex

