from src.nova.nova_ast import *

class ASTOptimizer:
    def optimize(self, node: Node) -> Node:
        method_name = f'opt_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_opt)
        return visitor(node)

    def generic_opt(self, node):
        if hasattr(node, "__dict__"):
            for attr, val in node.__dict__.items():
                if isinstance(val, list):
                    node.__dict__[attr] = [self.optimize(v) if isinstance(v, Node) else v for v in val]
                elif isinstance(val, Node):
                    node.__dict__[attr] = self.optimize(val)
        return node

    def opt_Program(self, node: Program):
        node.statements = [self.optimize(s) for s in node.statements]
        return node

    def opt_ForStatement(self, node: ForStatement):
        # Simple auto-vectorization pattern:
        # for (i in start..end) { target[i] = expr(i); }
        # where expr(i) uses i as index for other tensors

        if len(node.body) == 1 and isinstance(node.body[0], ExpressionStatement):
            expr = node.body[0].expression
            if isinstance(expr, BinaryOp) and expr.op == "=":
                target = expr.left
                value = expr.right

                # Check if target is indexing with the loop variable
                if self.is_indexing_with(target, node.target) and self.is_vectorizable(value, node.target):
                    # Convert to vectorized assignment
                    # a[i] = b[i] + c => a = b + c
                    vector_target = self.strip_index(target, node.target)
                    vector_value = self.strip_index(value, node.target)
                    return ExpressionStatement(BinaryOp(vector_target, "=", vector_value))

        node.body = [self.optimize(s) for s in node.body]
        return node

    def is_indexing_with(self, node, var_name):
        # match Call(MemberAccess(obj, "__getitem__"), [Identifier(var_name)])
        if isinstance(node, Call) and isinstance(node.callee, MemberAccess) and node.callee.member == "__getitem__":
            if len(node.arguments) == 1 and isinstance(node.arguments[0], Identifier) and node.arguments[0].name == var_name:
                return True
        return False

    def is_vectorizable(self, node, var_name):
        # Simplified: check if all usages of var_name are for indexing
        # and there are no non-vectorizable ops
        return True # For PoC

    def strip_index(self, node, var_name):
        if self.is_indexing_with(node, var_name):
            return node.callee.object

        if isinstance(node, BinaryOp):
            return BinaryOp(self.strip_index(node.left, var_name), node.op, self.strip_index(node.right, var_name))

        if isinstance(node, Literal):
            return node

        return node
