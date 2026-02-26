from dataclasses import dataclass, field
from typing import List, Optional, Union

@dataclass
class Node:
    pass

@dataclass
class Expression(Node):
    pass

@dataclass
class Statement(Node):
    pass

@dataclass
class Identifier(Expression):
    name: str

@dataclass
class Literal(Expression):
    value: Union[int, float, str, bool, None]

@dataclass
class BinaryOp(Expression):
    left: Expression
    op: str
    right: Expression

@dataclass
class Assignment(Statement):
    target: Expression
    value: Expression

@dataclass
class UnaryOp(Expression):
    op: str
    operand: Expression

@dataclass
class Call(Expression):
    callee: Expression
    arguments: List[Expression]

@dataclass
class MemberAccess(Expression):
    object: Expression
    member: str
    is_safe: bool = False  # For ?.

@dataclass
class ListLiteral(Expression):
    elements: List[Expression]

@dataclass
class TemplateLiteral(Expression):
    parts: List[Union[str, Expression]]

@dataclass
class DictLiteral(Expression):
    keys: List[Expression]
    values: List[Expression]

@dataclass
class NNBlock(Expression):
    statements: List[Statement]

@dataclass
class GradientExpr(Expression):
    function: Expression
    variables: List[Expression]

@dataclass
class WeightsExpr(Expression):
    shape: Expression

@dataclass
class MmapExpr(Expression):
    path: Expression

@dataclass
class Lambda(Expression):
    parameters: List[str]
    body: Union[Expression, List[Statement]]

@dataclass
class Pipeline(Expression):
    left: Expression
    right: Call

@dataclass
class VarDeclaration(Statement):
    name: str
    type_hint: Optional[str]
    value: Expression
    is_const: bool = False
    is_lazy: bool = False

@dataclass
class TrainStatement(Statement):
    model: Expression
    dataset: Expression
    options: Optional[Expression] = None

@dataclass
class FunctionDeclaration(Statement):
    name: str
    parameters: List[dict] # name, type, default
    return_type: Optional[str]
    body: List[Statement]
    is_async: bool = False

@dataclass
class ModelDeclaration(Statement):
    name: str
    base_class: Optional[str]
    members: List[Statement]

@dataclass
class StructDecl(Statement):
    name: str
    fields: List[dict] # name, type

@dataclass
class SchemaDecl(Statement):
    name: str
    definition: Expression

@dataclass
class IfStatement(Statement):
    condition: Expression
    then_block: List[Statement]
    else_block: Optional[Union[List[Statement], 'IfStatement']] = None

@dataclass
class WithStmt(Statement):
    context: Expression
    variable: Optional[str]
    body: List[Statement]

@dataclass
class CleanStmt(Statement):
    target: Expression

@dataclass
class PlotStmt(Statement):
    target: Expression
    options: Optional[Expression] = None

@dataclass
class ForStatement(Statement):
    target: str
    iterable: Expression
    body: List[Statement]
    is_parallel: bool = False
    is_async: bool = False

@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: List[Statement]

@dataclass
class BatchIterator(Expression):
    dataset: Expression
    size: Expression

@dataclass
class AwaitExpr(Expression):
    expression: Expression

@dataclass
class ReturnStatement(Statement):
    value: Optional[Expression]

@dataclass
class ExpressionStatement(Statement):
    expression: Expression

@dataclass
class Block(Statement):
    statements: List[Statement]

@dataclass
class MatchStatement(Statement):
    expression: Expression
    cases: List['MatchCase']

@dataclass
class MatchCase(Node):
    pattern: Expression
    guard: Optional[Expression]
    body: Union[Expression, List[Statement]]

@dataclass
class ImportStatement(Statement):
    names: List[str]
    source: str

@dataclass
class ExportStmt(Statement):
    declaration: Statement

@dataclass
class PanicStmt(Statement):
    message: Expression

@dataclass
class AssertStmt(Statement):
    condition: Expression

@dataclass
class RecoverStmt(Statement):
    body: List[Statement]

@dataclass
class TryStatement(Statement):
    body: List[Statement]
    catches: List['CatchBlock']
    finally_block: Optional[List[Statement]] = None

@dataclass
class CatchBlock(Node):
    variable: str
    type_hint: Optional[str]
    body: List[Statement]

@dataclass
class TestStmt(Statement):
    name: str
    body: List[Statement]

@dataclass
class BenchStmt(Statement):
    name: str
    body: List[Statement]

@dataclass
class PromptDecl(Statement):
    name: str
    body: List[Statement]

@dataclass
class SecureStmt(Statement):
    body: List[Statement]

@dataclass
class SharedStateStmt(Statement):
    body: List[Statement]

@dataclass
class DecoratorExpr(Node):
    name: str
    expression: Union[Statement, Expression]

@dataclass
class Program(Node):
    statements: List[Statement]
