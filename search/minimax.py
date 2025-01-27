from c4.state import C4State
from search.node import NodeMinimax
from search.util import evaluation_function, BudgetExceededError

class Minimax:

    def __init__(self, 
                 budget: int, 
                 depth: int, 
                 max_player: int
                 ):
        self.depth = depth
        self.budget = budget    # max number of game state evaluations
        self.rootnode = NodeMinimax()
        self.prev_rootnode = self.rootnode
        self.max_player = max_player

    def pick_move(self, rootstate: C4State):
        
        self.prev_rootnode = self.rootnode
        self.rootnode = NodeMinimax()

        state = rootstate.copy()

        try:
            self.alpha_beta(self.rootnode,
                            state,
                            self.depth,
                            alpha=float('-inf'),
                            beta=float('inf'),
                            is_maximizing=False if state.last_player == self.max_player else True)
        except BudgetExceededError:
            return self.fallback_mode(rootstate)
        
        return self.rootnode.best_move()["move"]

    def alpha_beta(self, 
                   node: NodeMinimax,
                   state: C4State, 
                   depth: int, 
                   alpha: float, 
                   beta: float, 
                   is_maximizing: bool,
                   ):
        
        if self.budget == 0:
            raise BudgetExceededError("Minimax budget exceeded on recursive call!")
        
        self.budget -= 1

        if is_maximizing:
            cmp_fn = max
            best_util = float('-inf')
        else:
            cmp_fn = min
            best_util = float('inf')

        if depth == 0 or state.winner != 0: # terminal state or maximum depth
            util = evaluation_function(state, self.max_player)
            node.update(util)
            return util

        for move in state.get_possible_moves():
                
            state.make_move(move)
            child = node.add_child(move)
            
            # recursive call
            util = self.alpha_beta(
                node=child, 
                state=state, 
                depth=depth - 1, 
                alpha=alpha, 
                beta=beta, 
                is_maximizing=not is_maximizing
            )

            # updating best utility
            best_util = cmp_fn(best_util, util)
            
            # undoing move
            state.undo_move(move)

            # update pruning values
            if is_maximizing:
                alpha = cmp_fn(alpha, best_util)
            else:
                beta = cmp_fn(beta, best_util)

            # pruning
            if beta <= alpha:
                node.pruned = True
                break

        node.update(best_util)

        return best_util
    
    def fallback_mode(self, state: C4State):
        """
        Function called once the computational budget is exhausted (AKA: no more evaluations left).
        Reuses the search tree from previous move.
        Called 'depth' times before search tree is exhausted. 
        """
        # if no more search tree left, forfeit the game
        if len(self.prev_rootnode.children) == 0:
            raise BudgetExceededError("Minimax ran out of computational budget!")
        
        possible_moves = state.get_possible_moves()
        sorted_children = sorted(self.prev_rootnode.children, key=lambda c: c.util, reverse=True)

        for child in sorted_children:
            if child.move not in possible_moves:
                continue
            self.rootnode = child
            return child.move

        # no possible moves left
        # unreacheable
        raise BudgetExceededError("Minimax ran out of computational budget!")
        