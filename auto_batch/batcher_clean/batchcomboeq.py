#from batchlang import *
#from batchparser import *
import sdlpath
from sdlparser.SDLParser import *
from batchtechniques import AbstractTechnique
from batchoptimizer import PairInstanceFinder, PairInstanceFinderImproved

# BEGIN: Small Exponent Related classes to assist with tracking index numbers assigned to delta variables 
# across multiple verification equations. 
class ApplyEqIndex(AbstractTechnique):
    def __init__(self, index):
        self.index = index
    
    def visit(self, node, data):
        pass
        
    def visit_attr(self, node, data):
        if node.getAttribute() != "1":
            node.setDeltaIndex(self.index)
    
    def visit_pair(self, node, data):
        node.setDeltaIndex(self.index)
    
class AfterTech2AddIndex(AbstractTechnique):
    def __init__(self):
        pass
    
    def visit(self, node, data):
        pass
    
    def visit_exp(self, node, data):
        a = []
        if data.get('pair_index'): a = data.get('pair_index') # [str(i) for i in data['pair_index']]
        if Type(node.right) == ops.ATTR and node.right.getAttribute() == "delta":
            if len(a) > 0: node.right.setDeltaIndexFromSet(a)
            else: node.right.setDeltaIndexFromSet( node.left.getDeltaIndex() )
        elif Type(node.right) == ops.MUL:
            mul = node.right
            if Type(mul.left) == ops.ATTR and mul.left.getAttribute() == "delta":
                if len(a) > 0: mul.left.setDeltaIndexFromSet(a)
                else: mul.left.setDeltaIndexFromSet( node.left.getDeltaIndex() )
            if Type(mul.right) == ops.ATTR and mul.right.getAttribute() == "delta":
                if len(a) > 0: mul.right.setDeltaIndexFromSet(a)
                else: mul.right.setDeltaIndexFromSet( node.left.getDeltaIndex() )
        return
  
    def visit_pair(self, node, data):
        d = { 'pair_index':node.getDeltaIndex() }
        return d

class UpdateDeltaIndex(AbstractTechnique):
    def __init__(self):
        pass
    
    def visit(self, node, data):
        pass
    
    def visit_exp(self, node, data):
        a = []
        if data.get('attr'): a = data.get('attr')
        if Type(node.right) == ops.ATTR and node.right.getAttribute() == "delta":
            if len(a) > 0: node.right.setDeltaIndexFromSet(a)
            else: node.right.setDeltaIndexFromSet( node.left.getDeltaIndex() )
        elif Type(node.right) == ops.MUL:
            mul = node.right
            if Type(mul.left) == ops.ATTR and mul.left.getAttribute() == "delta":
                if len(a) > 0: mul.left.setDeltaIndexFromSet(a)
                else: mul.left.setDeltaIndexFromSet( node.left.getDeltaIndex() )
            if Type(mul.right) == ops.ATTR and mul.right.getAttribute() == "delta":
                if len(a) > 0: mul.right.setDeltaIndexFromSet(a)
                else: mul.right.setDeltaIndexFromSet( node.left.getDeltaIndex() )
        return
  
    def visit_attr(self, node, data):
        d = { 'attr':node.getDeltaIndex() }
        return d


# END

class TestForMultipleEq:
    def __init__(self):
        self.multiple = False
    
    def visit_and(self, node, data):
        if Type(node.left) == Type(node.right) and Type(node.left) == ops.EQ_TST:
            self.multiple = True
            
    def visit(self, node, data):
        pass

# So called technique 0
# addIndex: means that CombineMultipleEq will add index numbers to each equation for tracking purposes
# so that deltas will have appropriate numbers later.
class CombineMultipleEq(AbstractTechnique):
    def __init__(self, sdl_data=None, variables=None, addIndex=True):
        if sdl_data:
            AbstractTechnique.__init__(self, sdl_data, variables)
        self.inverse = BinaryNode("-1")
        self.finalAND   = [ ]
        self.attr_index = 0
        self.addIndex = addIndex
        self.debug      = False
        
    def visit_and(self, node, data):
        left = BinaryNode("1")
        right = BinaryNode("1")
        #print("handle left :=>", node.left, node.left.type)
        #print("handle right :=>", node.right, node.right.type)        
        if Type(node.left) == ops.EQ_TST:
            self.attr_index += 1
            pair_eq_index = self.attr_index
            left = self.visit_equality(node.left, pair_eq_index)

        if Type(node.right) == ops.EQ_TST:
            self.attr_index += 1
            pair_eq_index2 = self.attr_index
            right = self.visit_equality(node.right, pair_eq_index2)
        combined_eq = BinaryNode(ops.EQ_TST, left, right)
        print("combined_eq first: ", combined_eq)
        
        # test whether technique 6 applies, if so, combine?
#        tech6      = PairInstanceFinder()
#        ASTVisitor(tech6).preorder(combined_eq)
#        if tech6.testForApplication(): tech6.makeSubstitution(combined_eq); print("Result: ", combined_eq)# ; exit(-1)
#        if self.debug: print("Combined eq: ", combined_eq)
        tech6      = PairInstanceFinderImproved()
        ASTVisitor(tech6).preorder(combined_eq)
        if tech6.testForApplication(): tech6.makeSubstitution(combined_eq); print("Result: ", combined_eq)# ; exit(-1)
        if self.debug: print("Combined eq: ", combined_eq)
        self.finalAND.append(combined_eq)
        return
    
    # won't be called automatically (ON PURPOSE)
    def visit_equality(self, node, index):
        #print("index :=", index, " => ", node)
        if self.addIndex:
            aei = ApplyEqIndex(index)
            ASTVisitor(aei).preorder(node)
        # count number of nodes on each side
        lchildnodes = []
        rchildnodes = []
        getListNodes(node.left, Type(node), lchildnodes)
        getListNodes(node.right, Type(node), rchildnodes)
        lsize = len(lchildnodes)
        rsize = len(rchildnodes)
        _list = [ops.EXP, ops.PAIR, ops.ATTR]
        if (lsize == 1 and rsize > 1) or (lsize == rsize):
            # move from left to right
            if self.debug: print("Moving from L to R: ", node)
            new_left = self.createExp2(BinaryNode.copy(node.left), BinaryNode.copy(self.inverse), _list)
            new_node = self.createMul(BinaryNode.copy(node.right), new_left)
            if self.debug: print("Result L to R: ", new_node)
            return new_node
        elif lsize > 1 and rsize == 1:
            # move from right to left
            if str(node.right) != "1":
                if self.debug: print("Moving from R to L: ", node)
                new_right = self.createExp2(BinaryNode.copy(node.right), BinaryNode.copy(self.inverse), _list)
                new_node = self.createMul(BinaryNode.copy(node.left), new_right)
            else:
                new_node = node.left
            if self.debug: print("Result R to L: ", new_node)
            return new_node
        else:
            print("CE: missing case!")
            print("node: ", lsize, rsize, node)
            return

class SmallExpTestMul:
    def __init__(self, prefix=None):
        self.prefix = prefix
        
    def visit(self, node, data):
        pass

    def visit_pair(self, node, data):
        pass
#        print("pair node: ", node, ", delta_index: ", node.getAttrIndex())

    # find  'prod{i} on x' transform into ==> 'prod{i} on (x)^delta_i'
    def visit_eq_tst(self, node, data):
        # Restrict to only product nodes that we've introduced for 
        # iterating over the N signatures
        delta = BinaryNode("delta")
        _list = [ops.EXP, ops.PAIR, ops.ATTR]
        if str(node.left) != "1":
            node.left = AbstractTechnique.createExp2(BinaryNode.copy(node.left), delta, _list)            
        if str(node.right) != "1":
            node.right = AbstractTechnique.createExp2(BinaryNode.copy(node.right), BinaryNode.copy(delta), _list)
            