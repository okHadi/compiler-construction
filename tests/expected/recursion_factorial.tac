func_begin fact
param n
t1 = n <= 1
if_false t1 goto L1
return 1
L1:
t2 = n - 1
param t2
t3 = call fact, 1
t4 = n * t3
return t4
func_end fact
func_begin main
param 6
t5 = call fact, 1
print t5
return 0
func_end main
