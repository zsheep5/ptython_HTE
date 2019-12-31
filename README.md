A simple python HTML parser.  takes in file object, file name, or string
and context dictionary
return type file object or string.  

Inspired by C Template Library 1.0 by Stephen C. Losen (http://libctemplate.sourceforge.net) 

Wanted a simple easy to use template engine, that was fast and easy to modify and get out better error messages 
Compare to other Python HTML template engines,  this is only 600 lines of code has all the same features that are found in other Engines. 

The one file, python_html_parser.py supports the following Template Tags 

'TMPL_VAR' = prints out variables in Context dictionary has default value , and function tag to first pass the variable through a function return that vale 

'TMPL_LOOP' = loops over a list of dictionaries in the context

'TMPL_BREAK' = breaks out of loop, can be a name loop to exit out of nested loops

'/TMPL_LOOP', = end loop tage

'TMPL_CONTINUE' = go to the next iteration of the loop

'TMPL_LOOPCOUNT' =  automatically created variable  to track current number the loop is on starts at 0

'TMPL_IF' = same a python if statement

'TMPL_ELSIF' =  same as python elsif statement

'TMPL_ELSE' = same as python else statement

'/TMPL_IF' = end tag of if statement 

'TMPL_FUNCTION' = call a function that is function_context dictionary,  a pointer to the function must be in the funciton_context Dictionary

There are a few cache methods. 

One cache the parsed template so the template does not have to be parsed to be rendered again  

Cache the rendered template, putting the results into memcache.

The template engine is written in function style,  meaning all the functions can be called independently of each other and out of sequence.  The only exception is the function_context dictionary is a global variable.

Test and use samples can be found at bottom of the python_HTML_parser.py

Performance of the engine is on par with Jinjia2 using simple test cases and  loops with a million entries,  more performance can be gained by changing the dictionary access from dic.get() to dic[''] as this is twice as fast.  Only problem is design goal was return more readable error messages and not throw exceptions.  The change is minor but requires add Try Except Catches in the code.  It was done a few key places such as get_context_value() and function_process()

The engine was complied with cthyon with no modification or type hinters,  this out performed Jinjia2 with simple test cases 
