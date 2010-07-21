# Modular toolkit for Data Processing (MDP)
"""
The Modular toolkit for Data Processing (MDP) is a library of widely
used data processing algorithms that can be combined according to a
pipeline analogy to build more complex data processing software.

From the user's perspective, MDP consists of a collection of
supervised and unsupervised learning algorithms, and other data
processing units (nodes) that can be combined into data processing
sequences (flows) and more complex feed-forward network
architectures. Given a set of input data, MDP takes care of
successively training or executing all nodes in the network. This
allows the user to specify complex algorithms as a series of simpler
data processing steps in a natural way.

The base of available algorithms is steadily increasing and includes,
to name but the most common, Principal Component Analysis (PCA and
NIPALS), several Independent Component Analysis algorithms (CuBICA,
FastICA, TDSEP, JADE, and XSFA), Slow Feature Analysis, Gaussian
Classifiers, Restricted Boltzmann Machine, and Locally Linear
Embedding.

Particular care has been taken to make computations efficient in terms
of speed and memory.  To reduce memory requirements, it is possible to
perform learning using batches of data, and to define the internal
parameters of the nodes to be single precision, which makes the usage
of very large data sets possible.  Moreover, the 'parallel' subpackage
offers a parallel implementation of the basic nodes and flows.

From the developer's perspective, MDP is a framework that makes the
implementation of new supervised and unsupervised learning algorithms
easy and straightforward.  The basic class, 'Node', takes care of
tedious tasks like numerical type and dimensionality checking, leaving
the developer free to concentrate on the implementation of the
learning and execution phases. Because of the common interface, the
node then automatically integrates with the rest of the library and
can be used in a network together with other nodes. A node can have
multiple training phases and even an undetermined number of phases.
This allows the implementation of algorithms that need to collect some
statistics on the whole input before proceeding with the actual
training, and others that need to iterate over a training phase until
a convergence criterion is satisfied. The ability to train each phase
using chunks of input data is maintained if the chunks are generated
with iterators. Moreover, crash recovery is optionally available: in
case of failure, the current state of the flow is saved for later
inspection.

MDP has been written in the context of theoretical research in
neuroscience, but it has been designed to be helpful in any context
where trainable data processing algorithms are used. Its simplicity on
the user side together with the reusability of the implemented nodes
make it also a valid educational tool.

http://mdp-toolkit.sourceforge.net
"""

class MDPException(Exception):
    """Base class for exceptions in MDP."""
    pass

class MDPWarning(UserWarning):
    """Base class for warnings in MDP."""
    pass

import os as _os

# list of supported numerical extensions
_NUMX_LABELS = ['scipy', 'numpy']

# To force MDP to use one specific extension module
# set the environment variable MDPNUMX
# Mainly useful for testing
_USR_LABEL = _os.getenv('MDPNUMX')
if _USR_LABEL in _NUMX_LABELS:
    _NUMX_LABELS = [_USR_LABEL]
elif _USR_LABEL is None:
    pass
else:
    err = ("\nExtension '%s' not supported. "
           "Supported extensions:\n %s" % (_USR_LABEL,str(_NUMX_LABELS)))
    raise ImportError(err)

# try to load in sequence: scipy, numpy
numx_description = None
numx_exceptions = {}
for _label in _NUMX_LABELS:
    try:
        if _label == 'scipy':
            import scipy, scipy.linalg, scipy.fftpack, scipy.version
            numx = scipy
            numx_rand = scipy.random
            numx_linalg = scipy.linalg
            numx_fft = scipy.fftpack
            numx_description = 'scipy'
            numx_version = scipy.version.version
            del scipy
            break
        else:
            import numpy
            import numpy as numx
            import numpy.random as numx_rand
            import numpy.linalg as numx_linalg
            import numpy.fft as numx_fft
            numx_description = 'numpy'
            numx_version = numpy.version.version
            del numpy
            break
    except ImportError, exc:
        # collect exceptions in case we don't find anything
        # should help in debugging
        numx_exceptions[_label] = exc
        pass

if numx_description is None:
    msg = ("Could not import any of the numeric modules.\n"
           "Import errors:\n"+'\n'.join([label+': '+str(exc) for label, exc in
                                         numx_exceptions.items()]))
    raise ImportError(msg)
else:
    # we have numx, we don't need the exceptions anymore
    del numx_exceptions

del _os, _NUMX_LABELS, _USR_LABEL, _label


class ExternalDep(object):
    def __init__(self, version=None, failmsg=None):
        self.available = None
        self.version = version
        self.failmsg = failmsg
        self.module = "unknown"

    def __repr__(self):
        if self.available:
            return "%s" % self.version
        else:
            return "FAILED: %s" % self.failmsg

class ExternalDepFail(ExternalDep):
    def __init__(self, failmsg):
        super(ExternalDepFail, self).__init__(version=None, failmsg=failmsg)
        self.available = False

class ExternalDepFound(ExternalDep):
    def __init__(self, version="unknown version"):
        super(ExternalDepFound, self).__init__(version=version, failmsg=None)
        self.available = True


import utils

__version__ = '2.6'
__revision__ = utils.get_git_revision()
__authors__ = 'Pietro Berkes, Rike-Benjamin Schuppner, Niko Wilbert, and Tiziano Zito'
__copyright__ = '(c) 2003-2010 Pietro Berkes, Rike-Benjamin Schuppner, Niko Wilbert, Tiziano Zito'
__license__ = 'LGPL v3, http://www.gnu.org/licenses/lgpl.html'
__contact__ = 'mdp-toolkit-users@lists.sourceforge.net'


from utils.routines import OrderedDict

class Requirements(object):
    def __getitem__(self, key):

        if key in self._features:
            return self._features[key]
        raise KeyError("'%s'" % key)

    def check_feature(self, feature, prop):
        self._features[feature] = prop()

    def add_info(self, feature, val):
        self._features[feature] = val

    def __init__(self):
        self._features = OrderedDict()

        self.add_info('MDP Version', __version__)
        self.add_info('MDP Revision', __revision__)
        self.check_feature("Numerical Backend", self.numerical_backend)
        self.check_feature("Parallel Python", self.has_parallel_python)
        self.check_feature("shogun", self.has_shogun)
        self.check_feature("LibSVM", self.has_libsvm)
        self.check_feature("Symeig Backend", self.symeig)
    
    def has_parallel_python(self):
        try:
            import pp as __pp
        except ImportError as msg:
            return ExternalDepFail(msg)
        return ExternalDepFound()

    def has_shogun(self):
        try:
            import shogun.Kernel as _sgKernel
            import shogun.Classifier as _sgClassifier
        except ImportError as msg:
            return ExternalDepFail(msg)
        # We need to have at least SHOGUN 0.9, as we rely on
        # SHOGUN's CClassifier::classify() method.
        # (It makes our code much nicer, by the way.)
        #
        if not hasattr(_sgClassifier.Classifier, 'classify'):
            return ExternalDepFail("CClassifier::classify not found")
        try:
            version = _sgKernel._Kernel.Version_get_version_release()
        except AttributeError:
            version = ""

        if not (version.startswith('v0.9') or version.startswith('v1.')):
            return ExternalDepFail("We need at least SHOGUN version 0.9.")
        return ExternalDepFound(version)

    def has_libsvm(self):
        try:
            import svm as libsvm
        except ImportError as msg:
            return ExternalDepFail(msg)
        return ExternalDepFound()

    def numerical_backend(self):
        return numx_description + numx_version

    def symeig(self):
        import utils
        # check what symeig are we using
        if utils.symeig is utils.wrap_eigh:
            SYMEIG = 'scipy.linalg.eigh'
        else:
            try:
                import symeig
                if utils.symeig is symeig.symeig:
                    SYMEIG = 'symeig'
                elif utils.symeig is utils._symeig_fake:
                    SYMEIG = 'symeig_fake'
                else:
                    SYMEIG = 'unknown'
            except ImportError:
                if utils.symeig is utils._symeig_fake:
                    SYMEIG = 'symeig_fake'
                else:
                    SYMEIG = 'unknown'
        return SYMEIG
    
    def info(self):
        """Return nicely formatted info about MDP."""
        return ''.join([feature+': ' + str(self[feature])+'\n' for feature in self._features])

req = Requirements()
print req.info()

# import the utils module (used by other modules)
# here we set scipy_emulation if needed.
import utils

# import exceptions from nodes and flows
from signal_node import (NodeException, TrainingException,
                         TrainingFinishedException, IsNotTrainableException,
                         IsNotInvertibleException)
from linear_flows import CrashRecoveryException, FlowException, FlowExceptionCR

# import base node and flow classes
from signal_node import NodeMetaclass, Node, Cumulator
from linear_flows import (Flow, CheckpointFlow,
                          CheckpointFunction, CheckpointSaveFunction)

# import helper functions:
from helper_funcs import pca, whitening, fastica, sfa, get_eta

# import extension mechanism
from extension import (ExtensionException, extension_method,
                       ExtensionNodeMetaclass,
                       ExtensionNode, get_extensions,
                       get_active_extensions, with_extension,
                       activate_extension, deactivate_extension,
                       activate_extensions, deactivate_extensions,
                       extension)

# import classifier node
from classifier_node import (ClassifierNode, ClassifierCumulator)

# import our modules
import nodes
import hinet
import parallel

# import test functions:
from test import test


def info():
    """Return nicely formatted info about MDP."""
    import sys
    sys.stderr.write(req.info())


# clean up namespace
del signal_node
del linear_flows
del classifier_node

# explicitly set __all__, mainly needed for epydoc
__all__ = ['CheckpointFlow', 'CheckpointFunction', 'CheckpointSaveFunction',
           'CrashRecoveryException', 'Cumulator', 'Flow', 'FlowException',
           'FlowExceptionCR', 'IsNotInvertibleException',
           'IsNotTrainableException', 'MDPException', 'MDPWarning', 'Node',
           'NodeException', 'TrainingException', 'TrainingFinishedException',
           'contrib', 'get_eta', 'graph', 'helper_funcs', 'hinet', 'nodes',
           'numx_description', 'pca', 'sfa', 'test', 'utils', 'whitening',
           'parallel', 'numx_version',
           'extension_method', 'ExtensionNodeMetaclass', 'ExtensionNode',
           'get_extensions', 'get_active_extension_names', 'with_extension',
           'activate_extension', 'deactivate_extension', 'activate_extensions',
           'deactivate_extensions',
           'ClassifierNode',
           'req',
           ]
