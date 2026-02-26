# Nova Language Specification

Nova is a modern, AI-first programming language designed as the evolutionary successor to Python. It transpiles to Python and runs on the CPython runtime, ensuring 100% compatibility with the existing Python ecosystem.

## 1. Syntax Grammar (EBNF)

```ebnf
program = { statement } ;

statement = variable_declaration
          | function_declaration
          | class_declaration
          | model_declaration
          | if_statement
          | for_statement
          | parallel_for_statement
          | while_statement
          | try_statement
          | return_statement
          | import_statement
          | export_statement
          | match_statement
          | train_statement
          | expression_statement
          | block ;

block = "{" { statement } "}" ;

variable_declaration = ( "let" | "const" ) identifier [ ":" type ] "=" expression [ ";" ] ;

function_declaration = [ "async" ] "fn" identifier "(" [ parameter_list ] ")" [ "->" type ] block ;

parameter_list = parameter { "," parameter } ;
parameter = identifier [ ":" type ] [ "=" expression ] ;

class_declaration = "class" identifier [ "(" identifier ")" ] "{" { member_declaration } "}" ;
model_declaration = "model" identifier [ "(" identifier ")" ] "{" { member_declaration } "}" ;
member_declaration = variable_declaration | function_declaration ;

if_statement = "if" "(" expression ")" block [ "else" ( if_statement | block ) ] ;

for_statement = "for" "(" identifier "in" expression ")" block ;

parallel_for_statement = "parallel" "for" "(" identifier "in" expression ")" block ;

while_statement = "while" "(" expression ")" block ;

train_statement = "train" identifier "with" expression block ;

try_statement = "try" block { "catch" "(" identifier [ ":" type ] ")" block } [ "finally" block ] ;

match_statement = "match" "(" expression ")" "{" { "case" expression [ "if" expression ] "=>" ( expression | block ) } "}" ;

import_statement = "import" ( identifier | "{" identifier { "," identifier } "}" ) "from" string [ ";" ] ;
export_statement = "export" ( variable_declaration | function_declaration | class_declaration ) ;

return_statement = "return" [ expression ] [ ";" ] ;

expression_statement = expression [ ";" ] ;

expression = assignment ;
assignment = [ identifier "=" ] logical_or ;
logical_or = logical_and { "||" logical_and } ;
logical_and = equality { "&&" equality } ;
equality = comparison [ ( "==" | "!=" ) comparison ] ;
comparison = term [ ( "<" | "<=" | ">" | ">=" | ".." ) term ] ;
term = factor { ( "+" | "-" | "??" ) factor } ;
factor = unary { ( "*" | "/" | "%" | "**" ) unary } ;
unary = [ "!" | "-" | "await" | "lazy" ] primary ;
primary = literal | identifier | call | member_access | list_literal | dict_literal | "(" expression ")" | lambda_expression | pipeline_expression ;

member_access = primary ( ( "." | "?." ) identifier | "[" expression "]" ) ;
call = primary "(" [ argument_list ] ")" ;
argument_list = expression { "," expression } ;

list_literal = "[" [ expression { "," expression } ] "]" ;
dict_literal = "{" [ expression ":" expression { "," expression ":" expression } ] "}" ;

lambda_expression = "(" [ identifier { "," identifier } ] ")" "=>" ( expression | block ) ;

pipeline_expression = expression "|>" call ;

type = identifier [ "[" type { "," type } "]" ] ;

identifier = [a-zA-Z_][a-zA-Z0-9_]* ;
literal = integer | float | string | "true" | "false" | "null" ;
```

## 2. Lexical Rules

- **Identifiers**: Case-sensitive, starting with a letter or underscore, followed by letters, digits, or underscores.
- **Keywords**: `let`, `const`, `fn`, `class`, `model`, `if`, `else`, `for`, `parallel`, `in`, `while`, `try`, `catch`, `finally`, `return`, `import`, `from`, `export`, `async`, `await`, `match`, `case`, `train`, `lazy`.
- **Comments**:
  - Single-line: `// comment`
  - Multi-line: `/* comment */`
- **Indentation**: Not syntactically significant. Blocks are delimited by curly braces `{}`.
- **Semicolons**: Optional at the end of statements.

## 3. Type System (Gradual Typing)

Nova employs a gradual typing system that is 100% compatible with Python's type hints.

- **Primitive Types**: `Int`, `Float`, `Str`, `Bool`, `Null`.
- **Collection Types**: `List[T]`, `Dict[K, V]`, `Set[T]`, `Tuple[...]`.
- **AI-Native Types**: `Tensor`, `DataFrame`, `Series`.
- **Type Inference**: Variables declared with `let` or `const` without explicit types have their types inferred where possible.
- **Static Analysis**: Nova tools provide static type checking, but types are erased or converted to standard Python type hints during transpilation.

## 4. Module System

Nova uses a modern module system that maps directly to Python modules.

- **Imports**: `import { Tensor, randn } from "torch"` transpiles to `from torch import Tensor, randn`.
- **Exports**: `export fn train() {}` makes the function available for import in other Nova or Python files.

## 5. Error Model

- **Try-Catch**: Nova uses `try { ... } catch (e: Exception) { ... } finally { ... }` syntax.
- **Compatibility**: All Python exceptions can be caught using Nova's `catch` blocks.
- **Panic/Recover**: Built-in support for unrecoverable errors that map to `SystemExit` or specific critical exceptions.

## 6. Memory Semantics

Nova inherits Python's memory management:
- **Reference Counting**: Objects are deleted when their reference count reaches zero.
- **Garbage Collection**: A cyclic garbage collector handles reference cycles.
- **Zero-Friction**: Developers do not need to manually manage memory.

## 7. Async/Concurrency Model

Nova provides first-class support for asynchronous programming via `async` and `await`, mapping directly to Python's `asyncio`.

- **Async Functions**: `async fn fetchData() { ... }`
- **Awaiting**: `let data = await fetchData();`
- **Concurrency**: Easy access to `asyncio.gather` and other concurrency primitives through the standard library.

## 8. Pattern Matching System

Nova introduces a powerful `match` statement that transpiles to Python 3.10+'s `match` statement.

```nova
match (response.status) {
    case 200 => print("Success")
    case 404 => print("Not Found")
    case _ => print("Unknown Error")
}
```

## 9. Macro & Metaprogramming Support

- **Decorators**: Supported using the `@decorator` syntax, same as Python.
- **Compile-time Constants**: `const` variables can be optimized during transpilation.
- **Template Literals**: `f"Value: {x}"` support for string interpolation.
