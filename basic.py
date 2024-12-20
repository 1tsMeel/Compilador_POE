### Importe de librerías

from strings_with_arrows import *

import string
import os
import math

### Constantes en nuestro compilador

DIGITOS = '0123456789'
LETRAS = string.ascii_letters
ALFANUMERICOS = LETRAS + DIGITOS

# PENDIENTE MODIFICAR
#######################################
# ERRORS
#######################################

class Error:
  def __init__(self, pos_comienzo, pos_fin, error_name, details):
    self.pos_comienzo = pos_comienzo
    self.pos_fin = pos_fin
    self.error_name = error_name
    self.details = details
  
  def as_string(self):
    result  = f'{self.error_name}: {self.details}\n'
    result += f'File {self.pos_comienzo.funcion}, line {self.pos_comienzo.linea + 1}'
    result += '\n\n' + string_with_arrows(self.pos_comienzo.funcion_texto, self.pos_comienzo, self.pos_fin)
    return result

class IllegalCharError(Error):
  def __init__(self, pos_comienzo, pos_fin, details):
    super().__init__(pos_comienzo, pos_fin, 'Illegal Character', details)

class ExpectedCharError(Error):
  def __init__(self, pos_comienzo, pos_fin, details):
    super().__init__(pos_comienzo, pos_fin, 'Expected Character', details)

class InvalidSyntaxError(Error):
  def __init__(self, pos_comienzo, pos_fin, details=''):
    super().__init__(pos_comienzo, pos_fin, 'Invalid Syntax', details)

class RTError(Error):
  def __init__(self, pos_comienzo, pos_fin, details, context):
    super().__init__(pos_comienzo, pos_fin, 'Runtime Error', details)
    self.context = context

  def as_string(self):
    result  = self.generate_traceback()
    result += f'{self.error_name}: {self.details}'
    result += '\n\n' + string_with_arrows(self.pos_comienzo.funcion_texto, self.pos_comienzo, self.pos_fin)
    return result

  def generate_traceback(self):
    result = ''
    pos = self.pos_comienzo
    ctx = self.context

    while ctx:
      result = f'  File {pos.funcion}, line {str(pos.linea + 1)}, in {ctx.display_name}\n' + result
      pos = ctx.parent_entry_pos
      ctx = ctx.parent

    return 'Traceback (most recent call last):\n' + result

### POSICIÓN

class Posicion:
  def __init__(self, idx, linea, columna, funcion, funcion_texto):
    self.idx = idx
    self.linea = linea
    self.columna = columna
    self.funcion = funcion
    self.funcion_texto = funcion_texto

  def avanzar(self, caracter_actual=None):
    self.idx += 1
    self.columna += 1

    if caracter_actual == '\n':
      self.linea += 1
      self.columna = 0

    return self

  def copiar(self):
    return Posicion(self.idx, self.linea, self.columna, self.funcion, self.funcion_texto)

### TOKENS a utilizar

TT_INT				= 'INT'
TT_FLOAT    	= 'FLOAT'
TT_STRING			= 'STRING'
TT_IDENTIFIER	= 'IDENTIFIER'
TT_KEYWORD		= 'KEYWORD'
TT_PLUS     	= 'PLUS'
TT_MINUS    	= 'MINUS'
TT_MUL      	= 'MUL'
TT_DIV      	= 'DIV'
TT_POW				= 'POW'
TT_EQ					= 'EQ'
TT_PARENIZQ   = 'PARENIZQ'
TT_PARENDER   = 'PARENDER'
TT_LSQUARE    = 'LSQUARE'
TT_RSQUARE    = 'RSQUARE'
TT_EE					= 'EE'
TT_NE					= 'NE'
TT_LT					= 'LT'
TT_GT					= 'GT'
TT_LTE				= 'LTE'
TT_GTE				= 'GTE'
TT_COMMA			= 'COMMA'
TT_ARROW			= 'ARROW'
TT_NEWLINE		= 'NEWLINE'
TT_EOF				= 'EOF'

KEYWORDS = [
  'VAR',
  'Y',
  'O',
  'NEL',
  'SI',
  'SINOSI',
  'SINO',
  'POR',
  'HASTA',
  'PASO',
  'MIENTRAS',
  'FUN',
  'ENTONCES',
  'FIN',
  'RETORNA',
  'CONTINUA',
  'ROMPER',
]

class Token:
  def __init__(self, tipo_, valor=None, pos_comienzo=None, pos_fin=None):
    self.tipo = tipo_
    self.valor = valor

    if pos_comienzo:
      self.pos_comienzo = pos_comienzo.copiar()
      self.pos_fin = pos_comienzo.copiar()
      self.pos_fin.avanzar()

    if pos_fin:
      self.pos_fin = pos_fin.copiar()

  def coincide(self, tipo_, valor):
    return self.tipo == tipo_ and self.valor == valor
  
  def __repr__(self):
    if self.valor: return f'{self.tipo}:{self.valor}'
    return f'{self.tipo}'

# LEXER a utilizar

class Lexer:
  def __init__(self, funcion, texto):
    self.funcion = funcion
    self.texto = texto
    self.pos = Posicion(-1, 0, -1, funcion, texto)
    self.caracter_actual = None
    self.avanzar()
  
  def avanzar(self):
    self.pos.avanzar(self.caracter_actual)
    self.caracter_actual = self.texto[self.pos.idx] if self.pos.idx < len(self.texto) else None

  def hacer_tokens(self):
    tokens = []

    while self.caracter_actual != None:
      if self.caracter_actual in ' \t':
        self.avanzar()
      elif self.caracter_actual == '#':
        self.omitir_comentario()
      elif self.caracter_actual in ';\n':
        tokens.append(Token(TT_NEWLINE, pos_comienzo=self.pos))
        self.avanzar()
      elif self.caracter_actual in DIGITOS:
        tokens.append(self.hacer_numero())
      elif self.caracter_actual in LETRAS:
        tokens.append(self.hacer_id())
      elif self.caracter_actual == '"':
        tokens.append(self.hacer_cadena())
      elif self.caracter_actual == '+':
        tokens.append(Token(TT_PLUS, pos_comienzo=self.pos))
        self.avanzar()
      elif self.caracter_actual == '-':
        tokens.append(self.hacer_menos_o_flecha())
      elif self.caracter_actual == '*':
        tokens.append(Token(TT_MUL, pos_comienzo=self.pos))
        self.avanzar()
      elif self.caracter_actual == '/':
        tokens.append(Token(TT_DIV, pos_comienzo=self.pos))
        self.avanzar()
      elif self.caracter_actual == '^':
        tokens.append(Token(TT_POW, pos_comienzo=self.pos))
        self.avanzar()
      elif self.caracter_actual == '(':
        tokens.append(Token(TT_PARENIZQ, pos_comienzo=self.pos))
        self.avanzar()
      elif self.caracter_actual == ')':
        tokens.append(Token(TT_PARENDER, pos_comienzo=self.pos))
        self.avanzar()
      elif self.caracter_actual == '[':
        tokens.append(Token(TT_LSQUARE, pos_comienzo=self.pos))
        self.avanzar()
      elif self.caracter_actual == ']':
        tokens.append(Token(TT_RSQUARE, pos_comienzo=self.pos))
        self.avanzar()
      elif self.caracter_actual == '!':
        token, error = self.hacer_no_igual()
        if error: return [], error
        tokens.append(token)
      elif self.caracter_actual == '=':
        tokens.append(self.hacer_igual())
      elif self.caracter_actual == '<':
        tokens.append(self.hacer_menor_que())
      elif self.caracter_actual == '>':
        tokens.append(self.hacer_mayor_que())
      elif self.caracter_actual == ',':
        tokens.append(Token(TT_COMMA, pos_comienzo=self.pos))
        self.avanzar()
      else:
        pos_comienzo = self.pos.copiar()
        caracter = self.caracter_actual
        self.avanzar()
        return [], IllegalCharError(pos_comienzo, self.pos, "'" + caracter + "'")

    tokens.append(Token(TT_EOF, pos_comienzo=self.pos))
    return tokens, None

  def hacer_numero(self):
    num_str = ''
    contador_puntos = 0
    pos_comienzo = self.pos.copiar()

    while self.caracter_actual != None and self.caracter_actual in DIGITOS + '.':
      if self.caracter_actual == '.':
        if contador_puntos == 1: break
        contador_puntos += 1
      num_str += self.caracter_actual
      self.avanzar()

    if contador_puntos == 0:
      return Token(TT_INT, int(num_str), pos_comienzo, self.pos)
    else:
      return Token(TT_FLOAT, float(num_str), pos_comienzo, self.pos)

  def hacer_cadena(self):
    cadena = ''
    pos_comienzo = self.pos.copiar()
    caracter_de_escape = False
    self.avanzar()

    caracteres_de_escape = {
      'n': '\n',
      't': '\t'
    }

    while self.caracter_actual != None and (self.caracter_actual != '"' or caracter_de_escape):
      if caracter_de_escape:
        cadena += caracteres_de_escape.get(self.caracter_actual, self.caracter_actual)
      else:
        if self.caracter_actual == '\\':
          caracter_de_escape = True
        else:
          cadena += self.caracter_actual
      self.avanzar()
      caracter_de_escape = False
    
    self.avanzar()
    return Token(TT_STRING, cadena, pos_comienzo, self.pos)

  def hacer_id(self):
    id_str = ''
    pos_comienzo = self.pos.copiar()

    while self.caracter_actual != None and self.caracter_actual in ALFANUMERICOS + '_':
      id_str += self.caracter_actual
      self.avanzar()

    tipo_token = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
    return Token(tipo_token, id_str, pos_comienzo, self.pos)

  def hacer_menos_o_flecha(self):
    tipo_token = TT_MINUS
    pos_comienzo = self.pos.copiar()
    self.avanzar()

    if self.caracter_actual == '>':
      self.avanzar()
      tipo_token = TT_ARROW

    return Token(tipo_token, pos_comienzo=pos_comienzo, pos_fin=self.pos)

  def hacer_no_igual(self):
    pos_comienzo = self.pos.copiar()
    self.avanzar()

    if self.caracter_actual == '=':
      self.avanzar()
      return Token(TT_NE, pos_comienzo=pos_comienzo, pos_fin=self.pos), None

    self.avanzar()
    return None, ExpectedCharError(pos_comienzo, self.pos, "'=' (after '!')")
  
  def hacer_igual(self):
    tipo_token = TT_EQ
    pos_comienzo = self.pos.copiar()
    self.avanzar()

    if self.caracter_actual == '=':
      self.avanzar()
      tipo_token = TT_EE

    return Token(tipo_token, pos_comienzo=pos_comienzo, pos_fin=self.pos)

  def hacer_menor_que(self):
    tipo_token = TT_LT
    pos_comienzo = self.pos.copiar()
    self.avanzar()

    if self.caracter_actual == '=':
      self.avanzar()
      tipo_token = TT_LTE

    return Token(tipo_token, pos_comienzo=pos_comienzo, pos_fin=self.pos)

  def hacer_mayor_que(self):
    tipo_token = TT_GT
    pos_comienzo = self.pos.copiar()
    self.avanzar()

    if self.caracter_actual == '=':
      self.avanzar()
      tipo_token = TT_GTE

    return Token(tipo_token, pos_comienzo=pos_comienzo, pos_fin=self.pos)

  def omitir_comentario(self):
    self.avanzar()

    while self.caracter_actual != '\n':
      self.avanzar()

    self.avanzar()

# NODOS

class NodoNumero:
  def __init__(self, tok):
    self.tok = tok

    self.pos_comienzo = self.tok.pos_comienzo
    self.pos_fin = self.tok.pos_fin

  def __repr__(self):
    return f'{self.tok}'

class NodoCadena:
  def __init__(self, tok):
    self.tok = tok

    self.pos_comienzo = self.tok.pos_comienzo
    self.pos_fin = self.tok.pos_fin

  def __repr__(self):
    return f'{self.tok}'

class NodoLista:
  def __init__(self, element_nodes, pos_comienzo, pos_fin):
    self.element_nodes = element_nodes

    self.pos_comienzo = pos_comienzo
    self.pos_fin = pos_fin

class NodoVariableAcceso:
  def __init__(self, var_name_tok):
    self.var_name_tok = var_name_tok

    self.pos_comienzo = self.var_name_tok.pos_comienzo
    self.pos_fin = self.var_name_tok.pos_fin

class VarAssignNode:
  def __init__(self, var_name_tok, value_node):
    self.var_name_tok = var_name_tok
    self.value_node = value_node

    self.pos_comienzo = self.var_name_tok.pos_comienzo
    self.pos_fin = self.value_node.pos_fin

class BinOpNode:
  def __init__(self, left_node, op_tok, right_node):
    self.left_node = left_node
    self.op_tok = op_tok
    self.right_node = right_node

    self.pos_comienzo = self.left_node.pos_comienzo
    self.pos_fin = self.right_node.pos_fin

  def __repr__(self):
    return f'({self.left_node}, {self.op_tok}, {self.right_node})'

class UnaryOpNode:
  def __init__(self, op_tok, node):
    self.op_tok = op_tok
    self.node = node

    self.pos_comienzo = self.op_tok.pos_comienzo
    self.pos_fin = node.pos_fin

  def __repr__(self):
    return f'({self.op_tok}, {self.node})'

class IfNode:
  def __init__(self, cases, else_case):
    self.cases = cases
    self.else_case = else_case

    self.pos_comienzo = self.cases[0][0].pos_comienzo
    self.pos_fin = (self.else_case or self.cases[len(self.cases) - 1])[0].pos_fin

class ForNode:
  def __init__(self, var_name_tok, start_value_node, end_value_node, step_value_node, body_node, should_return_null):
    self.var_name_tok = var_name_tok
    self.start_value_node = start_value_node
    self.end_value_node = end_value_node
    self.step_value_node = step_value_node
    self.body_node = body_node
    self.should_return_null = should_return_null

    self.pos_comienzo = self.var_name_tok.pos_comienzo
    self.pos_fin = self.body_node.pos_fin

class WhileNode:
  def __init__(self, condition_node, body_node, should_return_null):
    self.condition_node = condition_node
    self.body_node = body_node
    self.should_return_null = should_return_null

    self.pos_comienzo = self.condition_node.pos_comienzo
    self.pos_fin = self.body_node.pos_fin

class FuncDefNode:
  def __init__(self, var_name_tok, arg_name_toks, body_node, should_auto_return):
    self.var_name_tok = var_name_tok
    self.arg_name_toks = arg_name_toks
    self.body_node = body_node
    self.should_auto_return = should_auto_return

    if self.var_name_tok:
      self.pos_comienzo = self.var_name_tok.pos_comienzo
    elif len(self.arg_name_toks) > 0:
      self.pos_comienzo = self.arg_name_toks[0].pos_comienzo
    else:
      self.pos_comienzo = self.body_node.pos_comienzo

    self.pos_fin = self.body_node.pos_fin

class CallNode:
  def __init__(self, node_to_call, arg_nodes):
    self.node_to_call = node_to_call
    self.arg_nodes = arg_nodes

    self.pos_comienzo = self.node_to_call.pos_comienzo

    if len(self.arg_nodes) > 0:
      self.pos_fin = self.arg_nodes[len(self.arg_nodes) - 1].pos_fin
    else:
      self.pos_fin = self.node_to_call.pos_fin

class ReturnNode:
  def __init__(self, node_to_return, pos_comienzo, pos_fin):
    self.node_to_return = node_to_return

    self.pos_comienzo = pos_comienzo
    self.pos_fin = pos_fin

class ContinueNode:
  def __init__(self, pos_comienzo, pos_fin):
    self.pos_comienzo = pos_comienzo
    self.pos_fin = pos_fin

class BreakNode:
  def __init__(self, pos_comienzo, pos_fin):
    self.pos_comienzo = pos_comienzo
    self.pos_fin = pos_fin

#######################################
# PARSE RESULT
#######################################

class ParseResult:
  def __init__(self):
    self.error = None
    self.node = None
    self.last_registered_advance_count = 0
    self.advance_count = 0
    self.to_reverse_count = 0

  def register_advancement(self):
    self.last_registered_advance_count = 1
    self.advance_count += 1

  def register(self, res):
    self.last_registered_advance_count = res.advance_count
    self.advance_count += res.advance_count
    if res.error: self.error = res.error
    return res.node

  def try_register(self, res):
    if res.error:
      self.to_reverse_count = res.advance_count
      return None
    return self.register(res)

  def success(self, node):
    self.node = node
    return self

  def failure(self, error):
    if not self.error or self.last_registered_advance_count == 0:
      self.error = error
    return self

#######################################
# PARSER
#######################################

class Parser:
  def __init__(self, tokens):
    self.tokens = tokens
    self.tok_idx = -1
    self.avanzar()

  def avanzar(self):
    self.tok_idx += 1
    self.update_current_tok()
    return self.current_tok

  def reverse(self, amount=1):
    self.tok_idx -= amount
    self.update_current_tok()
    return self.current_tok

  def update_current_tok(self):
    if self.tok_idx >= 0 and self.tok_idx < len(self.tokens):
      self.current_tok = self.tokens[self.tok_idx]

  def parse(self):
    res = self.statements()
    if not res.error and self.current_tok.tipo != TT_EOF:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        "Token cannot appear after previous tokens"
      ))
    return res

  ###################################

  def statements(self):
    res = ParseResult()
    statements = []
    pos_comienzo = self.current_tok.pos_comienzo.copiar()

    while self.current_tok.tipo == TT_NEWLINE:
      res.register_advancement()
      self.avanzar()

    statement = res.register(self.statement())
    if res.error: return res
    statements.append(statement)

    more_statements = True

    while True:
      newline_count = 0
      while self.current_tok.tipo == TT_NEWLINE:
        res.register_advancement()
        self.avanzar()
        newline_count += 1
      if newline_count == 0:
        more_statements = False
      
      if not more_statements: break
      statement = res.try_register(self.statement())
      if not statement:
        self.reverse(res.to_reverse_count)
        more_statements = False
        continue
      statements.append(statement)

    return res.success(NodoLista(
      statements,
      pos_comienzo,
      self.current_tok.pos_fin.copiar()
    ))

  def statement(self):
    res = ParseResult()
    pos_comienzo = self.current_tok.pos_comienzo.copiar()

    if self.current_tok.coincide(TT_KEYWORD, 'RETORNA'):
      res.register_advancement()
      self.avanzar()

      expr = res.try_register(self.expr())
      if not expr:
        self.reverse(res.to_reverse_count)
      return res.success(ReturnNode(expr, pos_comienzo, self.current_tok.pos_comienzo.copiar()))
    
    if self.current_tok.coincide(TT_KEYWORD, 'CONTINUA'):
      res.register_advancement()
      self.avanzar()
      return res.success(ContinueNode(pos_comienzo, self.current_tok.pos_comienzo.copiar()))
      
    if self.current_tok.coincide(TT_KEYWORD, 'ROMPER'):
      res.register_advancement()
      self.avanzar()
      return res.success(BreakNode(pos_comienzo, self.current_tok.pos_comienzo.copiar()))

    expr = res.register(self.expr())
    if res.error:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        "Expected 'RETORNA', 'CONTINUA', 'ROMPER', 'VAR', 'SI', 'POR', 'MIENTRAS', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NEL'"
      ))
    return res.success(expr)

  def expr(self):
    res = ParseResult()

    if self.current_tok.coincide(TT_KEYWORD, 'VAR'):
      res.register_advancement()
      self.avanzar()

      if self.current_tok.tipo != TT_IDENTIFIER:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_comienzo, self.current_tok.pos_fin,
          "Expected identifier"
        ))

      var_name = self.current_tok
      res.register_advancement()
      self.avanzar()

      if self.current_tok.tipo != TT_EQ:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_comienzo, self.current_tok.pos_fin,
          "Expected '='"
        ))

      res.register_advancement()
      self.avanzar()
      expr = res.register(self.expr())
      if res.error: return res
      return res.success(VarAssignNode(var_name, expr))

    node = res.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, 'Y'), (TT_KEYWORD, 'O'))))

    if res.error:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        "Expected 'VAR', 'SI', 'POR', 'MIENTRAS', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NEL'"
      ))

    return res.success(node)

  def comp_expr(self):
    res = ParseResult()

    if self.current_tok.coincide(TT_KEYWORD, 'NEL'):
      op_tok = self.current_tok
      res.register_advancement()
      self.avanzar()

      node = res.register(self.comp_expr())
      if res.error: return res
      return res.success(UnaryOpNode(op_tok, node))
    
    node = res.register(self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))
    
    if res.error:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        "Expected int, float, identifier, '+', '-', '(', '[', 'SI', 'POR', 'MIENTRAS', 'FUN' or 'NEL'"
      ))

    return res.success(node)

  def arith_expr(self):
    return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

  def term(self):
    return self.bin_op(self.factor, (TT_MUL, TT_DIV))

  def factor(self):
    res = ParseResult()
    tok = self.current_tok

    if tok.tipo in (TT_PLUS, TT_MINUS):
      res.register_advancement()
      self.avanzar()
      factor = res.register(self.factor())
      if res.error: return res
      return res.success(UnaryOpNode(tok, factor))

    return self.power()

  def power(self):
    return self.bin_op(self.call, (TT_POW, ), self.factor)

  def call(self):
    res = ParseResult()
    atom = res.register(self.atom())
    if res.error: return res

    if self.current_tok.tipo == TT_PARENIZQ:
      res.register_advancement()
      self.avanzar()
      arg_nodes = []

      if self.current_tok.tipo == TT_PARENDER:
        res.register_advancement()
        self.avanzar()
      else:
        arg_nodes.append(res.register(self.expr()))
        if res.error:
          return res.failure(InvalidSyntaxError(
            self.current_tok.pos_comienzo, self.current_tok.pos_fin,
            "Expected ')', 'VAR', 'SI', 'POR', 'MIENTRAS', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NEL'"
          ))

        while self.current_tok.tipo == TT_COMMA:
          res.register_advancement()
          self.avanzar()

          arg_nodes.append(res.register(self.expr()))
          if res.error: return res

        if self.current_tok.tipo != TT_PARENDER:
          return res.failure(InvalidSyntaxError(
            self.current_tok.pos_comienzo, self.current_tok.pos_fin,
            f"Expected ',' or ')'"
          ))

        res.register_advancement()
        self.avanzar()
      return res.success(CallNode(atom, arg_nodes))
    return res.success(atom)

  def atom(self):
    res = ParseResult()
    tok = self.current_tok

    if tok.tipo in (TT_INT, TT_FLOAT):
      res.register_advancement()
      self.avanzar()
      return res.success(NodoNumero(tok))

    elif tok.tipo == TT_STRING:
      res.register_advancement()
      self.avanzar()
      return res.success(NodoCadena(tok))

    elif tok.tipo == TT_IDENTIFIER:
      res.register_advancement()
      self.avanzar()
      return res.success(NodoVariableAcceso(tok))

    elif tok.tipo == TT_PARENIZQ:
      res.register_advancement()
      self.avanzar()
      expr = res.register(self.expr())
      if res.error: return res
      if self.current_tok.tipo == TT_PARENDER:
        res.register_advancement()
        self.avanzar()
        return res.success(expr)
      else:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_comienzo, self.current_tok.pos_fin,
          "Expected ')'"
        ))

    elif tok.tipo == TT_LSQUARE:
      list_expr = res.register(self.list_expr())
      if res.error: return res
      return res.success(list_expr)
    
    elif tok.coincide(TT_KEYWORD, 'SI'):
      if_expr = res.register(self.if_expr())
      if res.error: return res
      return res.success(if_expr)

    elif tok.coincide(TT_KEYWORD, 'POR'):
      for_expr = res.register(self.for_expr())
      if res.error: return res
      return res.success(for_expr)

    elif tok.coincide(TT_KEYWORD, 'MIENTRAS'):
      while_expr = res.register(self.while_expr())
      if res.error: return res
      return res.success(while_expr)

    elif tok.coincide(TT_KEYWORD, 'FUN'):
      func_def = res.register(self.func_def())
      if res.error: return res
      return res.success(func_def)

    return res.failure(InvalidSyntaxError(
      tok.pos_comienzo, tok.pos_fin,
      "Expected int, float, identifier, '+', '-', '(', '[', SI', 'POR', 'MIENTRAS', 'FUN'"
    ))

  def list_expr(self):
    res = ParseResult()
    element_nodes = []
    pos_comienzo = self.current_tok.pos_comienzo.copiar()

    if self.current_tok.tipo != TT_LSQUARE:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected '['"
      ))

    res.register_advancement()
    self.avanzar()

    if self.current_tok.tipo == TT_RSQUARE:
      res.register_advancement()
      self.avanzar()
    else:
      element_nodes.append(res.register(self.expr()))
      if res.error:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_comienzo, self.current_tok.pos_fin,
          "Expected ']', 'VAR', 'SI', 'POR', 'MIENTRAS', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NEL'"
        ))

      while self.current_tok.tipo == TT_COMMA:
        res.register_advancement()
        self.avanzar()

        element_nodes.append(res.register(self.expr()))
        if res.error: return res

      if self.current_tok.tipo != TT_RSQUARE:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_comienzo, self.current_tok.pos_fin,
          f"Expected ',' or ']'"
        ))

      res.register_advancement()
      self.avanzar()

    return res.success(NodoLista(
      element_nodes,
      pos_comienzo,
      self.current_tok.pos_fin.copiar()
    ))

  def if_expr(self):
    res = ParseResult()
    all_cases = res.register(self.if_expr_cases('SI'))
    if res.error: return res
    cases, else_case = all_cases
    return res.success(IfNode(cases, else_case))

  def if_expr_b(self):
    return self.if_expr_cases('SINOSI')
    
  def if_expr_c(self):
    res = ParseResult()
    else_case = None

    if self.current_tok.coincide(TT_KEYWORD, 'SINO'):
      res.register_advancement()
      self.avanzar()

      if self.current_tok.tipo == TT_NEWLINE:
        res.register_advancement()
        self.avanzar()

        statements = res.register(self.statements())
        if res.error: return res
        else_case = (statements, True)

        if self.current_tok.coincide(TT_KEYWORD, 'FIN'):
          res.register_advancement()
          self.avanzar()
        else:
          return res.failure(InvalidSyntaxError(
            self.current_tok.pos_comienzo, self.current_tok.pos_fin,
            "Expected 'FIN'"
          ))
      else:
        expr = res.register(self.statement())
        if res.error: return res
        else_case = (expr, False)

    return res.success(else_case)

  def if_expr_b_or_c(self):
    res = ParseResult()
    cases, else_case = [], None

    if self.current_tok.coincide(TT_KEYWORD, 'SINOSI'):
      all_cases = res.register(self.if_expr_b())
      if res.error: return res
      cases, else_case = all_cases
    else:
      else_case = res.register(self.if_expr_c())
      if res.error: return res
    
    return res.success((cases, else_case))

  def if_expr_cases(self, case_keyword):
    res = ParseResult()
    cases = []
    else_case = None

    if not self.current_tok.coincide(TT_KEYWORD, case_keyword):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected '{case_keyword}'"
      ))

    res.register_advancement()
    self.avanzar()

    condition = res.register(self.expr())
    if res.error: return res

    if not self.current_tok.coincide(TT_KEYWORD, 'ENTONCES'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected 'ENTONCES'"
      ))

    res.register_advancement()
    self.avanzar()

    if self.current_tok.tipo == TT_NEWLINE:
      res.register_advancement()
      self.avanzar()

      statements = res.register(self.statements())
      if res.error: return res
      cases.append((condition, statements, True))

      if self.current_tok.coincide(TT_KEYWORD, 'FIN'):
        res.register_advancement()
        self.avanzar()
      else:
        all_cases = res.register(self.if_expr_b_or_c())
        if res.error: return res
        new_cases, else_case = all_cases
        cases.extend(new_cases)
    else:
      expr = res.register(self.statement())
      if res.error: return res
      cases.append((condition, expr, False))

      all_cases = res.register(self.if_expr_b_or_c())
      if res.error: return res
      new_cases, else_case = all_cases
      cases.extend(new_cases)

    return res.success((cases, else_case))

  def for_expr(self):
    res = ParseResult()

    if not self.current_tok.coincide(TT_KEYWORD, 'POR'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected 'POR'"
      ))

    res.register_advancement()
    self.avanzar()

    if self.current_tok.tipo != TT_IDENTIFIER:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected identifier"
      ))

    var_name = self.current_tok
    res.register_advancement()
    self.avanzar()

    if self.current_tok.tipo != TT_EQ:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected '='"
      ))
    
    res.register_advancement()
    self.avanzar()

    start_value = res.register(self.expr())
    if res.error: return res

    if not self.current_tok.coincide(TT_KEYWORD, 'HASTA'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected 'HASTA'"
      ))
    
    res.register_advancement()
    self.avanzar()

    end_value = res.register(self.expr())
    if res.error: return res

    if self.current_tok.coincide(TT_KEYWORD, 'PASO'):
      res.register_advancement()
      self.avanzar()

      step_value = res.register(self.expr())
      if res.error: return res
    else:
      step_value = None

    if not self.current_tok.coincide(TT_KEYWORD, 'ENTONCES'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected 'ENTONCES'"
      ))

    res.register_advancement()
    self.avanzar()

    if self.current_tok.tipo == TT_NEWLINE:
      res.register_advancement()
      self.avanzar()

      body = res.register(self.statements())
      if res.error: return res

      if not self.current_tok.coincide(TT_KEYWORD, 'FIN'):
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_comienzo, self.current_tok.pos_fin,
          f"Expected 'FIN'"
        ))

      res.register_advancement()
      self.avanzar()

      return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))
    
    body = res.register(self.statement())
    if res.error: return res

    return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))

  def while_expr(self):
    res = ParseResult()

    if not self.current_tok.coincide(TT_KEYWORD, 'MIENTRAS'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected 'MIENTRAS'"
      ))

    res.register_advancement()
    self.avanzar()

    condition = res.register(self.expr())
    if res.error: return res

    if not self.current_tok.coincide(TT_KEYWORD, 'ENTONCES'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected 'ENTONCES'"
      ))

    res.register_advancement()
    self.avanzar()

    if self.current_tok.tipo == TT_NEWLINE:
      res.register_advancement()
      self.avanzar()

      body = res.register(self.statements())
      if res.error: return res

      if not self.current_tok.coincide(TT_KEYWORD, 'FIN'):
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_comienzo, self.current_tok.pos_fin,
          f"Expected 'FIN'"
        ))

      res.register_advancement()
      self.avanzar()

      return res.success(WhileNode(condition, body, True))
    
    body = res.register(self.statement())
    if res.error: return res

    return res.success(WhileNode(condition, body, False))

  def func_def(self):
    res = ParseResult()

    if not self.current_tok.coincide(TT_KEYWORD, 'FUN'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected 'FUN'"
      ))

    res.register_advancement()
    self.avanzar()

    if self.current_tok.tipo == TT_IDENTIFIER:
      var_name_tok = self.current_tok
      res.register_advancement()
      self.avanzar()
      if self.current_tok.tipo != TT_PARENIZQ:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_comienzo, self.current_tok.pos_fin,
          f"Expected '('"
        ))
    else:
      var_name_tok = None
      if self.current_tok.tipo != TT_PARENIZQ:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_comienzo, self.current_tok.pos_fin,
          f"Expected identifier or '('"
        ))
    
    res.register_advancement()
    self.avanzar()
    arg_name_toks = []

    if self.current_tok.tipo == TT_IDENTIFIER:
      arg_name_toks.append(self.current_tok)
      res.register_advancement()
      self.avanzar()
      
      while self.current_tok.tipo == TT_COMMA:
        res.register_advancement()
        self.avanzar()

        if self.current_tok.tipo != TT_IDENTIFIER:
          return res.failure(InvalidSyntaxError(
            self.current_tok.pos_comienzo, self.current_tok.pos_fin,
            f"Expected identifier"
          ))

        arg_name_toks.append(self.current_tok)
        res.register_advancement()
        self.avanzar()
      
      if self.current_tok.tipo != TT_PARENDER:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_comienzo, self.current_tok.pos_fin,
          f"Expected ',' or ')'"
        ))
    else:
      if self.current_tok.tipo != TT_PARENDER:
        return res.failure(InvalidSyntaxError(
          self.current_tok.pos_comienzo, self.current_tok.pos_fin,
          f"Expected identifier or ')'"
        ))

    res.register_advancement()
    self.avanzar()

    if self.current_tok.tipo == TT_ARROW:
      res.register_advancement()
      self.avanzar()

      body = res.register(self.expr())
      if res.error: return res

      return res.success(FuncDefNode(
        var_name_tok,
        arg_name_toks,
        body,
        True
      ))
    
    if self.current_tok.tipo != TT_NEWLINE:
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected '->' or NEWLINE"
      ))

    res.register_advancement()
    self.avanzar()

    body = res.register(self.statements())
    if res.error: return res

    if not self.current_tok.coincide(TT_KEYWORD, 'FIN'):
      return res.failure(InvalidSyntaxError(
        self.current_tok.pos_comienzo, self.current_tok.pos_fin,
        f"Expected 'FIN'"
      ))

    res.register_advancement()
    self.avanzar()
    
    return res.success(FuncDefNode(
      var_name_tok,
      arg_name_toks,
      body,
      False
    ))

  ###################################

  def bin_op(self, func_a, ops, func_b=None):
    if func_b == None:
      func_b = func_a
    
    res = ParseResult()
    left = res.register(func_a())
    if res.error: return res

    while self.current_tok.tipo in ops or (self.current_tok.tipo, self.current_tok.valor) in ops:
      op_tok = self.current_tok
      res.register_advancement()
      self.avanzar()
      right = res.register(func_b())
      if res.error: return res
      left = BinOpNode(left, op_tok, right)

    return res.success(left)

#######################################
# RUNTIME RESULT
#######################################

class RTResult:
  def __init__(self):
    self.reset()

  def reset(self):
    self.valor = None
    self.error = None
    self.func_return_value = None
    self.loop_should_continue = False
    self.loop_should_break = False

  def register(self, res):
    self.error = res.error
    self.func_return_value = res.func_return_value
    self.loop_should_continue = res.loop_should_continue
    self.loop_should_break = res.loop_should_break
    return res.valor

  def success(self, valor):
    self.reset()
    self.valor = valor
    return self

  def success_return(self, valor):
    self.reset()
    self.func_return_value = valor
    return self
  
  def success_continue(self):
    self.reset()
    self.loop_should_continue = True
    return self

  def success_break(self):
    self.reset()
    self.loop_should_break = True
    return self

  def failure(self, error):
    self.reset()
    self.error = error
    return self

  def should_return(self):
    # Note: this will allow you to continue and break outside the current function
    return (
      self.error or
      self.func_return_value or
      self.loop_should_continue or
      self.loop_should_break
    )

#######################################
# VALUES
#######################################

class Value:
  def __init__(self):
    self.set_pos()
    self.set_context()

  def set_pos(self, pos_comienzo=None, pos_fin=None):
    self.pos_comienzo = pos_comienzo
    self.pos_fin = pos_fin
    return self

  def set_context(self, context=None):
    self.context = context
    return self

  def added_to(self, other):
    return None, self.illegal_operation(other)

  def subbed_by(self, other):
    return None, self.illegal_operation(other)

  def multed_by(self, other):
    return None, self.illegal_operation(other)

  def dived_by(self, other):
    return None, self.illegal_operation(other)

  def powed_by(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_eq(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_ne(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_lt(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_gt(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_lte(self, other):
    return None, self.illegal_operation(other)

  def get_comparison_gte(self, other):
    return None, self.illegal_operation(other)

  def anded_by(self, other):
    return None, self.illegal_operation(other)

  def ored_by(self, other):
    return None, self.illegal_operation(other)

  def notted(self, other):
    return None, self.illegal_operation(other)

  def execute(self, args):
    return RTResult().failure(self.illegal_operation())

  def copiar(self):
    raise Exception('No copiar method defined')

  def is_true(self):
    return False

  def illegal_operation(self, other=None):
    if not other: other = self
    return RTError(
      self.pos_comienzo, other.pos_fin,
      'Illegal operation',
      self.context
    )

class Number(Value):
  def __init__(self, valor):
    super().__init__()
    self.valor = valor

  def added_to(self, other):
    if isinstance(other, Number):
      return Number(self.valor + other.valor).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def subbed_by(self, other):
    if isinstance(other, Number):
      return Number(self.valor - other.valor).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def multed_by(self, other):
    if isinstance(other, Number):
      return Number(self.valor * other.valor).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def dived_by(self, other):
    if isinstance(other, Number):
      if other.valor == 0:
        return None, RTError(
          other.pos_comienzo, other.pos_fin,
          'Division by zero',
          self.context
        )

      return Number(self.valor / other.valor).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def powed_by(self, other):
    if isinstance(other, Number):
      return Number(self.valor ** other.valor).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_eq(self, other):
    if isinstance(other, Number):
      return Number(int(self.valor == other.valor)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_ne(self, other):
    if isinstance(other, Number):
      return Number(int(self.valor != other.valor)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_lt(self, other):
    if isinstance(other, Number):
      return Number(int(self.valor < other.valor)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_gt(self, other):
    if isinstance(other, Number):
      return Number(int(self.valor > other.valor)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_lte(self, other):
    if isinstance(other, Number):
      return Number(int(self.valor <= other.valor)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def get_comparison_gte(self, other):
    if isinstance(other, Number):
      return Number(int(self.valor >= other.valor)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def anded_by(self, other):
    if isinstance(other, Number):
      return Number(int(self.valor and other.valor)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def ored_by(self, other):
    if isinstance(other, Number):
      return Number(int(self.valor or other.valor)).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def notted(self):
    return Number(1 if self.valor == 0 else 0).set_context(self.context), None

  def copiar(self):
    copiar = Number(self.valor)
    copiar.set_pos(self.pos_comienzo, self.pos_fin)
    copiar.set_context(self.context)
    return copiar

  def is_true(self):
    return self.valor != 0

  def __str__(self):
    return str(self.valor)
  
  def __repr__(self):
    return str(self.valor)

Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)
Number.math_PI = Number(math.pi)

class String(Value):
  def __init__(self, valor):
    super().__init__()
    self.valor = valor

  def added_to(self, other):
    if isinstance(other, String):
      return String(self.valor + other.valor).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def multed_by(self, other):
    if isinstance(other, Number):
      return String(self.valor * other.valor).set_context(self.context), None
    else:
      return None, Value.illegal_operation(self, other)

  def is_true(self):
    return len(self.valor) > 0

  def copiar(self):
    copiar = String(self.valor)
    copiar.set_pos(self.pos_comienzo, self.pos_fin)
    copiar.set_context(self.context)
    return copiar

  def __str__(self):
    return self.valor

  def __repr__(self):
    return f'"{self.valor}"'

class List(Value):
  def __init__(self, elements):
    super().__init__()
    self.elements = elements

  def added_to(self, other):
    new_list = self.copiar()
    new_list.elements.append(other)
    return new_list, None

  def subbed_by(self, other):
    if isinstance(other, Number):
      new_list = self.copiar()
      try:
        new_list.elements.pop(other.valor)
        return new_list, None
      except:
        return None, RTError(
          other.pos_comienzo, other.pos_fin,
          'Element at this index could not be removed from list because index is out of bounds',
          self.context
        )
    else:
      return None, Value.illegal_operation(self, other)

  def multed_by(self, other):
    if isinstance(other, List):
      new_list = self.copiar()
      new_list.elements.extend(other.elements)
      return new_list, None
    else:
      return None, Value.illegal_operation(self, other)

  def dived_by(self, other):
    if isinstance(other, Number):
      try:
        return self.elements[other.valor], None
      except:
        return None, RTError(
          other.pos_comienzo, other.pos_fin,
          'Element at this index could not be retrieved from list because index is out of bounds',
          self.context
        )
    else:
      return None, Value.illegal_operation(self, other)
  
  def copiar(self):
    copiar = List(self.elements)
    copiar.set_pos(self.pos_comienzo, self.pos_fin)
    copiar.set_context(self.context)
    return copiar

  def __str__(self):
    return ", ".join([str(x) for x in self.elements])

  def __repr__(self):
    return f'[{", ".join([repr(x) for x in self.elements])}]'

class BaseFunction(Value):
  def __init__(self, name):
    super().__init__()
    self.name = name or "<anonymous>"

  def generate_new_context(self):
    new_context = Context(self.name, self.context, self.pos_comienzo)
    new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
    return new_context

  def check_args(self, arg_names, args):
    res = RTResult()

    if len(args) > len(arg_names):
      return res.failure(RTError(
        self.pos_comienzo, self.pos_fin,
        f"{len(args) - len(arg_names)} too many args passed into {self}",
        self.context
      ))
    
    if len(args) < len(arg_names):
      return res.failure(RTError(
        self.pos_comienzo, self.pos_fin,
        f"{len(arg_names) - len(args)} too few args passed into {self}",
        self.context
      ))

    return res.success(None)

  def populate_args(self, arg_names, args, exec_ctx):
    for i in range(len(args)):
      arg_name = arg_names[i]
      arg_value = args[i]
      arg_value.set_context(exec_ctx)
      exec_ctx.symbol_table.set(arg_name, arg_value)

  def check_and_populate_args(self, arg_names, args, exec_ctx):
    res = RTResult()
    res.register(self.check_args(arg_names, args))
    if res.should_return(): return res
    self.populate_args(arg_names, args, exec_ctx)
    return res.success(None)

class Function(BaseFunction):
  def __init__(self, name, body_node, arg_names, should_auto_return):
    super().__init__(name)
    self.body_node = body_node
    self.arg_names = arg_names
    self.should_auto_return = should_auto_return

  def execute(self, args):
    res = RTResult()
    interpreter = Interpreter()
    exec_ctx = self.generate_new_context()

    res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
    if res.should_return(): return res

    valor = res.register(interpreter.visit(self.body_node, exec_ctx))
    if res.should_return() and res.func_return_value == None: return res

    ret_value = (valor if self.should_auto_return else None) or res.func_return_value or Number.null
    return res.success(ret_value)

  def copiar(self):
    copiar = Function(self.name, self.body_node, self.arg_names, self.should_auto_return)
    copiar.set_context(self.context)
    copiar.set_pos(self.pos_comienzo, self.pos_fin)
    return copiar

  def __repr__(self):
    return f"<function {self.name}>"

class BuiltInFunction(BaseFunction):
  def __init__(self, name):
    super().__init__(name)

  def execute(self, args):
    res = RTResult()
    exec_ctx = self.generate_new_context()

    method_name = f'execute_{self.name}'
    method = getattr(self, method_name, self.no_visit_method)

    res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
    if res.should_return(): return res

    return_value = res.register(method(exec_ctx))
    if res.should_return(): return res
    return res.success(return_value)
  
  def no_visit_method(self, node, context):
    raise Exception(f'No execute_{self.name} method defined')

  def copiar(self):
    copiar = BuiltInFunction(self.name)
    copiar.set_context(self.context)
    copiar.set_pos(self.pos_comienzo, self.pos_fin)
    return copiar

  def __repr__(self):
    return f"<built-in function {self.name}>"

  #####################################

  def execute_print(self, exec_ctx):
    print(str(exec_ctx.symbol_table.get('valor')))
    return RTResult().success(Number.null)
  execute_print.arg_names = ['valor']
  
  def execute_print_ret(self, exec_ctx):
    return RTResult().success(String(str(exec_ctx.symbol_table.get('valor'))))
  execute_print_ret.arg_names = ['valor']
  
  def execute_input(self, exec_ctx):
    texto = input()
    return RTResult().success(String(texto))
  execute_input.arg_names = []

  def execute_input_int(self, exec_ctx):
    while True:
      texto = input()
      try:
        number = int(texto)
        break
      except ValueError:
        print(f"'{texto}' must be an integer. Try again!")
    return RTResult().success(Number(number))
  execute_input_int.arg_names = []

  def execute_clear(self, exec_ctx):
    os.system('cls' if os.name == 'nt' else 'cls') 
    return RTResult().success(Number.null)
  execute_clear.arg_names = []

  def execute_is_number(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("valor"), Number)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_number.arg_names = ["valor"]

  def execute_is_string(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("valor"), String)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_string.arg_names = ["valor"]

  def execute_is_list(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("valor"), List)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_list.arg_names = ["valor"]

  def execute_is_function(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("valor"), BaseFunction)
    return RTResult().success(Number.true if is_number else Number.false)
  execute_is_function.arg_names = ["valor"]

  def execute_append(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    valor = exec_ctx.symbol_table.get("valor")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_comienzo, self.pos_fin,
        "First argument must be list",
        exec_ctx
      ))

    list_.elements.append(valor)
    return RTResult().success(Number.null)
  execute_append.arg_names = ["list", "valor"]

  def execute_pop(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    index = exec_ctx.symbol_table.get("index")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_comienzo, self.pos_fin,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(index, Number):
      return RTResult().failure(RTError(
        self.pos_comienzo, self.pos_fin,
        "Second argument must be number",
        exec_ctx
      ))

    try:
      element = list_.elements.pop(index.valor)
    except:
      return RTResult().failure(RTError(
        self.pos_comienzo, self.pos_fin,
        'Element at this index could not be removed from list because index is out of bounds',
        exec_ctx
      ))
    return RTResult().success(element)
  execute_pop.arg_names = ["list", "index"]

  def execute_extend(self, exec_ctx):
    listA = exec_ctx.symbol_table.get("listA")
    listB = exec_ctx.symbol_table.get("listB")

    if not isinstance(listA, List):
      return RTResult().failure(RTError(
        self.pos_comienzo, self.pos_fin,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(listB, List):
      return RTResult().failure(RTError(
        self.pos_comienzo, self.pos_fin,
        "Second argument must be list",
        exec_ctx
      ))

    listA.elements.extend(listB.elements)
    return RTResult().success(Number.null)
  execute_extend.arg_names = ["listA", "listB"]

  def execute_len(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RTResult().failure(RTError(
        self.pos_comienzo, self.pos_fin,
        "Argument must be list",
        exec_ctx
      ))

    return RTResult().success(Number(len(list_.elements)))
  execute_len.arg_names = ["list"]

  def execute_run(self, exec_ctx):
    funcion = exec_ctx.symbol_table.get("funcion")

    if not isinstance(funcion, String):
      return RTResult().failure(RTError(
        self.pos_comienzo, self.pos_fin,
        "Second argument must be string",
        exec_ctx
      ))

    funcion = funcion.valor

    try:
      with open(funcion, "r") as f:
        script = f.read()
    except Exception as e:
      return RTResult().failure(RTError(
        self.pos_comienzo, self.pos_fin,
        f"Failed to load script \"{funcion}\"\n" + str(e),
        exec_ctx
      ))

    _, error = run(funcion, script)
    
    if error:
      return RTResult().failure(RTError(
        self.pos_comienzo, self.pos_fin,
        f"Failed to finish executing script \"{funcion}\"\n" +
        error.as_string(),
        exec_ctx
      ))

    return RTResult().success(Number.null)
  execute_run.arg_names = ["funcion"]

BuiltInFunction.print       = BuiltInFunction("print")
BuiltInFunction.print_ret   = BuiltInFunction("print_ret")
BuiltInFunction.input       = BuiltInFunction("input")
BuiltInFunction.input_int   = BuiltInFunction("input_int")
BuiltInFunction.clear       = BuiltInFunction("clear")
BuiltInFunction.is_number   = BuiltInFunction("is_number")
BuiltInFunction.is_string   = BuiltInFunction("is_string")
BuiltInFunction.is_list     = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append      = BuiltInFunction("append")
BuiltInFunction.pop         = BuiltInFunction("pop")
BuiltInFunction.extend      = BuiltInFunction("extend")
BuiltInFunction.len					= BuiltInFunction("len")
BuiltInFunction.run					= BuiltInFunction("run")

#######################################
# CONTEXT
#######################################

class Context:
  def __init__(self, display_name, parent=None, parent_entry_pos=None):
    self.display_name = display_name
    self.parent = parent
    self.parent_entry_pos = parent_entry_pos
    self.symbol_table = None

#######################################
# SYMBOL TABLE
#######################################

class SymbolTable:
  def __init__(self, parent=None):
    self.symbols = {}
    self.parent = parent

  def get(self, name):
    valor = self.symbols.get(name, None)
    if valor == None and self.parent:
      return self.parent.get(name)
    return valor

  def set(self, name, valor):
    self.symbols[name] = valor

  def remove(self, name):
    del self.symbols[name]

#######################################
# INTERPRETER
#######################################

class Interpreter:
  def visit(self, node, context):
    method_name = f'visit_{type(node).__name__}'
    method = getattr(self, method_name, self.no_visit_method)
    return method(node, context)

  def no_visit_method(self, node, context):
    raise Exception(f'No visit_{type(node).__name__} method defined')

  ###################################

  def visit_NodoNumero(self, node, context):
    return RTResult().success(
      Number(node.tok.valor).set_context(context).set_pos(node.pos_comienzo, node.pos_fin)
    )

  def visit_NodoCadena(self, node, context):
    return RTResult().success(
      String(node.tok.valor).set_context(context).set_pos(node.pos_comienzo, node.pos_fin)
    )

  def visit_NodoLista(self, node, context):
    res = RTResult()
    elements = []

    for element_node in node.element_nodes:
      elements.append(res.register(self.visit(element_node, context)))
      if res.should_return(): return res

    return res.success(
      List(elements).set_context(context).set_pos(node.pos_comienzo, node.pos_fin)
    )

  def visit_NodoVariableAcceso(self, node, context):
    res = RTResult()
    var_name = node.var_name_tok.valor
    valor = context.symbol_table.get(var_name)

    if not valor:
      return res.failure(RTError(
        node.pos_comienzo, node.pos_fin,
        f"'{var_name}' is not defined",
        context
      ))

    valor = valor.copiar().set_pos(node.pos_comienzo, node.pos_fin).set_context(context)
    return res.success(valor)

  def visit_VarAssignNode(self, node, context):
    res = RTResult()
    var_name = node.var_name_tok.valor
    valor = res.register(self.visit(node.value_node, context))
    if res.should_return(): return res

    context.symbol_table.set(var_name, valor)
    return res.success(valor)

  def visit_BinOpNode(self, node, context):
    res = RTResult()
    left = res.register(self.visit(node.left_node, context))
    if res.should_return(): return res
    right = res.register(self.visit(node.right_node, context))
    if res.should_return(): return res

    if node.op_tok.tipo == TT_PLUS:
      result, error = left.added_to(right)
    elif node.op_tok.tipo == TT_MINUS:
      result, error = left.subbed_by(right)
    elif node.op_tok.tipo == TT_MUL:
      result, error = left.multed_by(right)
    elif node.op_tok.tipo == TT_DIV:
      result, error = left.dived_by(right)
    elif node.op_tok.tipo == TT_POW:
      result, error = left.powed_by(right)
    elif node.op_tok.tipo == TT_EE:
      result, error = left.get_comparison_eq(right)
    elif node.op_tok.tipo == TT_NE:
      result, error = left.get_comparison_ne(right)
    elif node.op_tok.tipo == TT_LT:
      result, error = left.get_comparison_lt(right)
    elif node.op_tok.tipo == TT_GT:
      result, error = left.get_comparison_gt(right)
    elif node.op_tok.tipo == TT_LTE:
      result, error = left.get_comparison_lte(right)
    elif node.op_tok.tipo == TT_GTE:
      result, error = left.get_comparison_gte(right)
    elif node.op_tok.coincide(TT_KEYWORD, 'Y'):
      result, error = left.anded_by(right)
    elif node.op_tok.coincide(TT_KEYWORD, 'O'):
      result, error = left.ored_by(right)

    if error:
      return res.failure(error)
    else:
      return res.success(result.set_pos(node.pos_comienzo, node.pos_fin))

  def visit_UnaryOpNode(self, node, context):
    res = RTResult()
    number = res.register(self.visit(node.node, context))
    if res.should_return(): return res

    error = None

    if node.op_tok.tipo == TT_MINUS:
      number, error = number.multed_by(Number(-1))
    elif node.op_tok.coincide(TT_KEYWORD, 'NEL'):
      number, error = number.notted()

    if error:
      return res.failure(error)
    else:
      return res.success(number.set_pos(node.pos_comienzo, node.pos_fin))

  def visit_IfNode(self, node, context):
    res = RTResult()

    for condition, expr, should_return_null in node.cases:
      condition_value = res.register(self.visit(condition, context))
      if res.should_return(): return res

      if condition_value.is_true():
        expr_value = res.register(self.visit(expr, context))
        if res.should_return(): return res
        return res.success(Number.null if should_return_null else expr_value)

    if node.else_case:
      expr, should_return_null = node.else_case
      expr_value = res.register(self.visit(expr, context))
      if res.should_return(): return res
      return res.success(Number.null if should_return_null else expr_value)

    return res.success(Number.null)

  def visit_ForNode(self, node, context):
    res = RTResult()
    elements = []

    start_value = res.register(self.visit(node.start_value_node, context))
    if res.should_return(): return res

    end_value = res.register(self.visit(node.end_value_node, context))
    if res.should_return(): return res

    if node.step_value_node:
      step_value = res.register(self.visit(node.step_value_node, context))
      if res.should_return(): return res
    else:
      step_value = Number(1)

    i = start_value.valor

    if step_value.valor >= 0:
      condition = lambda: i < end_value.valor
    else:
      condition = lambda: i > end_value.valor
    
    while condition():
      context.symbol_table.set(node.var_name_tok.valor, Number(i))
      i += step_value.valor

      valor = res.register(self.visit(node.body_node, context))
      if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res
      
      if res.loop_should_continue:
        continue
      
      if res.loop_should_break:
        break

      elements.append(valor)

    return res.success(
      Number.null if node.should_return_null else
      List(elements).set_context(context).set_pos(node.pos_comienzo, node.pos_fin)
    )

  def visit_WhileNode(self, node, context):
    res = RTResult()
    elements = []

    while True:
      condition = res.register(self.visit(node.condition_node, context))
      if res.should_return(): return res

      if not condition.is_true():
        break

      valor = res.register(self.visit(node.body_node, context))
      if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False: return res

      if res.loop_should_continue:
        continue
      
      if res.loop_should_break:
        break

      elements.append(valor)

    return res.success(
      Number.null if node.should_return_null else
      List(elements).set_context(context).set_pos(node.pos_comienzo, node.pos_fin)
    )

  def visit_FuncDefNode(self, node, context):
    res = RTResult()

    func_name = node.var_name_tok.valor if node.var_name_tok else None
    body_node = node.body_node
    arg_names = [arg_name.valor for arg_name in node.arg_name_toks]
    func_value = Function(func_name, body_node, arg_names, node.should_auto_return).set_context(context).set_pos(node.pos_comienzo, node.pos_fin)
    
    if node.var_name_tok:
      context.symbol_table.set(func_name, func_value)

    return res.success(func_value)

  def visit_CallNode(self, node, context):
    res = RTResult()
    args = []

    value_to_call = res.register(self.visit(node.node_to_call, context))
    if res.should_return(): return res
    value_to_call = value_to_call.copiar().set_pos(node.pos_comienzo, node.pos_fin)

    for arg_node in node.arg_nodes:
      args.append(res.register(self.visit(arg_node, context)))
      if res.should_return(): return res

    return_value = res.register(value_to_call.execute(args))
    if res.should_return(): return res
    return_value = return_value.copiar().set_pos(node.pos_comienzo, node.pos_fin).set_context(context)
    return res.success(return_value)

  def visit_ReturnNode(self, node, context):
    res = RTResult()

    if node.node_to_return:
      valor = res.register(self.visit(node.node_to_return, context))
      if res.should_return(): return res
    else:
      valor = Number.null
    
    return res.success_return(valor)

  def visit_ContinueNode(self, node, context):
    return RTResult().success_continue()

  def visit_BreakNode(self, node, context):
    return RTResult().success_break()

#######################################
# RUN
#######################################

global_symbol_table = SymbolTable()
global_symbol_table.set("NULL", Number.null)
global_symbol_table.set("FALSE", Number.false)
global_symbol_table.set("TRUE", Number.true)
global_symbol_table.set("MATH_PI", Number.math_PI)
global_symbol_table.set("PRINT", BuiltInFunction.print)
global_symbol_table.set("PRINT_RET", BuiltInFunction.print_ret)
global_symbol_table.set("INPUT", BuiltInFunction.input)
global_symbol_table.set("INPUT_INT", BuiltInFunction.input_int)
global_symbol_table.set("CLEAR", BuiltInFunction.clear)
global_symbol_table.set("CLS", BuiltInFunction.clear)
global_symbol_table.set("IS_NUM", BuiltInFunction.is_number)
global_symbol_table.set("IS_STR", BuiltInFunction.is_string)
global_symbol_table.set("IS_LIST", BuiltInFunction.is_list)
global_symbol_table.set("IS_FUN", BuiltInFunction.is_function)
global_symbol_table.set("APPEND", BuiltInFunction.append)
global_symbol_table.set("POP", BuiltInFunction.pop)
global_symbol_table.set("EXTEND", BuiltInFunction.extend)
global_symbol_table.set("LEN", BuiltInFunction.len)
global_symbol_table.set("RUN", BuiltInFunction.run)

def run(funcion, texto):
  # Generate tokens
  lexer = Lexer(funcion, texto)
  tokens, error = lexer.hacer_tokens()
  if error: return None, error
  
  # Generate AST
  parser = Parser(tokens)
  ast = parser.parse()
  if ast.error: return None, ast.error

  # Run program
  interpreter = Interpreter()
  context = Context('<program>')
  context.symbol_table = global_symbol_table
  result = interpreter.visit(ast.node, context)

  return result.valor, result.error

""" def generate_object_code(funcion, texto, output_filename):
  # Tokeniza y parsea el código
  lexer = Lexer(funcion, texto)
  tokens, error = lexer.hacer_tokens()
  if error:
      return None, error.as_string()
  
  parser = Parser(tokens)
  ast = parser.parse()
  if ast.error:
      return None, ast.error.as_string()

  # Generar código objeto (aquí puedes personalizar según el formato que necesites)
  object_code = []
  for token in tokens:
      object_code.append(f"{token.tipo}: {token.valor}" if token.valor else f"{token.tipo}")

  # Guardar el código objeto en un archivo .txt
  with open(output_filename, 'w') as f:
      f.write("\n".join(object_code))
  
  return "Código objeto generado con éxito.", None
 """