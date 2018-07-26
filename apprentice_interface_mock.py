# -*- coding: utf-8 -*-
"""
Created on Fri Jun 22 16:33:23 2018

@author: robert.sheline

high level sketch of apprentice interfaces
the purpose is to allow concept learner, task learner, and
interaction patterns to be decoupled from each other, and from the
experiment implementation (e.g. mechanical turk, or chrome plugin)

any time e.g. teaching pattern refers to the task learner, it should happen
in the abstract base class, concrete implementations should not know about
anything other than their parent

what *are* the native concept{X}, context{C}, state{S}, action{A}, reward{R}
data types? 

what is the difference between concept, context, state? 
(concept is some sort of internal representation from the concept learner..?)
"""

#################
#concept_learner.py
#################
     

class AbstractConceptLearner: 
    # minimally implement fit, categorize, and _transform
    def fit(self, X):
        return self._fit(self._transform(X))
        
    def categorize(self, X):
        return self._categorize(self._transform(X))
        
    def ifit(self, X):
        self.fit(X)
        return self.categorize(X)
    
    def _transform(self, X):
        raise NotImplementedError
    
class TrestleConceptLeaner(AbstractConceptLearner):
    def __new__(self):
        TrestleTree = lambda _: True # placeholder
        self.tree = TrestleTree()
        
    def _transform(self, X):
        return X
    
    def _fit(self, X):
        self.tree.insert(X)
    
    def _categorize(self, X):
        return self.tree.categorize(X)

#################
# task_learner.py
#################
        
class AbstractTaskLearner:
    # minimally implement fit, decide, and _transform_context/action/reward
    def fit(self, C, A, R):
        return self._fit(self._transform_context(C),
                         self._transform_action(A),
                         self._transform_reward(R))
        
    def decide(self, C):
        return self._decide(self._transform_context(C))
    
    # ovverride these:
    def _transform_context(self, C):
        raise NotImplementedError
    
    def _transform_action(self, A):
    # transform task action data into implementation specific format, if needed
        raise NotImplementedError
    
    def _transform_reward(self, R):
    # transform reward into implementation specific format, if needed
        raise NotImplementedError
    
class QTaskLearner(AbstractTaskLearner):
    def __new__(self):
        QTable = lambda _: True # placeholder
        self.qt = QTable()
        
    def _transform_context(self, C):
        return C
    
    def _transform_action(self, A):
        return A
    
    def _transform_reward(self, R):
        return R
        
    def _fit(self, C, A, R):
        self.qt.update(C, A, R)
        
    def _decide(self, C):
        return self.qt.best_action(C)
        
#################
# teaching_interactions.py
#################

class AbstractTeachingModality:
    def transform(S):
        raise NotImplementedError

class HtmlModality(AbstractTeachingModality):
    def transform(S):
        return str(S)
    
#################


    
class AbstractTeachingType:
    ''' e.g., demo '''
    def __new__(self, modality):
        self.modality = modality
        
    
class DemoType(AbstractTeachingType):
    """ demonstrate a series of actions. """
    pass
    
    
class FeedbackType(AbstractTeachingType):
    pass
    

#################

class AbstractTeachingPattern:
    # (state machine of types)
    pass

class AlwaysDemo(AbstractTeachingPattern):
    pass
    
    

   
    





        
    
    

    
        
