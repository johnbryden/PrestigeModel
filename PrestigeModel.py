#!/usr/bin/python3 -u
# Copyright John Bryden under GPL3 license 
#
# However, don't publish any version of this code, any results
# generated using this code, or the underlying model, without my
# permission.

from pylab import *
from collections import namedtuple,Counter
import sys
import argparse
import random
import pickle

# We need some Gtk and gobject functions
#from graph_tool.all import *
#from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

# cm =get_cmap('inferno')
# def getColour (amount,maxAmount,font=False):
#     val = amount/maxAmount;
#     if val>1:
#         val = 1;

#     color = cm.colors[int(255*val)]

#     # If asking for the colour for the font, work out the perceived
#     # luminosity of the colour and then choose white or black
#     # according to how dark or light it is
#     if font:
#         a = ( 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]);
#         if a>0.5:
#             color = (0,0,0)
#         else:
#             color = (1,1,1)
        
#     return color
    
# this is a unidirectional link between two people
class Link:

    def __init__(self, outPerson, inPerson, linkValueToOut, linkValueToIn):
        self.outPerson = outPerson
        self.inPerson = inPerson
        self.linkValueToOut = linkValueToOut
        self.linkValueToIn = linkValueToIn
    
    def output(self):
        print (self.outPerson.personid,"->",self.inPerson.personid,)
        print ("Outval =",self.linkValueToOut,"Inval =",self.linkValueToIn)

# a person (or node) in the network
class Person:
    
    def __init__ (self,personid):

        # this the id of the person
        self.personid = personid

        # the person has a list of its Links to other people
        self.outgoingLinks=list()
        # they also have a dictionary (id -> link) of Links from others
        self.incomingLinks=dict()

        # this is the initial status of the person
        self.status=1.0
        # this is to record the status which is incoming from others
        self.incomingStatus = 0

    def show (self):
        print ("I am person",self.personid)
        print ("I have status",self.status)
        print ("Incoming status is",self.incomingStatus)
        for link in self.outgoingLinks:
            print ("->",link.inPerson.personid)
        print (self.numIncomingLinks,"incoming links")
        print ()

    def getNumLinks(self):
        return len(self.incomingLinks)+len(self.outgoingLinks)
        
    def updateStatus(self):
        status += statusChange
        statusChange = 0

    # This function calculates the outgoing link which is of least
    # value to the individual
    def getWorstLink(self):
        worstlink = None
        worstValue= 1e500
        for link in self.outgoingLinks:
            linkvalue = link.linkValueToOut
            if linkvalue < worstValue:
                worstValue = link.linkValueToOut
                worstlink = link

        return worstlink
    
    def output(self):
        print ("Person",self.personid)
        print ("outgoing")
        for link in self.outgoingLinks:
            link.output();

        print ("incoming")
        for link in self.incomingLinks.values():
            link.output();



class Population:
    # Manages a dictionary (id->person) of people and a list of links
    # between them
    

    def __init__(self, numPeople,numLinks,r=0.2,q=0.9,w=1.0,maxStatus=-1):

        self.numPeople = numPeople
        self.numLinks  = numLinks
        self.q = q
        self.r = r
        self.w = w
        self.noMutualLinks=True
        self.recordLinksVersusStatus = False

        if maxStatus == -1:
            maxStatus = numPeople
        self.maxStatus = maxStatus
        
        self.people = dict()
        self.links = list()

        # to record some data which will later be plotted
        self.numlinksvsstatus=list()

        for i in range (0,self.numPeople):
            self.people[i] = Person(i)

        self.idset = set(self.people.keys())


        # generate a random network
        for pid,person in self.people.items():
            avoidPeople=[person.personid,]
            if self.noMutualLinks:
                for inpersonid in person.incomingLinks.keys():
                    avoidPeople.append(inpersonid)

#            print (avoidPeople)
            if len(avoidPeople) >= self.numPeople:
                raise ("Noone to link to, perhaps too many links for the population?")
            for j in range (0,self.numLinks):
                linkedPerson=self.findIndividualToLinkTo(avoidPeople)
                avoidPeople.append(linkedPerson.personid)
                newlink = Link(outPerson = person, inPerson = linkedPerson, linkValueToOut = 0.1, linkValueToIn = 0.1)
                self.links.append (newlink)
                person.outgoingLinks.append(newlink)
                linkedPerson.incomingLinks[person.personid]=newlink


    # functions for getting random individuals
    def getRandomPerson (self):
        return self.people[random.randint(self.numPeople)]

    def findIndividualToLinkTo (self, avoidPeopleIDs):
        peopleleft = self.idset-set(avoidPeopleIDs)
        newPersonID = random.sample(peopleleft,1)
#        print (avoidPeopleIDs)
#        print (peopleleft)
#        print (newPersonID)
        return self.people[newPersonID[0]]
        

    def showPeople(self):
        for pid,person in self.people.items():
            person.show()

    def updateStatuses(self):
        # reset link values
        for link in self.links:
            link.linkValueToIn = 0.0
            link.linkValueToOut = 0.0
        
        
        for link in self.links:
            outPerson = link.outPerson
            inPerson = link.inPerson

            # Each person takes a proportion r of their status (which
            # will be deducted later) and divides that amongst their
            # links.
            outStatusForLink = self.r*outPerson.status/float(outPerson.getNumLinks())
            inStatusForLInk = self.r*inPerson.status/float(inPerson.getNumLinks())
         
            # The status attributed to each link is divided unevenly
            # between the pair - with a proportion q going to the
            # person who's getting their link
            linkValue = outStatusForLink+inStatusForLInk
            link.linkValueToIn = linkValue*self.q
            link.linkValueToOut = linkValue*(1.0-self.q)

            outPerson.incomingStatus += link.linkValueToOut
            inPerson.incomingStatus += link.linkValueToIn

        for pid,person in self.people.items():
            person.status += person.incomingStatus-self.r*person.status
            person.incomingStatus = 0

    def outputLinksVersusStatus (self):
        # I want to generate a heat map of status / num links
        if self.recordLinksVersusStatus:
            for pid,person in self.people.items():
                numlinks = person.getNumLinks()
                status = person.status
                self.numlinksvsstatus.append((numlinks,status))

#            self.numlinksvsstatus_output.write(str(numlinks)+' '+str(status)+'\n')
    
    def getStatuses (self):
        statuses = []
        for pid,person in self.people.items():
            statuses.append(person.status)
        return statuses

    def getLinkNumbers (self):
        linkNumbers= []
        for pid,person in self.people.items():
            linkNumbers.append(len(person.outgoingLinks)+len(person.incomingLinks))
        return linkNumbers

    
    def rewireLinksNew (self):
        for pid,person in self.people.items():
            for link in person.outgoingLinks:
                linkvalue = link.linkValueToOut

                p_rewire = 0.0

    def rewireLinks (self):

        for pid,person in self.people.items():

            # reWire with random probability w
            if self.w == 1.0 or random.random() < self.w:
            
                #            print ("Person",person.personid,"rewiring from",)

                worstLink = person.getWorstLink()
                personBeingRemoved = worstLink.inPerson
                #            print (personBeingRemoved.personid)

                #           personBeingRemoved.output()


                # In this version, it won't rewire to any of those
                # already linked to (including the person being
                # removed)
                avoidPeople = [person.personid,]
                for link in person.outgoingLinks:
                    avoidPeople.append(link.inPerson.personid)

                if self.noMutualLinks:
                    for inpersonid in person.incomingLinks.keys():
                        avoidPeople.append(inpersonid)
                #            print (pid,avoidPeople)
            
                if len(avoidPeople) < self.numPeople:
                    # Remove this link from the old person's links
                    personBeingRemoved.incomingLinks.pop(pid)

                    newPerson = self.findIndividualToLinkTo(avoidPeople)

                    #update the link and give it to the new person
                    worstLink.inPerson = newPerson
                
                    newPerson.incomingLinks[person.personid]=worstLink

                    # this checks if there is a bug where an invidual has
                    # too many incoming linsk
                    if len(newPerson.incomingLinks) == self.numPeople:
                        print (person.personid)
                        print (avoidPeople)
                        print (newPerson.personid)
                        print (personBeingRemoved.personid)
                        print (worstLink.outPerson.personid, worstLink.inPerson.personid)
                        #               print ("to",newPerson.personid)

    # for debugging purposes
    def findAnomalousIndividual (self):
        for pid,person in self.people.items():
            if person.getNumLinks() > (self.numLinks+self.numPeople-1):
                print ("Person: ",person.personid)
                for link in self.links:
                    if link.outPerson == person or link.inPerson == person:
                        print (link.outPerson.personid,"->",link.inPerson.personid)

    def outputNetwork (self):
        print ("Network")
        for pid,person in self.people.items():
            person.output()
        print ()
        


#print (sys.argv)

parser = argparse.ArgumentParser()
parser.add_argument ('-q',type=float,default=0.5, help="q: level of inequality in the model")
parser.add_argument ('-r',type=float,default=0.2, help="r: rate that status is contributed to others")
parser.add_argument ('-n',type=int,default=20, help="n: number of people")
parser.add_argument ('-l',type=int,default=3, help="l: number of links per person")
parser.add_argument ('-w',type=float,default=1, help="w: chance that a link is rewired")
parser.add_argument ('--plotStatuses',action="store_true", default=False, help="Plot status time trace graph")
parser.add_argument ('--plotLinkNumbers',action="store_true", default=False, help="Plot link number distribution")
parser.add_argument ('--saveLinkNumberPlot',action="store_true", default=False, help="Save link number distribution plot")
parser.add_argument ('--saveLinkNumberData',action="store_true", default=False, help="Save link number data")
parser.add_argument ('--saveFullLinkNumberData',action="store_true", default=False, help="Save full link number data")
parser.add_argument ('--saveStatusData',action="store_true", default=False, help="Save status data")
parser.add_argument ('--tlen',type=int,default=10000, help="Time length")
parser.add_argument ('--seed',type=int,default=-1, help="Random seed")

args = parser.parse_args()

#print (args)

qval = float(args.q)
rval = float(args.r)
nval = int(args.n)
lval = int(args.l)
wval = float(args.w)
tlen = int(args.tlen)
offscreen = True
doplot = bool(args.plotStatuses)
saveStatusData = bool(args.saveStatusData)
doplotLinkNumbers = bool (args.plotLinkNumbers)
saveLinkNumberPlot = bool (args.saveLinkNumberPlot)
saveLinkNumberData = bool (args.saveLinkNumberData)
saveFullLinkNumberData = bool (args.saveFullLinkNumberData)
seed = int(args.seed)
if seed == -1:
    random.seed()
    td=(datetime.datetime.now()-datetime.datetime(2017,1,1,0,0,0,0))
    seed = td.microseconds
    print ("Generating seed = ",seed)

random.seed(seed)

g = None

step = 0.005       # move step
K = 0.5            # preferred edge length

population = Population(nval,lval,rval,qval,wval,maxStatus=6)



statusData=[]
linkData=Counter()
linkValueData = []

t = 0

initialCentreOfMass = zeros(2)

collectStatusData = doplot or saveStatusData
collectLinkNumbers = doplotLinkNumbers or saveLinkNumberData or saveFullLinkNumberData
            
        
for t in range(0,tlen):
    population.updateStatuses()
    population.rewireLinks()
           
    if collectStatusData:
        statuses=population.getStatuses()
        statusData.append(statuses)

    if collectLinkNumbers:
        linkNumbers=population.getLinkNumbers()
        if saveFullLinkNumberData:
            linkValueData.append(linkNumbers)
        for linkNumber in linkNumbers:
            linkData[linkNumber] += 1

        
saveName='_q_'+str(qval)+'_r_'+str(rval)+'_n_'+str(nval)+'_l_'+str(lval)+'_w_'+str(wval)+'_'

adata=None
if collectStatusData:
    adata=array(statusData)
    pickle.dump(adata, open('statuses'+saveName+'.pkl',"wb"))

if doplot:
    figure(1,figsize=(20,10))
#    subplot (1,2,1)
    cla()
    plot (adata,alpha=0.5)
    xlabel('time')
    ylabel('status')

if doplotLinkNumbers:
    pdata = array(linkData.items())
    fig = figure (2,figsize=(20,10))
    cla()
    ax = fig.gca()
    bar (pdata[:,0],pdata[:,1]/float(nval*tlen))
    ax.set_yscale('log')
    oldaxis=axis()
    axis([0,nval,oldaxis[2],oldaxis[3]])
    xlabel('Number of links')
    ylabel('Frequency')
    title(saveName)
    if saveLinkNumberPlot:
        saveLNPName='linkDistribution'+saveName+'.png'
        savefig(saveLNPName)

if saveLinkNumberData:
    pdata = array(linkData.items())
    saveLNDName='linkDistribution'+saveName+'.pkl'
    pickle.dump (pdata, open(saveLNDName,"wb"))

if saveFullLinkNumberData:
    pdata = array(linkValueData)
    saveLNDName='linkNumbers'+saveName+'.pkl'
    pickle.dump (pdata, open(saveLNDName,"wb"))
    
#    subplot (1,2,2)
#    hold(False)
#    lvs=array(population.numlinksvsstatus)
#    plot (lvs[:,0],lvs[:,1],'o',alpha=0.01, markersize=30)
#    xlabel('Number of links')
#    ylabel('Status')
#    savefig('q_'+str(qval)+'_r_'+str(rval)+'_n_'+str(nval)+'_l_'+str(lval)+'_fig.png')

if doplot or (doplotLinkNumbers and not saveLinkNumberPlot):
    show()

