#!/usr/bin/env python
# -*- coding: utf-8 -*-
# $Id: lisp.py,v 1.17 2002-11-18 10:15:36-06 annis Exp $
# $Source: /u/annis/code/python/lib/lisp/RCS/lisp.py,v $
#
# Copyright (c) 2000 - 2002 William S. Annis.  All rights reserved.
# This is free software; you can redistribute it and/or modify it
# under the same terms as Perl (the Artistic Licence).  Developed at
# the Department of Biostatistics and Medical Informatics, University
# of Wisconsin, Madison.
#
# The S-expression parser (class Reader) probably came from someone
# else, but I am no longer sure where.  If you know, please tell me,
# though I have made many changes and its ancestry may no longer
# be apparent.

"""A trivial Lisp implementation.
"""

import sys
import string
import types
import re

SYMCHARS = string.digits + string.uppercase + string.lowercase + '-+*/:&$?='
WS = string.whitespace
SPECIAL = "()`',@"
SYNTAX = WS + SPECIAL

# simple conversions that are almost always useful:
INT = re.compile(r'^[+-]?\d+$')
LONGINT = re.compile(r'^[+-]?\d+[lL]$')
FLOAT = re.compile(r'^[+-]?(\d+\.\d*$|\d*\.\d+$)')
_nummap = {
    INT: string.atoi,
    LONGINT: string.atol,
    FLOAT: string.atof
    }


class Error(Exception): pass

# The type system: every type knows how to evaluate itself but must
# be handed an Environment to work with, plus any arguments it might
# take.  
class Evalable:
    """Evaluatable Lisp object interface."""
    def eval(self, environment, args=None):
        raise Error, "Unimplemented"


_PROPERTIES = {}                        # property list

class SymbolObject(Evalable):
    # Everything in Lisp is a list of symbols.
    def __init__(self, name):
        self.n = name
        if not _PROPERTIES.has_key(self.n):
            _PROPERTIES[self.n] = {}

    def __repr__(self):
        return self.n

    def __hash__(self):
        return hash(self.n)

    def eval(self, env, args=None):
        return env.get(self.n)

    def cons(self, item):
        return PairObject(item, self)

    def nullp(self):
        return FALSE

    # property lists (really a hash table here).
    def put(self, property, value):
        _PROPERTIES[self.n][property] = value

    def get(self, property):
        try:
            return _PROPERTIES[self.n][property]
        except:
            return FALSE


class StringObject(Evalable):
    def __init__(self, str):
        self.string = str

    def __repr__(self):
        return `self.string`

    def eval(self, env, args=None):
        return self.string

    def nullp(self):
        if self.string == "":
            return TRUE
        else:
            return FALSE

    def __getitem__(self, index):
        return self.string[index]


class NumberObject(Evalable):
    def __init__(self, value):
        self.v = value

    def __repr__(self):
        return `self.v`

    def eval(self, env, args=None):
        return self

    def __cmp__(self, other):
#        if isinstance(other, NumberObject) or isinstance(other, LogicObject):
        if type(self) == type(other):
            if self.v == other.v:
                return 0
            elif self.v > other.v:
                return 1
            else:
                return -1
        else:
            if self.v == other:
                return 0
            elif self.v > other:
                return 1
            else:
                return -1

    def __add__(self, other):
        if type(self) == type(other):
            return NumberObject(self.v + other.v)
        else:
            return self.v + other
    __radd__ = __add__

    def __sub__(self, other):
        if type(self) == type(other):
            return NumberObject(self.v - other.v)
        else:
            return self.v - other
    __rsub__ = __sub__

    def __mul__(self, other):
        if type(self) == type(other):
            return NumberObject(self.v * other.v)
        else:
            return self.v * other
    __rmul__ = __mul__

    def __div__(self, other):
        if type(self) == type(other):
            return NumberObject(self.v / other.v)
        else:
            return self.v / other
    __rdiv__ = __div__

    def __mod__(self, other):
        if type(self) == type(other):
            return NumberObject(self.v % other.v)
        else:
            return self.v % other
    __rmod__ = __mod__

    def nullp(self):
        if self.v == 0.0:
            return TRUE
        else:
            return FALSE


class LogicObject(Evalable):
    def __init__(self, value):
        if isinstance(value, NumberObject):
            self.v = value.v
        else:
            self.v = value

    def __repr__(self):
        if self.v == 1.0:
            return '*true*'
        elif self.v == 0.0:
            return '*false*'
        else:
            return "(logic %s)" % self.v

    def __cmp__(self, other):
        #if type(self) == type(other):
        if isinstance(other, LogicObject):
            if self.v == other.v:
                return 0
            elif self.v > other.v:
                return 1
            else:
                return -1
        else:
            if self.v == other:
                return 0
            elif self.v > other:
                return 1
            else:
                return -1

    def __neg__(self):
        return LogicObject(1.0 - self.v)

    def __and__(self, other):
        return LogicObject(min(self.v, other.v))

    def __or__(self, other):
        return LogicObject(max(self.v, other.v))

    def eval(self, env, args=None):
        return self

    def nullp(self):
        return -self


TRUE = LogicObject(1.0)
FALSE = LogicObject(0.0)


# Not quite a list.  In real Lisps, all lists are just piled up pairs.
# Not so in PyLisp.  Pairs are special case, mostly for association
# lists and the sort.
class PairObject(Evalable):
    def __init__(self, a, d):
        self.a, self.d = a, d

    def __repr__(self):
        if self.d == None:
            return "(%s)" % (self.a, self.d)
        else:
            return "(%s . %s)" % (self.a, self.d)

    def replaca(self, val):
        self.a = val
        return val

    def replacd(self, val):
        if isinstance(val, ListObject):
            return val.cons(self.a)
        else:
            self.d = val
            return val

    def first(self):
        return self.a

    def rest(self):
        return self.d

    def second(self):
        return self.d

    def nullp(self):
        return FALSE


class ListObject(Evalable):
    def __init__(self, lst=None):
        if lst is None:
            self.list = []
        else:
            self.list = lst

    def __repr__(self):
        if self.list == []:
            return "()"

        s = "(%s" % self.list[0]
        for e in self.list[1:]:
            s = s + " %s" % e

        return s + ")"

    def __len__(self):
        return len(self.list)

    def __getitem__(self, i):
        return self.list[i]

    def __and__(self, other):
        if isinstance(other, LogicObject):
            if self.nullp():
                return FALSE & other
            else:
                return TRUE & other

    def first(self):
        return self.list[0]

    def replaca(self, val):
        self.list[0] = val
        return val

    def second(self):
        try:
            return self.list[1]
        except:
            return ListObject([])

    def third(self):
        try:
            return self.list[2]
        except:
            return ListObject([])

    def rest(self):
        try:
            return ListObject(self.list[1:])
        except:
            return ListObject([])

    def replacd(self, val):
        self.list = [self.list[0]] + val.list
        return val

    def cons(self, item):
        n = ListObject(self.list[:])
        n.list.insert(0, item)
        return n

    def append(self, lst):
        if isinstance(lst, ListObject):
            return ListObject(self.list + lst.list)
        else:
            return ListObject(self.list + lst)

    def nconc(self, lst):
        self.list = self.append(lst)
        return self

    def eval(self, env, args=None):
        # Code and data look the same in lisp.
        fn = self.list[0].eval(env)
        if isinstance(fn, LambdaObject) or \
           isinstance(fn, MacroObject) or \
           isinstance(fn, FunctionObject) or \
           isinstance(fn, SyntaxObject):
            return fn.eval(env, self.list[1:])
        else:
            raise Error, "%s is not applyable" % fn

    def nullp(self):
        if len(self.list) == 0:
            return TRUE
        else:
            return FALSE

    def iquote(self, env):
        """l.iquote(environment) - do the back-tick substitutions"""
        answer = []
        length = len(self.list)
        i = 0
        while i < length:
            if isinstance(self.list[i], ListObject):
                answer.append(self.list[i].iquote(env))
            elif type(self.list[i]) == types.StringType:
                if self.list[i] == ',':
                    i = i + 1
                    if type(self.list[i]) == types.StringType:
                        if self.list[i] == '@':
                            # splice: `(a b ,@fred) -> (a b a b c)
                            i = i + 1
                            answer = answer + self.list[i].eval(env).list
                        else:
                            answer.append(self.list[i].eval(env))
                    else:
                        answer.append(self.list[i].eval(env))
            else:
                answer.append(self.list[i])

            i = i + 1

        return ListObject(answer)

    def assoc(self, item):
        for pair in self.list:
            if isinstance(pair, PairObject) or isinstance(pair, ListObject):
                key = pair.first()
                if isinstance(key, SymbolObject) and isinstance(item, SymbolObject):
                    if key.n == item.n:
                        return pair.second()
                else:
                    if key == item:
                        return pair.second()
            else:
                raise Error, "assoc: second argument must be list of lists/pairs"

        return FALSE

NIL = ListObject([])


class ObjectObject(Evalable):
    """A basic message-passing object orientation for PyLisp"""
    def __init__(self, name, *attrs, **opts):
        self.name = name

    def __repr__(self):
        return "<object %s>" % id(self.name)


class FunctionObject(Evalable):
    """Internal (Python) functions"""
    def __init__(self, fn):
        self.fn = fn

    def __repr__(self):
        return "<built-in function %s>" % id(self.fn)

    def eval(self, env, args):
        return self.fn(env, args)

    def nullp(self):
        return FALSE


class LambdaObject(Evalable):
    """Fuctions defined in PyLisp."""
    def __init__(self, bindings, code, env):
        self.bindings = bindings
        self.code = code
        self.env = env                  # Remember the defining environment.

    def eval(self, env, args):
        lisper = env.get('*self*')

        # If the lexical environment in which this was defined is different
        # than the one called from, push that saved environment's values
        # onto the new lambda's environment.
        if self.env:
            #print "PUSHED-FOREIGN"
            lisper.push_e(self.env.e)
        else:
            lisper.push_e()

        # Evaluate the arguments and bind to the correct names.
        i = 0
        n = len(self.bindings)
        while i < n:
            if self.bindings[i].n == "&rest":
                rest = []
                for arg in args[i:]:
                    rest.append(arg.eval(lisper.e))
                lisper.lexical_intern(self.bindings[i + 1].n, ListObject(rest))
                i = i + 1
            else:
                lisper.lexical_intern(self.bindings[i].n, args[i].eval(lisper.e))
            i = i + 1

        # Run the code.
        ans = FALSE
        for code in self.code:
            ans = code.eval(lisper.e)

        lisper.pop_e()
        return ans

    # Mostly transform things like the let into the lambda form, which
    # will speed things up a bit.
    def compile(self):
        pass

    def __repr__(self):
        if len(self.code) == 1:
            return "(lambda %s %s)" % (self.bindings, self.code[0])
        else:
            return "(lambda %s %s)" % (self.bindings, ListObject(['begin'] + self.code))

    def nullp(self):
        return FALSE


class MacroObject(Evalable):
    # (def incf (macro (x) `(+ ,x 1)))
    # ((macro (x) `(+ ,x 1)) swee)
    def __init__(self, bindings, code, env):
        self.bindings = bindings
        self.code = code
        self.env = env                  # defining environment

    def eval(self, env, args):
        lisper = env.get('*self*')

        # If the lexical environment in which this was defined is different
        # than the one called from, push that saved environment's values
        # onto the new macro's environment.
        if self.env:
            lisper.push_e(self.env.e)
        else:
            lisper.push_e()

        # Evaluate the arguments and bind to the correct names: UNEVALUATED.
        i = 0
        n = len(self.bindings)
        while i < n:
            if self.bindings[i].n == "&rest":
                lisper.lexical_intern(self.bindings[i + 1].n, ListObject(args[i:]))
                i = i + 1
            else:
                lisper.lexical_intern(self.bindings[i].n, args[i])
            i = i + 1
        
        # Run the code.  The first run to expand the macro.
        mcode = []
        for mc in self.code:
            mcode.append(mc.eval(lisper.e))

        # The macro bindings environment is finished.
        lisper.pop_e()

        # Now, run again, this time for real.
        ans = FALSE
        for code in mcode:
            ans = code.eval(lisper.e)

        return ans
        
    def expand(self, env, args):
        lisper = env.get('*self*')
        if self.env:
            lisper.push_e(self.env.e)
        else:
            lisper.push_e()

        # Evaluate the arguments and bind to the correct names: UNEVALUATED.
        i = 0
        n = len(self.bindings)
        while i < n:
            if self.bindings[i].n == "&rest":
                lisper.lexical_intern(self.bindings[i + 1].n, ListObject(args[i:]))
                i = i + 1
            else:
                lisper.lexical_intern(self.bindings[i].n, args[i])
            i = i + 1
        
        mcode = []
        for mc in self.code:
            mcode.append(mc.eval(lisper.e))
        lisper.pop_e()

        # The 'begin' turns the (Python) list of code into legally
        # parsable list of Pylisp code.
        return ListObject(mcode).cons('begin')

    def __repr__(self):
        if len(self.code) == 1:
            return "(macro %s %s)" % (self.bindings, self.code[0])
        else:
            # ???
            return "(macro %s %s)" % (self.bindings, ListObject(['begin'] + self.code))

    def nullp(self):
        return FALSE


class SyntaxObject(Evalable):
    # Same as the FunctionObject, but this object is expected to handle
    # the evaluation of the arguments it is passed.
    def __init__(self, fn):
        self.fn = fn

    def __repr__(self):
        return "<built-in syntax %s>" % id(self.fn)

    def eval(self, env, args):
        return self.fn(env, args)

    def nullp(self):
        return FALSE


# some syntactic sugar for the ' symbol.
QUOTE = SymbolObject('quote')
# and for `
IQUOTE = SymbolObject('i-quote')

class Reader:
    def __init__(self, str=None):
        self.str = str
        self.i = 0
        self.len = 0
        self.sexpr = []
        self.pounds = {}                # '#?' reader helper functions

        if str:
            self.sexpr = self.get_sexpr()

    def add_pound_helper(self, char, helper):
        self.pounds[char] = helper

    def get_token(self):
        if self.i >= self.len:
            return None

        # Munch leading whitespace.
        while self.i < self.len and self.str[self.i] in WS:
            self.i = self.i + 1

        if self.i == self.len:
            return None

        # Now, tokenize.
        if self.str[self.i] == '#':
            # Look ahead to get the second character of the pound escape
            # then sling on the next token for special treatment.
            self.i = self.i + 2
            return self.pounds[self.str[self.i - 1]](self.get_token())
        if self.str[self.i] in SPECIAL:
            self.i = self.i + 1
            #print "\tSPECIAL:", self.str[self.i - 1], "\t", self.i, self.len
            return self.str[self.i - 1]
        elif self.str[self.i] == '"':
            # Parse a string.
            str = ""
            self.i = self.i + 1
            while self.str[self.i] != '"' and self.i < self.len:
                if self.str[self.i] == '\\':
                    self.i = self.i + 1
                    spchar = self.str[self.i]
                    if spchar == "n":
                        str = str + "\n"
                    elif spchar == "t":
                        str = str + "\t"
                else:
                    str = str + self.str[self.i]
                self.i = self.i + 1
            self.i = self.i + 1               # Remove trailing quote
            return StringObject(str)
        else:
            tok = ""
            # First, build the token.
            while self.i < self.len - 1:
                if self.str[self.i] in SYNTAX:
                    break
                else:
                    tok = tok + self.str[self.i]
                    self.i = self.i + 1

            if not self.str[self.i] in SYNTAX:
                tok = tok + self.str[self.i]
                self.i = self.i + 1

            #print "\tTOK:", tok, "\t", self.i, self.len
            # If the thing is a number, convert it.
            numeric = 0
            for number in INT, LONGINT, FLOAT:
                n = number.match(tok)
                if n:
                    tok = NumberObject(_nummap[number](tok))
                    numeric = 1
                    break

            if not numeric:
                tok = SymbolObject(tok)

            return tok

    def get_sexpr(self, str=None):
        if str:
            self.i = 0
            self.str = str
            self.len = len(self.str)

        expr = None
        tok = self.get_token()
        if tok == ')':
            raise Error, "Unexpected ')'"
        elif tok == "(":
            expr = []
            tok = self.get_token()
            while tok != ")":
                if tok == '(':
                    # Start parsing again.
                    self.i = self.i - 1
                    expr.append(self.get_sexpr())
                elif tok == "'":
                    expr.append(ListObject([QUOTE, self.get_sexpr()]))
                elif tok == "`":
                    expr.append(ListObject([IQUOTE, self.get_sexpr()]))
                elif tok == None:
                    raise Error, "unexpected end of expression"
                else:
                    expr.append(tok)

                tok = self.get_token()
            return ListObject(expr)
        elif tok == "'":
            return ListObject([QUOTE, self.get_sexpr()])
        elif tok == "`":
            return ListObject([IQUOTE, self.get_sexpr()])
        else:
            return tok


class UnboundSymbolError(Error): pass


class Environment:
    def __init__(self, parent=None, bindings=None):
        if bindings:
            self.e = bindings
        else:
            self.e = {}

        self.parent = parent              # Parent environment.
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0

        self.init()

    def init(self):
        """Subclass customization code here."""
        pass

    def set(self, sym, value):
        """Assign a binding in the environment.

        Keeps looking for the symbol in outer environment until found or
        until it gets to the top-level environment.
        """
        #print "SET(%i):" % self.level, sym, value
        if self.e.has_key(sym):
            self.e[sym] = value
        elif self.parent:
            self.parent.set(sym, value)
        else:
            self.e[sym] = value

    def lexical_set(self, sym, value):
        """Set a binding in the immediate environment."""
        #print "LEXICAL_SET(%i):" % self.level, sym, value
        self.e[sym] = value

    def get(self, sym):
        if not self.e.has_key(sym):
            # Consult the parent environment if the symbol isn't here.
            if self.parent:
                return self.parent.get(sym)
            else:
                raise UnboundSymbolError, sym
        else:
            #print "GET(%i)" % self.level, sym, self.e[sym]
            return self.e[sym]

    def pop(self):
        """Throw myself away, returning the parent environment."""
        return self.parent

    def push(self, bindings=None):
        """Create a new environment."""
        return Environment(self, bindings=bindings)

    def __repr__(self):
        s = "\nLevel %s:\n" % self.level
        keys = self.e.keys()
        keys.sort()
        for key in keys:
            if key != "*env*":
                s = s + " %10s: %s\n" % (key, self.e[key])

        if self.parent:
            return s + `self.parent`# + s
        else:
            return s

    def nullp(self):
        return FALSE


# __init__ and IO routines contain code by Jerome Alet to give a user
# more control of IO.  The default behavior looks the same, though.
class Lisper:
    """A small lisp environment."""
    def __init__(self, iostreams=(sys.stdin, sys.stdout, sys.stderr)):
        (self.stdin, self.stdout, self.stderr) = iostreams
        
        self.r = Reader()
        self.e = Environment()

        # The default tiny lisp environment.
        self.intern('*self*', self)
        self.intern('*env*', self.e)
        self.intern('*true*', TRUE)
        self.intern('*false*', FALSE)
        self.intern('*true-enough*', TRUE)
        self.intern('*gensym-string*', SymbolObject('GENSYM@'))
        self.intern('*gensym-counter*', NumberObject(0))
        self.intern('print', FunctionObject(self.do_print))
        self.intern('first', FunctionObject(self.do_first))
        self.intern('car', FunctionObject(self.do_first))
        self.intern('replaca', FunctionObject(self.do_replaca))
        self.intern('second', FunctionObject(self.do_second))
        self.intern('cadr', FunctionObject(self.do_second))
        self.intern('third', FunctionObject(self.do_third))
        self.intern('rest', FunctionObject(self.do_rest))
        self.intern('cdr', FunctionObject(self.do_rest))
        self.intern('replacd', FunctionObject(self.do_replacd))
        self.intern('cons', FunctionObject(self.do_cons))
        self.intern('append', FunctionObject(self.do_append))
        self.intern('null?', FunctionObject(self.do_nullp))
        self.intern('list', FunctionObject(self.do_list))
        self.intern('assoc', FunctionObject(self.do_assoc))
        self.intern('+', FunctionObject(self.do_add))
        self.intern('-', FunctionObject(self.do_sub))
        self.intern('/', FunctionObject(self.do_div))
        self.intern('%', FunctionObject(self.do_mod))
        self.intern('*', FunctionObject(self.do_mul))
        self.intern('>', FunctionObject(self.do_gt))
        self.intern('>=', FunctionObject(self.do_ge))
        self.intern('<', FunctionObject(self.do_lt))
        self.intern('<=', FunctionObject(self.do_le))
        self.intern('==', FunctionObject(self.do_eql))
        self.intern('eql', FunctionObject(self.do_eql))
        self.intern('!=', FunctionObject(self.do_neq))
        self.intern('not', FunctionObject(self.do_not))
        self.intern('and', FunctionObject(self.do_and))
        self.intern('or', FunctionObject(self.do_or))
        self.intern('logic', FunctionObject(self.do_logic))
        self.intern('load', FunctionObject(self.do_read))
        self.intern('gensym', FunctionObject(self.do_gensym))
        self.intern('eval', FunctionObject(self.do_eval))
        self.intern('list?', FunctionObject(self.do_listp))
        self.intern('pair?', FunctionObject(self.do_pairp))
        self.intern('symbol?', FunctionObject(self.do_symbolp))
        self.intern('string?', FunctionObject(self.do_stringp))
        self.intern('number?', FunctionObject(self.do_numberp))
        self.intern('logic?', FunctionObject(self.do_logicp))
        self.intern('symbol-name', FunctionObject(self.do_symbol_name))
        self.intern('top-level', FunctionObject(self.do_top_level))
        self.intern('the-environment', FunctionObject(self.do_the_environment))
        self.intern('get-environment', FunctionObject(self.do_get_environment))
        self.intern('env-get', FunctionObject(self.do_env_get))
        self.intern('env-set', FunctionObject(self.do_env_set))
        self.intern('get', FunctionObject(self.do_get))
        self.intern('put', FunctionObject(self.do_put))
        self.intern('elt', FunctionObject(self.do_elt))
        self.intern('apply', FunctionObject(self.do_apply))
        self.intern('send', FunctionObject(self.do_send))
        
        # Chat with Python.
        #self.intern('py-setattr', FunctionObject(self.do_py_setattr))
        #self.intern('py-getattr', FunctionObject(self.do_py_getattr))
        #self.intern('py-hash-make', FunctionObject(self.do_py_hash_make))
        #self.intern('py-hash-get', FunctionObject(self.do_py_hash_get))
        #self.intern('py-hash-set', FunctionObject(self.do_py_hash_set))
        self.intern('py-format', FunctionObject(self.do_py_format))
        self.intern('py-type', FunctionObject(self.do_py_type))
        self.intern('py-eval', FunctionObject(self.do_py_eval))
        self.intern('py-exec', FunctionObject(self.do_py_eval))
        self.intern('keyword->pyhash', FunctionObject(self.do_kw_to_pyhash))
#        self.intern('py-send', FunctionObject(self.do_py_send))
#>>> class A:
#...   def __init__(self, a): self.a = a
#...   def foo(self, c, d): return self.a + c + d
#... 
#>>> f = A(12)
#>>> apply(f.foo, (3, 4))
#19
#>>> 
        # macros/syntax
        self.intern('begin', SyntaxObject(self.do_m_begin))
        self.intern('setq', SyntaxObject(self.do_m_setq))
        self.intern('def', SyntaxObject(self.do_m_setq))
        self.intern('let', SyntaxObject(self.do_m_let))
        self.intern('lambda', SyntaxObject(self.do_m_lambda))
        self.intern('macro', SyntaxObject(self.do_m_macro))
        self.intern('macro-expand', SyntaxObject(self.do_m_macro_expand))
        self.intern('quote', SyntaxObject(self.do_m_quote))
        self.intern('i-quote', SyntaxObject(self.do_m_iquote))
        self.intern('if', SyntaxObject(self.do_m_if))
        self.intern('cond', SyntaxObject(self.do_m_cond))
        self.intern('with-py-hash-env', SyntaxObject(self.do_m_with_hash))

        # Subclasses should override init() to add new functions
        # and syntax.
        self.init()

    def init(self):
        """Secondary initialization

        Subclasses should add new functionality to PyLisp in this method.
        """
        pass

    def add_pound_helper(self, char, helper):
        self.r.add_pound_helper(char, helper)

    def intern(self, sym, val):
        """assign a symbol value in the environment"""
        self.e.set(sym, val)

    def lexical_intern(self, sym, val):
        """assign a symbol value in the immediate environment"""
        self.e.lexical_set(sym, val)

    def lookup(self, sym):
        return self.e.get(sym, UnboundSymbolError)

    def set(self, sym, propery, value):
        if not _PROPERTIES.has_key(sym):
            _PROPERTIES[sym] = {}

        _PROPERTIES[sym][property] = value

    def get(self, sym, property):
        try:
            return _PROPERTIES[sym][property]
        except:
            return None

    def eval(self, form):
        """Evaluate a lisp form, returning the value."""
        return form.eval(self.e)

    def evalstring(self, str):
        return self.eval(self.r.get_sexpr(str))

    def raw_input(self, prompt) :
        """raw_input with pseudo I/O streams."""
        if prompt :
            self.stdout.write("%s" % prompt)
            self.stdout.flush()
        line = self.stdin.readline()    
        if line[-1] == "\n":
            line = line[:-1]

        return line
        
    # Code from Brian P Templeton <bpt@tunes.org>.  Now you can enter
    # multi-line sexps from the interactive interface.  *Much* nicer.
    def read_full_sexp(self, line="", parenlevel=0):
        """get a complete sexp"""
        if line != "":
            line = line + " "
        if self.e.level != 0:
            prompt = "lisp %i%s " % (self.e.level, ">" * (parenlevel+1))
        else:
            prompt = "lisp%s " % (">" * (parenlevel+1))
            line = line  + self.raw_input(prompt)
            oparens = 0
            cparens = 0
            for c in line:
                if c == "(":
                    oparens = oparens + 1
                elif c == ")":
                    cparens = cparens + 1
            if oparens > cparens:
                return self.read_full_sexp(line, parenlevel+1)
            else:
                return line


    def read(self, file):
        """l.read(file) - read in and evaluate a file of PyLisp code"""
        f = open(file, "r")
        code = f.readlines()
        f.close()
        code = re.sub(";.*(\n|$)", "", string.join(code))
        sexpr = self.r.get_sexpr(code)
        while sexpr:
            self.eval(sexpr)
            sexpr = self.r.get_sexpr()

    # A much friendlier version of the read-eval-print loop, care
    # of Ole Martin Bjørndalen.
    def repl(self):
        """Interactive lisp loop."""
        while 1:
            try:
                #if self.e.level != 0:
                #    prompt = "lisp %i> " % self.e.level
                #else:
                #    prompt = "lisp> "
                #line = raw_input(prompt)
                line = self.read_full_sexp()
            except EOFError:
                self.stdout.write("\n")
                break
            if not line:
                continue
            if line in ['(quit)', '(bye)']:
                break

            try:
                sexpr = self.r.get_sexpr(line)
                while sexpr:
                    self.stdout.write("\t%s\n" % self.eval(sexpr))
                    sexpr = self.r.get_sexpr()
            except UnboundSymbolError, e:
                self.stderr.write("ERROR: unbound symbol '%s'\n" % e.args[0])
            except:
                import traceback, sys
                traceback.print_exc(self.stderr)

    def repl_d(self):
        """l.repl_d() - debugging read-eval-print loop"""
        # allows access to the Python debugger when something dies
        line = self.raw_input("lisp> ")
        while line and line not in ['(quit)', '(bye)']:
            sexpr = self.r.get_sexpr(line)
            while sexpr:
                self.stdout.write("\t %s\n" % self.eval(sexpr))
                sexpr = self.r.get_sexpr()
            line = self.raw_input("lisp> ")

    def push_e(self, env=None):
        if env:
            self.e = self.e.push(env)
        else:
            self.e = self.e.push()

    def pop_e(self):
        self.e = self.e.pop()

    def unwind_e(self):
        # Unroll to the top environment level.
        while self.e.parent:
            self.e = self.e.parent

    def do_print(self, env, args):
        for a in args:
            result = a.eval(env)
            self.stdout.write("%s " % str(result))
        self.stdout.write("\n")    
        return TRUE

    def do_first(self, env, args):
        return args[0].eval(env).first()

    def do_replaca(self, env, args):
        return args[0].eval(env).replaca(args[1].eval(env))

    def do_second(self, env, args):
        return args[0].eval(env).second()

    def do_third(self, env, args):
        return args[0].eval(env).third()

    def do_rest(self, env, args):
        return args[0].eval(env).rest()

    def do_replacd(self, env, args):
        return args[0].eval(env).replacd(args[1].eval(env))

    def do_cons(self, env, args):
        return args[1].eval(env).cons(args[0].eval(env))

    def do_append(self, env, args):
        lst = args[0].eval(env)
        for l in args[1:]:
            lst = lst.append(l.eval(env))

        return lst

    def do_nullp(self, env, args):
        if len(args[0].eval(env)) == 0:
            return TRUE
        else:
            return FALSE

    def do_list(self, env, args):
        ans = []
        for n in args:
            ans.append(n.eval(env))

        return ListObject(ans)

    def do_assoc(self, env, args):
        return args[1].eval(env).assoc(args[0].eval(env))

    def do_add(self, env, args):
        ans = args[0].eval(env)
        for n in args[1:]:
            ans = ans + n.eval(env)

        return NumberObject(ans)

    def do_sub(self, env, args):
        ans = args[0].eval(env)
        if args[1:]:
            for n in args[1:]:
                ans = ans - n.eval(env)
        else:
            # (- 5) should negate
            ans = -ans.v

        return NumberObject(ans)

    def do_div(self, env, args):
        ans = args[0].eval(env)
        if args[1:]:
            for n in args[1:]:
                ans = ans / n.eval(env)
        else:
            # (/ 2) - give inverse
            ans = 1 / ans.v

        return NumberObject(ans)

    def do_mod(self, env, args):
        ans = args[0].eval(env)
        for n in args[1:]:
            ans = ans % n.eval(env)

        return NumberObject(ans)

    def do_mul(self, env, args):
        ans = args[0].eval(env)
        for n in args[1:]:
            ans = ans * n.eval(env)

        return NumberObject(ans)

    def do_gt(self, env, args):
        if args[0].eval(env) > args[1].eval(env):
            return TRUE
        else:
            return FALSE

    def do_ge(self, env, args):
        if args[0].eval(env) >= args[1].eval(env):
            return TRUE
        else:
            return FALSE


    def do_lt(self, env, args):
        if args[0].eval(env) < args[1].eval(env):
            return TRUE
        else:
            return FALSE

    def do_le(self, env, args):
        if args[0].eval(env) <= args[1].eval(env):
            return TRUE
        else:
            return FALSE

    def do_eql(self, env, args):
        a = args[0].eval(env)
        b = args[1].eval(env)
        if isinstance(a, SymbolObject) and isinstance(b, SymbolObject):
            if a.n == b.n:
                return TRUE
            else:
                return FALSE
        else:
            if a == b:
                return TRUE
            else:
                return FALSE

    def do_neq(self, env, args):
        if args[0].eval(env) != args[1].eval(env):
            return TRUE
        else:
            return FALSE

    def do_not(self, env, args):
        return -args[0].eval(env)

    def do_and(self, env, args):
        ans = args[0].eval(env)
        for arg in args[1:]:
            ans = ans & arg.eval(env)
            # Short circuit once falsity is known.
            if ans.v == 0.0:
            #if ans.nullp():
                break

        return ans

    def do_or(self, env, args):
        truth = env.get('*true-enough*')
        ans = args[0].eval(env)
        for arg in args[1:]:
            ans = ans | arg.eval(env)
            # Short circuit once truth is known.
            if ans.v >= truth:
                break

        return ans

    # All logic in PyLisp is fuzzy.  If you only use *true* and *false*
    # then you get normal T/F logic.  Once you introduce a fuzzy logic
    # value -- such as (logic 0.34) -- then the fuzziness propagates
    # as appropriate.  The normal lisp notion that anything that isn't
    # nil is true does *not* apply to this lisp.
    def do_logic(self, env, args):
        return LogicObject(args[0].eval(env))

    def do_read(self, env, args):
        self.read(args[0].eval(env))

    # Useful for complex macros.
    def do_gensym(self, env, args):
        env.set('*gensym-counter*', env.get('*gensym-counter*') + 1)
        return SymbolObject("%s%s" % (env.get('*gensym-string*'),
                                      env.get('*gensym-counter*')))

    def do_eval(self, env, args):
        return args[0].eval(env).eval(env)

    def do_listp(self, env, args):
        if isinstance(args[0].eval(env), ListObject):
            return TRUE
        else:
            return FALSE

    def do_pairp(self, env, args):
        if isinstance(args[0].eval(env), PairObject):
            return TRUE
        else:
            return FALSE

    def do_stringp(self, env, args):
        if isinstance(args[0].eval(env), StringObject):
            return TRUE
        else:
            return FALSE

    def do_symbolp(self, env, args):
        if isinstance(args[0].eval(env), SymbolObject):
            return TRUE
        else:
            return FALSE

    def do_numberp(self, env, args):
        if isinstance(args[0].eval(env), NumberObject):
            return TRUE
        else:
            return FALSE

    def do_logicp(self, env, args):
        if isinstance(args[0].eval(env), LogicObject):
            return TRUE
        else:
            return FALSE

    def do_symbol_name(self, env, args):
        sym = args[0].eval(env)
        return StringObject(sym.n)

    def do_top_level(self, env, args):
        self.unwind_e()
        return TRUE

    def do_the_environment(self, env, args):
        return self.e

    def do_get_environment(self, env, args):
        # Yank the environment bundled up with a lambda or macro
        form = args[0].eval(env)
        if isinstance(form, LambdaObject) or isinstance(form, MacroObject):
            return form.env
        else:
            raise Error, "get-environment: must take lambda or macro"

    def do_env_get(self, env, args):
        envform = args[0].eval(env)
        if isinstance(envform, Environment):
            return envform.get(args[1].eval(env).n)
        else:
            raise Error, "env-get: must get environment as first argument"

    def do_env_set(self, env, args):
        envform = args[0].eval(env)
        if isinstance(envform, Environment):
            value = args[2].eval(env)
            envform.set(args[1].eval(env).n, value)
            return value
        else:
            raise Error, "env-set: must get environment as first argument"

    def do_put(self, env, args):
        val = args[2].eval(env)
        args[0].eval(env).put(args[1].eval(env).n, val)
        return val
        
    def do_get(self, env, args):
        return args[0].eval(env).get(args[1].eval(env).n)

    def do_elt(self, env, args):
        return args[1].eval(env)[args[0].eval(env).v]

    def do_apply(self, env, args):
        # This shuffles the args about a bit, conses the function, then evals.
        return args[1].eval(env).cons(args[0]).eval(env)
        
    def do_send(self, env, args):
        return None

    def do_py_format(self, env, args):
        eargs = []
        for arg in args[1:]:
            eargs.append(arg.eval(env))

        fmt = args[0].eval(env)
        if isinstance(fmt, StringObject):
            return fmt.string % tuple(eargs)
        elif type(fmt) == types.StringType:
            return fmt % tuple(eargs)
        else:
            raise Error, "py-format: format must be a string"

    def do_py_type(self, env, args):
        """(py-type o) - try to convert object o into its Python value"""
        # This is most useful when trying to extend PyLisp with external
        # Python capabilities.
        o = args[0].eval(env)
        if isinstance(o, NumberObject) or isinstance(o, LogicObject):
            return o.v
        elif isinstance(o, StringObject):
            return o.string
        elif isinstance(o, ListObject):
            return o.list
        else:
            return o

    def do_py_eval(self, env, args):
        """(py-eval "python code") - evaluate a python expression"""
        return eval(args[0].eval(env))

    def do_py_exec(self, env, args):
        """(py-exec "python code") - execute python code"""
        exec(args[0].eval(env))

    # MOVE THIS TO class ListObject!!!!
    def do_kw_to_pyhash(self, env, args):
        """(keyword->pyhash '(a b :text "this is cool" :rate 0.53))

        This turns Lisp-style keyword lists into a python dictionary.
        """
        hsh = {}
        margs = args[0].eval(env).list
        n = len(margs)
        i = 0
        while i < n:
            sym = margs[i]
            #print sym, sym.__class__
            if isinstance(sym, SymbolObject) and sym.n[0] == ':':
                hsh[sym.n[1:]] = margs[i + 1]
                i = i + 1
            i = i + 1

        return hsh

    # ############################################################
    # macros/syntax

    def do_m_begin(self, env, args):
        answer = FALSE
        for code in args:
            answer = code.eval(env)

        return answer

    def do_m_setq(self, env, args):
        self.intern(args[0].n, args[1].eval(env))
        return self.e.get(args[0].n)

    def do_m_let(self, env, args):
        # Transform the let into a lambda
        # (let ((x 15) (y (+ 2 3)) z) code) ==
        # ((lambda (x y z) code) 15 (+ 2 3) '())
        #          ^^^^^^^       ^^ ^^^^^^^ ^^^
        #          bindings         vallist
        bindings = args[0]
        code = args[1:]
        arglist = []
        vallist = []

        # Rip out the binding names and their initializers if they exist.
        for b in bindings:
            if isinstance(b, SymbolObject):
                # bare symbol - no initializer
                arglist.append(b)
                vallist.append(ListObject([QUOTE, ListObject([])]))
            elif isinstance(b, ListObject):
                # list form - symbol and initializer
                arglist.append(b.first())
                vallist.append(b.second())
            else:
                raise Error, "malformed (let ...)"

        # Pull the whole mess together into the lambda form, then eval.
        return ListObject([ListObject([SymbolObject('lambda'), 
                                       ListObject(arglist)] + code)] +
                          vallist).eval(env)

    def do_m_lambda(self, env, args):
        # (lambda (x y z) (* x y z))
        if self.e == env.get('*env*'):
            #print "NULL DEFINED ENV"
            return LambdaObject(args[0], args[1:], None)
        else:
            #print "LEXICALLY DEFINED ENV"
            return LambdaObject(args[0], args[1:], env)

    def do_m_macro(self, env, args):
        # (def incq (macro (x) `(setq ,x (+ ,x 1)))
        if self.e == env.get('*env*'):
            #print "NULL DEFINED ENV"
            return MacroObject(args[0], args[1:], None)
        else:
            #print "LEXICALLY DEFINED ENV"
            return MacroObject(args[0], args[1:], env)

    def do_m_macro_expand(self, env, args):
        # Grab the first/only argument, pull out the first element of
        # that list and eval it -- it is a symbol which had better
        # resolve to a macro -- expand with the rest of its arguments,
        # which have to be ripped out of the argument list to trick
        # the expand method into looking like an eval call.  Return
        # the result, which is a list of PyLisp code.
        return args[0].first().eval(env).expand(env, args[0].rest())

    def do_m_quote(self, env, args):
        return args[0]

    def do_m_iquote(self, env, args):
        if isinstance(args[0], ListObject):
            return args[0].iquote(env)
        else:
            return args[0]

    def do_m_if(self, env, args):
        bool = args[0].eval(env)
        if isinstance(bool, LogicObject):
            if bool >= env.get('*true-enough*'):
                return args[1].eval(env)
            else:
                if len(args) == 3:
                    return args[2].eval(env)
                else:
                    return bool
        elif hasattr(bool, 'nullp'):
            # Null is false.
            #print "hasattr nullp"
            if args[0].eval(env).nullp() == TRUE:
                if len(args) == 3:
                    return args[2].eval(env)
                else:
                    return bool
            else:
                return args[1].eval(env)
        else:
            # This is also testing for the false case.
            if bool in [0, 0.0, ""]:
                if len(args) == 3:
                    return args[2].eval(env)
                else:
                    return bool
            else:
                return args[1].eval(env)

    def do_m_cond(self, env, args):
        # (cond (test0 return0)
        #       (test1 return1)
        #       (*true* returnt) )
        for clause in args:
            bool = clause.first().eval(env)
            if isinstance(bool, LogicObject):
                if bool >= env.get('*true-enough*'):
                    return clause.second().eval(env)
            elif hasattr(bool, 'nullp'):
                # Null is false.
                #print "hasattr nullp"
                if bool.nullp() == TRUE:
                    pass
                else:
                    return clause.second().eval(env)
            else:
                # This is also testing for the false case.
                if bool in [0, 0.0, ""]:
                    pass
                else:
                    return clause.second().eval(env)
    
        return FALSE

    def do_m_with_hash(self, env, args):
        # (with-py-hash-env some-hash-table ...)
        hsh = args[0].eval(env)

        # Set up the new environment.
        self.push_e()
        # Intern the new values.
        for (key, value) in hsh.items():
            if type(value) == types.StringType:
                self.intern(key, value)
            else:
                self.intern(key, self.r.get_sexpr(`value`))

        # Eval the code.
        for code in args[1:]:
            answer = code.eval(env)

        # Pop off the hash-table environemt.
        self.pop_e()

        # Return final form value?  Perhaps this should return the final
        # environment somehow, too?  Or require this:
        #   (with-py-has-env some-hash
        #     ...
        #     ...
        #     (the-environment))
        return answer


if __name__ == '__main__':
    tests = ['(a b c)',
             '(a (b c) d e)',
             '(a "b whaoo" c)',
             'freddie',
             "'frood",
             '(a (b (c (d (e (f (g)))))))',
             "(a 'froo b)",
             "(rule sec-1 (if (> load 1.5) (== host 'wazor) then (boo)))"
             ]

    g = Reader()
    #for test in tests:
    #    print test, ":", g.get_sexpr(test)

    eval_tests = ['(+ 5 3)',
                  '(+ 5 2.3 2.7)',
                  '(+ 5 (* 2 6.55))',
                  '(* 5 (+ 3 4 6) 22 (* 2.4 5 0.001) (- 5 (+ 2 (- 2 4))))',
                  "'(+ 5 3)",
                  "'a",
                  """'(this is "cool")""",
                  "(print 'wow)",
                  """(print "wow")""",
                  "(first '(a b c))",
                  "(rest '(a b c))",
                  "(cons 'a '(b c d))",
                  "(append '(a b c) '(d e f) (list 1 2 3 4))",
                  "(setq fred '(a b c))",
                  "(rest fred)",
                  "(put 'fred 'birthday 'june-12-1973)",
                  "(get 'fred 'birthday)",
                  "(logic 0.5)",
                  "(logic 1.0)",
                  "(not (logic 0.0))",
                  "(not (logic 0.35))",
                  "(and *true* (not *true*))",
                  "(or *true* (not *true*))",
                  "(setq *true* (logic .95))",
                  "(and *true* (not *true*))",
                  "(or *true* (not *true*))",
                  "(setq *true* (logic 1.0))",
                  "(> 5 2)", "(> 2 5)",
                  "(> 5 (* 3 (+ 2 1)))",
                  "(> (* 3 (+ 2 1)) (+ 1 2 3))",
                  '(== "wow" "fred")',
                  '(!= "wow" "fred")',
                  "(>= 5 5)",
                  '(<= "andy" "bobbie")',
                  "(if (> 5 2) 'true 'false)",
                  "(if (< 5 2) 'true 'false)",
                  "(if (< 5 2) 'true)",
                  "(if (not (< 5 2)) 'true)",
                  "(lambda (x y) (* x y))",
                  "((lambda (x y) (* x y)) 5 2)",
                  "(lambda (x y) (* x y) (+ x y))",
                  "((lambda (x y) (* x y) (+ x y)) 5 2)",
                  "(def mult (lambda (x y) (* x y)))",
                  "(mult 5 7)",
                  "(def dumb (lambda (x y) (if (> x y) (* x y) (/ x y))))",
                  "(dumb 5.0 3.0)",
                  "(dumb 3.0 5.0)",
                  "(let ((x 5) (y 3)) (+ x y))",
                  "(let ((x 5) (y 3) z) (+ x y))",
                  "(def dumb (lambda (x) (let ((y 12)) (* x y))))",
                  "(dumb 3)",
                  "`a",
                  "`(a b ,fred)",
                  "`(a b ,@fred)",
                  "`(a (b (c (d (e (f ,@fred))))))",
                  "((macro (x) `(+ ,x 5)) 4)",
                  "(def incf (macro (x) `(setq ,x (+ ,x 1))))",
                  "(setq whee 33)",
                  "(incf whee)",
                  "(print whee)",
                  "(def foo (lambda (x y) (if (<= y 0) x (begin (print x y (<= y 0)) (foo (cons y x) (- y 1))))))",
                  "(foo '() 12)",
                  "(let ((x 5)) (def bar (lambda () x)))",
                  "(bar)",
                  "(env-set (get-environment bar) 'x 33)",
                  "(bar)",
                  "(setq wow (list (cons 'a 'b) (cons 'q 'fun)))",
                  "(assoc 'a wow)"
                  ]
    l = Lisper()
    for test in eval_tests:
        print test, ":", l.eval(g.get_sexpr(test))

    l.repl()

# EOF
