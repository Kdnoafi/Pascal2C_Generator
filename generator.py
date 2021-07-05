import re

from ast import Block, Char, String, BinOp
from parser import forOperation
from visitor import Visitor


class Generator(Visitor):
    def __init__(self, ast):
        self.ast = ast
        self.py = ""
        self.level = 0

    def append(self, text):
        self.py += str(text)

    def newline(self):
        self.append('\n\r')

    def indent(self):
        for i in range(self.level):
            self.append('\t')

    def visit_Program(self, parent, node):
        for n in node.nodes:
            if isinstance(n, Block):
                self.append("int main() {")
                self.newline()
            self.visit(node, n)
        self.append("return 0;")
        self.newline()
        self.append("}")

    def visit_Decl(self, parent, node):
        global printType
        global typeSet
        tempId = node.id_.value

        if node.id_.value == "integer":
            tempId = "int"
        if node.id_.value == "boolean":
            tempId = "int"
        if node.id_.value == "real":
            tempId = "float"
        if node.id_.value == "char":
            tempId = "char"
        if typeSet == False:
            printType = tempId
            typeSet = True

        self.append(tempId)
        self.append(' ')
        self.append(node.type_.value)
        self.append(';')
        self.newline()

    def visit_ArrayDecl(self, parent, node):
        self.visit(node, node.type_)
        self.visit(node, node.id_)
        if node.elems is not None:
            self.append('={')
            # self.append(' = [')
            self.visit(node, node.elems)
            self.append('};')
        elif node.size is not None:
            # self.append(' = ')
            self.append('[')
            self.visit(node, node.size)
            self.append('];')

    def visit_ArrayElem(self, parent, node):
        self.visit(node, node.id_)
        self.append('[')
        self.visit(node, node.index)
        self.append(']')

    def visit_Assign(self, parent, node):
        self.visit(node, node.id_)
        self.append(' = ')
        self.visit(node, node.expr)
        self.append(";")

    def visit_If(self, parent, node):
        global ifEntered
        ifEntered = True

        self.append("if(")
        self.visit(node, node.cond)
        self.append(") {")
        self.newline()
        self.visit(node, node.true)
        self.newline()
        self.append("} ")
        if node.false is not None:
            self.indent()
            self.append('else {')
            self.newline()
            self.visit(node, node.false)
            self.newline()
            self.append("}")
            self.newline()
        ifEntered = False

    def visit_While(self, parent, node):
        self.append('while(')
        self.visit(node, node.cond)
        self.append(') {')
        self.newline()
        self.visit(node, node.block)
        self.newLine()
        self.append("}")
        self.newLine()

    def visit_Repeat(self, parent, node):
        self.append('do {')
        self.newline()
        self.visit(node, node.block)
        self.append('} while(')
        if node.cond.value == "false":
            self.append("1")
        elif node.cond.value == "true":
            self.append("0")
        else:
            self.visit(node, node.cond)
        self.append(');')
        self.newline()

    def visit_For(self, parent, node):
        global forEntered
        global forCounter
        global forStart
        global forEnd
        global forOpertaion
        global forCount
        global forSign
        global forCounterIndex

        self.append('for(')
        self.visit(node, node.start)
        if str(node.start.id_.value) == 'j':
            forCounter[forCounterIndex].value = 'j'
        self.append(forCounter[forCounterIndex].value)
        self.append(forOperation[forCounterIndex])
        self.append(forEnd[forCounterIndex])
        if forEnd[forCounterIndex] == 'ci' or forEnd[forCounterIndex] == 'bi':
            self.append('-1')
        self.append('; ')
        self.append(forCounter[forCounterIndex].value)
        self.append('=')
        self.append(forCounter[forCounterIndex].value)
        self.append(forSign[forCounterIndex])
        # self.visit(node, node.end)
        self.append('1')
        self.append(') {')
        self.newline()
        self.visit(node, node.block)
        self.append('}')
        self.newline()
        forCounterIndex += 1

    def visit_FuncImpl(self, parent, node):
        if node.type_.value == "boolean":
            self.append("int")
        elif node.type_.value == "integer":
            self.append("int")
        else:
            self.append(node.type_.value)
        self.append(' ')
        self.append(node.id_.value)
        self.append('(')
        self.visit(node, node.params)
        self.append(') {')
        self.newline()
        if node.var is not None:
            self.visit(node, node.var)
            self.newline()
        self.visit(node, node.block)
        self.append(';')
        self.newline()
        self.append('}')
        self.newline()

    def visit_ProcedureImpl(self, parent, node):
        self.append('void ')
        self.append(node.id_.value)
        self.append('(')
        self.visit(node, node.params)
        self.append(') {')
        self.newline()
        self.visit(node, node.var)
        self.newline()
        self.visit(node, node.block)
        self.newline()
        self.append('}')
        self.newline()

    def visit_FuncCall(self, parent, node):
        global printType
        global typeSet
        global writeType
        global pointFloat
        func = node.id_.value
        args = node.args.args
        tempType = None

        if printType == "int":
            tempType = "%d"
        elif printType == "char":
            tempType = "%c"
        elif printType == "string":
            tempType = "%s"
        elif printType == "float":
            tempType = "%f"
        if typeSet == True:
            writeType = tempType
        if func == 'readln' or func == 'read':
            self.append('scanf("')
            for arg in args:
                self.append(writeType)
            self.append('", &')
            for i, a in enumerate(args):
                if i > 0:
                    self.append(', &')
                self.visit(node.args, a)
            self.append(");")
            self.newline()
        elif func == 'write' or func == "writeln":
            self.append('printf("')
            spaces = 0
            nonSpaces = 0
            index = []

            if pointFloat == True and writeType == "%f":
                writeType = "%.2f"

            if len(args) == 0:
                string = '\\n");'
                self.append(string)
                self.newline()
                return

            for arg in args:
                if isinstance(arg, Char):
                    if arg.value == ' ':
                        if len(args) == 1:
                            self.append(arg.value)
                            self.append('");')
                            self.newline()
                            return
                        spaces += 1
                        index.append(' ')
                elif isinstance(arg, String):
                    self.append(arg.value)
                    self.append('");')
                    self.newline()
                    return
                else:
                    nonSpaces += 1
                    index.append('')
            i = 0
            for arg in args:
                if len(index) > 0:
                    if index[i] == ' ':
                        self.append(index[i])
                    else:
                        self.append(writeType)
                else:
                    if isinstance(arg, Char):
                        self.append(arg.value)
                        self.append('");')
                        self.newline()
                        return
                    self.append(writeType)
                i += 1
            if func == 'writeln':
                self.append('\\n')
            self.append('", ')
            for i, a in enumerate(args):
                if isinstance(a, Char):
                    if a.value == ' ':
                        continue
                if i > 0:
                    self.append(', ')
                self.visit(node.args, a)
            self.append(");")
            self.newline()
        elif func == 'chr':
            for i, a in enumerate(args):
                self.visit(node.args, a)
        elif func == 'ord':
            for i, a in enumerate(args):
                self.visit(node.args, a)
        else:
            self.append(func)
            self.append('(')
            self.visit(node, node.args)
            self.append(')')

        printType = None
        typeSet = False

    def visit_Var(self, parent, node):
        self.level += 1
        for n in node.nodes:
            self.indent()
            self.visit(node, n)
            self.newline()
        self.level -= 1

    def visit_Block(self, parent, node):
        self.level += 1
        for n in node.nodes:
            self.indent()
            self.visit(node, n)
            self.newline()
        self.level -= 1

    def visit_Params(self, parent, node):
        for i, p in enumerate(node.params):
            if i > 0:
                self.append(', ')
            self.visit(p, p.id_)
            self.append(p.type_.value)
            # self.visit(node, p)

    def visit_Args(self, parent, node):
        for i, a in enumerate(node.args):
            if i > 0:
                self.append(', ')
            self.visit(node, a)

    def visit_Elems(self, parent, node):
        for i, e in enumerate(node.elems):
            if i > 0:
                self.append(', ')
            self.visit(node, e)

    def visit_Break(self, parent, node):
        self.append('break;')

    def visit_Continue(self, parent, node):
        self.append('continue;')

    def visit_Return(self, parent, node):
        self.append('return')
        if node.expr is not None:
            self.append(' ')
            self.visit(node, node.expr)

    def visit_Exit(self, parent, node):
        if isinstance(node.arg, BinOp):
            self.append('return ')
            self.visit(node, node.arg)
        if node.arg == None:
            self.append('return;')
        elif not isinstance(node.arg, BinOp):
            if node.arg.value == None:
                self.append('return;')
            elif node.arg.value == 'true':
                self.append('return 1;')
            elif node.arg.value == 'false':
                self.append('return 0;')
            else:
                self.append('return ')
                self.append(node.arg.value)
                self.append(';')
        self.newline()

    def visit_Type(self, parent, node):
        global printType
        global typeSet
        tempId = node.value

        if node.value == "integer":
            tempId = "int"
        if node.value == "boolean":
            tempId = "int"
        if node.value == "real":
            tempId = "float"
        if typeSet == False:
            printType = tempId
            typeSet = True

        self.append(tempId)
        self.append(' ')

    def visit_Int(self, parent, node):
        self.append(node.value)

    def visit_Char(self, parent, node):
        self.append(ord(node.value))

    def visit_String(self, parent, node):
        self.append(node.value)

    def visit_Id(self, parent, node):
        self.append(node.value)

    def visit_BinOp(self, parent, node):
        self.visit(node, node.first)
        if node.symbol == '&&':
            self.append(' and ')
        elif node.symbol == '||':
            self.append(' or ')
        elif node.symbol == 'div':
            self.append('/')
        elif node.symbol == 'mod':
            self.append('%')
        elif node.symbol == '=':
            self.append('==')
        else:
            self.append(node.symbol)
        self.visit(node, node.second)

    def visit_UnOp(self, parent, node):
        if node.symbol == '!':
            self.append('not ')
        elif node.symbol != '&':
            self.append(node.symbol)
        self.visit(node, node.first)

    def generate(self, path):
        self.visit(None, self.ast)
        self.py = re.sub('\n\s*\n', '\n', self.py)
        with open(path, 'w') as source:
            source.write(self.py)
        return path