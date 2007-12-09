#!/usr/bin/env python

#!/usr/bin/env python

import os

commands = ("pyuic4 -o opencoin_ui.py ui/OpenCoin.ui",
	   )
            

for command in commands:
   print command
   os.system(command)

