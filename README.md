# Cystub

__CyStub__ is a `.pyi` Extension Stub Compiler tool for Cython users. 

This tool was Inspired by this pull request seen here: https://github.com/cython/cython/pull/3818
Which didn't make it into production...


Over the years people have had to overcome the hard challege of writing stubfiles manually and 
the incompatabilty with VS Code has thrown many people off including myself , some of which takes hours just to write manually down,
the other issue is that the compiled versions of your modules have to be slightly reserved engineered
if you want all the nitty gritty details needed when using your module...

Currently libraries that utilize cython such as __PyImgui__ and __PyDukTape2__ can be extremely difficult to navigate when it's hoverlist is not avalible. 

But now I bring a __New Solution__ to the table ...
We can now compile our own stubfiles in a more automatic fasion provided that we are using 
the already existing Cython Code Writer and it's Compilers for help.

I re-designed the original pyi compiler and made some modifications to it and then I
wrapped the compiler around __click__ as it's argument parser for now . 

Knowing how exciting this could end up being as well as revolutionary , I wanted to 
give you a Demo of this possible upcomming feature that I wish to have added to Cython itself in the future
by currently giving it it's own Temporary repository until 
I can have the time to move this functionality straight into cython itself....

Note that I'll stop maintaining this library 
when cython adds these features we all 
desperately need into it's own tools...

This is Currently Experimental But I plan to start with testing this on a larger scale with PyImgui and post my interesting results here especially like the way I had kept a dev-journal with winloop so that you can also keep track of my progress...

## Requirements
click and cython are both required to get this to work as this tool attempts to use/have direct acess to the cython compiler itself...

```
pip install click cython
```

## Commandline Example 

to use cd to the src directory and run the Cystub.py module to start using it... 
```
python Cystub.py --help
```
 
Compiling cython code. Here's an example if you need more help look into what I've written in Cystub...
```
python Cystub.py -o output yourmodule.pyx othermodule.pxd 
```

## This tool is not entirely ready to be used on a wide-scale yet but I Welcome Any Contributors with open arms...
There's still a few things I have left to add or change so you'll have to be patient with me but if your feeling egar to have these things or implemented/finished sooner, feel free to start contributing to what I have left on the table. When I get this tool to be stable I'm going to make a pull request to cython and start merging with the PyiCompiler...

## What I'm working with
I'm Currently working off of my own stubfiles that I am sort of reverse-engineering the definitions for the cython complier and all of it's own cython nodes as I go along 
https://gist.github.com/Vizonex/58f412067403975be3450bdd0b91298f
I'm working with VS Code which maybe also be part of my problem even though I like to have completeness in my code in order to verify that what I'm doing is absolutely correct...

I'll be asking some folks I know from one of the python discord servers for feedback 
as well since I was able to get some guidence from them with winloop. You will not find my actual alias there but I'm planning to swap the users soon . I mainly had a different alias in there because it's an account I made for guarding a bunch of my experimental discord bots. 

## Video
- https://www.youtube.com/watch?v=hIjV9vX0uiI
