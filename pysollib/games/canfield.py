## vim:ts=4:et:nowrap
##
##---------------------------------------------------------------------------##
##
## PySol -- a Python Solitaire game
##
## Copyright (C) 2000 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1999 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1998 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1998 Andrew Csillag <drew_csillag@geocities.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; see the file COPYING.
## If not, write to the Free Software Foundation, Inc.,
## 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
## Markus F.X.J. Oberhumer
## <markus@oberhumer.com>
## http://www.oberhumer.com/pysol
##
##---------------------------------------------------------------------------##

__all__ = []

# imports
import sys

# PySol imports
from pysollib.gamedb import registerGame, GameInfo, GI
from pysollib.util import *
from pysollib.stack import *
from pysollib.game import Game
from pysollib.layout import Layout
from pysollib.hint import AbstractHint, DefaultHint, CautiousDefaultHint
from pysollib.pysoltk import MfxCanvasText

# /***********************************************************************
# //
# ************************************************************************/

class Canfield_Hint(CautiousDefaultHint):
    # FIXME: demo is not too clever in this game

    # Score for moving a pile (usually a single card) from the WasteStack.
    def _getMoveWasteScore(self, score, color, r, t, pile, rpile):
        score, color = CautiousDefaultHint._getMovePileScore(self, score, color, r, t, pile, rpile)
        # we prefer moving cards from the waste over everything else
        return score + 100000, color


# /***********************************************************************
# // a Canfield row stack only accepts a full other row stack
# // (cannot move part of a sequence from row to row)
# ************************************************************************/

class Canfield_AC_RowStack(AC_RowStack):
    def basicAcceptsCards(self, from_stack, cards):
        if from_stack in self.game.s.rows:
            if len(cards) != 1 and len(cards) != len(from_stack.cards):
                return 0
        return AC_RowStack.basicAcceptsCards(self, from_stack, cards)


class Canfield_SS_RowStack(SS_RowStack):
    def basicAcceptsCards(self, from_stack, cards):
        if from_stack in self.game.s.rows:
            if len(cards) != 1 and len(cards) != len(from_stack.cards):
                return 0
        return SS_RowStack.basicAcceptsCards(self, from_stack, cards)


class Canfield_RK_RowStack(RK_RowStack):
    def basicAcceptsCards(self, from_stack, cards):
        if from_stack in self.game.s.rows:
            if len(cards) != 1 and len(cards) != len(from_stack.cards):
                return 0
        return RK_RowStack.basicAcceptsCards(self, from_stack, cards)


# /***********************************************************************
# // Canfield
# ************************************************************************/

class Canfield(Game):
    Foundation_Class = SS_FoundationStack
    RowStack_Class = StackWrapper(Canfield_AC_RowStack, mod=13)
    ReserveStack_Class = OpenStack
    Hint_Class = Canfield_Hint

    INITIAL_RESERVE_CARDS = 13
    INITIAL_RESERVE_FACEUP = 0
    FILL_EMPTY_ROWS = 1

    #
    # game layout
    #

    def createGame(self, rows=4, max_rounds=-1, num_deal=3, text=True):
        # create layout
        l, s = Layout(self), self.s
        decks = self.gameinfo.decks

        # set window
        # (piles up to 20 cards are playable in default window size)
        h = max(3*l.YS, l.YS+self.INITIAL_RESERVE_CARDS*l.YOFFSET)
        self.setSize(l.XM + (2+max(rows, 4*decks))*l.XS + l.XM, l.YM + l.YS + 20 + h)

        # extra settings
        self.base_card = None

        # create stacks
        x, y = l.XM, l.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=max_rounds, num_deal=num_deal)
        l.createText(s.talon, "s")
        x = x + l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, "s")
        x = x + l.XM
        for i in range(4):
            for j in range(decks):
                x = x + l.XS
                s.foundations.append(self.Foundation_Class(x, y, self, i, mod=13, max_move=0))
        if text:
            if rows >= 4 * decks:
                tx, ty, ta, tf = l.getTextAttr(None, "se")
                tx, ty = x + tx + l.XM, y + ty
            else:
                tx, ty, ta, tf = l.getTextAttr(None, "s")
                tx, ty = x + tx, y + ty + l.YM
            font = self.app.getFont("canvas_default")
            self.texts.info = MfxCanvasText(self.canvas, tx, ty, anchor=ta, font=font)
        x, y = l.XM, l.YM + l.YS + 20
        s.reserves.append(self.ReserveStack_Class(x, y, self))
        if self.INITIAL_RESERVE_FACEUP == 1:
            s.reserves[0].CARD_YOFFSET = l.YOFFSET ##min(l.YOFFSET, 14)
        else:
            s.reserves[0].CARD_YOFFSET = 10
        x = l.XM + 2 * l.XS + l.XM
        for i in range(rows):
            s.rows.append(self.RowStack_Class(x, y, self))
            x = x + l.XS

        # define stack-groups
        l.defaultStackGroups()

    #
    # game extras
    #

    def updateText(self):
        if self.preview > 1:
            return
        if not self.texts.info:
            return
        if not self.base_card:
            t = ""
        else:
            t = RANKS[self.base_card.rank]
        self.texts.info.config(text=t)

    #
    # game overrides
    #

    def startGame(self):
        self.startDealSample()
        self.base_card = None
        self.updateText()
        # deal base_card to Foundations, update foundations cap.base_rank
        self.base_card = self.s.talon.getCard()
        for s in self.s.foundations:
            s.cap.base_rank = self.base_card.rank
        n = self.base_card.suit * self.gameinfo.decks
        if self.s.foundations[n].cards:
            assert self.gameinfo.decks > 1
            n = n + 1
        self.flipMove(self.s.talon)
        self.moveMove(1, self.s.talon, self.s.foundations[n])
        self.updateText()
        # fill the Reserve
        for i in range(self.INITIAL_RESERVE_CARDS):
            if self.INITIAL_RESERVE_FACEUP:
                self.flipMove(self.s.talon)
            self.moveMove(1, self.s.talon, self.s.reserves[0], frames=4, shadow=0)
        if self.s.reserves[0].canFlipCard():
            self.flipMove(self.s.reserves[0])
        self.s.talon.dealRow(reverse=1)
        self.s.talon.dealCards()          # deal first 3 cards to WasteStack

    def fillStack(self, stack):
        if stack in self.s.rows and self.s.reserves:
            if self.FILL_EMPTY_ROWS:
                if not stack.cards and self.s.reserves[0].cards:
                    if not self.s.reserves[0].cards[-1].face_up:
                        self.s.reserves[0].flipMove()
                    self.s.reserves[0].moveMove(1, stack)
        elif stack in self.s.reserves:
            if stack.canFlipCard():
                stack.flipMove()

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.color != card2.color and
                ((card1.rank + 1) % 13 == card2.rank or (card2.rank + 1) % 13 == card1.rank))

    def _restoreGameHook(self, game):
        self.base_card = self.cards[game.loadinfo.base_card_id]
        for s in self.s.foundations:
            s.cap.base_rank = self.base_card.rank

    def _loadGameHook(self, p):
        self.loadinfo.addattr(base_card_id=None)    # register extra load var.
        self.loadinfo.base_card_id = p.load()

    def _saveGameHook(self, p):
        p.dump(self.base_card.id)


# /***********************************************************************
# // Superior Canfield
# ************************************************************************/

class SuperiorCanfield(Canfield):
    INITIAL_RESERVE_FACEUP = 1
    FILL_EMPTY_ROWS = 0


# /***********************************************************************
# // Rainfall
# ************************************************************************/

class Rainfall(Canfield):
    def createGame(self):
        Canfield.createGame(self, max_rounds=3, num_deal=1)


# /***********************************************************************
# // Rainbow
# ************************************************************************/

class Rainbow(Canfield):
    RowStack_Class = StackWrapper(Canfield_RK_RowStack, mod=13)

    def createGame(self):
        Canfield.createGame(self, max_rounds=1, num_deal=1)


# /***********************************************************************
# // Storehouse (aka Straight Up)
# ************************************************************************/

class Storehouse(Canfield):
    RowStack_Class = StackWrapper(Canfield_SS_RowStack, mod=13)

    def createGame(self):
        Canfield.createGame(self, max_rounds=3, num_deal=1)

    def _shuffleHook(self, cards):
        # move Twos to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(cards, lambda c: (c.rank == 1, c.suit))

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations[:3])
        Canfield.startGame(self)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit == card2.suit and
                ((card1.rank + 1) % 13 == card2.rank or (card2.rank + 1) % 13 == card1.rank))

    def updateText(self):
        pass


# /***********************************************************************
# // Chameleon (aka Kansas)
# ************************************************************************/

class Chameleon(Canfield):
    RowStack_Class = StackWrapper(Canfield_RK_RowStack, mod=13)

    INITIAL_RESERVE_CARDS = 12

    def createGame(self):
        Canfield.createGame(self, rows=3, max_rounds=1, num_deal=1)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return ((card1.rank + 1) % 13 == card2.rank or (card2.rank + 1) % 13 == card1.rank)


# /***********************************************************************
# // Double Canfield (Canfield with 2 decks and 5 rows)
# ************************************************************************/

class DoubleCanfield(Canfield):
    def createGame(self):
        Canfield.createGame(self, rows=5)


# /***********************************************************************
# // American Toad
# ************************************************************************/

class AmericanToad(Canfield):
    RowStack_Class = StackWrapper(Canfield_SS_RowStack, mod=13)

    INITIAL_RESERVE_CARDS = 20
    INITIAL_RESERVE_FACEUP = 1

    def createGame(self):
        Canfield.createGame(self, rows=8, max_rounds=2, num_deal=1)


# /***********************************************************************
# // Variegated Canfield
# ************************************************************************/

class VariegatedCanfield(Canfield):
    RowStack_Class = Canfield_AC_RowStack

    INITIAL_RESERVE_FACEUP = 1

    def createGame(self):
        Canfield.createGame(self, rows=5, max_rounds=3)

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(cards, lambda c: (c.rank == 0, c.suit))

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations[:7])
        Canfield.startGame(self)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.color != card2.color and
                ((card1.rank + 1) == card2.rank or (card2.rank + 1) == card1.rank))

    def updateText(self):
        pass


# /***********************************************************************
# // Eagle Wing
# ************************************************************************/

class EagleWing_ReserveStack(OpenStack):
    def canFlipCard(self):
        return len(self.cards) == 1 and not self.cards[-1].face_up


class EagleWing(Canfield):
    RowStack_Class = StackWrapper(SS_RowStack, mod=13, max_move=1, max_cards=3)
    ReserveStack_Class = EagleWing_ReserveStack

    def createGame(self):
        ##Canfield.createGame(self, rows=8, max_rounds=3, num_deal=1)
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + 9*l.XS + l.XM, l.YM + 4*l.YS)

        # extra settings
        self.base_card = None

        # create stacks
        x, y = l.XM, l.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=3, num_deal=1)
        l.createText(s.talon, "ss")
        x = x + l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, "ss")
        for i in range(4):
            x = l.XM + (i+3)*l.XS
            s.foundations.append(self.Foundation_Class(x, y, self, i, mod=13, max_move=0))
        tx, ty, ta, tf = l.getTextAttr(None, "se")
        tx, ty = x + tx + l.XM, y + ty
        font = self.app.getFont("canvas_default")
        self.texts.info = MfxCanvasText(self.canvas, tx, ty, anchor=ta, font=font)
        ry = l.YM + 2*l.YS
        for i in range(8):
            x = l.XM + (i + (i >= 4))*l.XS
            y = ry - (0.2, 0.4, 0.6, 0.4, 0.4, 0.6, 0.4, 0.2)[i]*l.CH
            s.rows.append(self.RowStack_Class(x, y, self))
        x, y = l.XM + 4*l.XS, ry
        s.reserves.append(self.ReserveStack_Class(x, y, self))
        ##s.reserves[0].CARD_YOFFSET = 0
        l.createText(s.reserves[0], "ss")

        # define stack-groups
        l.defaultStackGroups()


# /***********************************************************************
# // Gate
# // Little Gate
# ************************************************************************/

class Gate(Game):

    #
    # game layout
    #

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = l.XM+max(8*l.XS, 6*l.XS+8*l.XOFFSET), l.YM+3*l.YS+12*l.YOFFSET
        self.setSize(w, h)

        # create stacks
        y = l.YM
        for x in (l.XM+(w-(l.XM+8*l.XS))/2, w-l.XS-4*l.XOFFSET):
            stack = OpenStack(x, y, self, max_accept=0)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = l.XOFFSET, 0
            s.reserves.append(stack)
        x, y = l.XM+2*l.XS, l.YM
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i))
            x += l.XS
        x, y = l.XM, l.YM+l.YS
        for i in range(8):
            s.rows.append(AC_RowStack(x, y, self))
            x += l.XS
        s.talon = WasteTalonStack(l.XM, h-l.YS, self, max_rounds=1)
        l.createText(s.talon, "n")
        s.waste = WasteStack(l.XM+l.XS, h-l.YS, self)
        l.createText(s.waste, "n")

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self):
        for i in range(5):
            self.s.talon.dealRow(rows=self.s.reserves, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()

    def fillStack(self, stack):
        r1, r2 = self.s.reserves
        if stack in self.s.rows and not stack.cards:
            from_stack = None
            if r1.cards or r2.cards:
                from_stack = r1
                if len(r1.cards) < len(r2.cards):
                    from_stack = r2
            elif self.s.waste.cards:
                from_stack = self.s.waste
            if from_stack:
                from_stack.moveMove(1, stack)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.color != card2.color and
                abs(card1.rank-card2.rank) == 1)


class LittleGate(Gate):

    #
    # game layout
    #

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = l.XM+7*l.XS, l.YM+2*l.YS+12*l.YOFFSET
        self.setSize(w, h)

        # create stacks
        y = 4*l.YM+l.YS
        for x in (l.XM, w-l.XS):
            stack = OpenStack(x, y, self, max_accept=0)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, l.YOFFSET
            s.reserves.append(stack)
        x, y = l.XM+3*l.XS, l.YM
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i))
            x += l.XS
        x, y = int(l.XM+1.5*l.XS), 4*l.YM+l.YS
        for i in range(4):
            s.rows.append(AC_RowStack(x, y, self))
            x += l.XS
        s.talon = WasteTalonStack(l.XM, l.YM, self, max_rounds=1)
        l.createText(s.talon, "s")
        s.waste = WasteStack(l.XM+l.XS, l.YM, self)
        l.createText(s.waste, "s")

        # define stack-groups
        l.defaultStackGroups()


# /***********************************************************************
# // Munger
# ************************************************************************/

class Munger(Canfield):

    RowStack_Class = StackWrapper(AC_RowStack, base_rank=KING)

    FILL_EMPTY_ROWS = 0

    def createGame(self):
        Canfield.createGame(self, rows=7, max_rounds=1, num_deal=1)

    def startGame(self):
        self.s.talon.dealRow(frames=0, flip=0)
        self.s.talon.dealRow(frames=0)
        self.s.talon.dealRow(frames=0, flip=0)
        self.startDealSample()
        self.s.talon.dealRow()
        for i in range(7):
            self.moveMove(1, self.s.talon, self.s.reserves[0], frames=4, shadow=0)
        self.flipMove(self.s.reserves[0])
        self.s.talon.dealCards()

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.color != card2.color and
                abs(card1.rank-card2.rank) == 1)

    def _restoreGameHook(self, game):
        pass
    def _loadGameHook(self, p):
        pass
    def _saveGameHook(self, p):
        pass


# /***********************************************************************
# // Triple Canfield
# ************************************************************************/

class TripleCanfield(Canfield):
    INITIAL_RESERVE_CARDS = 26
    def createGame(self):
        Canfield.createGame(self, rows=7)


# /***********************************************************************
# // Acme
# ************************************************************************/

class Acme(Canfield):
    Foundation_Class = SS_FoundationStack
    RowStack_Class = StackWrapper(SS_RowStack, max_move=1)
    Hint_Class = Canfield_Hint

    def createGame(self):
        Canfield.createGame(self, max_rounds=2, num_deal=1)

    def _shuffleHook(self, cards):
        # move Aces to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(cards, lambda c: (c.rank == 0, c.suit))

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        self.startDealSample()
        for i in range(13):
            self.moveMove(1, self.s.talon, self.s.reserves[0], frames=4, shadow=0)
        self.flipMove(self.s.reserves[0])
        self.s.talon.dealRow(reverse=1)
        self.s.talon.dealCards()

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit == card2.suit and
                abs(card1.rank-card2.rank) == 1)

    def updateText(self):
        pass
    def _restoreGameHook(self, game):
        pass
    def _loadGameHook(self, p):
        pass
    def _saveGameHook(self, p):
        pass


# /***********************************************************************
# // Duke
# ************************************************************************/

class Duke(Game):

    def createGame(self):
        l, s = Layout(self), self.s

        w, h = l.XM+6*l.XS+4*l.XOFFSET, l.YM+2*l.YS+12*l.YOFFSET
        self.setSize(w, h)

        x, y = l.XM, l.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=3)
        l.createText(s.talon, 's')
        x += l.XS
        s.waste = WasteStack(x, y, self)
        l.createText(s.waste, 's')
        x += l.XS+4*l.XOFFSET
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i))
            x += l.XS
        x0, y0, w = l.XM, 3*l.YM+l.YS, l.XS+2*l.XOFFSET
        for i, j in ((0,0), (0,1), (1,0), (1,1)):
            x, y = x0+i*w, y0+j*l.YS
            stack = OpenStack(x, y, self, max_accept=0)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = l.XOFFSET, 0
            s.reserves.append(stack)
        x, y = l.XM+2*l.XS+4*l.XOFFSET, l.YM+l.YS
        for i in range(4):
            s.rows.append(AC_RowStack(x, y, self))
            x += l.XS

        l.defaultStackGroups()


    def startGame(self):
        for i in range(3):
            self.s.talon.dealRow(rows=self.s.reserves, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()


    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.color != card2.color and
                abs(card1.rank-card2.rank) == 1)


# /***********************************************************************
# // Minerva
# ************************************************************************/

class Minerva(Canfield):
    RowStack_Class = StackWrapper(AC_RowStack, base_rank=KING)

    INITIAL_RESERVE_CARDS = 11
    INITIAL_RESERVE_FACEUP = 1
    FILL_EMPTY_ROWS = 0

    def createGame(self):
        Canfield.createGame(self, rows=7, max_rounds=2, num_deal=1, text=False)

    def startGame(self):
        for i in range(self.INITIAL_RESERVE_CARDS):
            self.flipMove(self.s.talon)
            self.moveMove(1, self.s.talon, self.s.reserves[0], frames=0, shadow=0)
        flip = False
        for i in range(3):
            self.s.talon.dealRow(flip=flip, frames=0)
            flip = not flip
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()



# register the game
registerGame(GameInfo(105, Canfield, "Canfield",                # was: 262
                      GI.GT_CANFIELD | GI.GT_CONTRIB, 1, -1))
registerGame(GameInfo(101, SuperiorCanfield, "Superior Canfield",
                      GI.GT_CANFIELD, 1, -1))
registerGame(GameInfo(99, Rainfall, "Rainfall",
                      GI.GT_CANFIELD | GI.GT_ORIGINAL, 1, 2))
registerGame(GameInfo(108, Rainbow, "Rainbow",
                      GI.GT_CANFIELD, 1, 0))
registerGame(GameInfo(100, Storehouse, "Storehouse",
                      GI.GT_CANFIELD, 1, 2,
                      altnames=("Provisions", "Straight Up", "Thirteen Up") ))
registerGame(GameInfo(43, Chameleon, "Chameleon",
                      GI.GT_CANFIELD, 1, 0,
                      altnames="Kansas"))
registerGame(GameInfo(106, DoubleCanfield, "Double Canfield",   # was: 22
                      GI.GT_CANFIELD, 2, -1))
registerGame(GameInfo(103, AmericanToad, "American Toad",
                      GI.GT_CANFIELD, 2, 1))
registerGame(GameInfo(102, VariegatedCanfield, "Variegated Canfield",
                      GI.GT_CANFIELD, 2, 2))
registerGame(GameInfo(112, EagleWing, "Eagle Wing",
                      GI.GT_CANFIELD, 1, 2))
registerGame(GameInfo(315, Gate, "Gate",
                      GI.GT_CANFIELD, 1, 0))
registerGame(GameInfo(316, LittleGate, "Little Gate",
                      GI.GT_CANFIELD, 1, 0))
registerGame(GameInfo(360, Munger, "Munger",
                      GI.GT_CANFIELD, 1, 0))
registerGame(GameInfo(396, TripleCanfield, "Triple Canfield",
                      GI.GT_CANFIELD, 3, -1))
registerGame(GameInfo(403, Acme, "Acme",
                      GI.GT_CANFIELD, 1, 1))
registerGame(GameInfo(413, Duke, "Duke",
                      GI.GT_CANFIELD, 1, 2))
registerGame(GameInfo(422, Minerva, "Minerva",
                      GI.GT_CANFIELD, 1, 1))

