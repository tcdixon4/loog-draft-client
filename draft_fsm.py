#!/usr/bin/env python

# python has a FSM library
from fysom import *

# don't think I need any random library
import random
import types


#This module implements a Finite State Machine (FSM) to control the drafting procedure for the 
#League of Ordinary Gentlemen (LoOG) fantasy football group. 
#
#This FSM shall contain a data member that is populated with every eligible NFL fantasy player. As 
#players are drafted, they will be removed from this data member.
#
#Each team will be a data class that will populate it's sub fields with drafted players
#
#
#------------------------------------------------------------------------------------------
#|      STATES      |      NEXT_STATE        |                Transistion                 |
#------------------------------------------------------------------------------------------
#| GET_NEXT_DRAFTER |       DRAFTING         |           When drafter is received         |
#|                  |                        |                                            |
#|    DRAFTING      |    GET_NEXT_DRAFTER    |   When valid draft choice is received OR   |
#|                  |                        |   when timeout is reached.                 |
#------------------------------------------------------------------------------------------

__author__ = 'Daniel Kuiper'
__copyright__ = 'Copyright 2018, Daniel Kuiper'
__credits__ = ['Daniel Kuiper']
__license__ = 'MIT'
__version__ = '1.0'
__maintainer__ = 'Daniel Kuiper'
__email__ = 'dkuiper21@gmail.com'







# this is a fairly complicated framework for a simple problem but it's a learning experience 
# for python's fsm library

# create fsm with 2 states, get_next_drafter and drafting. 
# fsm.get_next will return the team to draft
# fsm.timeout will autodraft (or drop) and move to next drafter
# fsm.draft will draft and move to next drafter
fsm = Fysom({
  # 'initial' describes the initial state
  'initial': 'get_next_drafter',
  # 'events' describes functions and how they will transition from state to state
  'events':[
    {'name': 'get_next', 'src': 'get_next_drafter', 'dst': 'drafting'},
    {'name': 'timeout',  'src': 'drafting',         'dst': 'get_next_drafter'},
    {'name': 'draft',    'src': 'drafting',         'dst': 'get_next_drafter'},
    ]
  })

# traverse all paths and print for debug
print(fsm.current)
fsm.get_next()
print(fsm.current)
fsm.timeout()
print(fsm.current)
fsm.get_next()
print(fsm.current)
fsm.draft()
print(fsm.current)
