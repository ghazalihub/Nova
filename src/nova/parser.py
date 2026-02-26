from src.nova.lexer import Token, TokenType
from src.nova.nova_ast import *
from typing import List

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    @property
    def line(self):
        return self.peek().line

    def peek(self, offset=0) -> Token:
        if self.pos + offset >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos + offset]

    def advance(self) -> Token:
        token = self.peek()
        self.pos += 1
        return token

    def check(self, type: TokenType) -> bool:
        return self.peek().type == type

    def match(self, *types: TokenType) -> bool:
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False

    def consume(self, type: TokenType, message: str) -> Token:
        if self.check(type):
            return self.advance()
        raise RuntimeError(f"Error at line {self.line}: {message}")

    def _set_line(self, node: Node) -> Node:
        if hasattr(node, 'line'):
            node.line = self.line
        return node

    def parse(self) -> Program:
        line = self.line
        statements = []
        while not self.check(TokenType.EOF):
            statements.append(self.statement())
        node = Program(statements)
        node.line = line
        return node

    def statement(self) -> Statement:
        if self.match(TokenType.IMPORT):
            return self.import_statement()
        if self.match(TokenType.EXPORT):
            node = ExportStmt(self.statement())
            return self._set_line(node)
        if self.match(TokenType.LET, TokenType.CONST):
            return self.var_declaration(self.tokens[self.pos-1].type == TokenType.CONST, is_lazy=False)
        if self.match(TokenType.LAZY):
            if self.match(TokenType.LET):
                return self.var_declaration(is_const=False, is_lazy=True)
            elif self.match(TokenType.CONST):
                return self.var_declaration(is_const=True, is_lazy=True)
            else:
                raise RuntimeError("Expect 'let' or 'const' after 'lazy'")
        if self.match(TokenType.TRAIN):
            return self.train_statement()
        if self.match(TokenType.ASYNC):
            if self.match(TokenType.FN):
                return self.function_declaration(is_async=True)
            elif self.match(TokenType.FOR):
                return self.for_statement(is_parallel=False, is_async=True)
            else:
                raise RuntimeError("Expect 'fn' or 'for' after 'async'.")
        if self.match(TokenType.FN):
            return self.function_declaration()
        if self.match(TokenType.WITH):
            return self.with_statement()
        if self.match(TokenType.CLEAN):
            return self.clean_statement()
        if self.match(TokenType.PLOT):
            return self.plot_statement()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.FOR):
            return self.for_statement(is_parallel=False)
        if self.match(TokenType.PARALLEL):
            self.consume(TokenType.FOR, "Expect 'for' after 'parallel'.")
            return self.for_statement(is_parallel=True)
        if self.match(TokenType.MODEL):
            return self.model_declaration()
        if self.match(TokenType.DATASET):
            return self.dataset_declaration()
        if self.match(TokenType.DEPLOY):
            return self.deploy_statement()
        if self.match(TokenType.TAINT):
            return self.taint_statement()
        if self.match(TokenType.FREEZE):
            return self.freeze_statement()
        if self.match(TokenType.STRUCT):
            return self.struct_declaration()
        if self.match(TokenType.SCHEMA):
            return self.schema_declaration()
        if self.match(TokenType.PANIC):
            node = PanicStmt(self.expression())
            self.match(TokenType.SEMICOLON)
            return self._set_line(node)
        if self.match(TokenType.RECOVER):
            node = RecoverStmt(self.block())
            return self._set_line(node)
        if self.match(TokenType.ASSERT):
            node = AssertStmt(self.expression())
            self.match(TokenType.SEMICOLON)
            return self._set_line(node)
        if self.match(TokenType.TEST):
            return self.test_statement()
        if self.match(TokenType.BENCH):
            return self.bench_statement()
        if self.match(TokenType.PROMPT):
            return self.prompt_declaration()
        if self.match(TokenType.SECURE):
            node = SecureStmt(self.block())
            return self._set_line(node)
        if self.match(TokenType.SHARED):
            self.consume(TokenType.STATE, "Expect 'state' after 'shared'.")
            node = SharedStateStmt(self.block())
            return self._set_line(node)
        if self.match(TokenType.MATCH):
            return self.match_statement()
        if self.match(TokenType.TRY):
            return self.try_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.LBRACE):
            statements = self.block()
            node = Block(statements)
            return self._set_line(node)
        return self.expression_statement()

    def import_statement(self) -> ImportStatement:
        line = self.line
        names = []
        if self.match(TokenType.LBRACE):
            while True:
                if not self.check(TokenType.RBRACE):
                     names.append(self.advance().value)
                if not self.match(TokenType.COMMA): break
            self.consume(TokenType.RBRACE, "Expect '}' after import names.")
        else:
            names.append(self.consume(TokenType.IDENTIFIER, "Expect name to import.").value)
        self.consume(TokenType.FROM, "Expect 'from' after import names.")
        source = self.consume(TokenType.STRING, "Expect module source string.").value
        self.match(TokenType.SEMICOLON)
        node = ImportStatement(names, source)
        node.line = line
        return node

    def var_declaration(self, is_const: bool, is_lazy: bool) -> VarDeclaration:
        line = self.line
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.").value
        type_hint = None
        if self.match(TokenType.COLON):
            type_hint = self.consume(TokenType.IDENTIFIER, "Expect type name.").value
        self.consume(TokenType.ASSIGN, "Expect '=' after variable name.")
        value = self.expression()
        self.match(TokenType.SEMICOLON)
        node = VarDeclaration(name, type_hint, value, is_const, is_lazy)
        node.line = line
        return node

    def train_statement(self) -> TrainStatement:
        line = self.line
        model = self.expression()
        self.consume(TokenType.WITH, "Expect 'with' after model in train statement.")
        dataset = self.expression()
        options = None
        if self.match(TokenType.LBRACE):
            self.pos -= 1
            options = self.expression()
        self.match(TokenType.SEMICOLON)
        node = TrainStatement(model, dataset, options)
        node.line = line
        return node

    def struct_declaration(self) -> StructDecl:
        line = self.line
        name = self.consume(TokenType.IDENTIFIER, "Expect struct name.").value
        self.consume(TokenType.LBRACE, "Expect '{' before struct body.")
        fields = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            f_name = self.consume(TokenType.IDENTIFIER, "Expect field name.").value
            self.consume(TokenType.COLON, "Expect ':' after field name.")
            f_type = self.consume(TokenType.IDENTIFIER, "Expect field type.").value
            fields.append({"name": f_name, "type": f_type})
            self.match(TokenType.SEMICOLON)
        self.consume(TokenType.RBRACE, "Expect '}' after struct body.")
        node = StructDecl(name, fields)
        node.line = line
        return node

    def schema_declaration(self) -> SchemaDecl:
        line = self.line
        name = self.consume(TokenType.IDENTIFIER, "Expect schema name.").value
        self.consume(TokenType.ASSIGN, "Expect '=' after schema name.")
        definition = self.expression()
        self.match(TokenType.SEMICOLON)
        node = SchemaDecl(name, definition)
        node.line = line
        return node

    def function_declaration(self, is_async: bool = False) -> FunctionDeclaration:
        line = self.line
        name = self.consume(TokenType.IDENTIFIER, "Expect function name.").value
        self.consume(TokenType.LPAREN, "Expect '(' after function name.")
        parameters = []
        if not self.check(TokenType.RPAREN):
            while True:
                p_name = self.consume(TokenType.IDENTIFIER, "Expect parameter name.").value
                p_type = None
                if self.match(TokenType.COLON):
                    p_type = self.consume(TokenType.IDENTIFIER, "Expect parameter type.").value
                parameters.append({"name": p_name, "type": p_type})
                if not self.match(TokenType.COMMA): break
        self.consume(TokenType.RPAREN, "Expect ')' after parameters.")
        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.consume(TokenType.IDENTIFIER, "Expect return type.").value
        body = self.block() if self.check(TokenType.LBRACE) else [self.expression_statement()]
        if name == "constructor": name = "__init__"
        node = FunctionDeclaration(name, parameters, return_type, body if isinstance(body, list) else [body], is_async)
        node.line = line
        return node

    def with_statement(self) -> WithStmt:
        line = self.line
        self.consume(TokenType.LPAREN, "Expect '(' after 'with'.")
        context = self.expression()
        variable = None
        if self.match(TokenType.AS):
            variable = self.consume(TokenType.IDENTIFIER, "Expect variable name after 'as'.").value
        self.consume(TokenType.RPAREN, "Expect ')' after with expression.")
        body = self.block()
        node = WithStmt(context, variable, body)
        node.line = line
        return node

    def clean_statement(self) -> CleanStmt:
        line = self.line
        target = self.expression()
        self.match(TokenType.SEMICOLON)
        node = CleanStmt(target)
        node.line = line
        return node

    def plot_statement(self) -> PlotStmt:
        line = self.line
        target = self.expression()
        options = None
        if self.match(TokenType.LBRACE):
            self.pos -= 1
            options = self.expression()
        self.match(TokenType.SEMICOLON)
        node = PlotStmt(target, options)
        node.line = line
        return node

    def test_statement(self) -> TestStmt:
        line = self.line
        name = self.consume(TokenType.STRING, "Expect test name string.").value
        body = self.block()
        node = TestStmt(name, body)
        node.line = line
        return node

    def bench_statement(self) -> BenchStmt:
        line = self.line
        name = self.consume(TokenType.STRING, "Expect bench name string.").value
        body = self.block()
        node = BenchStmt(name, body)
        node.line = line
        return node

    def prompt_declaration(self) -> PromptDecl:
        line = self.line
        name = self.consume(TokenType.IDENTIFIER, "Expect prompt name.").value
        self.consume(TokenType.LBRACE, "Expect '{' before prompt body.")
        content = ""
        brace_count = 1
        while brace_count > 0 and not self.check(TokenType.EOF):
             if self.check(TokenType.LBRACE): brace_count += 1
             elif self.check(TokenType.RBRACE): brace_count -= 1
             if brace_count > 0: content += self.advance().value + " "
        self.consume(TokenType.RBRACE, "Expect '}' after prompt body.")
        node = PromptDecl(name, [ExpressionStatement(Literal(content.strip()))])
        node.line = line
        return node

    def if_statement(self) -> IfStatement:
        line = self.line
        self.consume(TokenType.LPAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RPAREN, "Expect ')' after if condition.")
        then_block = self.block()
        else_block = None
        if self.match(TokenType.ELSE):
            if self.match(TokenType.IF): else_block = self.if_statement()
            else: else_block = self.block()
        node = IfStatement(condition, then_block, else_block)
        node.line = line
        return node

    def for_statement(self, is_parallel: bool, is_async: bool = False) -> ForStatement:
        line = self.line
        self.consume(TokenType.LPAREN, "Expect '(' after 'for'.")
        target = self.consume(TokenType.IDENTIFIER, "Expect loop variable name.").value
        self.consume(TokenType.IN, "Expect 'in' after loop variable.")
        iterable = self.expression()
        self.consume(TokenType.RPAREN, "Expect ')' after for clauses.")
        body = self.block()
        node = ForStatement(target, iterable, body, is_parallel, is_async)
        node.line = line
        return node

    def model_declaration(self) -> ModelDeclaration:
        line = self.line
        name = self.consume(TokenType.IDENTIFIER, "Expect model name.").value
        base_class = None
        if self.match(TokenType.LPAREN):
            base_class = self.consume(TokenType.IDENTIFIER, "Expect base class name.").value
            self.consume(TokenType.RPAREN, "Expect ')' after base class.")
        version = None
        if self.match(TokenType.AT):
            version = self.consume(TokenType.STRING, "Expect version string after '@'.").value
        self.consume(TokenType.LBRACE, "Expect '{' before model body.")
        members = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            members.append(self.statement())
        self.consume(TokenType.RBRACE, "Expect '}' after model body.")
        node = ModelDeclaration(name, base_class, members, version)
        node.line = line
        return node

    def dataset_declaration(self) -> DatasetDecl:
        line = self.line
        name = self.consume(TokenType.IDENTIFIER, "Expect dataset name.").value
        self.consume(TokenType.ASSIGN, "Expect '=' after dataset name.")
        source = self.expression()
        schema = None
        if self.match(TokenType.SCHEMA): schema = self.expression()
        self.match(TokenType.SEMICOLON)
        node = DatasetDecl(name, source, schema)
        node.line = line
        return node

    def deploy_statement(self) -> DeployStmt:
        line = self.line
        target = self.expression()
        options = None
        if self.match(TokenType.LBRACE):
            self.pos -= 1
            options = self.expression()
        self.match(TokenType.SEMICOLON)
        node = DeployStmt(target, options)
        node.line = line
        return node

    def taint_statement(self) -> TaintStmt:
        line = self.line
        target = self.expression()
        self.match(TokenType.SEMICOLON)
        node = TaintStmt(target)
        node.line = line
        return node

    def freeze_statement(self) -> FreezeStmt:
        line = self.line
        target = self.expression()
        layer = None
        if not self.check(TokenType.SEMICOLON): layer = self.expression()
        self.match(TokenType.SEMICOLON)
        node = FreezeStmt(target, layer)
        node.line = line
        return node

    def match_statement(self) -> MatchStatement:
        line = self.line
        self.consume(TokenType.LPAREN, "Expect '(' after 'match'.")
        expression = self.expression()
        self.consume(TokenType.RPAREN, "Expect ')' after match expression.")
        self.consume(TokenType.LBRACE, "Expect '{' before match body.")
        cases = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            self.consume(TokenType.CASE, "Expect 'case' in match body.")
            pattern = self.expression()
            guard = None
            if self.match(TokenType.IF): guard = self.expression()
            self.consume(TokenType.ARROW, "Expect '=>' after pattern.")
            body = self.block() if self.check(TokenType.LBRACE) else [self.statement()]
            case = MatchCase(pattern, guard, body)
            case.line = self.line
            cases.append(case)
        self.consume(TokenType.RBRACE, "Expect '}' after match body.")
        node = MatchStatement(expression, cases)
        node.line = line
        return node

    def try_statement(self) -> TryStatement:
        line = self.line
        body = self.block()
        catches = []
        while self.match(TokenType.CATCH):
            self.consume(TokenType.LPAREN, "Expect '(' after 'catch'.")
            variable = self.consume(TokenType.IDENTIFIER, "Expect variable name in catch.").value
            type_hint = None
            if self.match(TokenType.COLON): type_hint = self.consume(TokenType.IDENTIFIER, "Expect type in catch.").value
            self.consume(TokenType.RPAREN, "Expect ')' after catch variable.")
            catch_body = self.block()
            catch = CatchBlock(variable, type_hint, catch_body)
            catch.line = self.line
            catches.append(catch)
        finally_block = None
        if self.match(TokenType.FINALLY): finally_block = self.block()
        node = TryStatement(body, catches, finally_block)
        node.line = line
        return node

    def block(self) -> List[Statement]:
        if not self.match(TokenType.LBRACE): return [self.statement()]
        statements = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            statements.append(self.statement())
        self.consume(TokenType.RBRACE, "Expect '}' after block.")
        return statements

    def return_statement(self) -> ReturnStatement:
        line = self.line
        value = None
        if not self.check(TokenType.SEMICOLON) and not self.check(TokenType.RBRACE): value = self.expression()
        self.match(TokenType.SEMICOLON)
        node = ReturnStatement(value)
        node.line = line
        return node

    def expression_statement(self) -> ExpressionStatement:
        line = self.line
        expr = self.expression()
        self.match(TokenType.SEMICOLON)
        node = ExpressionStatement(expr)
        node.line = line
        return node

    def expression(self) -> Expression:
        return self.assignment()

    def assignment(self) -> Expression:
        line = self.line
        expr = self.nullish_coalesce()
        if self.match(TokenType.ASSIGN):
            value = self.assignment()
            if isinstance(expr, (Identifier, Call, MemberAccess)):
                node = BinaryOp(expr, "=", value)
                node.line = line
                return node
        return expr

    def nullish_coalesce(self) -> Expression:
        line = self.line
        expr = self.logical_or()
        while self.match(TokenType.NULL_COALESCE):
            op = self.tokens[self.pos-1].value
            right = self.logical_or()
            expr = BinaryOp(expr, op, right)
            expr.line = line
        return expr

    def logical_or(self) -> Expression:
        line = self.line
        expr = self.logical_and()
        while self.match(TokenType.OR):
            op = self.tokens[self.pos-1].value
            right = self.logical_and()
            expr = BinaryOp(expr, op, right)
            expr.line = line
        return expr

    def logical_and(self) -> Expression:
        line = self.line
        expr = self.pipeline()
        while self.match(TokenType.AND):
            op = self.tokens[self.pos-1].value
            right = self.pipeline()
            expr = BinaryOp(expr, op, right)
            expr.line = line
        return expr

    def pipeline(self) -> Expression:
        line = self.line
        expr = self.equality()
        while self.match(TokenType.PIPELINE):
            right = self.call()
            if not isinstance(right, (Call, Lambda)): raise RuntimeError("Right side of pipeline must be a function call or lambda")
            expr = Pipeline(expr, right)
            expr.line = line
        return expr

    def equality(self) -> Expression:
        line = self.line
        expr = self.comparison()
        while self.match(TokenType.EQ, TokenType.NE):
            op = self.tokens[self.pos-1].value
            right = self.comparison()
            expr = BinaryOp(expr, op, right)
            expr.line = line
        return expr

    def comparison(self) -> Expression:
        line = self.line
        expr = self.term()
        while self.match(TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE, TokenType.RANGE):
            op = self.tokens[self.pos-1].value
            right = self.term()
            expr = BinaryOp(expr, op, right)
            expr.line = line
        return expr

    def term(self) -> Expression:
        line = self.line
        expr = self.factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.tokens[self.pos-1].value
            right = self.factor()
            expr = BinaryOp(expr, op, right)
            expr.line = line
        return expr

    def factor(self) -> Expression:
        line = self.line
        expr = self.unary()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT, TokenType.POWER):
            op = self.tokens[self.pos-1].value
            right = self.unary()
            expr = BinaryOp(expr, op, right)
            expr.line = line
        return expr

    def unary(self) -> Expression:
        line = self.line
        if self.match(TokenType.AT):
            name = self.consume(TokenType.IDENTIFIER, "Expect decorator name.").value
            expr = self.statement()
            node = DecoratorExpr(name, expr)
            node.line = line
            return node
        if self.match(TokenType.NOT, TokenType.MINUS):
            op = self.tokens[self.pos-1].value
            operand = self.unary()
            node = UnaryOp(op, operand)
            node.line = line
            return node
        if self.match(TokenType.AWAIT):
            node = AwaitExpr(self.unary())
            node.line = line
            return node
        return self.call()

    def call(self) -> Expression:
        line = self.line
        expr = self.primary()
        while True:
            if self.match(TokenType.LPAREN):
                arguments = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        arguments.append(self.expression())
                        if not self.match(TokenType.COMMA): break
                self.consume(TokenType.RPAREN, "Expect ')' after arguments.")
                expr = Call(expr, arguments)
                expr.line = line
            elif self.match(TokenType.DOT):
                if self.match(TokenType.SELECT, TokenType.WHERE, TokenType.AVG_BY):
                    member = self.tokens[self.pos-1].value
                    if not self.check(TokenType.LPAREN):
                         arg = self.expression()
                         if member == "select" and isinstance(arg, Identifier): arg = Literal(arg.name)
                         if member == "avg_by":
                             group_by = self.expression()
                             if isinstance(arg, Identifier): arg = Literal(arg.name)
                             if isinstance(group_by, Identifier): group_by = Literal(group_by.name)
                             expr = AvgByStmt(expr, arg.value if hasattr(arg, 'value') else str(arg), group_by.value if hasattr(group_by, 'value') else str(group_by))
                         else: expr = Call(MemberAccess(expr, member), [arg])
                    else: expr = MemberAccess(expr, member)
                else:
                    member = self.consume(TokenType.IDENTIFIER, "Expect member name.").value
                    expr = MemberAccess(expr, member)
                expr.line = line
            elif self.match(TokenType.LBRACKET):
                index_expr = self.expression()
                if self.match(TokenType.COLON):
                    value = self.expression()
                    expr = Call(Identifier("dim_index"), [expr, index_expr, value])
                else: expr = Call(MemberAccess(expr, "__getitem__"), [index_expr])
                self.consume(TokenType.RBRACKET, "Expect ']' after index.")
                expr.line = line
            elif self.match(TokenType.SAFE_NAV):
                member = self.consume(TokenType.IDENTIFIER, "Expect member name.").value
                expr = MemberAccess(expr, member, is_safe=True)
                expr.line = line
            else: break
        return expr

    def primary(self) -> Expression:
        line = self.line
        if self.match(TokenType.BOOLEAN): node = Literal(self.tokens[self.pos-1].value == "true")
        elif self.match(TokenType.NULL): node = Literal(None)
        elif self.match(TokenType.INTEGER): node = Literal(int(self.tokens[self.pos-1].value))
        elif self.match(TokenType.FLOAT): node = Literal(float(self.tokens[self.pos-1].value))
        elif self.match(TokenType.STRING): node = Literal(self.tokens[self.pos-1].value)
        elif self.match(TokenType.TEMPLATE_STRING):
            val = self.tokens[self.pos-1].value
            parts = []
            last_idx = 0
            import re
            from src.nova.lexer import Lexer
            for match in re.finditer(r'\$\{(.*?)\}', val):
                parts.append(val[last_idx:match.start()])
                inner_tokens = Lexer(match.group(1)).tokenize()
                parts.append(Parser(inner_tokens).expression())
                last_idx = match.end()
            parts.append(val[last_idx:])
            node = TemplateLiteral(parts)
        elif self.match(TokenType.GPU): node = Identifier("gpu_context")
        elif self.match(TokenType.NN): node = NNBlock(self.block())
        elif self.match(TokenType.GRADIENT):
             self.consume(TokenType.LPAREN, "Expect '(' after gradient.")
             fn = self.expression()
             vars = []
             if self.match(TokenType.COMMA):
                 while True:
                     vars.append(self.expression())
                     if not self.match(TokenType.COMMA): break
             self.consume(TokenType.RPAREN, "Expect ')' after gradient args.")
             node = GradientExpr(fn, vars)
        elif self.match(TokenType.WEIGHTS):
             self.consume(TokenType.LPAREN, "Expect '(' after weights.")
             shape = self.expression()
             shared = False
             if self.match(TokenType.COMMA):
                  self.consume(TokenType.SHARED, "Expect 'shared' parameter.")
                  self.consume(TokenType.ASSIGN, "Expect '='.")
                  shared = (self.consume(TokenType.BOOLEAN, "Expect boolean.").value == "true")
             self.consume(TokenType.RPAREN, "Expect ')' after weights args.")
             node = WeightsExpr(shape, shared)
        elif self.match(TokenType.BATCH):
             self.consume(TokenType.LPAREN, "Expect '(' after batch.")
             data = self.expression()
             self.consume(TokenType.COMMA, "Expect ',' after dataset in batch.")
             size = self.expression()
             self.consume(TokenType.RPAREN, "Expect ')' after batch args.")
             node = BatchIterator(data, size)
        elif self.match(TokenType.MMAP):
             self.consume(TokenType.LPAREN, "Expect '(' after mmap.")
             path = self.expression()
             self.consume(TokenType.RPAREN, "Expect ')' after mmap path.")
             node = MmapExpr(path)
        elif self.match(TokenType.IDENTIFIER): node = Identifier(self.tokens[self.pos-1].value)
        elif self.match(TokenType.LPAREN):
            temp_pos = self.pos
            is_lambda = False
            paren_count = 1
            while temp_pos < len(self.tokens) and paren_count > 0:
                if self.tokens[temp_pos].type == TokenType.LPAREN: paren_count += 1
                elif self.tokens[temp_pos].type == TokenType.RPAREN: paren_count -= 1
                temp_pos += 1
            if temp_pos < len(self.tokens) and self.tokens[temp_pos].type == TokenType.ARROW: is_lambda = True
            if is_lambda:
                parameters = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        parameters.append(self.consume(TokenType.IDENTIFIER, "Expect parameter name.").value)
                        if not self.match(TokenType.COMMA): break
                self.consume(TokenType.RPAREN, "Expect ')' after parameters.")
                self.consume(TokenType.ARROW, "Expect '=>' after lambda parameters.")
                body = self.expression()
                node = Lambda(parameters, body)
            else:
                expr = self.expression()
                self.consume(TokenType.RPAREN, "Expect ')' after expression.")
                return expr
        elif self.match(TokenType.LBRACKET):
            elements = []
            if not self.check(TokenType.RBRACKET):
                while True:
                    elements.append(self.expression())
                    if not self.match(TokenType.COMMA): break
            self.consume(TokenType.RBRACKET, "Expect ']' after list elements.")
            node = ListLiteral(elements)
        elif self.match(TokenType.LBRACE):
            keys = []; values = []
            if not self.check(TokenType.RBRACE):
                while True:
                    keys.append(self.expression())
                    self.consume(TokenType.COLON, "Expect ':' after dictionary key.")
                    values.append(self.expression())
                    if not self.match(TokenType.COMMA): break
            self.consume(TokenType.RBRACE, "Expect '}' after dictionary elements.")
            node = DictLiteral(keys, values)
        else: raise RuntimeError(f"Unexpected token: {self.peek().type} on line {self.line}")
        node.line = line
        return node
