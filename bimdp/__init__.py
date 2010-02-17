"""
The BiNet package is an extension of the pure feed-forward flow concept in MDP.

It defines a framework for far more general flow sequences, involving 
top-down processes (e.g. for error backpropagation) or even loops.
So the 'bi' in BiNet primarily stands for 'bidirectional'.

BiNet is implemented by extending both the Node and the Flow concept. Both the
new BiNode and BiFlow classes are downward compatible with the classical
Nodes and Flows, allowing them to be combined with BiNet elements. 

The fundamental addition in BiNet is that BiNodes can specify a target node for
their output and that they can send messages to other nodes. A BiFlow is then
needed to interpret these arguments, e.g. to continue the flow execution at the
specified target node.

BiNet is fully integrated with the HiNet and the Parallel packages.


New BiNet concepts: Jumps and Messages
======================================

Jump targets are numbers (relative position in the flow) or strings, which are
then compared to the optional node_id. The target number 0 refers to the node
itself.
During execution a node can also use the value of EXIT_TARGET (which is
currently just 'exit') as target value to end the execution. The BiFlow
will then return the last output as result.  

Messages are standard Python dictionaries to transport information
that would not fit well into the standard x array. The dict keys also support
target specifications and other magic for more convenient usage.
This is described in more detail in the BiNode module.
"""

### T O D O ###

# TODO: rename binet to bimdp, use the standard subpackage name for nodes,
#    hinet and parallel, but maybe keep inspection in base bimdp

# TODO: use a special wrapper for classifier nodes
#    can already access methods like prop via the method magic,
#    but the return values of these methods have to be put into msg,
#    maybe make it also possible to use both prob and rank at the same time,
#    maybe by adding flags to the init or execute method?
#    Maybe make the standard classifier execute return a message dict if
#    requested, then no special wrapper would be required, could still use
#    this in standard MDP via the special classifier flow (no downsides!)

# TODO: provide ParallelBiNode to copy the stop_result attribute?
#    Or can we guarantee that stop_training is always called on the original
#    version? If we relly on this then it should be specified in the API. 

# ------------- optional ----------------

# TODO: use a target seperator like : and allow multiple occurances,
#    when the node is reached then one is removed until there is only one left.
#    Example: node_id:::target will use the target value when the node is
#        reached for the third time.

# TODO: Implement more internal checks for node output result?
#    Check that last element is not None? Use assume?

# TODO: implement switchlayer, a layer where each column represents a different
#    target, so the target value determines which nodes are used

# TODO: show more information in trace slides via mouse hover,
#    or enable some kind of folding (might be possible via CSS like suckerfish)

# TODO: make comments conform to RST format for use with sphinx


from binode import BiNodeException, BiNode, NODE_ID_KEY
from biflow import (MessageResultContainer, BiFlowException, BiFlow,
                    BiCheckpointFlow, EXIT_TARGET)
from binodes import *
from bihinet import *
from inspection import *
from parallel import *
import test

del binode
del binodes
del biflow
del bihinet
del inspection
del parallel