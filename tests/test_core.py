import pytest
from src.nova.lexer import Lexer, TokenType
from src.nova.parser import Parser
from src.nova.codegen import CodeGenerator

def test_lexer():
    source = "let x = 10; fn add(a, b) { return a + b; }"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens]
    assert TokenType.LET in types
    assert TokenType.FN in types
    assert TokenType.LBRACE in types

def test_parser_basic():
    source = "let x = 10;"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    assert len(ast.statements) == 1

def test_codegen_basic():
    source = "fn greet() { print(\"hello\"); }"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = CodeGenerator()
    code = generator.generate(ast)
    assert "def greet():" in code
    assert "print(\"hello\")" in code

def test_pipeline():
    source = "5 |> double();"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = CodeGenerator()
    code = generator.generate(ast)
    assert "double(5)" in code

def test_safe_navigation():
    source = "obj?.prop;"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = CodeGenerator()
    code = generator.generate(ast)
    assert "getattr(obj, 'prop', None)" in code

def test_match_statement():
    source = "match (x) { case 1 => { print(1); } case 2 if y > 0 => { print(2); } }"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = CodeGenerator()
    code = generator.generate(ast)
    assert "match x:" in code
    assert "case 1:" in code
    assert "case 2 if (y > 0):" in code

def test_model_declaration():
    source = "model MyModel(Base) { fn init() { print(\"init\"); } }"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = CodeGenerator()
    code = generator.generate(ast)
    assert "class MyModel(Base):" in code
    assert "def init(self):" in code

def test_parallel_for():
    source = "parallel for (i in range(10)) { print(i); }"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = CodeGenerator()
    code = generator.generate(ast)
    assert "# Parallel loop" in code
    assert "_nova_pool.map" in code

def test_try_catch():
    source = "try { dangerous(); } catch (e: ValueError) { handle(e); } finally { cleanup(); }"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = CodeGenerator()
    code = generator.generate(ast)
    assert "try:" in code
    assert "except ValueError as e:" in code
    assert "finally:" in code

def test_nullish_coalesce():
    source = "let x = a ?? b;"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = CodeGenerator()
    code = generator.generate(ast)
    assert "(a if a is not None else b)" in code

def test_template_literal():
    source = "let s = `hello ${name}`; "
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = CodeGenerator()
    code = generator.generate(ast)
    assert "f\"hello {name}\"" in code

def test_with_gpu():
    source = "with (gpu(0)) { print(1); }"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = CodeGenerator()
    code = generator.generate(ast)
    assert "with torch.cuda.device(0):" in code

def test_nn_block():
    source = "let m = nn { Linear(10, 5); };"
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    generator = CodeGenerator()
    code = generator.generate(ast)
    assert "torch.nn.Sequential(" in code
    assert "torch.nn.Linear(10, 5)" in code
