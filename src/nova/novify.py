import ast
import sys

class NovaUnparser(ast.NodeVisitor):
    def __init__(self):
        self.indent_level = 0
        self.result = ""

    def write(self, text):
        self.result += text

    def fill(self, text=""):
        self.write("\n" + "    " * self.indent_level + text)

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)
        return self.result

    def visit_FunctionDef(self, node):
        self.fill(f"fn {node.name}(")
        self.visit(node.args)
        self.write(") {")
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1
        self.fill("}")

    def visit_arguments(self, node):
        args = [arg.arg for arg in node.args]
        self.write(", ".join(args))

    def visit_ClassDef(self, node):
        self.fill(f"class {node.name} {{")
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1
        self.fill("}")

    def visit_Import(self, node):
        for alias in node.names:
            self.fill(f"import {alias.name} from \"{alias.name}\";")

    def visit_ImportFrom(self, node):
        names = ", ".join(alias.name for alias in node.names)
        self.fill(f"import {{ {names} }} from \"{node.module}\";")

    def visit_If(self, node):
        self.fill("if (")
        self.write(self.expr_to_str(node.test))
        self.write(") {")
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1
        self.fill("}")
        if node.orelse:
            self.write(" else {")
            self.indent_level += 1
            for stmt in node.orelse:
                self.visit(stmt)
            self.indent_level -= 1
            self.fill("}")

    def visit_For(self, node):
        self.fill("for (")
        self.write(self.expr_to_str(node.target))
        self.write(" in ")
        self.write(self.expr_to_str(node.iter))
        self.write(") {")
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1
        self.fill("}")

    def visit_Assign(self, node):
        target = self.expr_to_str(node.targets[0])
        value = self.expr_to_str(node.value)
        self.fill(f"let {target} = {value};")

    def visit_Expr(self, node):
        self.fill(self.expr_to_str(node.value) + ";")

    def visit_Return(self, node):
        if node.value:
            self.fill(f"return {self.expr_to_str(node.value)};")
        else:
            self.fill("return;")

    def expr_to_str(self, node):
        return ast.unparse(node)

def main():
    if len(sys.argv) < 2:
        print("Usage: novify <input.py>")
        sys.exit(1)

    input_file = sys.argv[1]
    with open(input_file, "r") as f:
        code = f.read()

    tree = ast.parse(code)
    unparser = NovaUnparser()
    nova_code = unparser.visit(tree)

    output_file = input_file.replace(".py", ".nv")
    with open(output_file, "w") as f:
        f.write(nova_code)
    print(f"Successfully converted {input_file} to {output_file}")

if __name__ == "__main__":
    main()
