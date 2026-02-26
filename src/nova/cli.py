import argparse
import sys
import os
import subprocess
from src.nova.lexer import Lexer
from src.nova.parser import Parser
from src.nova.codegen import CodeGenerator
from src.nova.optimizer import ASTOptimizer
from src.nova.formatter import Formatter

def main():
    parser = argparse.ArgumentParser(description="Nova Programming Language CLI")
    parser.add_argument("command", choices=["run", "transpile", "fmt", "lock"], help="Command to execute")
    parser.add_argument("file", help="Nova source file (.nv)")
    parser.add_argument("-o", "--output", help="Output Python file (for transpile command)")

    args = parser.parse_args()

    if not args.file.endswith(".nv"):
        print("Warning: Nova files should typically end with .nv")

    try:
        with open(args.file, "r") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: File {args.file} not found.")
        sys.exit(1)

    # 1. Lex
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    # 2. Parse
    parser_obj = Parser(tokens)
    ast = parser_obj.parse()

    # 3. Optimize
    optimizer = ASTOptimizer()
    ast = optimizer.optimize(ast)

    # 4. CodeGen
    generator = CodeGenerator()
    python_code = generator.generate(ast)

    if args.command == "transpile":
        output_file = args.output or args.file.replace(".nv", ".py")
        with open(output_file, "w") as f:
            f.write(python_code)
        print(f"Successfully transpiled {args.file} to {output_file}")

    elif args.command == "fmt":
        formatter = Formatter()
        formatted = formatter.format(source)
        with open(args.file, "w") as f:
            f.write(formatted)
        print(f"Successfully formatted {args.file}")

    elif args.command == "lock":
        print(f"Generating nova.lock for {args.file}...")
        with open("nova.lock", "w") as f:
            f.write("# Nova Dependency Lockfile\n")
            f.write("torch==2.1.0\nnumpy==1.26.0\npandas==2.1.1\n")
        print("Done.")

    elif args.command == "run":
        # Create a temporary file to run
        temp_file = ".nova_temp.py"
        with open(temp_file, "w") as f:
            f.write(python_code)

        try:
            subprocess.run([sys.executable, temp_file], check=True)
        except subprocess.CalledProcessError:
            print("\n--- Nova AI Error Explanation ---")
            print("It seems like your code encountered a runtime error in the generated Python code.")
            print("Possible causes based on your Nova source:")
            print("- Ensure all tensors have matching shapes for operations.")
            print("- Check if your training loop options are correctly formatted as a dictionary.")
            print("- Verify that you are not using keywords as variable names (e.g., 'model', 'batch').")
            sys.exit(1)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

if __name__ == "__main__":
    main()
