#    This file is part of EAP.
#
#    EAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    EAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with EAP. If not, see <http://www.gnu.org/licenses/>.

import random
import operator
import csv
import itertools
import numpy
import difflib
import functools
from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp
# import ui

# Read the spam list features and put it in a list of lists.
# The dataset is from http://archive.ics.uci.edu/ml/datasets/Spambase
# This example is a copy of the OpenBEAGLE example :
# http://beagle.gel.ulaval.ca/refmanual/beagle/html/d2/dbe/group__Spambase.html
# with open("spambase.csv") as spambase:
#     spamReader = csv.reader(spambase)
#     spam = list(list(float(elem) for elem in row) for row in spamReader)

# defined a new primitive set for strongly typed GP
global result_program 
result_program = set([])
pset = gp.PrimitiveSetTyped("MAIN", [list, list], list)

# boolean operators
pset.addPrimitive(operator.and_, [bool, bool], bool)
pset.addPrimitive(operator.or_, [bool, bool], bool)
pset.addPrimitive(operator.not_, [bool], bool)
# pset.addTerminal("mylambda", str)
# pset.addTerminal("length", str)
# pset.addTerminal("reverse", str)
# pset.addTerminal("concat", str)
# pset.addTerminal("delete", str)
# pset.addTerminal("split", str)
# pset.addTerminal("mysum", str)
# pset.addTerminal("find", str)
# pset.addTerminal("maximum", str)
# pset.addTerminal("minimum", str)
# pset.addTerminal("addn", str)
# pset.addTerminal("if_then_else", str)
# pset.addTerminal("gt", str)
# pset.addTerminal("lt", str)
# pset.addTerminal("equal", str)
# pset.addTerminal("hd", str)
# pset.addTerminal("tl", str)


# pset.addTerminal(1, int)
# pset.addTerminal(2, int)
# pset.addTerminal(3, int)
# pset.addTerminal(4, int)
# pset.addTerminal(5, int)
# pset.addTerminal(6, int)
# pset.addTerminal(7, int)
# pset.addTerminal(8, int)
# pset.addTerminal(9, int)
# pset.addTerminal(10, int)
pset.addTerminal(False, bool)
pset.addTerminal(True, bool)

# floating point operators
# Define a protected division function
def protectedDiv(left, right):
    try: return left / right
    except ZeroDivisionError: return 1

def length(mylist):
	return len(mylist)

def reverse(mylist):
	mylist.reverse()
	return mylist

def concat(mylist1, mylist2):
	return mylist1 + mylist2

def delete(mylist1, mylist2):
	for item in mylist2:
		try:
			mylist1.remove(item)
		except:
			continue
	return mylist1

def split(mylist, index):
	return [mylist[0:index-1], mylist[index:]]

def mysum(mylist):
	s = 0;
	for item in mylist:
		s += item
	return s

def find(mylist, index):
	return mylist[index-1]

def maximum(mylist):
	a = mylist[0]
	for item in mylist:
		if (item > a):
			a = item
	return a

def minimum(mylist):
	a = mylist[0]
	for item in mylist:
		if (item < a):
			a = item
	return a

def addn(mylist, number):
	mylist.append(number)
	return mylist

def if_then_else(condition, output1, output2):
	if (condition):
		return output1
		# try:
		# 	eval(output1)
		# except:
		# 	return output1
	else:
		return output2
		# try:
		# 	eval(output2)
		# except:
		# 	return output2

def gt (number1, number2):
	if (number1 > number2):
		return True;
	else:
		return False

def lt (number1, number2):
	if (number1 < number2):
		return True
	else:
		return False;

def equal (number1, number2):
	if (number1 == number2):
		return True;
	else:
		return False;

def hd (mylist):
	ret = []
	ret[0] = mylist[0]
	return ret

def tl (mylist):
	return list(mylist[1:])

# def mylambda (func, list1, list2): 
# 	return  eval(func)(list1, list2)





# def equals()

# def intersection(mylist1, mylist2):





pset.addPrimitive(operator.add, [int,int], int)
pset.addPrimitive(operator.sub, [int,int], int)
pset.addPrimitive(operator.mul, [int,int], int)
pset.addPrimitive(protectedDiv, [int,int], float)
pset.addPrimitive(length, [list], int)
pset.addPrimitive(reverse, [list], list)
pset.addPrimitive(concat, [list, list], list)
pset.addPrimitive(delete, [list, list], list)
pset.addPrimitive(find, [list, int], int)
pset.addPrimitive(maximum, [list], int)
pset.addPrimitive(minimum, [list], int)
pset.addPrimitive(addn, [list, int], int)
pset.addPrimitive(if_then_else, [bool, list, list], list)
pset.addPrimitive(if_then_else, [bool, int, int], int)
pset.addPrimitive(if_then_else, [bool, float, float], float)
# pset.addPrimitive(mylambda, [str, list, list], list)
pset.addPrimitive(gt, [int, int], bool)
pset.addPrimitive(lt, [int, int], bool)
pset.addPrimitive(hd, [list], list)
pset.addPrimitive(tl, [list], list)


# pset.addPrimitive(split, [list, int], list)


# List
#   length
#   reverse
#   add
#   concat
#   delete
#   split
# Integer

# example


# logic operators
# Define a new if-then-else function
# def if_then_else(input, output1, output2):
#     if input: return output1
#     else: return output2

# pset.addPrimitive(operator.lt, [float, float], bool)
# pset.addPrimitive(operator.eq, [float, float], bool)
# pset.addPrimitive(if_then_else, [bool, float, float], float)

# terminals
# pset.addEphemeralConstant("rand100", lambda: random.random() * 100, float)
# pset.addTerminal(False, bool)
# pset.addTerminal(True, bool)
pset.renameArguments(ARG0='x')
pset.renameArguments(ARG1='y')


creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=2)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)

def parsedata ():
	result = [[]]
	example = open("example", "rw+")
	while (1):
		a = example.readline()
		if (a != "" and a[0] != '#'):
			each = []
			i = a.split("->")[0]
			o = a.split("->")[1]
			each.append(i.split(" ")[0])
			each.append(i.split(" ")[1])
			each.append(o.rstrip())
			result.append(each)
		else:
			break
	return result



def evalSpambase(individual):
    # Transform the tree expression in a callable function
    # print individual
    func = toolbox.compile(expr=individual)
    # print func
    example = parsedata()
    example.remove([])
    list_sm = []
    for item in example:
    	args1 = eval(item[0])
    	args2 = eval(item[1])
    	try:
        	sm = difflib.SequenceMatcher(None, func(args1, args2), eval(item[2])).ratio()
        	list_sm.append(sm)
    	except:
    		continue
        	
    # fitness = 0.0
    fitness = 0
    if (list_sm == []):
    	# print 0
    	return 0,
    else:
	    for item in list_sm:
	    	fitness += item
	    # print fitness/len(list_sm)
	    if (abs(fitness/len(list_sm) - 1) < 0.001):
	    	result_program.add(str(individual))
	    	# print result_program
	    	# print "YAHOO"
	    return fitness/len(list_sm),


    # sm=difflib.SequenceMatcher(None,s1,s2)
    # sqerrors = 0
    # sqerrors += ((func(eval(item[0]),eval(item[1])) - item[2] )**2 for item in example)
    # return math.fsum(sqerrors) / len(example),

    # example

    # Randomly sample 400 mails in the spam database
    # spam_samp = random.sample(spam, 400)
    # # Evaluate the sum of correctly identified mail as spam
    # result = sum(bool(func(*mail[:57])) is bool(mail[57]) for mail in spam_samp)

    # return result,

toolbox.register("evaluate", evalSpambase)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

def main():
    random.seed(10)
    pop = toolbox.population(n=1000)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    algorithms.eaSimple(pop, toolbox, 0.5, 0.2, 10, stats, halloffame=hof)
    # print result_program
    return result_program

if __name__ == "__main__":
    main()
    output = sorted(list(result_program), key=len)

    print output[0:100]
