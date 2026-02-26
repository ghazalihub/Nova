from src.nova.nova_ast import *

class CodeGenerator:
    def __init__(self):
        self.indent_level = 0
        self.in_class_context = [] # Stack of bools

    def indent(self):
        return "    " * self.indent_level

    def generate(self, node: Node) -> str:
        method_name = f'gen_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_gen)
        return visitor(node)

    def generic_gen(self, node):
        raise Exception(f'No gen_{type(node).__name__} method')

    def gen_Program(self, node: Program):
        # Add necessary imports based on features used
        header = ""
        if any(self.contains_node_type(node, StructDecl) for stmt in node.statements):
             header += "from dataclasses import dataclass\n"
        if any(self.contains_node_type(node, (NNBlock, GradientExpr, WeightsExpr, BatchIterator)) for stmt in node.statements):
             header += "import torch\nfrom torch.utils.data import DataLoader\n"
        if any(self.contains_node_type(node, MmapExpr) for stmt in node.statements):
             header += "import numpy as np\n"

        return header + "\n".join(self.generate(stmt) for stmt in node.statements)

    def contains_node_type(self, node, types):
        if isinstance(node, types):
            return True
        if hasattr(node, "__dict__"):
            for val in node.__dict__.values():
                if isinstance(val, list):
                    if any(self.contains_node_type(v, types) for v in val):
                        return True
                elif self.contains_node_type(val, types):
                    return True
        return False

    def gen_ImportStatement(self, node: ImportStatement):
        names = ", ".join(node.names)
        return f"{self.indent()}from {node.source} import {names}"

    def gen_ExportStmt(self, node: ExportStmt):
        # We can maintain a set of exported names if we want to generate __all__
        # For now, just generate the declaration
        return self.generate(node.declaration)

    def gen_VarDeclaration(self, node: VarDeclaration):
        # Python doesn't have const at runtime in the same way, so we just generate assignment
        # We can add type hints if provided
        type_hint = ""
        if node.type_hint:
            type_hint = f": {self.map_type(node.type_hint)}"

        if node.is_lazy:
            return f"{self.indent()}{node.name}{type_hint} = LazyProxy(lambda: {self.generate(node.value)})"
        return f"{self.indent()}{node.name}{type_hint} = {self.generate(node.value)}"

    def map_type(self, type_name):
        mapping = {
            "Int": "int",
            "Float": "float",
            "Str": "str",
            "Bool": "bool",
            "Null": "None"
        }
        return mapping.get(type_name, type_name)

    def gen_TrainStatement(self, node: TrainStatement):
        options = self.generate(node.options) if node.options else "None"
        return f"{self.indent()}train_loop({self.generate(node.model)}, {self.generate(node.dataset)}, {options})"

    def gen_FunctionDeclaration(self, node: FunctionDeclaration):
        async_prefix = "async " if node.is_async else ""
        params = []
        # Check if we are inside a class/model (top-level method)
        if self.in_class_context and self.in_class_context[-1]:
             params.append("self")

        # Nested functions should NOT have self injected unless they are inside a nested class
        self.in_class_context.append(False) # Entering function body context

        for p in node.parameters:
            p_str = p['name']
            if p.get('type'):
                p_str += f": {self.map_type(p['type'])}"
            params.append(p_str)

        header = f"{self.indent()}{async_prefix}def {node.name}({', '.join(params)})"
        if node.return_type:
            header += f" -> {self.map_type(node.return_type)}"
        header += ":"

        self.indent_level += 1
        body = "\n".join(self.generate(stmt) for stmt in node.body)
        if not body:
            body = f"{self.indent()}pass"
        self.indent_level -= 1

        self.in_class_context.pop()
        return f"{header}\n{body}"

    def gen_IfStatement(self, node: IfStatement):
        res = f"{self.indent()}if {self.generate(node.condition)}:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(stmt) for stmt in node.then_block)
        if not node.then_block:
             res += f"{self.indent()}pass"
        self.indent_level -= 1

        if node.else_block:
            if isinstance(node.else_block, IfStatement):
                # elif case
                # We need to adjust indentation because we are nesting it
                gen = CodeGenerator()
                gen.indent_level = self.indent_level
                elif_code = gen.generate(node.else_block).strip()
                res += f"\nel{elif_code}"
            else:
                res += f"\n{self.indent()}else:\n"
                self.indent_level += 1
                res += "\n".join(self.generate(stmt) for stmt in node.else_block)
                if not node.else_block:
                    res += f"{self.indent()}pass"
                self.indent_level -= 1
        return res

    def gen_ForStatement(self, node: ForStatement):
        if node.is_parallel:
            # Parallel loop using multiprocessing (simplified PoC)
            # We assume a global pool or a simple map
            res = f"{self.indent()}# Parallel loop\n"
            res += f"{self.indent()}from multiprocessing import Pool\n"
            res += f"{self.indent()}with Pool() as _nova_pool:\n"
            self.indent_level += 1
            body_expr = "None"
            if node.body and isinstance(node.body[0], ExpressionStatement):
                # We need the expression without the indentation and semicolon
                body_expr = self.generate(node.body[0].expression).strip()
            res += f"{self.indent()}_nova_pool.map(lambda {node.target}: {body_expr}, {self.generate(node.iterable)})\n"
            self.indent_level -= 1
            return res
        else:
            res = f"{self.indent()}for {node.target} in {self.generate(node.iterable)}:\n"

        self.indent_level += 1
        body = "\n".join(self.generate(stmt) for stmt in node.body)
        if not body:
            body = f"{self.indent()}pass"
        res += body
        self.indent_level -= 1
        return res

    def gen_StructDecl(self, node: StructDecl):
        res = f"{self.indent()}@dataclass\n{self.indent()}class {node.name}:\n"
        self.indent_level += 1
        for field in node.fields:
            res += f"{self.indent()}{field['name']}: {self.map_type(field['type'])}\n"
        if not node.fields:
            res += f"{self.indent()}pass\n"
        self.indent_level -= 1
        return res.rstrip()

    def gen_SchemaDecl(self, node: SchemaDecl):
        # Mapping to a dictionary for validation at runtime
        return f"{self.indent()}{node.name} = {self.generate(node.definition)}"

    def gen_PanicStmt(self, node: PanicStmt):
        return f"{self.indent()}raise RuntimeError({self.generate(node.message)})"

    def gen_RecoverStmt(self, node: RecoverStmt):
        res = f"{self.indent()}try:\n"
        self.indent_level += 1
        res += f"{self.indent()}pass # No-op for recover logic in PoC"
        self.indent_level -= 1
        res += f"\n{self.indent()}except Exception as e:\n"
        self.indent_level += 1
        body = "\n".join(self.generate(stmt) for stmt in node.body)
        res += body if body else f"{self.indent()}pass"
        self.indent_level -= 1
        return res

    def gen_ModelDeclaration(self, node: ModelDeclaration):
        base = f"({node.base_class})" if node.base_class else ""
        res = f"{self.indent()}class {node.name}{base}:\n"
        self.indent_level += 1
        self.in_class_context.append(True)
        body = "\n".join(self.generate(stmt) for stmt in node.members)
        if not body:
            body = f"{self.indent()}pass"
        res += body
        self.in_class_context.pop()
        self.indent_level -= 1
        return res

    def gen_MatchStatement(self, node: MatchStatement):
        # Transpiling to Python 3.10 match statement
        res = f"{self.indent()}match {self.generate(node.expression)}:\n"
        self.indent_level += 1
        for case in node.cases:
            guard = f" if {self.generate(case.guard)}" if case.guard else ""
            res += f"{self.indent()}case {self.generate(case.pattern)}{guard}:\n"
            self.indent_level += 1
            if isinstance(case.body, list):
                body = "\n".join(self.generate(stmt) for stmt in case.body)
            else:
                body = f"{self.indent()}{self.generate(case.body)}"
            if not body:
                body = f"{self.indent()}pass"
            res += body + "\n"
            self.indent_level -= 1
        self.indent_level -= 1
        return res.rstrip()

    def gen_TryStatement(self, node: TryStatement):
        res = f"{self.indent()}try:\n"
        self.indent_level += 1
        body = "\n".join(self.generate(stmt) for stmt in node.body)
        if not body:
            body = f"{self.indent()}pass"
        res += body + "\n"
        self.indent_level -= 1

        for catch in node.catches:
            type_hint = f" as {catch.variable}"
            exc_type = catch.type_hint if catch.type_hint else "Exception"
            res += f"{self.indent()}except {exc_type}{type_hint}:\n"
            self.indent_level += 1
            catch_body = "\n".join(self.generate(stmt) for stmt in catch.body)
            if not catch_body:
                catch_body = f"{self.indent()}pass"
            res += catch_body + "\n"
            self.indent_level -= 1

        if node.finally_block:
            res += f"{self.indent()}finally:\n"
            self.indent_level += 1
            fin_body = "\n".join(self.generate(stmt) for stmt in node.finally_block)
            if not fin_body:
                fin_body = f"{self.indent()}pass"
            res += fin_body + "\n"
            self.indent_level -= 1

        return res.rstrip()

    def gen_ReturnStatement(self, node: ReturnStatement):
        val = f" {self.generate(node.value)}" if node.value else ""
        return f"{self.indent()}return{val}"

    def gen_ExpressionStatement(self, node: ExpressionStatement):
        return f"{self.indent()}{self.generate(node.expression)}"

    def gen_BinaryOp(self, node: BinaryOp):
        if node.op == "=":
            # Check if we are in an expression context or statement context
            # Simplified: always assume assignment if op is "="
            return f"{self.generate(node.left)} = {self.generate(node.right)}"
        if node.op == "??":
            l = self.generate(node.left)
            r = self.generate(node.right)
            return f"({l} if {l} is not None else {r})"
        if node.op == "..":
            return f"range({self.generate(node.left)}, {self.generate(node.right)})"
        op_map = {"&&": "and", "||": "or", "!": "not "}
        op = op_map.get(node.op, node.op)
        return f"({self.generate(node.left)} {op} {self.generate(node.right)})"

    def gen_UnaryOp(self, node: UnaryOp):
        op_map = {"!": "not ", "-": "-"}
        op = op_map.get(node.op, node.op)
        return f"({op}{self.generate(node.operand)})"

    def gen_Call(self, node: Call):
        args = ", ".join(self.generate(arg) for arg in node.arguments)
        return f"{self.generate(node.callee)}({args})"

    def gen_MemberAccess(self, node: MemberAccess):
        if node.is_safe:
            return f"getattr({self.generate(node.object)}, '{node.member}', None)"
        return f"{self.generate(node.object)}.{node.member}"

    def gen_Identifier(self, node: Identifier):
        if node.name == "this":
            return "self"
        return node.name

    def gen_Literal(self, node: Literal):
        if isinstance(node.value, str):
            return f'"{node.value}"'
        if node.value is None:
            return "None"
        return str(node.value)

    def gen_TemplateLiteral(self, node: TemplateLiteral):
        # Simplistic f-string generation
        parts = []
        for p in node.parts:
            if isinstance(p, str):
                # Escape curly braces in f-strings
                escaped = p.replace("{", "{{").replace("}", "}}")
                parts.append(escaped)
            else:
                parts.append("{" + self.generate(p) + "}")
        return f'f"{"".join(parts)}"'

    def gen_NNBlock(self, node: NNBlock):
        # Mapping to torch.nn.Sequential
        res = "torch.nn.Sequential(\n"
        self.indent_level += 1
        items = []
        for stmt in node.statements:
             if isinstance(stmt, ExpressionStatement):
                 # Automatic torch.nn. prefix for identifiers in nn block
                 expr_code = self.generate(stmt.expression)
                 if isinstance(stmt.expression, Call) and isinstance(stmt.expression.callee, Identifier):
                      expr_code = "torch.nn." + expr_code
                 items.append(f"{self.indent()}{expr_code}")
        res += ",\n".join(items)
        self.indent_level -= 1
        res += "\n)"
        return res

    def gen_GradientExpr(self, node: GradientExpr):
        vars = ", ".join(self.generate(v) for v in node.variables)
        return f"torch.autograd.grad({self.generate(node.function)}, [{vars}])"

    def gen_WeightsExpr(self, node: WeightsExpr):
        return f"torch.randn({self.generate(node.shape)}, requires_grad=True)"

    def gen_BatchIterator(self, node: BatchIterator):
        return f"DataLoader({self.generate(node.dataset)}, batch_size={self.generate(node.size)})"

    def gen_MmapExpr(self, node: MmapExpr):
        return f"np.memmap({self.generate(node.path)})"

    def gen_AwaitExpr(self, node: AwaitExpr):
        return f"await {self.generate(node.expression)}"

    def gen_Lambda(self, node: Lambda):
        params = ", ".join(node.parameters)
        if isinstance(node.body, list):
             # Simplified: lambda body can't be a block in Python unless we use a nested function
             # For PoC, just support expression bodies
             return f"lambda {params}: {self.generate(node.body[0])}"
        return f"lambda {params}: {self.generate(node.body)}"

    def gen_Pipeline(self, node: Pipeline):
        # x |> f(y)  => f(x, y)
        # Assuming the right side is a call
        callee = self.generate(node.right.callee)
        args = [self.generate(node.left)] + [self.generate(arg) for arg in node.right.arguments]
        return f"{callee}({', '.join(args)})"

    def gen_ListLiteral(self, node: ListLiteral):
        elements = ", ".join(self.generate(e) for e in node.elements)
        return f"[{elements}]"

    def gen_DictLiteral(self, node: DictLiteral):
        items = []
        for k, v in zip(node.keys, node.values):
            key_code = self.generate(k)
            if isinstance(k, Identifier):
                key_code = f'"{key_code}"'
            items.append(f"{key_code}: {self.generate(v)}")
        return "{" + ", ".join(items) + "}"

    def gen_List(self, node: list):
        # For block bodies
        return "\n".join(self.generate(stmt) for stmt in node)
