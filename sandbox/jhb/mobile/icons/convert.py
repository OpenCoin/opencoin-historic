import os, glob
command = 'wine ~/projects/opencoin/bmconv.exe ocicons.mbm '
names = glob.glob('*.bmp')
names.sort()
for name in names:
    if 'mask' in name.lower():
        continue
    base = name.split('.')[0]
    command += "/c24%s.bmp " % base
    command += "%s_mask.bmp " % base
print command    
print os.system(command)
