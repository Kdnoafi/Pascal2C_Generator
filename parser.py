from functools import wraps
import pickle
from numbers import Real

from ast import *
from lexer import Class

funcName = None
forInFunc = False
funcReturn = None
printType = None
typeSet = False
writeType = None

arrayDeclared = False
firstElemDeleted = False
arrayNames = []

ifEntered = False

pointFloat = False

forCounter = []
forStart = []
forOperation = []
forSign = []
forEnd = []
forCount = 0
forEntered = False
forCounterIndex = 0


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.curr = tokens.pop(0)
        self.prev = None

    def restorable(call):
        @wraps(call)
        def wrapper(self, *args, **kwargs):
            state = pickle.dumps(self.__dict__)
            result = call(self, *args, **kwargs)
            self.__dict__ = pickle.loads(state)
            return result

        return wrapper

    def eat(self, class_):
        if self.curr.class_ == class_:
            self.prev = self.curr
            self.curr = self.tokens.pop(0)
        else:
            self.die_type(class_.name, self.curr.class_.name)

    varTypeList = []

    def program(self):
        global funcName
        nodes = []

        while self.curr.class_ != Class.EOF:
            if self.curr.class_ == Class.VAR:
                nodes.append(self.var())
            elif self.curr.class_ == Class.PROCEDURE:
                self.eat(Class.PROCEDURE)
                nodes.append(self.procedure())
            elif self.curr.class_ == Class.FUNCTION:
                self.eat(Class.FUNCTION)
                nodes.append(self.function())
            elif self.curr.class_ == Class.BEGIN:
                funcName = None
                self.eat(Class.BEGIN)
                nodes.append(self.block())
            else:
                print(self.curr.class_)
                self.die_deriv(self.program.__name__)
        return Program(nodes)

    def id_(self):
        global funcName
        global funcReturn
        global forEntered
        global forInFunc
        global arrayDeclared

        id_ = Id(self.curr.lexeme)
        self.eat(Class.ID)
        if self.curr.class_ == Class.LPAREN and self.is_func_call():
            self.eat(Class.LPAREN)
            args = self.args()
            self.eat(Class.RPAREN)
            return FuncCall(id_, args)
        if self.curr.class_ == Class.LBRACKET:
            self.eat(Class.LBRACKET)
            index = self.expr()
            self.eat(Class.RBRACKET)
            id_ = ArrayElem(id_, index)
            arrayDeclared = True
        if self.curr.class_ == Class.ASSIGN:
            self.eat(Class.ASSIGN)
            elems = None
            expr = self.expr()
            if forInFunc == True and forEntered == True:
                return Assign(id_, expr)
            if funcName is not None:
                funcReturn = expr
                funcName = None
                return Return(expr)
            else:
                return Assign(id_, expr)
        else:
            return id_

    def decl(self, nodes):
        global varTypeList
        global arrayDeclared
        global firstElemDeleted
        global arrayNames

        if self.curr.class_ == Class.VAR:
            self.eat(Class.VAR)
            ids = []
            varTypeList = []
            firstArr = False
            while self.curr.class_ != Class.VAR and self.curr.class_ != Class.FUNCTION and self.curr.class_ != Class.PROCEDURE and self.curr.class_ != Class.BEGIN:
                if self.curr.class_ == Class.ID:
                    tempId = self.id_()
                if self.curr.class_ == Class.SET:
                    varTypeList.append(tempId)
                    self.eat(Class.SET)
                    tempType = None
                    if self.curr.class_ == Class.ARRAY:
                        self.eat(Class.ARRAY)
                        self.eat(Class.LBRACKET)
                        start = self.curr.lexeme
                        self.expr()
                        self.eat(Class.ARLEN)
                        end = self.curr.lexeme
                        self.expr()
                        tempSize = (end - start) + 1
                        size = Int(tempSize)
                        self.eat(Class.RBRACKET)
                        self.eat(Class.OF)
                        tempType = self.type_()

                        tempElems = None
                        if self.curr.class_ == Class.EQ:
                            self.eat(Class.EQ)
                            self.eat(Class.LPAREN)
                            tempElems = self.elems()
                            self.eat(Class.RPAREN)
                        self.eat(Class.SEMICOLON)

                        for x in varTypeList:
                            nodes.append(ArrayDecl(tempType, x, size, tempElems))
                            arrayNames.append(x)

                        firstArr = True
                        arrayDeclared = True
                    elif self.curr.class_ == Class.TYPE:
                        tempType = self.type_()

                        if self.curr.class_ == Class.SEMICOLON:
                            for x in varTypeList:
                                if x not in arrayNames:
                                    nodes.append(Decl(x, tempType))
                        elif self.curr.class_ == Class.LBRACKET:
                            self.eat(Class.LBRACKET)
                            size = self.expr()
                            self.eat(Class.RBRACKET)
                            self.eat(Class.SEMICOLON)
                            for x in varTypeList:
                                nodes.append(ArrayDecl(tempType, x, size, None))
                            varTypeList.clear()
                elif self.curr.class_ == Class.COMMA:
                    varTypeList.append(tempId)
                    self.eat(Class.COMMA)
                if self.curr.class_ == Class.SEMICOLON:
                    self.eat(Class.SEMICOLON)
                    varTypeList.clear()
                if self.curr.class_ == Class.TYPE:
                    self.eat(Class.TYPE)
                    exit()

    def if_(self):
        self.eat(Class.IF)
        cond = self.logic()
        self.eat(Class.THEN)
        self.eat(Class.BEGIN)
        true = self.block()
        false = None
        if self.curr.class_ == Class.ELSE:
            self.eat(Class.ELSE)
            self.eat(Class.BEGIN)
            false = self.block()
        return If(cond, true, false)

    def while_(self):
        self.eat(Class.WHILE)
        cond = self.logic()
        self.eat(Class.DO)
        self.eat(Class.BEGIN)
        block = self.block()
        return While(cond, block)

    def repeat_(self):
        self.eat(Class.REPEAT)
        block = self.block()
        self.eat(Class.UNTIL)
        cond = self.logic()
        self.eat(Class.SEMICOLON)
        return Repeat(cond, block)

    def for_(self):
        global forEntered
        global forCounter
        global forStart
        global forEnd
        global forOperation
        global forCount
        global forSign
        forEntered = True
        forCount += 1

        self.eat(Class.FOR)
        forCounter.append(Id(self.curr.lexeme))
        start = self.id_()

        if self.curr.class_ == Class.TO:
            self.eat(Class.TO)
            forOperation.append('<=')
            forSign.append('+')
        elif self.curr.class_ == Class.DOWNTO:
            self.eat(Class.DOWNTO)
            forOperation.append('>=')
            forSign.append('-')

        forEnd.append(self.curr.lexeme)  ###
        end = self.expr()
        self.eat(Class.DO)
        self.eat(Class.BEGIN)
        forEntered = False  ###
        block = self.block()
        cond = BinOp(forOperation[-1], forCounter[-1], forEnd[-1])
        return For(start, end, block, cond)

    def var(self):
        global firstElemDeleted

        firstElemDeleted = False
        nodes = []
        self.decl(nodes)
        return Var(nodes)

    def procedure(self):
        nodes = []
        varBlock = None
        block = None

        id_ = self.id_()
        self.eat(Class.LPAREN)
        params = self.params()
        self.eat(Class.RPAREN)
        self.eat(Class.SEMICOLON)
        if self.curr.class_ == Class.VAR:
            varBlock = self.var()
            nodes.append(varBlock)
        if self.curr.class_ == Class.BEGIN:
            self.eat(Class.BEGIN)
            block = self.block()
            nodes.append(block)
        return ProcedureImpl(id_, params, varBlock, block)

    def function(self):
        global funcName
        global funcReturn
        global forInFunc
        nodes = []
        block = None
        varBlock = None
        forInFunc = True

        id_ = self.id_()
        funcName = id_.value
        self.eat(Class.LPAREN)
        params = self.params()
        self.eat(Class.RPAREN)
        self.eat(Class.SET)
        type_ = self.type_()
        self.eat(Class.SEMICOLON)
        if self.curr.class_ == Class.VAR:
            varBlock = self.var()
            nodes.append(varBlock)
        if self.curr.class_ == Class.BEGIN:
            self.eat(Class.BEGIN)
            block = self.block()
            nodes.append(block)
        funcReturn = None
        forInFunc = False
        return FuncImpl(type_, id_, params, varBlock, block)

    def block(self):
        nodes = []
        tempClass = None
        while self.curr.class_ != Class.END and self.curr.class_ != Class.UNTIL:
            if self.curr.class_ == Class.IF:
                nodes.append(self.if_())
            elif self.curr.class_ == Class.WHILE:
                nodes.append(self.while_())
            elif self.curr.class_ == Class.FOR:
                nodes.append(self.for_())
            elif self.curr.class_ == Class.REPEAT:
                nodes.append(self.repeat_())
            elif self.curr.class_ == Class.BREAK:
                nodes.append(self.break_())
            elif self.curr.class_ == Class.CONTINUE:
                nodes.append(self.continue_())
            elif self.curr.class_ == Class.EXIT:
                nodes.append(self.exit_())
            elif self.curr.class_ == Class.VAR:
                tempClass = Class.VAR
                self.decl(nodes)
            elif self.curr.class_ == Class.ID:
                nodes.append(self.id_())
            else:
                self.die_deriv(self.block.__name__)
            if self.curr.class_ == Class.SEMICOLON:
                self.eat(Class.SEMICOLON)
        if self.curr.class_ == Class.END:
            self.eat(Class.END)
        if self.curr.class_ == Class.SEMICOLON:
            self.eat(Class.SEMICOLON)
        return Block(nodes)

    def params(self):
        params = []
        ids = []

        tempId = None
        while self.curr.class_ != Class.SET:
            if self.curr.class_ == Class.ID:
                tempId = self.id_()
            elif self.curr.class_ == Class.COMMA:
                ids.append(tempId)
                self.eat(Class.COMMA)
        ids.append(tempId)
        self.eat(Class.SET)
        tempType = self.type_()
        for x in ids:
            params.append(Decl(x, tempType))
        return Params(params)

    def args(self):
        global pointFloat

        args = []
        while self.curr.class_ != Class.RPAREN:
            if len(args) > 0:
                self.eat(Class.COMMA)
            args.append(self.expr())
            if self.curr.class_ == Class.INT:
                self.eat(Class.INT)
            elif self.curr.class_ == Class.CHAR:
                self.eat(Class.CHAR)
            elif self.curr.class_ == Class.STRING:
                self.eat(Class.STRING)
            elif self.curr.class_ == Class.REAL:
                self.eat(Class.REAL)
            elif self.curr.class_ == Class.VAR:
                self.eat(Class.VAR)
            elif self.curr.class_ == Class.BOOLEAN:
                self.eat(Class.BOOLEAN)
            elif self.curr.class_ == Class.SET and self.prev.class_ == Class.RPAREN:
                self.eat(Class.SET)
                self.expr()
                self.eat(Class.SET)
                self.expr()
                pointFloat = True
        return Args(args);

    def elems(self):
        elems = []
        while self.curr.class_ != Class.RPAREN:
            if len(elems) > 0:
                self.eat(Class.COMMA)
            elems.append(self.expr())
        return Elems(elems)

    def exit_(self):
        self.eat(Class.EXIT)

        arg = None
        if self.curr.class_ == Class.LPAREN:
            self.eat(Class.LPAREN)
            arg = self.expr()
            self.eat(Class.RPAREN)

        self.eat(Class.SEMICOLON)
        return Exit(arg)

    def break_(self):
        self.eat(Class.BREAK)
        self.eat(Class.SEMICOLON)
        return Break()

    def continue_(self):
        self.eat(Class.CONTINUE)
        self.eat(Class.SEMICOLON)
        return Continue()

    def type_(self):
        type_ = Type(self.curr.lexeme)
        self.eat(Class.TYPE)
        return type_

    def factor(self):
        if self.curr.class_ == Class.INT:
            value = Int(self.curr.lexeme)
            self.eat(Class.INT)
            return value
        elif self.curr.class_ == Class.CHAR:
            value = Char(self.curr.lexeme)
            self.eat(Class.CHAR)
            return value
        elif self.curr.class_ == Class.STRING:
            value = String(self.curr.lexeme)
            self.eat(Class.STRING)
            return value
        elif self.curr.class_ == Class.REAL:
            value = Real(self.curr.lexeme)
            self.eat(Class.REAL)
            return value
        elif self.curr.class_ == Class.ID:
            return self.id_()
        elif self.curr.class_ in [Class.MINUS, Class.NOT, Class.ADDRESS]:
            op = self.curr
            self.eat(self.curr.class_)
            first = None
            if self.curr.class_ == Class.LPAREN:
                self.eat(Class.LPAREN)
                first = self.logic()
                self.eat(Class.RPAREN)
            else:
                first = self.factor()
            return UnOp(op.lexeme, first)
        elif self.curr.class_ == Class.LPAREN:
            self.eat(Class.LPAREN)
            first = self.logic()
            self.eat(Class.RPAREN)
            return first
        elif self.curr.class_ == Class.SEMICOLON:
            return None
        else:
            self.die_deriv(self.factor.__name__)

    def term(self):
        first = self.factor()
        while self.curr.class_ in [Class.STAR, Class.DIV, Class.MOD, Class.EQ, Class.FWDSLASH, Class.NEQ]:  #
            if self.curr.class_ == Class.STAR:
                op = self.curr.lexeme
                self.eat(Class.STAR)
                second = self.factor()
                first = BinOp(op, first, second)
            elif self.curr.class_ == Class.DIV:
                op = self.curr.lexeme
                self.eat(Class.DIV)
                second = self.factor()
                first = BinOp(op, first, second)
            elif self.curr.class_ == Class.MOD:
                op = self.curr.lexeme
                self.eat(Class.MOD)
                second = self.factor()
                first = BinOp(op, first, second)
            elif self.curr.class_ == Class.EQ:
                op = self.curr.lexeme
                self.eat(Class.EQ)
                second = self.factor()
                first = BinOp(op, first, second)
            elif self.curr.class_ == Class.NEQ:
                op = self.curr.lexeme
                self.eat(Class.NEQ)
                second = self.factor()
                first = BinOp(op, first, second)
            elif self.curr.class_ == Class.FWDSLASH:
                op = self.curr.lexeme
                self.eat(Class.FWDSLASH)
                second = self.factor()
                first = BinOp(op, first, second)
        return first

    def expr(self):
        first = self.term()
        while self.curr.class_ in [Class.PLUS, Class.MINUS]:
            if self.curr.class_ == Class.PLUS:
                op = self.curr.lexeme
                self.eat(Class.PLUS)
                second = self.term()
                first = BinOp(op, first, second)
            elif self.curr.class_ == Class.MINUS:
                op = self.curr.lexeme
                self.eat(Class.MINUS)
                second = self.term()
                first = BinOp(op, first, second)
        return first

    def compare(self):
        first = self.expr()
        if self.curr.class_ == Class.EQ:
            op = self.curr.lexeme
            self.eat(Class.EQ)
            second = self.expr()
            return BinOp(op, first, second)
        elif self.curr.class_ == Class.NEQ:
            op = self.curr.lexeme
            self.eat(Class.NEQ)
            second = self.expr()
            return BinOp(op, first, second)
        elif self.curr.class_ == Class.LT:
            op = self.curr.lexeme
            self.eat(Class.LT)
            second = self.expr()
            return BinOp(op, first, second)
        elif self.curr.class_ == Class.GT:
            op = self.curr.lexeme
            self.eat(Class.GT)
            second = self.expr()
            return BinOp(op, first, second)
        elif self.curr.class_ == Class.LTE:
            op = self.curr.lexeme
            self.eat(Class.LTE)
            second = self.expr()
            return BinOp(op, first, second)
        elif self.curr.class_ == Class.GTE:
            op = self.curr.lexeme
            self.eat(Class.GTE)
            second = self.expr()
            return BinOp(op, first, second)
        else:
            return first

    def logic(self):
        first = self.compare()
        while self.curr.class_ in [Class.AND, Class.OR]:
            if self.curr.class_ == Class.AND:
                op = self.curr.lexeme
                self.eat(Class.AND)
                second = self.compare()
                return BinOp(op, first, second)
            elif self.curr.class_ == Class.OR:
                op = self.curr.lexeme
                self.eat(Class.OR)
                second = self.compare()
                return BinOp(op, first, second)
        return first

    @restorable
    def is_func_call(self):
        global pointFloat

        try:
            self.eat(Class.LPAREN)
            self.args()
            self.eat(Class.RPAREN)
            if self.curr.class_ == Class.SET:
                print(self.prev.lexeme)
                self.eat(Class.SET)
                self.expr()
                self.eat(Class.SET)
                self.expr()
                pointFloat = True
            return True
        except:
            return False

    def parse(self):
        return self.program()

    def die(self, text):
        raise SystemExit(text)

    def die_deriv(self, fun):
        self.die("Derivation error: {}".format(fun))

    def die_type(self, expected, found):
        self.die("Expected: {}, Found: {}".format(expected, found))