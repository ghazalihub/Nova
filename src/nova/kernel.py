from ipykernel.kernelbase import Kernel
from src.nova.lexer import Lexer
from src.nova.parser import Parser
from src.nova.codegen import CodeGenerator
from src.nova.optimizer import ASTOptimizer
import sys
import io
from contextlib import redirect_stdout

class NovaKernel(Kernel):
    implementation = 'Nova'
    implementation_version = '1.0'
    language = 'nova'
    language_version = '1.0'
    language_info = {
        'name': 'nova',
        'mimetype': 'text/x-nova',
        'file_extension': '.nv',
    }
    banner = "Nova - The evolutionary successor to Python"

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count, 'payload': [], 'user_expressions': {}}

        try:
            # Transpile Nova to Python
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            optimizer = ASTOptimizer()
            ast = optimizer.optimize(ast)
            generator = CodeGenerator()
            python_code = generator.generate(ast)

            # Execute Python code
            output = io.StringIO()
            with redirect_stdout(output):
                exec(python_code, globals())

            if not silent:
                self.send_response(self.iopub_socket, 'stream', {
                    'name': 'stdout', 'text': output.getvalue()
                })

            return {'status': 'ok', 'execution_count': self.execution_count, 'payload': [], 'user_expressions': {}}
        except Exception as e:
            if not silent:
                self.send_response(self.iopub_socket, 'stream', {
                    'name': 'stderr', 'text': str(e)
                })
            return {'status': 'error', 'ename': type(e).__name__, 'evalue': str(e), 'traceback': []}

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=NovaKernel)
