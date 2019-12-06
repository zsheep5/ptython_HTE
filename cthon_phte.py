from distutils.core import setup 
from Cython.Build import cythonize

dd = open('python_html_parser.py').read()
cc = open('cython_html_parser.pyx', 'w')
cc.write(dd)
cc.flush()
cc.close()

setup(
    ext_modules = cythonize("cython_html_parser.pyx")
)