from jinja2 import Template


def loop_test_build( psize = 50):
    _list= []
    import random
    for i in range(psize):
        _list.append({ 'row_count': i,
                    'loopVar': random.random()*1000, 
                    'loopVar2': random.choice([True, False, 'hiho', 'diped'])
                    })
    return _list

fd = open('benchmark.html').read()
template = Template(fd)
import datetime
context = loop_test_build(1000000)
t= datetime.datetime.now()
dd = template.render(aloop=context )
print('Time to render jinja  %s'%( (datetime.datetime.now() - t)) )

#print(dd)