from src.nova.lexer import Token, TokenType
from src.nova.nova_ast import *

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

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
        raise RuntimeError(f"Error at line {self.peek().line}: {message}")

    def parse(self) -> Program:
        statements = []
        while not self.check(TokenType.EOF):
            statements.append(self.statement())
        return Program(statements)

    def statement(self) -> Statement:
        if self.match(TokenType.IMPORT):
            return self.import_statement()
        if self.match(TokenType.LET, TokenType.CONST):
            return self.var_declaration(self.tokens[self.pos-1].type == TokenType.CONST)
        if self.match(TokenType.FN):
            return self.function_declaration()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.FOR):
            return self.for_statement(is_parallel=False)
        if self.match(TokenType.PARALLEL):
            self.consume(TokenType.FOR, "Expect 'for' after 'parallel'.")
            return self.for_statement(is_parallel=True)
        if self.match(TokenType.MODEL):
            return self.model_declaration()
        if self.match(TokenType.MATCH):
            return self.match_statement()
        if self.match(TokenType.TRY):
            return self.try_statement()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.LBRACE):
            return self.block()
        return self.expression_statement()

    def import_statement(self) -> ImportStatement:
        names = []
        if self.match(TokenType.LBRACE):
            while True:
                names.append(self.consume(TokenType.IDENTIFIER, "Expect name to import.").value)
                if not self.match(TokenType.COMMA):
                    break
            self.consume(TokenType.RBRACE, "Expect '}' after import names.")
        else:
            names.append(self.consume(TokenType.IDENTIFIER, "Expect name to import.").value)

        self.consume(TokenType.FROM, "Expect 'from' after import names.")
        source = self.consume(TokenType.STRING, "Expect module source string.").value
        self.match(TokenType.SEMICOLON)
        return ImportStatement(names, source)

    def var_declaration(self, is_const: bool) -> VarDeclaration:
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.").value
        type_hint = None
        if self.match(TokenType.COLON):
            type_hint = self.consume(TokenType.IDENTIFIER, "Expect type name.").value # Simplified
        self.consume(TokenType.ASSIGN, "Expect '=' after variable name.")
        value = self.expression()
        self.match(TokenType.SEMICOLON)
        return VarDeclaration(name, type_hint, value, is_const)

    def function_declaration(self) -> FunctionDeclaration:
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
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RPAREN, "Expect ')' after parameters.")
        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.consume(TokenType.IDENTIFIER, "Expect return type.").value
        body = self.block() if self.check(TokenType.LBRACE) else [self.expression_statement()]
        return FunctionDeclaration(name, parameters, return_type, body if isinstance(body, list) else [body])

    def if_statement(self) -> IfStatement:
        self.consume(TokenType.LPAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RPAREN, "Expect ')' after if condition.")
        then_block = self.block()
        else_block = None
        if self.match(TokenType.ELSE):
            if self.match(TokenType.IF):
                else_block = self.if_statement()
            else:
                else_block = self.block()
        return IfStatement(condition, then_block, else_block)

    def for_statement(self, is_parallel: bool) -> ForStatement:
        self.consume(TokenType.LPAREN, "Expect '(' after 'for'.")
        target = self.consume(TokenType.IDENTIFIER, "Expect loop variable name.").value
        self.consume(TokenType.IN, "Expect 'in' after loop variable.")
        iterable = self.expression()
        self.consume(TokenType.RPAREN, "Expect ')' after for clauses.")
        body = self.block()
        return ForStatement(target, iterable, body, is_parallel)

    def model_declaration(self) -> ModelDeclaration:
        name = self.consume(TokenType.IDENTIFIER, "Expect model name.").value
        base_class = None
        if self.match(TokenType.LPAREN):
            base_class = self.consume(TokenType.IDENTIFIER, "Expect base class name.").value
            self.consume(TokenType.RPAREN, "Expect ')' after base class.")
        self.consume(TokenType.LBRACE, "Expect '{' before model body.")
        members = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            members.append(self.statement())
        self.consume(TokenType.RBRACE, "Expect '}' after model body.")
        return ModelDeclaration(name, base_class, members)

    def match_statement(self) -> MatchStatement:
        self.consume(TokenType.LPAREN, "Expect '(' after 'match'.")
        expression = self.expression()
        self.consume(TokenType.RPAREN, "Expect ')' after match expression.")
        self.consume(TokenType.LBRACE, "Expect '{' before match body.")
        cases = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            self.consume(TokenType.CASE, "Expect 'case' in match body.")
            pattern = self.expression()
            guard = None
            if self.match(TokenType.IF):
                guard = self.expression()
            self.consume(TokenType.ARROW, "Expect '=>' after pattern.")
            body = self.block() if self.check(TokenType.LBRACE) else [self.statement()]
            cases.append(MatchCase(pattern, guard, body))
        self.consume(TokenType.RBRACE, "Expect '}' after match body.")
        return MatchStatement(expression, cases)

    def try_statement(self) -> TryStatement:
        body = self.block()
        catches = []
        while self.match(TokenType.CATCH):
            self.consume(TokenType.LPAREN, "Expect '(' after 'catch'.")
            variable = self.consume(TokenType.IDENTIFIER, "Expect variable name in catch.").value
            type_hint = None
            if self.match(TokenType.COLON):
                type_hint = self.consume(TokenType.IDENTIFIER, "Expect type in catch.").value
            self.consume(TokenType.RPAREN, "Expect ')' after catch variable.")
            catch_body = self.block()
            catches.append(CatchBlock(variable, type_hint, catch_body))

        finally_block = None
        if self.match(TokenType.FINALLY):
            finally_block = self.block()

        return TryStatement(body, catches, finally_block)

    def block(self) -> List[Statement]:
        if not self.match(TokenType.LBRACE):
            # If not a brace, it might be a single statement (not recommended but supported in some cases)
            return [self.statement()]
        statements = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            statements.append(self.statement())
        self.consume(TokenType.RBRACE, "Expect '}' after block.")
        return statements

    def return_statement(self) -> ReturnStatement:
        value = None
        if not self.check(TokenType.SEMICOLON) and not self.check(TokenType.RBRACE):
            value = self.expression()
        self.match(TokenType.SEMICOLON)
        return ReturnStatement(value)

    def expression_statement(self) -> ExpressionStatement:
        expr = self.expression()
        self.match(TokenType.SEMICOLON)
        return ExpressionStatement(expr)

    def expression(self) -> Expression:
        return self.pipeline()

    def pipeline(self) -> Expression:
        expr = self.assignment()
        while self.match(TokenType.PIPELINE):
            right = self.call()
            if not isinstance(right, Call):
                 raise RuntimeError("Right side of pipeline must be a function call")
            expr = Pipeline(expr, right)
        return expr

    def assignment(self) -> Expression:
        expr = self.equality()
        if self.match(TokenType.ASSIGN):
            value = self.assignment()
            if isinstance(expr, Identifier):
                return BinaryOp(expr, "=", value) # Simplified
        return expr

    def equality(self) -> Expression:
        expr = self.comparison()
        while self.match(TokenType.EQ, TokenType.NE):
            op = self.tokens[self.pos-1].value
            right = self.comparison()
            expr = BinaryOp(expr, op, right)
        return expr

    def comparison(self) -> Expression:
        expr = self.term()
        while self.match(TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE):
            op = self.tokens[self.pos-1].value
            right = self.term()
            expr = BinaryOp(expr, op, right)
        return expr

    def term(self) -> Expression:
        expr = self.factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.tokens[self.pos-1].value
            right = self.factor()
            expr = BinaryOp(expr, op, right)
        return expr

    def factor(self) -> Expression:
        expr = self.unary()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.tokens[self.pos-1].value
            right = self.unary()
            expr = BinaryOp(expr, op, right)
        return expr

    def unary(self) -> Expression:
        if self.match(TokenType.NOT, TokenType.MINUS):
            op = self.tokens[self.pos-1].value
            operand = self.unary()
            return UnaryOp(op, operand)
        return self.call()

    def call(self) -> Expression:
        expr = self.primary()
        while True:
            if self.match(TokenType.LPAREN):
                arguments = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        arguments.append(self.expression())
                        if not self.match(TokenType.COMMA):
                            break
                self.consume(TokenType.RPAREN, "Expect ')' after arguments.")
                expr = Call(expr, arguments)
            elif self.match(TokenType.DOT):
                member = self.consume(TokenType.IDENTIFIER, "Expect member name.").value
                expr = MemberAccess(expr, member)
            elif self.match(TokenType.SAFE_NAV):
                member = self.consume(TokenType.IDENTIFIER, "Expect member name.").value
                expr = MemberAccess(expr, member, is_safe=True)
            else:
                break
        return expr

    def primary(self) -> Expression:
        if self.match(TokenType.BOOLEAN):
            return Literal(self.tokens[self.pos-1].value == "true")
        if self.match(TokenType.NULL):
            return Literal(None)
        if self.match(TokenType.INTEGER):
            return Literal(int(self.tokens[self.pos-1].value))
        if self.match(TokenType.FLOAT):
            return Literal(float(self.tokens[self.pos-1].value))
        if self.match(TokenType.STRING):
            return Literal(self.tokens[self.pos-1].value)
        if self.match(TokenType.IDENTIFIER):
            return Identifier(self.tokens[self.pos-1].value)
        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expect ')' after expression.")
            return expr

        if self.match(TokenType.LBRACKET):
            elements = []
            if not self.check(TokenType.RBRACKET):
                while True:
                    elements.append(self.expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RBRACKET, "Expect ']' after list elements.")
            return ListLiteral(elements)

        if self.match(TokenType.LBRACE):
            keys = []
            values = []
            if not self.check(TokenType.RBRACE):
                while True:
                    keys.append(self.expression())
                    self.consume(TokenType.COLON, "Expect ':' after dictionary key.")
                    values.append(self.expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RBRACE, "Expect '}' after dictionary elements.")
            return DictLiteral(keys, values)

        raise RuntimeError(f"Unexpected token: {self.peek().type} on line {self.peek().line}")
