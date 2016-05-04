"""
While we use Cython as programming language for the extension modules, we
follow Cython's recommendation to distribute pre-generated .c/.cpp files.
Thus, Cython does not need to be installed on the machine of the user installing
WhatsHap. Pass --cython on the command line to force Cython to be run.

If the .c/.cpp files are not found or out of date, such as in a fresh Git
checkout, then Cython is always run.
"""
import sys
import os.path
from setuptools import setup, Extension
from distutils.version import LooseVersion
from distutils.command.sdist import sdist as _sdist
from distutils.command.build_ext import build_ext as _build_ext

# set __version__
exec(next(open('whatshap/__init__.py')))

MIN_CYTHON_VERSION = '0.17'

if sys.version_info < (3, 2):
	sys.stdout.write("At least Python 3.2 is required.\n")
	sys.exit(1)
if sys.version_info < (3, 3):
	# need backport of contextlib.ExitStack
	extra_install_requires = ['contextlib2']
else:
	extra_install_requires = []


def no_cythonize(extensions, **_ignore):
	"""
	Change file extensions from .pyx to .c or .cpp.

	Copied from Cython documentation
	"""
	for extension in extensions:
		sources = []
		for sfile in extension.sources:
			path, ext = os.path.splitext(sfile)
			if ext in ('.pyx', '.py'):
				if extension.language == 'c++':
					ext = '.cpp'
				else:
					ext = '.c'
				sfile = path + ext
			sources.append(sfile)
		extension.sources[:] = sources


def check_cython_version():
	"""exit if Cython not found or out of date"""
	try:
		from Cython import __version__ as cyversion
	except ImportError:
		sys.stdout.write(
			"ERROR: Cython is not installed. Install at least Cython version " +
			str(MIN_CYTHON_VERSION) + " to continue.\n")
		sys.exit(1)
	if LooseVersion(cyversion) < LooseVersion(MIN_CYTHON_VERSION):
		sys.stdout.write(
			"ERROR: Your Cython is at version '" + str(cyversion) +
			"', but at least version " + str(MIN_CYTHON_VERSION) + " is required.\n")
		sys.exit(1)


extensions = [
	Extension('whatshap.core',
		sources=['whatshap/core.pyx',
			'src/pedigree.cpp', 'src/dptable.cpp', 'src/columncostcomputer.cpp',
			'src/pedigreedptable.cpp', 'src/pedigreecolumncostcomputer.cpp',
			'src/columnindexingiterator.cpp', 'src/columnindexingscheme.cpp',
			'src/entry.cpp', 'src/graycodes.cpp', 'src/read.cpp',
			'src/readset.cpp', 'src/columniterator.cpp', 'src/indexset.cpp',
			'src/pedigreepartitions.cpp'
		], language='c++', extra_compile_args=["-std=c++11"],),
	Extension('whatshap.priorityqueue',
		sources=['whatshap/priorityqueue.pyx'], language='c++', extra_compile_args=["-std=c++11"]),
]


class build_ext(_build_ext):
	def run(self):
		# If we encounter a PKG-INFO file, then this is likely a .tar.gz/.zip
		# file retrieved from PyPI that already includes the pre-cythonized
		# extension modules, and then we do not need to run cythonize().
		if os.path.exists('PKG-INFO'):
			no_cythonize(extensions)
		else:
			# Otherwise, this is a 'developer copy' of the code, and then the
			# only sensible thing is to require Cython to be installed.
			check_cython_version()
			from Cython.Build import cythonize
			self.extensions = cythonize(self.extensions)
		_build_ext.run(self)


class sdist(_sdist):
	def run(self):
		# Make sure the compiled Cython files in the distribution are up-to-date
		from Cython.Build import cythonize
		cythonize(extensions)
		_sdist.run(self)


setup(
	name = 'whatshap',
	version = __version__,
	author = 'WhatsHap authors',
	author_email = 'whatshap@cwi.nl',
	url = 'https://bitbucket.org/whatshap/whatshap/',
	description = 'phase genomic variants using DNA sequencing reads',
	license = 'MIT',
	cmdclass = {'sdist': sdist, 'build_ext': build_ext},
	ext_modules = extensions,
	packages = ['whatshap', 'whatshap.scripts'],
	scripts = ['bin/whatshap', 'bin/phasingstats'],
	install_requires = ['pysam<0.9.0', 'PyVCF'] + extra_install_requires,
	classifiers = [
		"Development Status :: 4 - Beta",
		"Environment :: Console",
		"Intended Audience :: Science/Research",
		"License :: OSI Approved :: MIT License",
		"Natural Language :: English",
		"Programming Language :: Cython",
		"Programming Language :: Python",
		"Programming Language :: Python :: 3",
		"Topic :: Scientific/Engineering :: Bio-Informatics"
	]
)
