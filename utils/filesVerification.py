import os
import shutil
#If the folder 'items' doesn't exist, we create it, and go in
def itemsFolderVerification():
	print("itemsFolder")
    #Absolute path of parent direct
	parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
	print(str(parent_dir))
	#Relative path of "items" folder
	filepathItems = os.path.join(parent_dir, '/items/')
	print(str(filepathItems))
	#filepathItems = '../items/'
 
	#If doesn't exist
	if os.path.exists(filepathItems) == False:
		#Create folder with 511 permission
		os.makedirs(filepathItems, mode = 0o777, exist_ok= False)
	else:
		shutil.rmtree(filepathItems)
		os.makedirs(filepathItems, mode = 0o777, exist_ok= False)
	os.chdir(filepathItems)