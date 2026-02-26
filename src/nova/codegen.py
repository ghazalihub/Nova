from src.nova.nova_ast import *

class CodeGenerator:
    def __init__(self):
        self.indent_level = 0

    def indent(self):
        return "    " * self.indent_level

    def generate(self, node: Node) -> str:
        method_name = f'gen_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_gen)
        return visitor(node)

    def generic_gen(self, node):
        raise Exception(f'No gen_{type(node).__name__} method')

    def gen_Program(self, node: Program):
        return "\n".join(self.generate(stmt) for stmt in node.statements)

    def gen_ImportStatement(self, node: ImportStatement):
        names = ", ".join(node.names)
        return f"{self.indent()}from {node.source} import {names}"

    def gen_VarDeclaration(self, node: VarDeclaration):
        # Python doesn't have const at runtime in the same way, so we just generate assignment
        # We can add type hints if provided
        type_hint = f": {node.type_hint}" if node.type_hint else ""
        return f"{self.indent()}{node.name}{type_hint} = {self.generate(node.value)}"

    def gen_FunctionDeclaration(self, node: FunctionDeclaration):
        async_prefix = "async " if node.is_async else ""
        params = []
        for p in node.parameters:
            p_str = p['name']
            if p.get('type'):
                p_str += f": {p['type']}"
            params.append(p_str)

        header = f"{self.indent()}{async_prefix}def {node.name}({', '.join(params)})"
        if node.return_type:
            header += f" -> {node.return_type}"
        header += ":"

        self.indent_level += 1
        body = "\n".join(self.generate(stmt) for stmt in node.body)
        if not body:
            body = f"{self.indent()}pass"
        self.indent_level -= 1

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
            # Parallel loop using multiprocessing (simplified)
            # In a real implementation, we would wrap the body in a function
            res = f"{self.indent()}# Parallel loop (Note: Requires multiprocessing orchestration in runtime)\n"
            res += f"{self.indent()}for {node.target} in {self.generate(node.iterable)}:\n"
        else:
            res = f"{self.indent()}for {node.target} in {self.generate(node.iterable)}:\n"

        self.indent_level += 1
        body = "\n".join(self.generate(stmt) for stmt in node.body)
        if not body:
            body = f"{self.indent()}pass"
        res += body
        self.indent_level -= 1
        return res

    def gen_ModelDeclaration(self, node: ModelDeclaration):
        base = f"({node.base_class})" if node.base_class else ""
        res = f"{self.indent()}class {node.name}{base}:\n"
        self.indent_level += 1
        body = "\n".join(self.generate(stmt) for stmt in node.members)
        if not body:
            body = f"{self.indent()}pass"
        res += body
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
            return f"{self.generate(node.left)} = {self.generate(node.right)}"
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
        return node.name

    def gen_Literal(self, node: Literal):
        if isinstance(node.value, str):
            return f'"{node.value}"'
        if node.value is None:
            return "None"
        return str(node.value)

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
            items.append(f"{self.generate(k)}: {self.generate(v)}")
        return "{" + ", ".join(items) + "}"

    def gen_List(self, node: list):
        # For block bodies
        return "\n".join(self.generate(stmt) for stmt in node)
