func_begin add
param a
param b
t1 = a + b
return t1
func_end add
func_begin main
param 2
param 3
t2 = call add, 2
x = t2
print x
return 0
func_end main
