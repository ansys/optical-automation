Readme Projection grid export

The Intent of the script is to simplify the curves exported by Gridexport feature from SPEOS

Speos exports pixel grid as many single lines to export the data back to catia we need to reduce the line count to a reasonable amount (standart project have about 250k) we need a reduction to atleast 10k
Basic examples delivered as far less curves.

Important requirements:
	Curves shall not be changed in chape-> spline conversion only if shape difference is small-> sharp edges need to be kept
	No curve selection needed-> selecting 250k curves takes  too long
	Curves will be in a specific part
	the less curves the better
	
