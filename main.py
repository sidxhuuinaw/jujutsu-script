operators = ["+","-","*","/"]
keywords = [
    "=",
    "[",
    "]",
    "skill",
    "branch",
    "run",
    "jump"
] + operators

class JJS:
    def __init__(self, code):
        self.code = code
        self.line = 0
        self.tokens = self.lex()
        self.returned_token = None
        self.stack = []
        self.vars = {}
        self.character_data = []

    def raise_error(self, message):
        raise ValueError(f"{self.line}: {message}")

    def lex(self):
        for line in self.code.strip().split("\n"):
            self.line += 1
            for token in line.strip().split(" "):
                if token in keywords:
                    yield (token,)
                elif token[-1] == ":":
                    yield "index", token[:-1]
                elif token.isnumeric():
                    # for now, every number is handled as a float
                    yield "number", float(token)
                elif token[0].isalpha():
                    yield "identifier", token
                else:
                    self.raise_error(f"Syntax Error: Invalid token {token}")
            yield ("\n",)

    def next_token(self):
        if self.returned_token:
            token = self.returned_token
            self.returned_token = None
        else:
            try:
                token = next(self.tokens)
            except StopIteration:
                token = None
        return token

    def return_token(self, token):
        if self.returned_token is not None:
            raise RuntimeError("Cannot return more than one token at a time")
        self.returned_token = token

    def parse_program(self):
        if not self.parse_statement():
            self.raise_error('Expected: statement')
        while (token := self.next_token()) is not None:
            self.return_token(token)
            if not self.parse_statement():
                self.raise_error('Expected: statement')
        return True

    def parse_statement(self):
        if not self.parse_keyword_statement() and not self.parse_assignment():
            self.raise_error("Expected: keyword statement")
        token = self.next_token()
        if token[0] != "\n":
            self.raise_error("Expected: end of line")
        return True

    def parse_keyword_statement(self):
        token = self.next_token()
        if not token[0] in keywords:
            self.return_token(token)
            return False
        if not self.parse_expression():
            self.raise_error("Expected: expression")
        if token[0] == "skill":
            skill = self.stack_collapse()
            self.character_data.append({"node_type": "skill", "data": skill})
        return True

    def parse_assignment(self):
        token = self.next_token()
        if token[0] != "identifier":
            self.return_token(token)
            return False
        identifier = token[1]
        token = self.next_token()
        if token[0] != "=":
            self.raise_error("Expected: =")
        if not self.parse_expression():
            self.raise_error("Expected: expression")

        self.vars[identifier] = self.stack_collapse()
        return True

    def parse_expression(self):
        if not self.parse_value():
            return False
        if self.parse_operator():
            self.parse_expression()
        return True

    def parse_value(self):
        token = self.next_token()
        if token[0] not in ["number", "identifier", "[", "]"]:
            self.return_token(token)
            return False

        if token[0] == "identifier":
            if token[1] not in self.vars:
                self.raise_error(f"Syntax Error: Unknown variable {token[1]}")
            else:
                self.stack_push(self.vars[token[1]])
        elif token[0] == "[":
            self.parse_table()
        else:
            self.stack_push(token[1])
        return True

    def parse_table(self):
        table = {}
        key = self.next_token()
        if key[0] == "\n":
            key = self.next_token()
        if key == "]":
            self.raise_error(f"Table Error: Tables cannot be empty")
        elif key[0] != "index":
            self.raise_error(f"Syntax Error: Malformed table")
        elif self.parse_expression():
            table[key[1]] = self.stack_collapse()
        while (key := self.next_token())[0] != "]":
            if key[0] == "\n":
                key = self.next_token()
                if key[0] == "]":
                    break
            if key[0] != "index":
                self.raise_error(f"Syntax Error: Malformed table")
            elif self.parse_expression():
                table[key[1]] = self.stack_collapse()
        self.stack_push(table)

    def parse_operator(self):
        token = self.next_token()
        if token[0] not in operators:
            self.return_token(token)
            return False

        self.stack_push(self.stack_collapse())
        self.stack_push(token[0])
        return True

    def run(self):
        try:
            return self.parse_program()
        except ValueError as exc:
            print(str(exc))
            return False

    def stack_push(self, value):
        self.stack.append(value)

    def stack_pop(self):
        return self.stack.pop()

    def stack_collapse(self):
        while len(self.stack) > 1:
            value2 = self.stack_pop()
            prev_op = self.stack_pop()
            value1 = self.stack_pop()
            if prev_op == '+':
                self.stack_push(value1 + value2)
            elif prev_op == '-':
                self.stack_push(value1 - value2)
            elif prev_op == '*':
                self.stack_push(value1 * value2)
            elif prev_op == '/':
                self.stack_push(value1 / value2)
        return self.stack.pop()
