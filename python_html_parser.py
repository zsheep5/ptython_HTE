"""
A simple python HTML parser.  takes in file object, file name, or string
context dictionary
return type file or stinrg
"""

from pickle import dumps, loads
from memcache import Client
from datetime import datetime as dt 
from datetime import timedelta as td
import os 
import io
import re 
import html

class Parse_Tree ():
    #simple class to hold the structure of the tags parsed
    tag_type = None
    tag_name = None  #Name of the tag for vars it the name in the context dictionary
    tag_value = None #used by if statments is the value compared against 
    tag_sposition = -1 #start of the caret  for the tag
    tag_eposition = -1 # ending carent close of the tag unless IF or LOOP then its the end of the caret for the closing tag 
    tag_function = ''  #python function
    tag_func_args = ''
    tag_include_file_name = None #if the template has an include line this should be the file 
    tag_default = ''  #default value for 
    tag_children = [] #tags that appear in below this tag typically in If or loops will have children
    tag_raw = '' #raw tag that has been extracted prior to parsing
    tag_string_to_process = '' # contains only the extracted text to be processed by the if or loop statements
    tag_processed_string = '' #contains the text after it has been processed by the template engine 
    tag_skip = False #tells processor to skip this tag primary used by if statements so else and elseif are not process just removed
    tag_caret_close = -1 # the closing caret for the tag  
    tag_else_position = -1
    tag_logicoperator = 'equal'

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
                preturn_fname = 'rendered', preturn_fext='.html',
                puse_cache=False, pcache_path='', pcache_type='file', pcache_age=30):
    _template = None
    rtag_tree = None
    _count = 1
    _rtext = ''
    ctag_tree = None
    global function_context
    function_context.update(pfunc_context)
    #if puse_cache and os.f :
    #    if pcache_type == 'file'
    #        _template = open(pcache_path + 'cached.' + pfile).read()
    #        if 

    if puse_cache == True:
        rtag_tree = cache_get_ptree(preturn_fname + preturn_fext, pcache_path, pcache_type, pcache_age)
        _rtext = cache_get_rtemplate(preturn_fname + preturn_fext, pcache_path, pcache_type, pcache_age )
        if _rtext != '' or _rtext is not None: ##the cache had a rendered template return that.
                if isinstance(_rtext, io.IOBase) and preturn_type == 'file' :
                    return _rtext
                else:
                    _rtext.read()  
                
    if ptype == 'file' :
        import io
        if isinstance(pfile, io.IOBase):
            pfile.seek(0) ##make sure start at the beginning 
            _template = pfile.read()
        else :
            _template = open(pfile, 'r').read()
    if ptype == 'string' :
        _template = pfile

    _template = tags_to_upper(_template, ('TMPL_INCLUDE',) )
    _template = process_include_files(_template, pmax_search=pmax_search)
    _template = tags_to_upper(_template, tag_list() )
    if rtag_tree is None: ##the cache failed to find a rendered template but we found the parse_tree so parse it  
        _count, rtag_tree =parse_template(_template)

    _rtext, ctag_tree = process_tag_tree( pcontext, rtag_tree, _template, pmisstag_text, 0, pbranch_limit, pdebug_mode)

    if puse_cache == True: 
        cache_ptree(rtag_tree, preturn_fname , pcache_path, pcache_type, pcache_age)
        cache_template(_rtext, preturn_fname + preturn_fext, pcache_path, pcache_type, pcache_age)

    if preturn_type == 'string':
        return _rtext
    elif preturn_type == 'file':
        return flush_template_to_disk (_rtext, pcache_path, preturn_fname, preturn_fext )

def tags_to_upper(ptemplate='', tag_list=()):
    r = ptemplate
    for i in tag_list:
        r = re.sub( i, i, r, flags=re.IGNORECASE)
    return r

def cache_ptree(p_ptree = None, pname='', pcache_path='', pcache_type='file', pcache_age=30 ):
    if pcache_type == 'file':
        flush_template_to_disk( dumps(p_ptree), pcache_path, 'parse_tree_'+ pname, pcache_path, 'wb' )
    elif pcache_type == 'memcache':
        if isinstance(pcache_path, Client):
            pcache_path.set(pname + "_" + str(dt.now()) , dumps(p_ptree) )
    return True

def cache_template(ptempl = '', pname='', pcache_path='', pcache_type='file', pcache_age=30):
    if pcache_type == 'file':
        flush_template_to_disk( ptempl, pcache_path, 'parse_tree_'+ pname, pcache_path )
    elif pcache_type == 'memcache':
        if isinstance(pcache_path, Client):
            pcache_path.set(pname + "_" + pcache_age , dumps(ptempl), pcache_age )
    return True

def cache_get_ptree(pname='', pcache_path='', pcache_type='file', pcache_age=30):
    if pcache_type == 'file':
        _f = pcache_path + 'parse_tree_'+ pname, pcache_path
        if  os.path.isfile(_f):
            age = dt.fromtimestamp(os.path.getmtime(_f)) + td(pcache_age)
            if dt.now() > age :
                os.remove(_f)
                return ''
            else:
                open(_f, pcache_path, 'rb' ).read()
                return loads(open(_f, pcache_path, 'rb' ).read())
        else: 
            return None
    elif pcache_type == 'memcache':
        _f = pname+ "_" + pcache_age
        if isinstance(pcache_path, Client):
            return loads(pcache_path.get(pname + "_" + pcache_age ))
    return None

def cache_get_rtemplate(pname='', pcache_path='', pcache_type='file', pcache_age=30):
    if pcache_type == 'file':
        _f = pcache_path + pname+ "_" + pcache_age
        if  os.path.isfile(_f):
            age = dt.fromtimestamp(os.path.getmtime(_f)) + td(pcache_age)
            if dt.now() > age :
                os.remove(_f)
                return ''
            else:
                return open (_f, pcache_path, 'r' )
        else :
            return ''
    elif pcache_type == 'memcache':
        _f = pname+ "_" + pcache_age
        if isinstance(pcache_path, Client):
            return pcache_path.get(pname + "_" + pcache_age )
    return ''

def flush_template_to_disk(ptemplate, pcache_path, preturn_fname, preturn_fext, pmode='w'):
    _t = open(pcache_path + preturn_fname + preturn_fext, pmode,)
    _t.write(ptemplate)
    _t.flush()
    _t.seek(0)
    return _t

def process_include_files(ptemplate = '', ptag='<TMPL_INCLUDE', pmax_search =100 ):
    _newtemplate = ptemplate
    while True:  ##simply while loop that should catch all the includes even after new text is added in
        _spos = _newtemplate.find('<TMPL_INCLUDE')
        if _spos == -1:
            return _newtemplate
        _epos = find_closing_caret( _newtemplate, sposition = _spos, p_tag_type='TMPL_INCLUDE', pmax_search=pmax_search)
        _filename = tag_attributes_extract(_newtemplate[_spos:_epos], 'name')
        try :
            _ntext = open(_filename,'r').read()
            _ntext = tags_to_upper(_ntext, ('TMPL_INCLUDE',)) ##fix up the tags to upper.. 
        except Exception:
            _newtemplate = _newtemplate[0:_spos] + "File Not Found" + _newtemplate[_epos+1:]

def logic_test(pleft, pright, poperator='equal' ):
    if poperator=='equal':
        return pleft == pright
    elif poperator=='greater':
        return pleft > pright
    elif poperator=='egreater':
        return pleft >= pright
    elif poperator=='less':
        return pleft < pright
    elif poperator=='eless':
        return pleft <= pright
    elif poperator=='notequal':
        return pleft != pright
    raise Exception('Bad If logic')
    
def process_tag_tree(pcontext={}, ptag_tree=[], ptemplate= '',
                    pmisstag_text = 'Tag Name not Found in Context', 
                    pbranch_count=0, pbranch_limit=10, pdebug_mode=False):
    #handles the logic, matching up the context variables template tags and text replacement in the template
    _return = ptemplate
    #_context_value= ''
    #_break_or_continue = None
    _an_else_is= False
    if pbranch_count == pbranch_limit:
        raise Exception(html.escape("Template Branch/Call Stack limit reached. current limit %s "%(pbranch_limit)))
    
    for itag in ptag_tree:
        if itag.tag_skip == True:
            _return = _return.replace(itag.tag_raw, '',1)
            continue
        elif itag.tag_type == 'TMPL_VAR' :
            if itag.tag_function == '':
                _return = _return.replace(itag.tag_raw, get_context_value(pcontext, itag.tag_name, itag.tag_default, pmisstag_text ),1)
            else:
                _return = _return.replace(itag.tag_raw, function_process(itag.tag_function, itag.tag_name, pcontext, itag.tag_default ), 1)
        elif itag.tag_type == 'TMPL_IF':
            _start =  _return.find(itag.tag_raw)
            #_end = _return.find(find_child_tag('/TMPL_IF', None, itag.tag_children).tag_raw)+8
            _context_value = get_context_value(pcontext, itag.tag_name, itag.tag_default, pmisstag_text )
            _compare = get_context_value(pcontext, itag.tag_value, itag.tag_value,'' )
            if logic_test(_context_value, _compare, itag.tag_logicoperator) :  ## process what is below or show text below this
                itag.tag_children = set_elseif_to_skip(itag.tag_children)
                _to_pass = ptemplate[itag.tag_caret_close+1: itag.tag_eposition ]
            else:
                itag.tag_children = set_if_children_to_skip(itag.tag_children) #need to process any elseif or else but do not process the template tags in the top if
                itag.tag_processed_string = ''
                _to_pass = ptemplate[itag.tag_else_position-1: itag.tag_eposition]
            if len(itag.tag_children)>0:  #have children need to processed them as the related else and if on nested in this
                itag.tag_processed_string, _break_or_continue  = process_tag_tree( pcontext, 
                                                                    itag.tag_children,
                                                                    _to_pass,
                                                                    #ptemplate[itag.tag_caret_close+1: itag.tag_eposition],  
                                                                    pmisstag_text, 
                                                                    (pbranch_count +1), 
                                                                    pbranch_limit)
                _return = _return.replace(itag.tag_raw, itag.tag_processed_string,1)
                if _break_or_continue is not None:  #hit a break event so exit this loop go back to calling function... 
                    return _return, _break_or_continue
            else: ##no childrened processed should have processed at least the /TMP_IF tag  this should never be executed
                _return = _return.replace(itag.tag_raw, itag.tag_processed_string,1)
        elif itag.tag_type == 'TMPL_ELSE' :
            if _an_else_is==True :
                _return = _return.replace(itag.tag_raw, '', 1)
                continue
            _an_else_is = True
            itag.tag_processed_string, _break_or_continue  = process_tag_tree( 
                                                            pcontext, 
                                                            itag.tag_children,
                                                            itag.tag_raw[itag.tag_raw.find('>')+1:],  
                                                            pmisstag_text, 
                                                            (pbranch_count +1), 
                                                            pbranch_limit)
            _return = _return.replace(itag.tag_raw, itag.tag_processed_string,1)
            if _break_or_continue is not None:
                return _return, _break_or_continue
        elif itag.tag_type == 'TMPL_ELSEIF':
            if _an_else_is==True :
                _return = _return.replace(itag.tag_raw, '', 1)
                continue
            _context_value = get_context_value(pcontext, itag.tag_name, itag.tag_default, pmisstag_text )
            _compare = get_context_value(pcontext, itag.tag_value, itag.tag_value,'' )
            if logic_test(_context_value, _compare, itag.tag_logicoperator):
                _an_else_is = True
                itag.tag_processed_string, _break_or_continue = process_tag_tree( pcontext, 
                                                                    itag.tag_children, 
                                                                    itag.tag_raw[itag.tag_raw.find('>')+1:],
                                                                    pmisstag_text, 
                                                                    (pbranch_count +1), 
                                                                    pbranch_limit)
                _return = _return.replace(itag.tag_raw, itag.tag_processed_string, 1)
                if _break_or_continue is not None:
                    return _return, _break_or_continue
        elif itag.tag_type =='/TMPL_IF':
            _return = _return.replace(itag.tag_raw, '',1)
        elif itag.tag_type == 'TMPL_LOOP' :
            ## now in a loop conidition need to check a few things
            ##if not check_child_tree('/TMPL_LOOP', itag.tag_children):
            ##    raise Exception("LOOP is missing an /TMP_LOOP TAG.  TMPL_LOOP position is %s"% (itag.tag_sposition))
            loop_context = pcontext.get(itag.tag_name, None)
            if loop_context is None:  ##failed to find the LIST of dictionariares in the context replace with pmisstag_text
               _return = _return.replace(itag.tag_raw, pmisstag_text, 1)
               continue
            if not isinstance(loop_context, list):
                e = html.escape("LOOP name: %s at position %s the context is not a list" % (itag.tag_name, itag.tag_sposition))
                raise Exception(e)
            _append_loop_text = ''
            _count = 0
            _pass_text = ptemplate[itag.tag_caret_close+1: itag.tag_eposition-12]
            _pass_bc = pbranch_count +1
            for iloop in loop_context:
                _count = _count + 1
                #if not isinstance(iloop, dict):
                #    raise Exception("LOOP name: %s at position %s context is a list, needs to be a Dictionary" % (itag.tag_name, itag.tag_sposition))
                iloop.update({'TMP_LOOPCOUNT':_count})    
                _result = process_tag_tree(iloop, 
                                                itag.tag_children, 
                                                _pass_text,
                                                pmisstag_text, 
                                                _pass_bc, 
                                                pbranch_limit)
                _append_loop_text +=  _result[0]
                if _result[1] is not None:
                    if  _result[1].tag_type == 'TMPL_BREAK': 
                        if  _result[1].tag_name == '' or  _result[1].tag_name == itag.tag_name:
                            break
                        else :
                            # break out to higher function call 
                            return _return.replace(itag.tag_raw, _append_loop_text, 1 ),  _result[1]
                    else:  ## has to be a continue
                        continue
            _return = _return.replace(itag.tag_raw, _append_loop_text, 1 )        
        elif itag.tag_type == 'TMPL_BREAK' or itag.tag_type== 'TMPL_CONTINUE':
            return _return, itag 
        
        elif itag.tag_type == 'TMPL_FUNCTION':
            itag.tag_processed_string = str(function_process(itag.tag_name, itag.tag_func_args, pcontext, 
                                                pdefault_text=pmisstag_text, pdebug_mode=pdebug_mode))
            _return = _return.replace(itag.tag_raw, itag.tag_processed_string , 1)
    return _return, None

def set_elseif_to_skip( ptag_tree=[] ):
    for itag in ptag_tree:
        if itag.tag_type in ('TMPL_ELSE', 'TMPL_ELSEIF' ):
           itag.tag_skip = True
        if itag.tag_type == '/TMPL_IF':
            _epurge = itag.tag_caret_close
            return ptag_tree
    return ptag_tree

def set_if_children_to_skip( ptag_tree=[] ):
    for itag in ptag_tree:
        if itag.tag_type in ('TMPL_VAR', 'TMPL_LOOP', 'TMPL_FUNCTION', 'TMPL_IF' ):
           itag.tag_skip = True
    return ptag_tree

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
        
def get_context_value(pcontext ={}, pname='', pdefault = None, pmisstag_text = 'Tag Name {ContextName} not Found in Context'):

    try :
        return str(pcontext[pname])
    except:
        _dots = pname.split('.') #test to see if the name has dots in the name this dotnotation is being used access the child dictionary
        if len(_dots) > 1 :
            _tempcontext = pcontext.get(_dots[0])
            if _tempcontext is not None:
                _return = get_context_child_value(_tempcontext, _dots[1:])
            else:
                _return = None
        else :
            _return = pcontext.get(pname, None)
            #_return = pcontext[pname]
        if _return is not None :
            return str(_return)
        if pdefault is not None and pdefault is not '' :
            return pdefault
        return pmisstag_text.format(ContextName=pname)

def get_context_child_value(pcontext={}, pdots=''):
    _tempcontext = pcontext.get(pdots[0])
    if _tempcontext is None:
        return None

    if len(pdots)>1: #still have child(en) to sort through
        _tempcontext = pcontext.get(pdots[0])
        return get_context_child_value(_tempcontext, pdots[1:])
    
    return _tempcontext

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
    _search_limit = sposition+ pmax_search
    while _count < _len:
        _test = ptemplate[_count] 
        if _test == '>':
            return _count
        if _count > _search_limit:
            raise Exception(html.escape("Failed to find the closing > after %s characters search for %s position %s " %
                        (pmax_search, p_tag_type, sposition) )) 
        _count = _count + 1
    else:
        raise Exception(html.escape("Failed to find the closing > for  %s position %s "% (p_tag_type,sposition)))

def find_closing_tag(ptemplate='', sposition =0, p_otage_type = '<TMPL_IF', p_ctag_type = '/TMPL_IF'):
    ##searchs a string finding the closeing /TMPL_if returning its starting position in the string 
    ## the template passed can not have the opening tag for the if or loop
    
    ## quick check if the string only has one great return that one
    _end_tag_count = ptemplate.count(p_ctag_type) 
    _tag_size = len(p_otage_type)
    if _end_tag_count == 1:
        _end_tag_position = ptemplate.find(p_ctag_type)
        return Parse_Tree(p_ctag_type, '', '',-1, _end_tag_position, 
                            ptag_caret_close=find_closing_caret(
                                            ptemplate, _end_tag_position, 
                                            p_ctag_type),
                            )
    if _end_tag_count == 0:
        e = html.escape("Cound not find the Closing tag for %s starting from position %s of the template: %s ptemplate" %(p_otage_type, sposition, ptemplate ))
        raise Exception(e)
    _count = 0 
    _open_tag_position = 0
    _end_tag_position = 0
    
    while _count <=_end_tag_count:
        _end_tag_position = ptemplate.find(p_ctag_type, _end_tag_position +_tag_size )
        _open_tag_position = ptemplate.find(p_otage_type, _open_tag_position+_tag_size)
        if _end_tag_position < _open_tag_position or _open_tag_position ==-1: ## great found the closing tag return it
            return Parse_Tree(p_ctag_type, '', '', -1, 
                            _end_tag_position, 
                            find_closing_caret(ptemplate, _end_tag_position, p_ctag_type) 
                            )
        _count = _count + 1
    
    raise Exception(html.escape("Closing Tag Mismatch for %s starting from position %s "%(p_otage_type, sposition)))

def find_sibling_tag_position ( ptemplate='', sposition =0, p_otage_type = '<TMPL_IF', p_stag_type = ('TMPL_ELSE', 'TMPL_ELSEIF' )):
    #scan for the sibling tag in template
    _closingif = ptemplate.count('/TMPL_IF')
    _len = len(ptemplate)
    _position = sposition
    while _position < _len :
        _otag_pos = ptemplate.find('<TMPL_IF', _position)
        _stag_else = ptemplate.find('<TMPL_ELSE', _position)
        
        if _otag_pos == -1 and _stag_else > 1 : # we do not have nested ifs to sort through to find our sibling
            return _stag_else
        elif _otag_pos == -1 and _stag_else == -1:
            _position = ptemplate.find('/TMPL_IF', _position)
            if _position ==-1:
                return _len
            return _position
        else : # nested ifs jump to the end if end tag and rerun search 
            _position = ptemplate.find('/TMPL_IF',_otag_pos)
            #_position = ptemplate.find('/TMPL_IF', _position)

def tag_attributes_extract(pstring='', pattribute='name', ptempate_snip= '' ):
    _swhere = pstring.lower().find(pattribute.lower())
    _offset = len(pattribute)
    _rstring = ''
    if _swhere >=0:
        _cuts = pstring[_swhere+_offset:]
        if _cuts.count('"')%2 == 0 and _cuts.count('"')> 0:
            _s = _cuts.find('"')+1
            return _cuts[_s: _cuts.find('"', _s)]
        elif _cuts.count("'")%2 == 0 and _cuts.count("'")>0:
            _s = _cuts.find("'")+1
            return _cuts[_s: _cuts.find('"', _s)]
        else:
            raise Exception(html.escape(""" ' or " are not matching  in the attributes for tag :  %s Template Snip %s"""
                            % (pattribute, pstring)))
    return ''

def tag_func_extract(pstring="function(list, of, args)" ):
    _step = pstring
    _inner_par =  _step.count('(')
    _outer_par = _step.count(')')
    _child_funcs = None
    if _inner_par != _outer_par:  ## have syntax errors  
        raise Exception(html.escape("function tag has mismatched '(' ')' fix template")) 
        
    if _inner_par > 1: #this has inner function to find and append as a child..
        _func_name, _func_args, _child_funcs = tag_func_extract(_step[_step.find('(')+1 : _step.rfind(')')])
        _child_funcs = Parse_Tree('TMPL_FUNCTION', ptag_name = _func_name, ptag_children=_child_funcs)
        _child_funcs.tag_func_args = _func_args
    _func_name = _step.strip()[:_step.find('(')-1]
    _func_args = _step[_step.find('(')+1 : _step.rfind(')')]
    return _func_name, _func_args, _child_funcs

def scan_tag(ptemplate= '', sposition=0):
    _pt = Parse_Tree()
    _pt.tag_sposition = sposition-1 # scan 
    cposition = 0
    test = ptemplate[sposition:sposition+8]
   
    if ptemplate[sposition:sposition+8]== 'TMPL_VAR':
        _pt.tag_type = 'TMPL_VAR'
        _count = sposition + 8
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition + 9)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_caret_close+1]
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw)
        _pt.tag_default = tag_attributes_extract(_pt.tag_raw, 'default' )
        _pt.tag_function = tag_attributes_extract(_pt.tag_raw, 'function')
        return _pt.tag_caret_close, _pt    

    elif ptemplate[sposition:sposition+9] == 'TMPL_LOOP' :
        _pt.tag_type = 'TMPL_LOOP'
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition+9)
        _pt.tag_name = tag_attributes_extract(ptemplate[sposition+9: _pt.tag_caret_close], 'name')
        _pt.tag_default = tag_attributes_extract(_pt.tag_raw, 'default')
        _end_tag = find_closing_tag(ptemplate[sposition+9:], 0, p_otage_type='<TMPL_LOOP', p_ctag_type='/TMPL_LOOP' )
        if _end_tag is None:
            raise Exception(html.escape("LOOP is missing an /TMP_LOOP TAG.  TMPL_LOOP position is %s"% (_pt.tag_sposition)))
        _pt.tag_eposition = _end_tag.tag_caret_close+sposition+10
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_eposition ]
        _cposition, _pt.tag_children = parse_template(ptemplate[_pt.tag_caret_close: _pt.tag_eposition])
        _pt.tag_children.append(_end_tag)
        return _pt.tag_eposition , _pt

    elif ptemplate[sposition:sposition+10] == 'TMPL_BREAK': 
        _pt.tag_type = 'TMPL_BREAK'
        
        _pt.tag_caret_close =find_closing_caret(ptemplate, sposition+ 10)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_caret_close+1]
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw, 'name')
        return _pt.tag_caret_close, _pt

    elif ptemplate[sposition:sposition+13] == 'TMPL_CONTINUE': 
        _pt.tag_type = 'TMPL_CONTINUE'
        _pt.tag_caret_close =find_closing_caret(ptemplate, sposition+ 13)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_caret_close+1]
        _pt.tag_name = tag_attributes_extract(_pt.tag_raw, 'name')
        return _pt.tag_caret_close, _pt

    elif ptemplate[sposition:sposition+7] == 'TMPL_IF'   :
        _pt.tag_type = 'TMPL_IF'
        _pt.tag_logicoperator = 'equal'
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition+7, 'TMPL_IF')
        _pt.tag_name = tag_attributes_extract(ptemplate[sposition+7: _pt.tag_caret_close], 'name')
        _pt.tag_value = tag_attributes_extract(ptemplate[sposition+7: _pt.tag_caret_close], 'value')
        _end_tag = find_closing_tag(ptemplate[sposition+7:])
        _pt.tag_logicoperator = logic_operation(ptemplate[sposition+7: _pt.tag_caret_close])
        if _end_tag is None:
            raise Exception(html.escape("TMP_IF is missing an /TMP_IF TAG.  TMPL_LOOP position is %s"% (_pt.tag_sposition)))
        _pt.tag_eposition = _end_tag.tag_caret_close+sposition+8
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_eposition]
        _cposition, _pt.tag_children = parse_template(ptemplate[_pt.tag_caret_close: _pt.tag_eposition-10])
        _end_tag.tag_raw = '</TMPL_IF>' 
        _pt.tag_children.append(_end_tag)
        _pt.tag_else_position = find_sibling_tag_position(ptemplate[sposition + 8: _pt.tag_eposition], 0) + 8 + sposition
        return _pt.tag_eposition, _pt

    elif ptemplate[sposition:sposition+11] == 'TMPL_ELSEIF' : 
        _pt.tag_type = 'TMPL_ELSEIF'
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition+11)
        _pt.tag_eposition = _pt.tag_caret_close+sposition+12
        _pt.tag_name = tag_attributes_extract(ptemplate[sposition+11: _pt.tag_caret_close], 'name')
        _pt.tag_value = tag_attributes_extract(ptemplate[sposition+11: _pt.tag_caret_close], 'value')
        _pt.tag_logicoperator = logic_operation(ptemplate[sposition+7: _pt.tag_caret_close])
        _stagpos = find_sibling_tag_position(ptemplate, sposition+11)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _stagpos ]
        _cposition, _pt.tag_children = parse_template(ptemplate[_pt.tag_caret_close+1: _stagpos ], 0 )
        
        return _stagpos, _pt

    elif ptemplate[sposition:sposition+9] == 'TMPL_ELSE': 
        _pt.tag_type = 'TMPL_ELSE'
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition+9)
        _pt.tag_eposition = _pt.tag_caret_close+sposition+10
        _pt.tag_name = tag_attributes_extract(ptemplate[sposition+9: _pt.tag_caret_close], 'name')
        _pt.tag_value = tag_attributes_extract(ptemplate[sposition+9: _pt.tag_caret_close], 'value')
        _stagpos = find_sibling_tag_position(ptemplate, sposition+9)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _stagpos ]
        _cposition, _pt.tag_children = parse_template(ptemplate[_pt.tag_caret_close+1: _stagpos ], 0 )
        return _stagpos, _pt

    elif ptemplate[sposition:sposition+13] == 'TMPL_FUNCTION': 
        _pt.tag_type = 'TMPL_FUNCTION'
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition+14)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_caret_close+1]
        _pt.tag_name, _pt.tag_func_args, _pt.tag_children = tag_func_extract( _pt.tag_raw[14:_pt.tag_caret_close])
        _pt.tag_default = tag_attributes_extract(_pt.tag_raw[14:_pt.tag_caret_close], 'default')
        return _pt.tag_caret_close+1, _pt

    elif ptemplate[sposition:sposition+14] == 'TMPL_LOOPCOUNT' :
        _pt.tag_type = 'TMPL_LOOPCOUNT'
        _pt.tag_caret_close = find_closing_caret(ptemplate, sposition+15)
        _pt.tag_raw = ptemplate[_pt.tag_sposition: _pt.tag_caret_close+1]
        return _pt.tag_caret_close+1, _pt

    else :
        _pt = None
    
    return sposition, _pt

def logic_operation(_psearch_string=''):
    _logic_operators =[
        'equal',
        'greater',
        'egreater',
        'less',
        'eless',
        'notequal',
    ]
    for i in _logic_operators:
        if _psearch_string.find(i) > 0:
            return i
    return 'equal'

def function_process(pfunc_name = '', pargs='', pcontext= {}, pinner_funcs=None,
                    pdefault_text ='Function not Found in Context or is not a Built-In Function', 
                    pdebug_mode=False ):
    
    global function_context
    _pass_in =[]
    _func = function_context.get(pfunc_name, None)
    if _func is None:
        return pdefault_text
    
    if pinner_funcs is not None:
        _pass_in.append(function_process(pinner_funcs.tag_name, 
                                    pinner_funcs.tag_func_args, 
                                    pcontext,  
                                    pinner_funcs.tag_children ))
    
    for _iargs in pargs.split(','):
        if _iargs == '':
            continue
        _pass_in.append(get_context_value(pcontext, _iargs))
    
    try:
        _return = _func(*_pass_in)
    except Exception as e:
        if pdebug_mode:
            raise 
        _return = html.escape(str(e))
    return _return 
 
def tag_list():
    """ <TMPL_VAR name = "varname" default = "value" function = "functionname">
    * <TMPL_INCLUDE name = "filename">
    * <TMPL_LOOP name = "loopname">
    * <TMPL_BREAK name = N>
    * <TMPL_CONTINUE name = N>
    * <TMP_LOOPCOUNT> returns the current count in a loop primary use is for conditional formating..
    * </TMPL_LOOP name = "" >
    * <TMPL_IF name = "varname" value = "testvalue" >
    * <TMPL_NIF name = "varname" value = "testvalue" >
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
    context = build_test_context()
    context.update({'aloop':loop_test_build()})
    print( render_html( test_template(), 'string', context ))

def build_test_context () :
    return {"varName":"haha1",
        "aLoop":[
            {"loopVar":"bool","loopVar2":True},
            {"loopVar":"float","loopVar2":'Unicode Test'} ],
        "sweet":{"name":"æ  ñ",
                "price":None, 
                "isBig": 44
                }
        }

def run_test_files():
    import random
    name= str(int(random.random()*100000)) + '.html'
    dd = open(name, 'w')
    dd.write(test_template())
    dd2 = open('include_'+name, 'w')
    dd2.write('get an include file: <TMPL_var name="file_include">' )
    dd2.flush()
    dd2.close()
    dd.write('\n' + '<TMPL_INCLUDE name = "'+'include_'+name +'" >'  )
    dd.flush()
    dd.close()
    context = build_test_context()
    context.update({'aLoop':loop_test_build(1000000)})
    context.update({'file_include':'include_'+name})
    import datetime 
    
    _template = test_template2()
    t= datetime.datetime.now()
    _count, rtag_tree =parse_template(_template)
    #return {'rtag_tree':rtag_tree, 'context':context}
    print('Time to build parse tree %s'%( (datetime.datetime.now() - t)) )
    t= datetime.datetime.now()
    process_tag_tree(context, rtag_tree)
    print('Time to render parse tree %s'%( (datetime.datetime.now() - t)) )
#    return test

def loop_test_build( psize = 50):
    _list= []
    import random
    for i in range(psize):
        _list.append({ 'row_count': i,
                    'loopVar': random.random()*1000, 
                    'loopVar2': random.choice([True, False, 'hiho', 'diped'])
                    })
    return _list

def test_template ():
    return """ <* This is a comment *>
    File var Name: <TMPL_var name="varName"> 
    <TMPL_LOOP name="aLoop"> 
    <li><a href=
    file _Loop has var <TMPL_var name="loopVar"> 
        value <TMPL_var name="loopVar2"> 
    </a></li>
    </TMPL_LOOP> 
        rowcount: <TMPL_var name="sweet.name">
        Sweet name: <TMPL_var name="sweet.name">
        Sweet price: <TMPL_var name="sweet.price">
    <TMPL_IF name="sweet.isBig" value="44">
        Sweet is big
    </TMPL_IF>

    <TMPL_IF name="sweet.isBig" value="66">
        test failed if Sweet is big
        <TMPL_var name="sweet.price">
    <TMPL_ELSEIF name="sweet.isBig" value="44">
        test children
        <TMPL_var name="sweet.price">
        <TMPL_IF name="sweet.name" value="haha1" >
            testing nested
            <TMPL_IF name="sweet.name" value="haha1" >
                test3 nested
            </TMPL_IF>
        </TMPL_IF>
    <TMPL_ELSEIF name="sweet.isBig" value="77">
      another test
    <TMPL_ELSE name="sweet.isBig" value="44">
    </TMPL_IF>

    <TMPL_FUNCTION len(sweet.isBig) >"""

def test_template2():
    return """
    <ul>
        <TMPL_LOOP name="aLoop"> 
            <li><a href=" <TMPL_var name="loopVar"> "
            value <TMPL_var name="loopVar2"> 
            </a></li>
        </TMPL_LOOP> 
    </ul>

    """

#dd = run_test_files()
#import cProfile
#g = {'process_tag_tree':process_tag_tree}
#cProfile.runctx('process_tag_tree(context, rtag_tree)', globals=g, locals=dd)    
#run_test_code()

#run_test_files()