"""
A simple python HTML parser.  takes in file point or file name,
context dictionary
return type file or stinrg
"""

class Parse_Tree ():
    #simple class to hold the structure of the tags parsed
    tag_type = None
    tag_name = None  #Name of the tag for vars it the name in the context dictionary
    tag_sposition = -1
    tag_eposition = -1
    tag_function = None  #python function
    tag_include_file_name = None #if the template has an include line this should be the file 
    tag_default = ''  #default value for 
    tag_children = [] #tags that appear in below this tag typically in If or loops will have children
    tag_raw = '' #raw tag that has been extracted prior to parsing  

    def __init__(self, ptag_type= 'TMPL_VAR', 
                ptag_name='', 
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
         

def render_html( pfile, ptype = 'file', pcontext = {}, preturn_type= 'string', ):
    _template = None
    if ptype == 'file':
        if isinstance(pfile, file):
            _template = pfile 
        else :
            _template = open(pfile, 'r').read()
    else:
        _template = pfile

    _count, tag_tree  =parse_template(_template)
    process_template(_template, pcontext, tag_tree)

def process_template(ptemplate='', pcontext={}, ptag_tree=[], pmisstag_text = 'Tag not Found in Conext'):
    #handles the logic, matching up the context variables template tags and text replacement in the template
    _return = ptemplate

    for itag in ptag_tree:
        if itag.tag_type == 'TMPL_VAR':
            _replace_text = pcontext.get(itag.tag_name, None)
            if _replace_text is None and itag.tag_default is not None:
                _replace_text = itag.tagdefault 



    return _return    

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
            break 
        _count = _count + 1
    else:
        raise Exception("Failed to find the closing > for  %s position %s "% (p_tag_type,sposition))

def tag_attributes_extract(pstring='', pattribute='name' ):
    _swhere = pstring.lower().find(pattribute.lower())
    _rstring
    if swhere >=0:
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
        ##find the end of this entry and the attributes
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
        _pt.tag_default = tag_attributes_extract(_pt.tag_raw, 'value')
        _cposition, _pt.tag_children = scan_tag(ptemplate, _pt.tag_eposition)
        return cposition, _pt
    elif ptemplate[sposition, 9].upper() == 'TMPL_ELSIF': 
        _pt.tag_type = 'TMPL_ELSEIF'
        _pt.tag_eposition = find_closing_tag(ptemplate, sposition+7)
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw, 'name')
        _pt.tag_default = tag_attributes_extract(_pt.tag_raw, 'value')
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
    elif ptemplate[sposition, 10].upper() == 'TMPL_COUNT' :
        _pt.tag_type = 'TMPL_COUNT'
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
        'TMPL_COUNT',
        '/TMPL_LOOP',
        'TMPL_IF',
        'TMPL_ELSIF',
        'TMPL_ELSE',
        '/TMPL_IF',
        'TMPL_FUNCTION',
       
    )

