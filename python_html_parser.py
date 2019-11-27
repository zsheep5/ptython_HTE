"""
A simple python HTML parser.  takes in file point or file name,
context dictionary
return type file or stinrg
"""

class Parse_Tree ():
    #simple class to hold the structure of the tags parsed
    tag_type = None
    tag_name = None  #Name of the tag for vars it the name in the context dictionary
    tag_value = None #used by if statments is the value compared against 
    tag_sposition = -1 #start of the caret  for the tag
    tag_eposition = -1 # ending carent close of the tag unless IF or LOOP then its the end of the caret for the closing tag 
    tag_function = None  #python function
    tag_func_args = ''
    tag_include_file_name = None #if the template has an include line this should be the file 
    tag_default = ''  #default value for 
    tag_children = [] #tags that appear in below this tag typically in If or loops will have children
    tag_raw = '' #raw tag that has been extracted prior to parsing
    tag_string_to_process = '' # contains only the extracted text to be processed by the if or loop statements
    tag_processed_string = '' #contains the text after it has been processed by the template engine 
    tag_skip = False #tells processor to skip this tag primary used by if statements so else and elseif are not process just removed
    tag_caret_close = -1 # the closing caret for the tag  

    def __init__(self, ptag_type= 'TMPL_VAR', 
                ptag_name='', 
                ptag_value='',
                ptag_sposition=-1, 
                ptag_eposition = -1,
                ptag_caret_close=-1,

                ptag_function= None,
                ptag_include_file_name='',
                ptag_default = '',
                ptag_children = [],
                ptag_raw = ''):
        self.tag_type = ptag_type
        self.tag_name = ptag_name
        self.tag_sposition = ptag_sposition
        self.tag_eposition = ptag_eposition
        self.tag_caret_close = ptag_caret_close
        self.tag_function = ptag_function
        self.tag_include_file_name = ptag_include_file_name
        self.tag_default = ptag_default
        self.tag_children = ptag_children
        self.tag_raw = ptag_raw
         

function_context = {'abs':abs, 'all':all, 'any':any, 'ascii':ascii, 'bin':bin,  'bytearray':bytearray, 'callable':callable, 
    'chr':chr, 'complex':complex,  'divmod':divmod,  'format':format, 'hash':hash, 'hex':hex, 'len':len, 'max':max, 'min':min,
    'oct':oct, 'ord':ord, 'pow':pow, 'round':round, 'str':str, }

def add_function(pname= 'name_of_the_function', pfunc=None ):
    function_context.update({pname:pfunc})

def render_html( pfile, ptype = 'file', pcontext = {}, preturn_type= 'string', 
                pcustom_tags=(), pcustom_attributes=(), 
                pmisstag_text= 'Tag Name not Found in Context', 
                pbranch_limit=10, pdebug_mode=False , pmax_search = 500,
                pfunc_context={'func_name':'function'}, 
                preturn_fname = 'rendered', preturn_fext='.html'):
    _template = None
    global function_context
    function_context.update(pfunc_context)
    if ptype == 'file':
        import io
        if isinstance(pfile, io.IOBase):
            _template = pfile 
        else :
            _template = open(pfile, 'r').read()
    else:
        _template = pfile

    _template = process_include_files(_template, pmax_search=pmax_search)

    _count, rtag_tree =parse_template(_template)
    _text, ctag_tree = process_tag_tree( pcontext, rtag_tree, _template, pmisstag_text, 0, pbranch_limit, pdebug_mode)

    if preturn_type == 'string':
        return _text
    elif preturn_type == 'file':
        _t = open(preturn_fname + preturn_fext)
        _t.write(_text)
        _t.flush()
        return _t

def process_include_files(ptemplate = '', ptag='<TMPL_INCLUDE', pmax_search =100 ):
    _newtemplate = ptemplate
    while True:
        _spos = _newtemplate.upper().find('<TMPL_INCLUDE')
        if _spos == -1:
            return _newtemplate
        _epos = find_closing_caret( _newtemplate, sposition = _spos, p_tag_type='TMPL_INCLUDE', pmax_search=pmax_search)
        _filename = tag_attributes_extract(_newtemplate[_spos, _epos], 'name')
        _file = open(_filename,'r')
        _newtemplate = _newtemplate[0:_spos] + _file.read() + _newtemplate[_epos+1:]

def process_tag_tree(pcontext={}, ptag_tree=[], ptemplate= '',
                    pmisstag_text = 'Tag Name not Found in Context', 
                    pbranch_count=0, pbranch_limit=10, pdebug_mode=False):
    #handles the logic, matching up the context variables template tags and text replacement in the template
    _return = ptemplate
    _context_value= ''
    _break_or_continue = None
    if pbranch_count == pbranch_limit:
        raise Exception("Template Branch/Call Stack limit reached. current limit %s ")

    for itag in ptag_tree:
        if itag.tag_type == 'TMPL_VAR':
            if itag.tag_function is None:
                _return = _return.replace(itag.tag_raw, get_context_value(pcontext, itag.tag_name, itag.tag_default, pmisstag_text ),1)
            else:
                _return = _return.replace(itag.tag_raw, function_process(itag.tag_function, itag.tag_name, pcontext, itag.tag_default ), 1)
        elif itag.tag_type == 'TMPL_IF':
            if not check_child_tree('/TMPL_IF', itag.tag_children):
                    raise Exception('Template If statement does not have closing /TMPL_IF;  TMPL_IF position is: %s' % (itag.tag_sposition)) 
            _start =  _return.find(itag.tag_raw)
            _end = _return.find(find_child_tag('/TMPL_IF', None, itag.tag_children).tag_raw)+8
            _context_value == get_context_value(pcontext, itag.tag_name, itag.tag_default, pmisstag_text )
            if _context_value == itag.tag_value :  ## process what is below or show text below this
                if len(itag.tag_children)> 1:  #have children need to processed them 

                    itag.tag_processed_string, _break_or_continue  = itag.tag_processed_string + process_tag_tree( 
                                                                                                            pcontext, 
                                                                                                            itag.tag_children,  
                                                                                                            pmisstag_text, 
                                                                                                            (pbranch_count +1), 
                                                                                                            pbranch_limit)
                    _return = _return.replace(itag.tag_raw, itag.tag_processed_string)
            elif check_child_tree('TMPL_ELSE', itag.tag_children) or check_child_tree('TMPL_ELSEIF', itag.tag_children):
                itag.tag_processed_string, _break_or_continue = process_tag_tree( 
                                                                    pcontext, 
                                                                    itag.tag_children, 
                                                                    pmisstag_text, 
                                                                    (pbranch_count +1), 
                                                                    pbranch_limit)
                if _break_or_continue is not None:
                    return itag.tag_processed_string, _break_or_continue
                _return = itag.tag_processed_string
            else:
                itag.tag_processed_string = ''
        elif itag.tag_type == 'TMPL_ELSEIF' :
            if itag.tag_skip: #remove this from template up to the next elesif, else, /TMPL_IF
                itag.tag_processed_string = ''
            _context_value == get_context_value(pcontext, itag.tag_name, itag.tag_default, pmisstag_text )
            if itag.value == _context_value:
                itag.tag_processed_string, _break_or_continue = process_tag_tree( 
                                                                    pcontext, 
                                                                    itag.tag_children, 
                                                                    pmisstag_text, 
                                                                    (pbranch_count +1), 
                                                                    pbranch_limit)
                if _break_or_continue is not None:
                    return itag.tag_processed_string, _break_or_continue
        elif itag.tag_type == 'TMPL_LOOP':
            ## now in a loop conidition need to check a few things
            if not check_child_tree('/TMPL_LOOP', itag.tag_children):
                raise Exception("LOOP is missing an /TMP_LOOP TAG.  TMPL_LOOP position is %s"% (itag.tag_sposition))
            loop_context = pcontext.get(itag.tag_name, None)
            if loop_context is None:  ##failed to find the LIST of dictionariares in the context replace with pmisstag_text
               _return = _return.replace(itag.tag_raw, pmisstag_text, 1)
               return _return
            if not isinstance(loop_context, list):
                raise Exception("LOOP name: %s at position %s the context is not a list" % (itag.tag_name, itag.tag_sposition))
            _append_loop_text = ''
            for iloop in loop_context:
                if not isinstance(iloop, dict):
                    raise Exception("LOOP name: %s at position %s context is a list, needs to be a Dictionary" % (itag.tag_name, itag.tag_sposition))

                _append_loop_text, _break_or_continue = process_tag_tree(iloop, 
                                                itag.tag_children, ptemplate[itag.tag_caret_close+1: itag.tag_eposition-12],
                                                pmisstag_text, 
                                                (pbranch_count +1), 
                                                pbranch_limit)
                _append_loop_text +=  _append_loop_text
                if _break_or_continue is not None:
                    if _break_or_continue.tag_type == 'TMPL_BREAK': 
                        if _break_or_continue.tag_name == '' or _break_or_continue.tag_name == itag.tag_name:
                            # break this loop NOW
                            break
                        else :
                            # break out to the next loop level 
                            return _return + itag.tag_processed_string, _break_or_continue
                    else:  ## has to be a continue
                        continue
                _return = itag.tag_processed_string = ptemplate.replace(itag.tag_raw, _append_loop_text, 1 )        
        elif itag.tag_type == 'TMPL_BREAK' or itag.tag_type== 'TMPL_CONTINUE':
            return _return, itag 
        elif itag.tag_type == '/TMPL_IF' or itag.tag_type == '/TMPL_LOOP' : ##this just removes the end tag for the template
            return _return, itag
        elif itag.tag_type == '/TMPL_FUNCTION':
            itag.tag_processed_string = function_process(itag.tag_name, itag.tag_func_args, pcontext, pmisstag_text, pdebug_mode)
            _return = _return +  ptemplate.replace(itag.tag_raw, itag.tag_processed_string , 1)
    return _return, ptag_tree

def set_elseif_to_skip( ptag_tree=[] ):
    to_process = ptag_tree
    for itag in to_process:
        if itag.tag_type in ('TMPL_ELSE', 'TMPL_ELSEIF' ):
           itag.tag_skip = True
        if itag.tage_type == '/TMPL_IF':
            _epurge = itag.tag_caret_close
            return True
    return True

def find_child_tag (ptag_type = ('TMPL_ELSE', 'TMPL_ELSEIF' ), pname = None, pchildren=[]):
    for itag in pchildren :
        if itag.tag_type in ptag_type:
            if pname is not None:
                if itag.tag_name == pname:
                    return itag
                else :
                    continue
            return itag
    return None
        
def get_context_value(pcontext ={}, pname='', pdefault = None, pmisstag_text = 'Tag Name not Found in Context'):
    _return = pcontext.get(pname, None)
    if _return is not None :
        return str(_return)
    if _return is None and pdefault is not None:
        _return = pdefault
    if _return is None and pdefault is None :
        return pmisstag_text

def check_child_tree(ptag_type, pchildren):
    if pchildren is None:
        return False 
    for ichild in pchildren:
        if  ichild.tag_type == ptag_type :
            return True
    return False

def parse_template( ptemplate, sposition=0):
# parses the template making sure all the tags are correct if not returns an error
    _tag_tree = []
    _count = sposition
    _len = len(ptemplate)
    while _count < _len: 
        _match = ptemplate[_count]
        if  ptemplate[_count] =='<':
           _count, _pt = scan_tag(ptemplate, _count+1)
           if _pt is not None :
               _tag_tree.append(_pt)
        else:
            _count = _count + 1
    return _count, _tag_tree

def find_closing_caret(ptemplate='', sposition =0, p_tag_type = 'TMPL_VAR', pmax_search= 500):
    _count = sposition
    _len = len(ptemplate)
    while _count < _len:
        _test = ptemplate[_count] 
        if _test == '>':
            return _count
        if _count > pmax_search:
            raise Exception("Failed to find the closing > after %s characters search for %s position %s " %
                        (pmax_search, p_tag_type, sposition) ) 
        _count = _count + 1
    else:
        raise Exception("Failed to find the closing > for  %s position %s "% (p_tag_type,sposition))

def find_closing_tag(ptemplate='', sposition =0, p_otage_type = 'TMPL_IF', p_ctag_type = '/TMPL_IF'):
    ##searchs a string finding the closeing /TMPL_if returning its starting position in the string 
    ## the template passed can not have the opening tag for the if or loop
    
    ## quick check if the string only has one great return that one
    _end_tag_count = ptemplate.count(p_ctag_type) 
    _tag_size = len(p_otage_type)
    if _end_tag_count == 1:
        _end_tag_position = ptemplate.find(p_ctag_type)
        return Parse_Tree(p_ctag_type, '', '', _end_tag_position, ptag_caret_close=find_closing_caret(ptemplate, _end_tag_position, '/TMPL_LOOP'), )
    if _end_tag_count == 0:
        raise Exception("Cound not find the Closing tag for %s starting position %s" %(p_otage_type, sposition))
    _count = 0 
    _open_tag_position = 0
    
    while _count <_end_tag_count:
        _end_tag_position = ptemplate.find(p_ctag_type, _open_tag_position)
        _open_tag_position = ptemplate.find(p_otage_type, _open_tag_position+_tag_size)
        if _end_tag_count < _open_tag_position: ## great found the closing tag return it
            return Parse_Tree(p_ctag_type, '', '', _end_tag_position, find_closing_caret(ptemplate, _end_tag_position, '/TMPL_LOOP') )
        _count = _count + 1
    
    raise Exception("Closing Tag Mismatch for %s starting from position %s "%(p_otage_type, sposition))
        
def tag_attributes_extract(pstring='', pattribute='name' ):
    _swhere = pstring.lower().find(pattribute.lower())
    _rstring = ''
    if _swhere >=0:
        if pstring.count('"')%2 == 0 and pstring.count('"')> 0:
            _s = pstring.find('"')+1
            return pstring[_s: pstring.find('"', _s)]
        elif pstring.count("'")%2 == 0 and pstring.count("'")>0:
            _s = pstring.find("'")+1
            return pstring[_s: pstring.find('"', _s)]
        else:
            raise Exception(""" ' or " are not matching  in the attributes in for %s"""
                            % (pstring))
    return ''

def tag_func_extract(pstring="<TMPL_FUNCTION function(list, of, args)>" ):
    _step = pstring.upper().replace('<TMPL_FUNCTION', '', 1)
    _step = _step.replace('>', '', 1)
    _func_name = _step.strip()[:_step.find('(')]
    _func_ars = _step[_step.find('('): _step.find(')') ]

def scan_tag(ptemplate= '', sposition=0):
    _pt = Parse_Tree()
    _pt.tag_sposition = sposition-1 # scan 
    cposition = 0
    test = ptemplate[sposition:sposition+8].upper()
    if ptemplate[sposition:sposition+8].upper()== 'TMPL_VAR':
        _pt.tag_type = 'TMPL_VAR'
        _count = sposition + 8
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition + 9)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_caret_close+1]
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw)
        _pt.tag_default = tag_attributes_extract(_pt.tag_raw, 'default')
        _pt.tag_function = tag_attributes_extract(_pt.tag_raw, 'function')
        return _pt.tag_caret_close, _pt    

    elif ptemplate[sposition:sposition+9].upper() == 'TMPL_LOOP' :
        _pt.tag_type = 'TMPL_LOOP'
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition+9)
        _pt.tag_name = tag_attributes_extract(ptemplate[sposition+9: _pt.tag_caret_close], 'name')
        _pt.tag_default = tag_attributes_extract(_pt.tag_raw, 'default')
        _end_tag = find_closing_tag(ptemplate[sposition+9:], 0, p_otage_type='TMPL_LOOP', p_ctag_type='/TMPL_LOOP' )
        if _end_tag is None:
            raise Exception("LOOP is missing an /TMP_LOOP TAG.  TMPL_LOOP position is %s"% (_pt.tag_sposition))
        _pt.tag_eposition = _end_tag.tag_caret_close+sposition+10
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_eposition ]
        _cposition, _pt.tag_children = parse_template(ptemplate[_pt.tag_caret_close: _pt.tag_eposition])
        _pt.tag_children.append(_end_tag)
        return _pt.tag_eposition , _pt

    elif ptemplate[sposition:sposition+10].upper() == 'TMPL_BREAK': 
        _pt.tag_type = 'TMPL_BREAK'
        
        _pt.tag_caret_close =find_closing_caret(ptemplate, sposition+ 10)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_caret_close+1]
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw, 'name')
        return _pt.tag_caret_close, _pt

    elif ptemplate[sposition:sposition+13].upper() == 'TMPL_CONTINUE': 
        _pt.tag_type = 'TMPL_CONTINUE'
        _pt.tag_caret_close =find_closing_caret(ptemplate, sposition+ 13)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_caret_close+1]
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw, 'name')
        return _pt.tag_caret_close, _pt

    elif ptemplate[sposition:sposition+7].upper() == 'TMPL_IF' :
        _pt.tag_type = 'TMPL_IF'
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition+7)
        _pt.tag_name = tag_attributes_extract(ptemplate[sposition+9: _pt.tag_caret_close], 'name')
        _pt.tag_value = tag_attributes_extract(_pt.tag_raw, 'value')
        _end_tag = find_closing_tag(ptemplate[sposition+7:])
        if _end_tag is None:
            raise Exception("TMP_IF is missing an /TMP_IF TAG.  TMPL_LOOP position is %s"% (_pt.tag_sposition))
        _pt.tag_eposition = _end_tag.tag_caret_close+sposition+8
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_eposition+1]
        _cposition, _pt.tag_children = parse_template(ptemplate[_pt.tag_caret_close: _pt.tag_eposition])
        _pt.tag_children.append(_end_tag)
        return _pt.tag_eposition, _pt

    elif ptemplate[sposition:sposition+9].upper() == 'TMPL_ELSIF': 
        _pt.tag_type = 'TMPL_ELSEIF'
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition+7)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_caret_close+1]
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw, 'name')
        _pt.tag_value = tag_attributes_extract(_pt.tag_raw, 'value')
        _cposition, _pt.tag_children = parse_template(ptemplate, _pt.tag_caret_close)
        return cposition, _pt

    elif ptemplate[sposition:sposition+13].upper() == 'TMPL_FUNCTION': 
        _pt.tag_type = 'TMPL_FUNCTION'
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition+13)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_caret_close+1]
        _pt.tag_name, _pt.tag_func_args = tag_func_extract( _pt.tag_raw)
        _pt.tag_default = tag_attributes_extract(_pt.tag_raw, 'default')
        return _pt.tag_caret_close+1, _pt

    elif ptemplate[sposition:sposition+10].upper() == 'TMPL_LOOPCOUNT' :
        _pt.tag_type = 'TMPL_LOOPCOUNT'
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition+13)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_caret_close+1]
        return _pt.tag_caret_close+1, _pt

    else :
        _pt = None

    return sposition, _pt

def function_process(pfunc_name = '', pargs='', pcontext= {}, pdefault_text ='Function not Found in Context or is not a Built-In Function', pdebug_mode=False ):
    
    global function_context
    _func = function_context.get(pfunc_name, None)
    if _func is None:
        return pdefault_text
    
    _pass_in =[]
    for _iargs in pargs.split(','):
        _pass_in.append(pcontext.get(_iargs))
    
    try:
        _return = _func(*_pass_in)
    except Exception as e:
        if pdebug_mode:
            raise 
        _return = str(e)
    return _return 
    
def tag_list():
    """ <TMPL_VAR name = "varname" default = "value" function = "functionname">
    * <TMPL_INCLUDE name = "filename">
    * <TMPL_LOOP name = "loopname">
    * <TMPL_BREAK name = N>
    * <TMPL_CONTINUE name = N>
    * <TMP_LOOPCOUNT> returns the current count in a loop primary use is for conditional formating..
    * </TMPL_LOOP name = "" >
    * <TMPL_IF name = "varname" value = "testvalue">
    * <TMPL_ELSIF name = "varname" value = "testvalue">
    * <TMPL_ELSE>
    * </TMPL_IF>
    * <TMPL_FUNCTION "function(list, of, args)" default="Function Not Found">
    """ 
 #13 is the longest string to search for
    return ('TMPL_VAR',
        'TMPL_LOOP',
        'TMPL_BREAK',
        'TMPL_BREAK',
        'TMPL_CONTINUE',
        'TMPL_LOOPCOUNT',
        '/TMPL_LOOP',
        'TMPL_IF',
        'TMPL_ELSIF',
        'TMPL_ELSE',
        '/TMPL_IF',
        'TMPL_FUNCTION',
       
    )

def run_test_code():
    #create test calls 
    import time , datetime 
    gg = time.localtime()
    gg = datetime.date.today()
    utf_context = {"varName":"haha1",
        "aLoop":[
            {"loopVar":"bool","loopVar2":True},
            {"loopVar":"float","loopVar2":'Unicode Test'} ],
        "sweet":{"name":"æ  ñ",
                "price":None, "isBig": 44
                }
        }
    ascii_context = {"varName":"file template test",
        "aLoop":[
            {"loopVar":"bool","loopVar2":False},
            {"loopVar":"float","loopVar2":98} ],
        "sweet":{"name":"it works with files",
                "price":gg,"isBig": 0
                }
        }


    test_template = """ <* This is a comment *>
    File var Name: <TMPL_var name="varName"> 
    <TMPL_LOOP name="aLoop"> 
    file _Loop has var <TMPL_var name="loopVar"> 
        value <TMPL_var name="loopVar2"> 
    </TMPL_LOOP> 
    Sweet name: <TMPL_var name="sweet.name">
    Sweet price: <TMPL_var name="sweet.price">
    <TMPL_if name="sweet.isBig" value="0">
    Sweet is big
    </TMPL_IF>"""

    print( render_html( test_template, 'string', utf_context ))

run_test_code()