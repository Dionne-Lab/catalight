from NKTP_DLL import *

result = registerWriteU8('COM27', 15, 0x30, 0x00, -1)
print('Setting emission OFF - Extreme:', RegisterResultTypes(result))


