## this is an underdevelopment feature
import sys, getopt

def main(argv):
   inputfile = ''
   outputfile = ''
   print(argv)
   print(len(argv))
   print(argv[0])

   if(argv[0]=="init"):
      print("inititating....")
      import os,random
      os.mkdir("hello there"+str(random.randint(1,101)))
   try:
      opts, args = getopt.getopt(argv,"h init i:o:",["ifile=","ofile=","init"])
      print(opts)
   except getopt.GetoptError:
      print ('test.py -i <inputfile> -o <outputfile>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print ('test.py -i <inputfile> -o <outputfile>')
         sys.exit()
      elif opt in ("-i", "--ifile"):
         inputfile = arg
      elif opt in ("-o", "--ofile"):
         outputfile = arg
      elif opt == "init":
         print("initaitind ...")
   print ('Input file is "', inputfile)
   print ('Output file is "', outputfile)

if __name__ == "__main__":
   main(sys.argv[1:])
