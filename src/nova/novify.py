import libcst as cst
import sys
import os
import argparse
import subprocess

class NovaConverter(cst.CSTVisitor):
    def __init__(self):
        self.indent_level = 0
        self.result = ""

    def write(self, text):
        self.result += text

    def fill(self, text=""):
        self.result += "\n" + "    " * self.indent_level + text

    def visit_Module(self, node: cst.Module):
        for stmt in node.body:
            stmt.visit(self)
        return False

    def visit_FunctionDef(self, node: cst.FunctionDef):
        # Handle decorators
        for deco in node.decorators:
            self.fill(f"@{self.code_for(deco.decorator)}")

        params = []
        for param in node.params.params:
            params.append(param.name.value)

        self.fill(f"fn {node.name.value}({', '.join(params)}) {{")
        self.indent_level += 1
        node.body.visit(self)
        self.indent_level -= 1
        self.fill("}")
        return False

    def visit_ClassDef(self, node: cst.ClassDef):
        bases = ""
        if node.bases:
            bases = f"({', '.join(self.code_for(b.value) for b in node.bases)})"

        self.fill(f"class {node.name.value}{bases} {{")
        self.indent_level += 1
        node.body.visit(self)
        self.indent_level -= 1
        self.fill("}")
        return False

    def visit_SimpleStatementLine(self, node: cst.SimpleStatementLine):
        for stmt in node.body:
            stmt.visit(self)
        return False

    def visit_Assign(self, node: cst.Assign):
        target = self.code_for(node.targets[0].target)
        value = self.code_for(node.value)
        self.fill(f"let {target} = {value};")
        return False

    def visit_Expr(self, node: cst.Expr):
        self.fill(self.code_for(node.value) + ";")
        return False

    def visit_Return(self, node: cst.Return):
        if node.value:
            self.fill(f"return {self.code_for(node.value)};")
        else:
            self.fill("return;")
        return False

    def visit_If(self, node: cst.If):
        self.fill(f"if ({self.code_for(node.test)}) {{")
        self.indent_level += 1
        node.body.visit(self)
        self.indent_level -= 1
        self.fill("}")

        if node.orelse:
            self.write(" else ")
            node.orelse.visit(self)
        return False

    def visit_Else(self, node: cst.Else):
        if isinstance(node.body, cst.If):
            node.body.visit(self)
        else:
            self.write("{")
            self.indent_level += 1
            node.body.visit(self)
            self.indent_level -= 1
            self.fill("}")
        return False

    def visit_For(self, node: cst.For):
        target = self.code_for(node.target)
        iterable = self.code_for(node.iter)
        self.fill(f"for ({target} in {iterable}) {{")
        self.indent_level += 1
        node.body.visit(self)
        self.indent_level -= 1
        self.fill("}")
        return False

    def visit_While(self, node: cst.While):
        self.fill(f"while ({self.code_for(node.test)}) {{")
        self.indent_level += 1
        node.body.visit(self)
        self.indent_level -= 1
        self.fill("}")
        return False

    def visit_Import(self, node: cst.Import):
        for alias in node.names:
            name = self.code_for(alias.name)
            self.fill(f"import {name} from \"{name}\";")
        return False

    def visit_ImportFrom(self, node: cst.ImportFrom):
        module = self.code_for(node.module) if node.module else ""
        names = []
        if isinstance(node.names, cst.ImportStar):
            names = ["*"]
        else:
            for alias in node.names:
                names.append(alias.name.value)

        self.fill(f"import {{ {', '.join(names)} }} from \"{module}\";")
        return False

    def code_for(self, node):
        return cst.Module([]).code_for_node(node)

def novify_file(input_file):
    with open(input_file, "r") as f:
        code = f.read()

    try:
        tree = cst.parse_module(code)
        visitor = NovaConverter()
        tree.visit(visitor)

        output_file = input_file.replace(".py", ".nv")
        with open(output_file, "w") as f:
            f.write(visitor.result.strip())
        print(f"Successfully converted {input_file} to {output_file} using LibCST")
    except Exception as e:
        print(f"Failed to convert {input_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Novify: Convert Python to Nova")
    parser.add_argument("path", help="File or directory to convert")
    parser.add_argument("--test", action="store_true", help="Run tests before and after conversion")

    args = parser.parse_args()

    if args.test:
        print("Running tests before conversion...")
        subprocess.run(["pytest"], check=False)

    if os.path.isfile(args.path):
        novify_file(args.path)
    elif os.path.isdir(args.path):
        for root, _, files in os.walk(args.path):
            for file in files:
                if file.endswith(".py"):
                    novify_file(os.path.join(root, file))
    else:
        print(f"Error: path {args.path} not found.")
        sys.exit(1)

    if args.test:
        print("Running tests after conversion...")
        subprocess.run(["pytest"], check=False)

if __name__ == "__main__":
    main()
