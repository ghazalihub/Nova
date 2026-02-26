from src.nova.lexer import Lexer, Token, TokenType

class Formatter:
    def format(self, source):
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        result = ""
        indent_level = 0

        for i, token in enumerate(tokens):
            if token.type == TokenType.EOF:
                break

            if token.type == TokenType.LBRACE:
                result += " {\n"
                indent_level += 1
                result += "    " * indent_level
            elif token.type == TokenType.RBRACE:
                indent_level -= 1
                result = result.rstrip()
                result += "\n" + ("    " * indent_level) + "}\n"
                if i + 1 < len(tokens) and tokens[i+1].type != TokenType.EOF:
                    result += "    " * indent_level
            elif token.type == TokenType.SEMICOLON:
                result += ";\n"
                result += "    " * indent_level
            elif token.type == TokenType.COMMA:
                result += ", "
            elif token.type in [TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.ASSIGN, TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.GT, TokenType.PIPELINE]:
                result += f" {token.value} "
            elif token.type in [TokenType.FN, TokenType.LET, TokenType.CONST, TokenType.MODEL, TokenType.IF, TokenType.FOR, TokenType.WHILE, TokenType.IMPORT, TokenType.FROM, TokenType.EXPORT, TokenType.ASYNC, TokenType.AWAIT, TokenType.MATCH, TokenType.CASE, TokenType.TRAIN, TokenType.LAZY, TokenType.WITH, TokenType.AS]:
                result += f"{token.value} "
            else:
                result += token.value

        # Clean up empty lines and spaces
        import re
        result = re.sub(r' +', ' ', result)
        result = re.sub(r'\n +', '\n' + ("    " * indent_level), result)
        return result.strip()

if __name__ == "__main__":
    import sys
    with open(sys.argv[1], "r") as f:
        print(Formatter().format(f.read()))
