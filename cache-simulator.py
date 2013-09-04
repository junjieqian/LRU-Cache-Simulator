#!/usr/bin/python

# -----------------------------------------------------------------------------
#  Cache simulation
#  LRU replacement
#  calculate the proportion of BIAS objects in total
# -----------------------------------------------------------------------------

import os
import string
import sys
import linecache

# -----------------------------------------------------------------------------
class g:
   # Global constants
   MEMORY_TIME   = 50 # Number of clocks for read/write
   CACHE_SIZE    = 0  # Number of blocks in cache
   N_WAY         = 2  # For set associative, size of each set

   # Global variables
   cycles        = 0  # Clock cycle count
   inFile        = "" # Filename of input file (cmd line)
   intersizeFile = "" # Filename of inter size file (cmd line)
   addressFile   = "" # Filename of addresses file (cmd line)
   mappingStrat  = 0  # Numeric code for mapping strategy* (cmd line)
   writeStrat    = 0  # Numeric code for write strategy** (cmd line)
   cache         = 0  # Instance of cache class

   hit           = 0  # the total hit numbers
   miss          = 0  # the total miss numbers
   biaslist      = [] # the list used to maintain the bias objects in cache
   biasdict      = {} # the dict contains the bias objects

   # * Mapping Strategy:
   #     1 -> Direct mapped
   #     2 -> Fully associative
   #     3 -> Set associative

   # ** Write Strategy:
   #     1 -> Write through
   #     2 -> Write back

# -----------------------------------------------------------------------------
class Cache:
   """
   Representation of the cache. The cache is represented as a
   dictionary (hash) with the keys being the block numbers and
   the address stored as the value. In addition, there are two
   complementary hashes whose keys are identical to the cache
   blocks. One holds dirty flags for each block, used for the
   write back writing strategy; the other contains LRU values
   for each block, used with the fully associative and set
   associative mapping strategies.
   """
   def __init__(self):
      self.cacheBlocks = {}
      self.dirtyFlags  = {}
      self.lruValue    = {}
      self.clearCache()

   # Zero out cache blocks/flags/values
   def clearCache(self):
      for n in range(g.CACHE_SIZE):
         self.cacheBlocks[n] = 0
         self.dirtyFlags[n]  = 0
         self.lruValue[n]    = 0

   # Check to see if a block is in the cache
   def checkCacheHit(self, address):
      block = self.mapToBlock(address)
      if address == self.cacheBlocks[block]: # Cache hit
         self.incrementLRU(block) # Increase LRU value for this block
         return block
      else:
         return -1

   # Increment specific block LRU value and decrement all
   # others. This represents a simple LRU counting strategy
   def incrementLRU(self, block):
      for n in range(g.CACHE_SIZE): # First, decrement all LRU values
         if self.lruValue[n] > 0 and n != block:
            self.lruValue[n] -= 1

      if self.lruValue[block] < 10: # Then, increment active block (cap is 10)
         self.lruValue[block] += 1

   # Return LRU block from specified slice
   def getLRUBlock(self, dictSlice):
      self.lruSlice = {}

      # Build new dictionary based on slice
      for n in range(dictSlice[0], dictSlice[1]):
         self.lruSlice[n] = self.lruValue[n]

      # Sort LRU values, return first lowest value
      lruValues = self.lruSlice.items()
      lruValues.sort()

      # Sorted list is a list of tuples,
      # so slice out the first of both
      return lruValues[0][0]

   # Store the "data" into the cache
   def storeCacheBlock(self, address, biasdict):
      block = self.mapToBlock(address)

      # Check to see if block is dirty before
      # replacing it. If dirty, write it out to
      # memory before replacement
      if self.isBlockDirty(address) == 1:
         g.cycles += g.MEMORY_TIME
         self.dirtyFlags[block] = 0

      # Return value default is 1
      # If less than 1, means it is the BIAS object's access
      returnvalue = 1
      # Check to see if the block be replaced is biasdict
      if self.cacheBlocks[block] in biasdict:
         if biasdict[self.cacheBlocks[block]] == 0:
            returnvalue = -1
            del biasdict[self.cacheBlocks[block]]

      self.cacheBlocks[block] = address

      return returnvalue

   # Return status of a block's dirty flag
   def isBlockDirty(self, address):
      block = self.mapToBlock(address)

      return self.dirtyFlags[block]

   # Set the dirty flag for a particular address
   def setDirtyFlag(self, address):
      block = self.mapToBlock(address)
      self.dirtyFlags[block] = 1

   # Map memory address to cache block
   def mapToBlock(self, address):
      if g.mappingStrat == 1:   # Direct mapped cache
         return address % g.CACHE_SIZE
      elif g.mappingStrat == 2: # Fully associative cache
         return self.getLRUBlock((0, g.CACHE_SIZE - 1))
      elif g.mappingStrat == 3: # Set associative cache (assume 2-way)
         nWay = g.CACHE_SIZE / g.N_WAY
         set  = address % nWay
         return self.getLRUBlock((set*g.N_WAY, (set*g.N_WAY)+g.N_WAY))

# -----------------------------------------------------------------------------
def readReference(inFile, lineNum):
   """
   Get specified line from input file. The incoming line is
   split into subfields, only two of which are returned. If
   the line does not exist in the file, a zero tuple is
   returned to indicate failure.
   """
   line = linecache.getline(inFile, lineNum)
   if line != '':
      try:
         (rw, addressHex, size) = string.splitfields(line, " ")
         return (rw, int(addressHex, 0))
      except:
         sys.exit("Trace file format: RW-type(0/1) Address Size")
   else:
      return (0, 0)

# -----------------------------------------------------------------------------
def readBias(intersizeFile, addressFile):
   """
   Get the bias objects addresses, only first 0-4 accesses.
   """
   interlist = []
   tmplist = []
   fp = open(intersizeFile, "r")
   for line in fp:
      if line.find("[") == 0:
         tmplist = []
         count = line.count(",")
         if count > 0:
            word = string.split(line, " ")
            tempcoma = string.split(word[0], "[")
            tempaddress = string.split(tempcoma[1], ",")[0]
            tmplist.append(int(tempaddress))
            for n in range(1, count):
               tmplist.append(int(string.split(word[n], ",")[0]))
            temp = string.split(word[count], ']')
            tmplist.append(int(temp[0]))
            interlist.append(tmplist)
         else:
            word = string.split(line, ']')
            tmplist.append(int((string.split(word[0], '['))[1]))
            interlist.append(tmplist)
   fp.close()

   fp = open(addressFile, "r")
   addrlist = []
   for line in fp:
      word = string.split(line, "\n")
      addrlist.append(word[0])
   fp.close()
      
   biasdict = {}
   for i in range(0, 4):
      for j in range(0, len(interlist)):
         try:
            if interlist[j][i] >= 8388608:
               addr = int(addrlist[j], 0)
               biasdict[addr] = i
         except:
            pass

   del interlist[:]
   del addrlist[:]
   del tmplist[:]

   return biasdict

# -----------------------------------------------------------------------------
def printSummary():
   """
   Print results of program execution. This is called at the
   end of the program run to provide a summary of what
   settings were used and the resulting time. In addition,
   the command line number codes are converted to text for
   readability.
   """
   mapping = ""
   write   = ""

   if g.mappingStrat == 1:
      mapping = "Direct mapped"
   elif g.mappingStrat == 2:
      mapping = "Fully associative"
   elif g.mappingStrat == 3:
      mapping = "Set associative"

   if g.writeStrat == 1:
      write = "Write through"
   elif g.writeStrat == 2:
      write = "Write back"

   print "o--------------------------o"
   print "|           Input file:", g.inFile
   print "|       Intersize file:", g.intersizeFile
   print "|         Address file:", g.addressFile
   print "|           Cache size:", repr(g.CACHE_SIZE)
   print "|     Mapping strategy:", mapping
   print "|       Write strategy:", write
   print "|         Clock cycles:", repr(g.cycles)
   print "|           Total hits:", g.hit
   print "|         Total misses:", g.miss
   print "| Most BIAS cache line:", max(g.biaslist)
   print "o--------------------------o"

# =============================================================================
# Everything starts from here
def main():
   """
   Main program; contains primary clock loop and core logic.
   """
   if not len(sys.argv) == 7: # Check for command line arguments
      sys.exit("Usage: %s [ cache size ] [ mapping ] [ write ] [ tracefilename ] [ intersizefilename ] [ addressfilename ] \n" % \
         os.path.basename(sys.argv[0]))

   # Read input file from command line
   g.CACHE_SIZE    = int(sys.argv[1]) # Cache size
   g.mappingStrat  = int(sys.argv[2]) # Cache mapping (1, 2, 3)
   g.writeStrat    = int(sys.argv[3]) # Cache write strategy (1, 2)
   g.inFile        = sys.argv[4]      # Input text file
   g.intersizeFile = sys.argv[5]      # Inter Size file
   g.addressFile   = sys.argv[6]      # Address file

   # Initialize variables
   g.cache  = Cache() # Set instance of cache class
   rw       = ""      # Reference read/write flag
   address  = 0       # Reference address
   line     = 1       # Current line number in input file
   cnt      = 0       # Count of cache lines having BIAS objects in cache
   temp     = 0       # Use this number to compare the cnt number, reduce the memory usage to record biaslist

   # read the bias objects along with occurance index
   g.biasdict = readBias(g.intersizeFile, g.addressFile)

   # Core logic
   while 1:
      # Get references --------------------------------------------------------
      (rw, address) = readReference(g.inFile, line)
      line += 1
      temp = cnt
      if address == 0:
         break # EOF, so shut down

      # For speed, make these function calls once so
      # we can just test the return values
      cacheHit = g.cache.checkCacheHit(address)

      if address in g.biasdict:
         if g.biasdict[address] > 0:
            g.biasdict[address] -= 1
         else:
            cnt += 1
         #   del g.biasdict[address]

      # Read reference --------------------------------------------------------
      if rw == '0':
         if cacheHit > 0:
            # Data is in cache, so move on
            g.hit += 1
            g.cycles += 1
         else:
            # Data is not in cache, so pull it from
            # lower memory and then store it in the
            # cache
            g.miss += 1
            g.cycles += g.MEMORY_TIME
            if g.cache.storeCacheBlock(address, g.biasdict) < 0:
               cnt -= 1

      # Write reference -------------------------------------------------------
      elif rw == '1':
         if g.writeStrat == 1: # <<<----------------------- Write through
            if cacheHit > 0:
               # Write data to block in lower memory
               g.hit += 1
               g.cycles += g.MEMORY_TIME + 1
            else:
               # Data is not in cache, so add it to the
               # cache and then update memory
               g.miss += 1
               if g.cache.storeCacheBlock(address, g.biasdict) < 0:
                  cnt -= 1
               g.cycles += g.MEMORY_TIME + 1
         elif g.writeStrat == 2: # <<<--------------------- Write back
            if cacheHit > 0:
               # Flag block as dirty; this data will
               # be written back out to memory on replacement
               g.hit += 1
               g.cycles += 1
               g.cache.setDirtyFlag(address)
            else:
               # Data is not in cache, so write it to the
               # cache and then flag the block as dirty
               g.miss += 1
               if g.cache.storeCacheBlock(address, g.biasdict) < 0:
                  cnt -= 1
               g.cycles += 1
               g.cache.setDirtyFlag(address)

   # Update the BIAS cache line list
   if temp != cnt:
      g.biaslist.append(cnt)
   # Display results of program run
   printSummary()

if __name__ == "__main__": 
   main()