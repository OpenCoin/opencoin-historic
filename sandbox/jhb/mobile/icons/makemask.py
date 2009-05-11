import Image,sys
filename = sys.argv[1]
print filename,
base = filename.split('.')[0]
image = Image.open(filename)
width,height = image.size
mask = Image.new('1',image.size)
for x in range(width):
    for y in range(height):
        color = image.getpixel((x,y))
        if sum(color)==0:
            mask.putpixel((x,y),1)
outname = base+'_mask.bmp'
print ' => ',
print outname
mask.save(outname)
