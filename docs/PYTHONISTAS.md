# Nova for Pythonistas

Welcome to Nova, the evolutionary successor to Python. This guide helps you transition from Python's indentation-based syntax to Nova's modern, AI-first ecosystem.

## Syntax Comparison

| Concept | Python | Nova |
|---------|--------|------|
| Blocks | Indentation | Curly Braces `{}` |
| Functions | `def name():` | `fn name() { ... }` |
| Variables | `x = 10` | `let x = 10;` or `const x = 10;` |
| Type Hints | `x: int = 10` | `let x: Int = 10;` |
| Lambda | `lambda x: x * 2` | `(x) => x * 2` |
| Classes | `class C:` | `class C { ... }` |
| Method `self` | Manual `def m(self):` | Automatic |
| Constructor | `__init__` | `constructor` |
| Pipeline | `f(g(x))` | `x \|> g() \|> f()` |
| Async | `async def` / `await` | `async fn` / `await` |

## Why Switch?

1. **Brace-based Syntax**: No more "IndentationError". Copy-paste code with confidence.
2. **AI-Native Primitives**: Built-in support for Tensors, GPU contexts, and training loops.
3. **Improved Data Science**: SQL-like selectors and declarative data cleaning.
4. **Performance**: Built-in auto-vectorization and parallel loops.
5. **Zero Friction**: 100% compatible with existing Python libraries like NumPy, PyTorch, and Pandas.

## Migration

Use the `novify` tool to convert your existing Python projects:

```bash
python3 src/nova/novify.py my_project/ --test
```

This will convert all `.py` files to `.nv` and run tests to ensure behavioral consistency.
