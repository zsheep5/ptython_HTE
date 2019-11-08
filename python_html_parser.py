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
    tag_sposition = -1
    tag_eposition = -1
    tag_function = None  #python function
    tag_include_file_name = None #if the template has an include line this should be the file 
    tag_default = ''  #default value for 
    tag_children = [] #tags that appear in below this tag typically in If or loops will have children
    tag_raw = '' #raw tag that has been extracted prior to parsing
    tag_skip = False #tells processor to skip this tag primary used by if statements so else and elseif are not process just removed  

    def __init__(self, ptag_type= 'TMPL_VAR', 
                ptag_name='', 
                ptag_value='',
                ptag_sposition=-1, 
                ptag_eposition=-1,
                ptag_function= None,
                ptag_include_file_name='',
                ptag_default = '',
                ptag_children = [],
                ptag_raw = ''):
        self.tag_type = ptag_type
        self.tag_name = ptag_name
        self.tag_sposition = ptag_sposition
        self.tag_eposition = ptag_eposition
        self.tag_function = ptag_function
        self.tag_include_file_name = ptag_include_file_name
        self.tag_default = ptag_default
        self.tag_children = ptag_children
        self.tag_raw = ptag_raw
         

def render_html( pfile, ptype = 'file', pcontext = {}, preturn_type= 'string', pcustom_tags=(), pcustom_attributes=() ):
    _template = None

    if ptype == 'file':
        import io
        if isinstance(pfile, io.IOBase):
            _template = pfile 
        else :
            _template = open(pfile, 'r').read()
    else:
        _template = pfile

    _count, tag_tree =parse_template(_template)
    process_template(_template, pcontext, tag_tree)

def process_template(ptemplate='', pcontext={}, ptag_tree=[], 
                    pmisstag_text = 'Tag Name not Found in Context', 
                    pbranch_count=0, pbranch_limit=10):
    #handles the logic, matching up the context variables template tags and text replacement in the template
    _return = ptemplate
    _context_value= ''
    if pbranch_count == pbranch_limit:
        raise Exception("Template Branch/Call Stack limit reached. current limit %s ")

    for itag in ptag_tree:
        if itag.tag_type == 'TMPL_VAR':
            _context_value = get_context_value(pcontext, itag.tag_name, itag.tag_default, pmisstag_text )
            _return =  _return.replace(itag.tag_raw, _context_value, 1)
        elif itag.tag_type == 'TMPL_IF':
            if not check_child_tree('/TMPL_IF', itag.tag_children):
                    raise Exception('Template If statement does not have closing /TMPL_IF;  TMPL_IF position is: %s' % (itag.tag_sposition)) 
            _start =  _return.find(itag.tag_raw)
            _end = _return.find(find_child_tag('/TMPL_IF', None, itag.tag_children).tag_raw)+8
            _context_value == get_context_value(pcontext, itag.tag_name, itag.tag_default, pmisstag_text )
            if _context_value == itag.tag_value :  ## process what is below or show text below this
                if len(itag.tag_children)> 1:  #have children need to process them 
                    #remove the if statement tag from the templage
                    _return = _return.replace(itag.tag_raw, '' ,1)
                    itag.tag_children = set_elseif_to_skip(itag.tag_children )
                    _r = process_template( _return[_start:_end], 
                                                        pcontext, 
                                                        itag.tag_children,  
                                                        pmisstag_text, 
                                                        (pbranch_count +1), 
                                                        pbranch_limit)
                    _return = _return[0:_start] + _r + _return[_end:]
            elif check_child_tree('TMPL_ELSE', itag.tag_children) or check_child_tree('TMPL_ELSEIF', itag.tag_children):
                ## remove text from start of if tag up to else or elseif
                _ctag = find_child_tag(pchildren = itag.tag_children)
                # idea here is to cut down the amount text being process in recursive calls 
                _s2 = _return.find(_ctag.tag_raw-1)
                _r = process_template( _return[_s2:_end], 
                                            pcontext, 
                                            itag.tag_children, 
                                            pmisstag_text, 
                                            (pbranch_count +1), 
                                            pbranch_limit)
                ## replace the text in the template
                _return = _return[0:_start] + _r + _return[_end:]
            else:
                ## no else or elseif to process and the logic returned NONE remove the text for between the TMPL_IF to the /TMPL_IF
                _return = _return[0:_start] + '' + _return[_end:]
        elif itag.tag_type == 'TMPL_ELSEIF' :
            if itag.tag_skip: #remove this from template up to the next elesif, else, /TMPL_IF
                _return = _return[ 0:_return.find(itag.tag_raw)] + '' + \
                          _return[ _return.find(find_child_tag(('TMPL_ELSEIF','TMPL_ELSE', '/TMPL_IF'), ptag_tree).tag_raw)-1:]
                return _return 
            _start =  _return.find(itag.tag_raw)
            _end = _return.find(find_child_tag('/TMPL_IF', None, itag.tag_children).tag_raw)+8
            _context_value == get_context_value(pcontext, itag.tag_name, itag.tag_default, pmisstag_text )
            if itag.value == _context_value:
                _r = process_template( _return[_s2:_end], 
                                            pcontext, 
                                            itag.tag_children, 
                                            pmisstag_text, 
                                            (pbranch_count +1), 
                                            pbranch_limit)
                ## replace the text in the template
                _return = _return[0:_start] + _r + _return[_end:]
        elif itag.tag_type == 'TMPL_LOOP':
            ## now in a loop conidition need to check a few things
            if not check_child_tree('/TMP_LOOP', itag.tag_children):
                raise Exception("LOOP is missing an /TMP_LOOP TAG.  TMPL_LOOP position is %s"% (itag.tag_sposition))
            loop_context = pcontext.get(itag.tag_name, None)
            _start =  _return.find(itag.tag_raw)
            _end = _return.find(find_child_tag('/TMPL_LOOP', None, itag.tag_children).tag_raw)+11
            if loop_context is None:  ##failed to find the LIST of dictionariares in the context replace with pmisstag_text
               _return = _return[0:_start] + pmisstag_text + _return[_end:]
               return _return
            if not isinstance(loop_context, list):
                raise Exception("LOOP name: %s at position %s the context is not a list" % (itag.tag_name, itag.tag_sposition))
            _append_loop_text = ''
            for iloop in loop_context:
                if not isinstance(iloop, dict):
                    raise Exception("LOOP name: %s at position %s context is a list but is not dictionary" % (itag.tag_name, itag.tag_sposition))
                process_template(_return[_start:_end],)

        elif itag.tag_type == '/TMPL_IF' or itag.tag_type == '/TMPL_LOOP' : ##this just removes the end tag for the templage
            _return = _return.replace(itag.tag_raw, '')
            


    return _return

def set_elseif_to_skip( ptag_tree=[] ):
    to_process = ptag_tree
    for itag in to_process:
        if itag.tag_type in ('TMPL_ELSE', 'TMPL_ELSEIF' ):
           itag.tag_skip = True
        if itag.tage_type == '/TMPL_IF':
            _epurge = itag.tag_eposition
            return True
    return True

def find_child_tag (ptag_type = ('TMPL_ELSE', 'TMPL_ELSEIF' ), pname = None, pchildren=[]):
    for itag in pchildren :
        if itag in ptag_type:
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
        return _return
    if _return is None and pdefault is not None:
        _return = pdefault
    if _return is None and pdefault is None :
        return pmisstag_text

def check_child_tree(ptag_type, pchildren):
    for ichild in pchildren:
        if  ichild.tag_type == ptag_type :
            return True
    return False

def parse_template( ptemplate, sposition=0):
# parses the template making sure all the tags are correct if not returns an error
    _tag_tree = []
    _count = sposition
    _len = len(ptemplate)
    while _count <= _len: 
        if  ptemplate[_count,1] =='<':
           _count, _pt = scan_tag(ptemplate, _count)
           _tag_tree.append(_pt)
           if _pt.tag_type in ('/TMPL_LOOP', '/TMPL_IF', ):
               return _count, _tag_tree
        _count = _count + 1
    return _count, _tag_tree

def find_closing_tag (ptemplate='', sposition =0, p_tag_type = 'TMPL_VAR', pmax_search= 500):
    _count = sposition
    _len = len(ptemplate)
    while _count <= _len:
        _test = ptemplate[_count, 1] 
        if _test == '>':
            return _count
        if _count > pmax_search:
            raise Exception("Failed to find the closing > after 500 characters search for %s position %s " %
                        (p_tag_type, sposition) ) 
        _count = _count + 1
    else:
        raise Exception("Failed to find the closing > for  %s position %s "% (p_tag_type,sposition))

def tag_attributes_extract(pstring='', pattribute='name' ):
    _swhere = pstring.lower().find(pattribute.lower())
    _rstring = ''
    if _swhere >=0:
        if pstring.count('"')%2 == 0 and pstring.count('"')> 0:
            _rstring = pstring[pstring.find('"'), pstring.find('"', 1)]
        elif pstring.count("'")%2 == 0 and pstring.count("'")>0:
            _rstring = pstring[pstring.find('"'), pstring.find('"', 1)]
        else:
            raise Exception(""" ' or " are not matching or missing completely in the attributes in for %s"""
                            % (pstring))
    return ''

def scan_tag(ptemplate= '', sposition=0):
    _pt = Parse_Tree()
    _pt.tag_sposition = sposition
    cposition = 0
    
    if ptemplate[sposition, 8 ].upper()== 'TMPL_VAR':
        _pt.tag_type = 'TMPL_VAR'
        _count = sposition + 8
        _pt.tag_eposition = find_closing_tag(ptemplate, sposition + 8)
        _pt.tag_raw = ptemplate(_pt.tag_sposition, _pt.tag_eposition)
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw)
        _pt.tag_default = tag_attributes_extract(_pt.tag_raw, 'default')
        _pt.tag_function = tag_attributes_extract(_pt.tag_raw, 'function')
        return _pt.tag_eposition, _pt    

    elif ptemplate[sposition, 9].upper() == 'TMPL_LOOP' :
        _pt.tag_type = 'TMPL_LOOP'
        _pt.tag_eposition = find_closing_tag(ptemplate, sposition+9)
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw, 'name')
        _pt.tag_default = tag_attributes_extract(_pt.tag_raw, 'default')
        _cposition, _pt.tag_children = scan_tag(ptemplate, _pt.tag_eposition)
        return _cposition, _pt

    elif ptemplate[sposition, 10].upper() == 'TMPL_BREAK': 
        _pt.tag_type = 'TMPL_BREAK'
        _pt.tag_eposition =find_closing_tag(ptemplate, sposition+ 10)
        return _pt.tag_eposition, _pt

    elif ptemplate[sposition, 13].upper() == 'TMPL_CONTINUE': 
        _pt.tag_type = 'TMPL_CONTINUE'
        _pt.tag_eposition =find_closing_tag(ptemplate, sposition+ 13)
        return _pt.tag_eposition, _pt

    elif ptemplate[sposition, 10].upper() == '/TMPL_LOOP' :
        _pt.tag_type = '/TMPL_LOOP'   
        _pt.tag_eposition =find_closing_tag(ptemplate, sposition+ 10)
        return _pt.tag_eposition, _pt

    elif ptemplate[sposition, 7].upper() == 'TMPL_IF' :
        _pt.tag_type = 'TMPL_IF'
        _pt.tag_eposition = find_closing_tag(ptemplate, sposition+7)
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw, 'name')
        _pt.tag_value = tag_attributes_extract(_pt.tag_raw, 'value')
        _cposition, _pt.tag_children = scan_tag(ptemplate, _pt.tag_eposition)
        return cposition, _pt

    elif ptemplate[sposition, 9].upper() == 'TMPL_ELSIF': 
        _pt.tag_type = 'TMPL_ELSEIF'
        _pt.tag_eposition = find_closing_tag(ptemplate, sposition+7)
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw, 'name')
        _pt.tag_value = tag_attributes_extract(_pt.tag_raw, 'value')
        _cposition, _pt.tag_children = scan_tag(ptemplate, _pt.tag_eposition)
        return cposition, _pt

    elif ptemplate[sposition, 8].upper() == '/TMPL_IF' :
        _pt.tag_type = '/TMPL_IF'
        _pt.tag_eposition =find_closing_tag(ptemplate, sposition+ 8)
        return _pt.tag_eposition, _pt

    elif ptemplate[sposition, 13].upper() == 'TMPL_FUNCTION': 
        _pt.tag_type = 'TMPL_FUNCTION'
        _pt.tag_eposition = find_closing_tag(ptemplate, sposition+13)
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw, 'name')
        _pt.tag_default = tag_attributes_extract(_pt.tag_raw, 'value')

    elif ptemplate[sposition, 10].upper() == 'TMPL_LOOPCOUNT' :
        _pt.tag_type = 'TMPL_LOOPCOUNT'

    elif ptemplate[sposition, 10].upper() == 'TMPL_INCLUDE':
        _pt.tag_type = 'TMPL_INCLUDE'

    else :
        _pt = None

    return sposition, _pt

    

def tag_list():
    """ <TMPL_VAR name = "varname" default = "value" function = "functionname", args>
    * <TMPL_INCLUDE name = "filename">
    * <TMPL_LOOP name = "loopname">
    * <TMPL_BREAK level = N>
    * <TMPL_CONTINUE level = N>
    * <TMP_LOOPCOUNT> returns the current count in a loop primary use is for conditional formating..
    * </TMPL_LOOP>
    * <TMPL_IF name = "varname" value = "testvalue">
    * <TMPL_ELSIF name = "varname" value = "testvalue">
    * <TMPL_ELSE>
    * </TMPL_IF>
    * <TMPL_FUNCTION name="function_name", args="comma delimited list of arguments that can be found in dictionary">
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

