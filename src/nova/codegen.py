import ast as py_ast
from src.nova.nova_ast import *
from typing import Union, List
import json

class SourceMapper:
    def __init__(self):
        self.mapping = {} # py_line -> nova_line

    def add(self, py_line, nova_line):
        if nova_line > 0:
            self.mapping[py_line] = nova_line

    def to_json(self):
        return json.dumps(self.mapping)

class PythonASTGenerator:
    """Maps Nova AST nodes to Python AST nodes."""
    def __init__(self):
        self.in_class = False

    def generate(self, node: Node) -> Union[py_ast.AST, List[py_ast.AST]]:
        method_name = f'gen_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_gen)
        return visitor(node)

    def generic_gen(self, node):
        return py_ast.Pass()

    def gen_Program(self, node: Program):
        body = []
        for stmt in node.statements:
            res = self.generate(stmt)
            if isinstance(res, list): body.extend(res)
            else: body.append(res)
        return py_ast.Module(body=body, type_ignores=[])

    def gen_VarDeclaration(self, node: VarDeclaration):
        target = py_ast.Name(id=node.name, ctx=py_ast.Store())
        value = self.generate(node.value)
        return py_ast.Assign(targets=[target], value=value)

    def gen_FunctionDeclaration(self, node: FunctionDeclaration):
        args = py_ast.arguments(posonlyargs=[], args=[py_ast.arg(arg=p['name']) for p in node.parameters], kwonlyargs=[], kw_defaults=[], defaults=[])
        if self.in_class: args.args.insert(0, py_ast.arg(arg='self'))
        body = []
        for s in node.body:
            res = self.generate(s)
            if isinstance(res, list): body.extend(res)
            else: body.append(res)
        if not body: body = [py_ast.Pass()]
        if node.is_async: return py_ast.AsyncFunctionDef(name=node.name, args=args, body=body, decorator_list=[], returns=None)
        return py_ast.FunctionDef(name=node.name, args=args, body=body, decorator_list=[], returns=None)

    def gen_Identifier(self, node: Identifier):
        id = "self" if node.name == "this" else node.name
        return py_ast.Name(id=id, ctx=py_ast.Load())

    def gen_Literal(self, node: Literal):
        return py_ast.Constant(value=node.value)

    def gen_BinaryOp(self, node: BinaryOp):
        left = self.generate(node.left)
        right = self.generate(node.right)
        op_map = {'+': py_ast.Add(), '-': py_ast.Sub(), '*': py_ast.Mult(), '/': py_ast.Div()}
        return py_ast.BinOp(left=left, op=op_map.get(node.op, py_ast.Add()), right=right)

    def gen_Call(self, node: Call):
        return py_ast.Call(func=self.generate(node.callee), args=[self.generate(arg) for arg in node.arguments], keywords=[])

    def gen_ExpressionStatement(self, node: ExpressionStatement):
        return py_ast.Expr(value=self.generate(node.expression))

    def gen_ReturnStatement(self, node: ReturnStatement):
        return py_ast.Return(value=self.generate(node.value) if node.value else None)

class CodeGenerator:
    """The main Nova Code Generator (Hybrid Pipeline)."""
    def __init__(self):
        self.indent_level = 0
        self.in_class_context = []
        self.current_py_line = 1
        self.mapper = SourceMapper()
        self.ast_generator = PythonASTGenerator()

    def indent(self):
        return "    " * self.indent_level

    def generate(self, node: Node) -> str:
        if node.line > 0:
            self.mapper.add(self.current_py_line, node.line)
        method_name = f'gen_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_gen)
        result = visitor(node)
        self.current_py_line += result.count('\n')
        return result

    def generic_gen(self, node):
        raise Exception(f'No gen_{type(node).__name__} method')

    def gen_Program(self, node: Program):
        self.top_level_calls = []
        header_template = """import sys
import os
{imports}

_nova_source_map = {source_map}

def _nova_excepthook(etype, value, tb):
    import traceback
    print("\\n--- Nova Traceback (Mapped) ---")
    curr_tb = tb
    while curr_tb:
        frame = curr_tb.tb_frame
        lineno = curr_tb.tb_lineno
        filename = frame.f_code.co_filename
        mapped_line = _nova_source_map.get(str(lineno), lineno)
        print(f'  File "{{filename}}", line {{mapped_line}}, in {{frame.f_code.co_name}}')
        curr_tb = curr_tb.tb_next
    print(f"\\n{{etype.__name__}}: {{value}}")
    print("\\n--- Nova AI Error Explanation ---")
    print("Possible causes based on your Nova source:")
    print("- Ensure all tensors have matching shapes for operations.")
    print("- Check if your training loop options are correctly formatted as a dictionary.")

sys.excepthook = _nova_excepthook
"""
        imports = []
        if self.contains_node_type(node, StructDecl): imports.append("from dataclasses import dataclass")
        if self.contains_node_type(node, (NNBlock, GradientExpr, WeightsExpr, BatchIterator)):
             imports.append("import torch\nfrom torch.utils.data import DataLoader")
        if self.contains_node_type(node, DatasetDecl): imports.append("from src.nova.data import Dataset")
        if self.contains_node_type(node, DeployStmt): imports.append("from src.nova.stdlib import deploy_model")
        if self.contains_node_type(node, TaintStmt): imports.append("from src.nova.stdlib import taint")
        if self.contains_node_type(node, FreezeStmt): imports.append("from src.nova.stdlib import freeze")
        if self.contains_node_type(node, MmapExpr): imports.append("import numpy as np")
        if self.contains_node_type(node, TestStmt): imports.append("import pytest")
        if self.contains_node_type(node, BenchStmt): imports.append("import timeit")

        import_str = "\n".join(imports)
        header_no_map = header_template.format(imports=import_str, source_map="{}")
        header_lines = header_no_map.count('\n') + 1

        self.current_py_line = header_lines + 1
        body = "\n".join(self.generate(stmt) for stmt in node.statements)
        header = header_template.format(imports=import_str, source_map=self.mapper.to_json())
        return header + "\n" + body

    def contains_node_type(self, node, types):
        if isinstance(node, types): return True
        if hasattr(node, "__dict__"):
            for val in node.__dict__.values():
                if isinstance(val, list):
                    if any(self.contains_node_type(v, types) for v in val): return True
                elif self.contains_node_type(val, types): return True
        return False

    def gen_ImportStatement(self, node: ImportStatement):
        names = ", ".join(node.names)
        return f"{self.indent()}from {node.source} import {names}"

    def gen_ExportStmt(self, node: ExportStmt):
        return self.generate(node.declaration)

    def gen_VarDeclaration(self, node: VarDeclaration):
        type_hint = f": {self.map_type(node.type_hint)}" if node.type_hint else ""
        if node.is_lazy: return f"{self.indent()}{node.name}{type_hint} = LazyProxy(lambda: {self.generate(node.value)})"
        return f"{self.indent()}{node.name}{type_hint} = {self.generate(node.value)}"

    def map_type(self, type_name):
        mapping = {"Int": "int", "Float": "float", "Str": "str", "Bool": "bool", "Null": "None"}
        return mapping.get(type_name, type_name)

    def gen_TrainStatement(self, node: TrainStatement):
        options = self.generate(node.options) if node.options else "None"
        return f"{self.indent()}train_loop({self.generate(node.model)}, {self.generate(node.dataset)}, {options})"

    def gen_FunctionDeclaration(self, node: FunctionDeclaration):
        async_prefix = "async " if node.is_async else ""
        params = ["self"] if self.in_class_context and self.in_class_context[-1] else []
        for p in node.parameters:
            p_str = p['name']
            if p.get('type'): p_str += f": {self.map_type(p['type'])}"
            params.append(p_str)
        header = f"{self.indent()}{async_prefix}def {node.name}({', '.join(params)})"
        if node.return_type: header += f" -> {self.map_type(node.return_type)}"
        header += ":"
        is_constructor = (node.name == "__init__" and self.in_class_context and self.in_class_context[-1])
        self.indent_level += 1
        self.in_class_context.append(False)
        body_parts = []
        if is_constructor: body_parts.append(f"{self.indent()}super().__init__()")
        body_parts.extend([self.generate(stmt) for stmt in node.body])
        body = "\n".join(body_parts) if body_parts else f"{self.indent()}pass"
        self.in_class_context.pop()
        self.indent_level -= 1
        return f"{header}\n{body}"

    def gen_IfStatement(self, node: IfStatement):
        res = f"{self.indent()}if {self.generate(node.condition)}:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(stmt) for stmt in node.then_block) or f"{self.indent()}pass"
        self.indent_level -= 1
        if node.else_block:
            if isinstance(node.else_block, IfStatement): res += f"\nel{self.generate(node.else_block).strip()}"
            else:
                res += f"\n{self.indent()}else:\n"
                self.indent_level += 1
                res += "\n".join(self.generate(stmt) for stmt in node.else_block) or f"{self.indent()}pass"
                self.indent_level -= 1
        return res

    def gen_ForStatement(self, node: ForStatement):
        if node.is_parallel:
            res = f"{self.indent()}# Parallel loop\n{self.indent()}from multiprocessing.pool import ThreadPool\n{self.indent()}with ThreadPool() as _nova_pool:\n"
            self.indent_level += 1
            body_expr = self.generate(node.body[0].expression).strip() if node.body and isinstance(node.body[0], ExpressionStatement) else "None"
            res += f"{self.indent()}_nova_pool.map(lambda {node.target}: {body_expr}, {self.generate(node.iterable)})\n"
            self.indent_level -= 1
            return res
        res = f"{self.indent()}for {node.target} in {self.generate(node.iterable)}:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(stmt) for stmt in node.body) or f"{self.indent()}pass"
        self.indent_level -= 1
        return res

    def gen_StructDecl(self, node: StructDecl):
        res = f"{self.indent()}@dataclass\n{self.indent()}class {node.name}:\n"
        self.indent_level += 1
        for field in node.fields: res += f"{self.indent()}{field['name']}: {self.map_type(field['type'])}\n"
        if not node.fields: res += f"{self.indent()}pass\n"
        self.indent_level -= 1
        return res.rstrip()

    def gen_SchemaDecl(self, node: SchemaDecl):
        return f"{self.indent()}{node.name} = {self.generate(node.definition)}"

    def gen_PanicStmt(self, node: PanicStmt):
        return f"{self.indent()}raise RuntimeError({self.generate(node.message)})"

    def gen_AssertStmt(self, node: AssertStmt):
        return f"{self.indent()}assert {self.generate(node.condition)}"

    def gen_RecoverStmt(self, node: RecoverStmt):
        res = f"{self.indent()}try:\n{self.indent()}    pass\n{self.indent()}except Exception as e:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(stmt) for stmt in node.body) or f"{self.indent()}pass"
        self.indent_level -= 1
        return res

    def gen_TestStmt(self, node: TestStmt):
        func_name = f"test_{node.name.replace(' ', '_')}"
        res = f"{self.indent()}def {func_name}():\n"
        self.indent_level += 1
        res += "\n".join(self.generate(stmt) for stmt in node.body) or f"{self.indent()}pass"
        self.indent_level -= 1
        return res + f"\n{self.indent()}{func_name}()"

    def gen_BenchStmt(self, node: BenchStmt):
        func_name = f"bench_{node.name.replace(' ', '_')}"
        res = f"{self.indent()}def {func_name}():\n"
        self.indent_level += 1
        res += f"{self.indent()}start = timeit.default_timer()\n"
        res += "\n".join(self.generate(stmt) for stmt in node.body) or f"{self.indent()}pass"
        res += f"\n{self.indent()}end = timeit.default_timer()\n{self.indent()}print(f'Bench {node.name}: {{end - start}}s')\n"
        self.indent_level -= 1
        return res + f"\n{self.indent()}{func_name}()"

    def gen_PromptDecl(self, node: PromptDecl):
        content = " ".join(self.generate(stmt) if not isinstance(stmt, ExpressionStatement) or not isinstance(stmt.expression, Literal) else str(stmt.expression.value) for stmt in node.body)
        return f"{self.indent()}{node.name} = \"\"\"{content.strip()}\"\"\""

    def gen_SecureStmt(self, node: SecureStmt):
        res = f"{self.indent()}# Secure block\n{self.indent()}try:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(stmt) for stmt in node.body) or f"{self.indent()}pass"
        self.indent_level -= 1
        return res + f"\n{self.indent()}except Exception as e: print(f'Security violation: {{e}}')"

    def gen_SharedStateStmt(self, node: SharedStateStmt):
        return f"{self.indent()}# Shared State\n" + "\n".join(self.generate(stmt) for stmt in node.body)

    def gen_DecoratorExpr(self, node: DecoratorExpr):
        inner = self.generate(node.expression).strip()
        if node.name == "jit": return f"{self.indent()}@torch.jit.script\n{inner}"
        return f"{self.indent()}@{node.name}\n{inner}"

    def gen_WithStmt(self, node: WithStmt):
        as_var = f" as {node.variable}" if node.variable else ""
        context_code = self.generate(node.context)
        import re
        context_code = re.sub(r'gpu_context\((\d+)\)', r'torch.cuda.device(\1)', context_code)
        context_code = re.sub(r'gpu_context', r'torch.cuda.device(0)', context_code)
        res = f"{self.indent()}with {context_code}{as_var}:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(stmt) for stmt in node.body) or f"{self.indent()}pass"
        self.indent_level -= 1
        return res

    def gen_CleanStmt(self, node: CleanStmt):
        target = self.generate(node.target)
        return f"{self.indent()}{target} = DataFrame({target}.dropna().drop_duplicates())"

    def gen_PlotStmt(self, node: PlotStmt):
        target = self.generate(node.target)
        options = self.generate(node.options) if node.options else "{}"
        return f"{self.indent()}plot({target}, type={options}.get('type', 'scatter'))"

    def gen_ModelDeclaration(self, node: ModelDeclaration):
        base_cls = node.base_class if node.base_class else "torch.nn.Module"
        res = f"{self.indent()}class {node.name}({base_cls}):\n"
        self.indent_level += 1
        if node.version: res += f"{self.indent()}_version = \"{node.version}\"\n"
        self.in_class_context.append(True)
        res += "\n".join(self.generate(stmt) for stmt in node.members) or f"{self.indent()}pass"
        self.in_class_context.pop()
        self.indent_level -= 1
        return res

    def gen_DatasetDecl(self, node: DatasetDecl):
        schema = f", schema={self.generate(node.schema)}" if node.schema else ""
        return f"{self.indent()}{node.name} = Dataset({self.generate(node.source)}{schema})"

    def gen_DeployStmt(self, node: DeployStmt):
        options = self.generate(node.options) if node.options else "{}"
        return f"{self.indent()}deploy_model({self.generate(node.target)}, {options})"

    def gen_TaintStmt(self, node: TaintStmt):
        return f"{self.indent()}taint({self.generate(node.target)})"

    def gen_FreezeStmt(self, node: FreezeStmt):
        layer = f", {self.generate(node.layer)}" if node.layer else ""
        return f"{self.indent()}freeze({self.generate(node.target)}{layer})"

    def gen_AvgByStmt(self, node: AvgByStmt):
        return f"{self.generate(node.dataset)}.avg_by(\"{node.column}\", \"{node.group_by}\")"

    def gen_MatchStatement(self, node: MatchStatement):
        res = f"{self.indent()}match {self.generate(node.expression)}:\n"
        self.indent_level += 1
        for case in node.cases:
            guard = f" if {self.generate(case.guard)}" if case.guard else ""
            res += f"{self.indent()}case {self.generate(case.pattern)}{guard}:\n"
            self.indent_level += 1
            body = "\n".join(self.generate(stmt) for stmt in case.body) if isinstance(case.body, list) else self.generate(case.body)
            res += body + "\n"
            self.indent_level -= 1
        self.indent_level -= 1
        return res.rstrip()

    def gen_TryStatement(self, node: TryStatement):
        res = f"{self.indent()}try:\n"
        self.indent_level += 1
        res += "\n".join(self.generate(stmt) for stmt in node.body) or f"{self.indent()}pass"
        self.indent_level -= 1
        for catch in node.catches:
            type_hint = f" as {catch.variable}"; exc_type = catch.type_hint or "Exception"
            res += f"\n{self.indent()}except {exc_type}{type_hint}:\n"
            self.indent_level += 1
            res += "\n".join(self.generate(stmt) for stmt in catch.body) or f"{self.indent()}pass"
            self.indent_level -= 1
        if node.finally_block:
            res += f"\n{self.indent()}finally:\n"
            self.indent_level += 1
            res += "\n".join(self.generate(stmt) for stmt in node.finally_block) or f"{self.indent()}pass"
            self.indent_level -= 1
        return res

    def gen_ReturnStatement(self, node: ReturnStatement):
        return f"{self.indent()}return {self.generate(node.value)}" if node.value else f"{self.indent()}return"

    def gen_ExpressionStatement(self, node: ExpressionStatement):
        return f"{self.indent()}{self.generate(node.expression)}"

    def gen_BinaryOp(self, node: BinaryOp):
        if node.op == "=": return f"{self.generate(node.left)} = {self.generate(node.right)}"
        if node.op == "??": l = self.generate(node.left); r = self.generate(node.right); return f"({l} if {l} is not None else {r})"
        if node.op == "..": return f"range({self.generate(node.left)}, {self.generate(node.right)})"
        op_map = {"&&": "and", "||": "or", "!": "not "}
        return f"({self.generate(node.left)} {op_map.get(node.op, node.op)} {self.generate(node.right)})"

    def gen_UnaryOp(self, node: UnaryOp):
        return f"({('not ' if node.op == '!' else node.op)}{self.generate(node.operand)})"

    def gen_Call(self, node: Call):
        return f"{self.generate(node.callee)}({', '.join(self.generate(arg) for arg in node.arguments)})"

    def gen_MemberAccess(self, node: MemberAccess):
        if node.is_safe: return f"getattr({self.generate(node.object)}, '{node.member}', None)"
        return f"{self.generate(node.object)}.{node.member}"

    def gen_Identifier(self, node: Identifier):
        return "self" if node.name == "this" else node.name

    def gen_Literal(self, node: Literal):
        return f'"{node.value}"' if isinstance(node.value, str) else str(node.value)

    def gen_TemplateLiteral(self, node: TemplateLiteral):
        return 'f"' + "".join(p.replace("{", "{{").replace("}", "}}") if isinstance(p, str) else "{" + self.generate(p) + "}" for p in node.parts) + '"'

    def gen_NNBlock(self, node: NNBlock):
        self.indent_level += 1
        items = []
        for stmt in node.statements:
             if isinstance(stmt, ExpressionStatement):
                 expr_code = self.generate(stmt.expression)
                 if isinstance(stmt.expression, Call) and isinstance(stmt.expression.callee, Identifier): expr_code = "torch.nn." + expr_code
                 items.append(f"{self.indent()}{expr_code}")
        self.indent_level -= 1
        return "torch.nn.Sequential(\n" + ",\n".join(items) + "\n)"

    def gen_GradientExpr(self, node: GradientExpr):
        return f"torch.autograd.grad({self.generate(node.function)}, [{', '.join(self.generate(v) for v in node.variables)}])"

    def gen_WeightsExpr(self, node: WeightsExpr):
        code = f"torch.randn({self.generate(node.shape)}, requires_grad=True)"
        if node.shared: code += ".share_memory_()"
        return code

    def gen_BatchIterator(self, node: BatchIterator):
        return f"DataLoader({self.generate(node.dataset)}, batch_size={self.generate(node.size)})"

    def gen_MmapExpr(self, node: MmapExpr):
        return f"np.memmap({self.generate(node.path)})"

    def gen_AwaitExpr(self, node: AwaitExpr):
        return f"await {self.generate(node.expression)}"

    def gen_Lambda(self, node: Lambda):
        return f"lambda {', '.join(node.parameters)}: {self.generate(node.body[0] if isinstance(node.body, list) else node.body)}"

    def gen_Pipeline(self, node: Pipeline):
        if isinstance(node.right, Call):
            args = [self.generate(node.left)] + [self.generate(arg) for arg in node.right.arguments]
            return f"{self.generate(node.right.callee)}({', '.join(args)})"
        return f"({self.generate(node.right)})({self.generate(node.left)})"

    def gen_ListLiteral(self, node: ListLiteral):
        return f"[{', '.join(self.generate(e) for e in node.elements)}]"

    def gen_DictLiteral(self, node: DictLiteral):
        return "{" + ", ".join(f'"{self.generate(k)}": {self.generate(v)}' if isinstance(k, Identifier) else f"{self.generate(k)}: {self.generate(v)}" for k, v in zip(node.keys, node.values)) + "}"
