
import unittest

import mdp
n = mdp.numx

from binet import (
    BiNode, IdentityBiNode, NODE_ID_KEY, SFABiNode, FDABiNode
)

from testnodes import JumpBiNode


class TestBiNode(unittest.TestCase):
    
    def test_msg_parsing1(self):
        """Test the message parsing and recombination."""
        class TestBiNode(BiNode):
            def _execute(self, x, a, b, d):
                self.a = a
                self.b = b
                self.d = d
                return x, {"g": 15, "z": 3}
            def is_trainable(self): return False
        binode = TestBiNode(node_id="test")
        b_key = "test" + NODE_ID_KEY + "b"
        d_key = "test" + NODE_ID_KEY + "d"
        msg = {"c": 12, b_key: 42, "a": 13, d_key: "bla"}
        _, msg = binode.execute(None, msg)
        self.assert_("a" in msg)
        self.assert_(b_key not in msg)
        self.assert_(d_key not in msg)
        self.assert_(binode.a == 13)
        self.assert_(binode.b == 42)
        self.assert_(binode.d == "bla")
        # test the message combination
        self.assert_(msg["g"] == 15)
        self.assert_(msg["z"] == 3)
        
    def test_msg_parsing2(self):
        """Test that an adressed argument is not found."""
        class TestBiNode(BiNode):
            def _execute(self, x, a, b):
                self.a = a
                self.b = b
            def is_trainable(self): return False
        binode = TestBiNode(node_id="test")
        b_key = "test" + NODE_ID_KEY + "b"
        d_key = "test" + NODE_ID_KEY + "d"
        msg = {"c": 12, b_key: 42, "a": 13, d_key: "bla"}
        binode.execute(None, msg)
        # TODO: could change this behavior to raise an exception if an
        #    adressed argument is not found.
        # self.assertRaises(Exception, lambda: binode.execute(None, msg))
        
    def test_msg_magic(self):
        """Test that the magic msg argument works."""
        class TestBiNode(BiNode):
            def _execute(self, x, a, msg, b):
                self.a = a
                self.b = b
                del msg["c"]
                msg["f"] = 1
                return x, msg
            def is_trainable(self): return False
        binode = TestBiNode(node_id="test")
        b_key = "test" + NODE_ID_KEY + "b"
        msg = {"c": 12, b_key: 42, "a": 13}
        _, msg = binode.execute(None, msg)
        self.assert_("a" in msg)
        self.assert_("c" not in msg)  # was deleted in _execute  
        self.assert_(msg["f"] == 1)
        self.assert_(b_key not in msg)
        self.assert_(binode.a == 13)
        self.assert_(binode.b == 42)
        
    def test_method_magic(self):
        """Test the magic method message key."""
        class TestBiNode(BiNode):
            def _test(self, x, a, b):
                self.a = a
                self.b = b
            def is_trainable(self): return False
        binode = TestBiNode(node_id="test")
        b_key = "test" + NODE_ID_KEY + "b"
        msg = {"c": 12, "a": 13, b_key: 42, "method": "test"}
        binode.execute(None, msg)
        self.assert_("a" in msg)
        self.assert_(b_key not in msg)
        self.assert_(binode.b == 42)
        
    def test_target_magic(self):
        """Test the magic target message key."""
        class TestBiNode(BiNode):
            def _execute(self, x, a, b):
                self.a = a
                self.b = b
            def is_trainable(self): return False
        binode = TestBiNode(node_id="test")
        b_key = "test" + NODE_ID_KEY + "b"
        target_key = "test" + NODE_ID_KEY + "target"
        msg = {"c": 12, b_key: 42, "a": 13, target_key: "test2"}
        result = binode.execute(None, msg)
        self.assert_(len(result) == 3)
        self.assert_(result[2] == "test2")
        
    def test_inverse_magic1(self):
        """Test the magic inverse method argument."""
        class TestBiNode(BiNode):
            def _inverse(self, x, a, b):
                self.a = a
                self.b = b
                y = n.zeros((len(x), self.input_dim))
                return y
            def is_trainable(self): return False
        binode = TestBiNode(node_id="test", input_dim=20, output_dim=10)
        b_key = "test" + NODE_ID_KEY + "b"
        msg = {"c": 12, "a": 13, b_key: 42, "method": "inverse"}
        x = n.zeros((5, binode.output_dim))
        result = binode.execute(x, msg)
        self.assert_(len(result) == 3)
        self.assert_(result[2] == -1)
        self.assert_(result[0].shape == (5, 20))

    def test_inverse_magic2(self):
        """Test overriding the magic inverse target."""
        class TestBiNode(BiNode):
            def _inverse(self, x, a, b):
                self.a = a
                self.b = b
                y = n.zeros((len(x), self.input_dim))
                return y, None, "test2"
            def is_trainable(self): return False
        binode = TestBiNode(node_id="test", input_dim=20, output_dim=10)
        b_key = "test" + NODE_ID_KEY + "b"
        msg = {"c": 12, "a": 13, b_key: 42, "method": "inverse"}
        x = n.zeros((5, binode.output_dim))
        result = binode.execute(x, msg)
        self.assert_(result[2] == "test2")
    
    def test_stoptrain_result1(self):
        """Test that stop_result is handled correctly."""
        stop_result = ({"test": 0}, 1)
        bi_sfa_node = SFABiNode(stop_result=stop_result,
                                node_id="testing binode")
        self.assertTrue(bi_sfa_node.is_trainable())
        x = n.random.random((100,10))
        train_result = bi_sfa_node.train(x)
        self.assertTrue(train_result == None)
        self.assertTrue(bi_sfa_node.is_training())
        result = bi_sfa_node.stop_training()
        self.assertTrue(result == stop_result)
        self.assertTrue(bi_sfa_node.input_dim == 10)
        self.assertTrue(bi_sfa_node.output_dim == 10)
        self.assertTrue(bi_sfa_node.dtype == "float64")

    def test_stoptrain_result2(self):
        """Test that stop_result is handled correctly for multiple phases."""
        stop_result = [({"test": 0}, 1), ({"test2": 0}, 2)]
        binode = FDABiNode(stop_result=stop_result,
                           node_id="testing binode")
        x = n.random.random((100,10))
        msg = {"cl": n.zeros(len(x))}
        binode.train(x, msg)
        result = binode.stop_training()
        self.assertTrue(result == stop_result[0])
        binode.train(x, msg)
        result = binode.stop_training()
        self.assertTrue(result == stop_result[1])

    
class TestIdentityBiNode(unittest.TestCase):
    
    def test_idnode(self):
        """Perform a basic test on the IdentityBiNode.
        
        Instantiation is tested and it should perform like an id node, but 
        accept msg arguments.
        """
        binode = IdentityBiNode(node_id="testing binode")
        x = n.random.random((10,5))
        msg = {"some array": n.random.random((10,3))}
        # see if msg causes no problem
        y, msg = binode.execute(x, msg)
        self.assertTrue(n.all(x==y))
        # see if missing msg causes problem
        y = binode.execute(x)
        self.assertTrue(n.all(x==y))

        
class TestJumpBiNode(unittest.TestCase):

    def test_node(self):
        """Test the JumpBiNode."""
        train_results = [[(0, "t1")], [None], [(3, "t3")]]
        stop_train_results = [None, (5, "st2"), (6, "st3")]
        execute_results = [(None, {}), None, (None, {}, "et4")]
        jumpnode = JumpBiNode(train_results=train_results, 
                              stop_train_results=stop_train_results, 
                              execute_results=execute_results)
        x = n.random.random((2,2))
        self.assertTrue(jumpnode.is_trainable())
        # training
        rec_train_results = []
        rec_stop_train_results = []
        for _ in range(len(train_results)):
            rec_train_results.append([jumpnode.train(x)])
            jumpnode.bi_reset()
            rec_stop_train_results.append(jumpnode.stop_training())
            jumpnode.bi_reset()
        self.assertTrue(not jumpnode.is_training())
        self.assertTrue(rec_train_results == train_results)
        self.assertTrue(rec_stop_train_results == rec_stop_train_results)
        # execution
        rec_execute_results = []
        for _ in range(4):  # note that this is more then the execute_targets
            rec_execute_results.append(jumpnode.execute(x))
        execute_results[1] = x
        execute_results.append(x)
        self.assertTrue((rec_execute_results == execute_results))
        self.assertTrue(jumpnode.loop_counter == 4)
        
    def test_node_bi(self):
        """Test the message and stop_message of JumpBiNode."""
        tmsg = {"test value": n.zeros((10))}  # test msg
        execute_results = [(tmsg, "test", tmsg, "test"), None, 
                           (tmsg, "e3", tmsg, "e4")]
        stop_message_results = [(tmsg, "test"), None]
        jumpnode = JumpBiNode(
                        execute_results=execute_results, 
                        stop_message_results=stop_message_results)
        x = n.random.random((10,5))
        self.assertTrue(not jumpnode.is_trainable())
        # stop_message results
        result = jumpnode.stop_message()
        self.assertTrue(result == stop_message_results[0])
        result = jumpnode.stop_message(tmsg)
        self.assertTrue(result is None)
        jumpnode.bi_reset()


def get_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBiNode))
    suite.addTest(unittest.makeSuite(TestIdentityBiNode))
    suite.addTest(unittest.makeSuite(TestJumpBiNode))
    return suite
            
if __name__ == '__main__':
    unittest.main() 